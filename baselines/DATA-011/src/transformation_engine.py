"""Data Transformation Engine"""
import json
import re
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
import hashlib

import pandas as pd
from jinja2 import Template, Environment, meta
from jsonschema import validate, ValidationError
import structlog

logger = structlog.get_logger()


@dataclass
class TransformationRule:
    """Defines a transformation rule"""
    rule_id: str
    name: str
    rule_type: str  # map, filter, aggregate, join, custom
    source_fields: List[str]
    target_field: Optional[str]
    expression: Optional[str]
    conditions: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    
    def validate(self) -> bool:
        """Validate transformation rule"""
        if self.rule_type not in ["map", "filter", "aggregate", "join", "custom"]:
            return False
        
        if self.rule_type == "map" and not self.target_field:
            return False
        
        return True


class TransformationEngine:
    """Engine for data transformations"""
    
    def __init__(self):
        self.rules: Dict[str, TransformationRule] = {}
        self.custom_functions: Dict[str, Callable] = {}
        self.jinja_env = Environment()
        self.statistics: Dict[str, int] = {
            "total_transformed": 0,
            "total_filtered": 0,
            "total_errors": 0
        }
    
    def add_rule(self, rule: TransformationRule):
        """Add transformation rule"""
        if not rule.validate():
            raise ValueError(f"Invalid transformation rule: {rule.rule_id}")
        
        self.rules[rule.rule_id] = rule
        logger.info(f"Added transformation rule", rule_id=rule.rule_id, type=rule.rule_type)
    
    def register_custom_function(self, name: str, func: Callable):
        """Register custom transformation function"""
        self.custom_functions[name] = func
        self.jinja_env.globals[name] = func
    
    async def transform(self, data: Dict[str, Any], rules: Optional[List[str]] = None) -> Dict[str, Any]:
        """Apply transformations to data"""
        result = data.copy()
        
        # Get rules to apply
        rules_to_apply = rules if rules else list(self.rules.keys())
        
        for rule_id in rules_to_apply:
            if rule_id not in self.rules:
                logger.warning(f"Rule not found", rule_id=rule_id)
                continue
            
            rule = self.rules[rule_id]
            
            try:
                # Check conditions
                if rule.conditions and not self._check_conditions(result, rule.conditions):
                    continue
                
                # Apply transformation based on type
                if rule.rule_type == "map":
                    result = await self._apply_map(result, rule)
                elif rule.rule_type == "filter":
                    if not await self._apply_filter(result, rule):
                        self.statistics["total_filtered"] += 1
                        return None
                elif rule.rule_type == "aggregate":
                    result = await self._apply_aggregate(result, rule)
                elif rule.rule_type == "custom":
                    result = await self._apply_custom(result, rule)
                
                self.statistics["total_transformed"] += 1
                
            except Exception as e:
                logger.error(f"Transformation error", rule_id=rule_id, error=str(e))
                self.statistics["total_errors"] += 1
                
                if rule.parameters and rule.parameters.get("on_error") == "skip":
                    continue
                else:
                    raise
        
        return result
    
    def _check_conditions(self, data: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Check if conditions are met"""
        for field, condition in conditions.items():
            value = self._get_nested_value(data, field)
            
            if isinstance(condition, dict):
                operator = condition.get("operator", "equals")
                expected = condition.get("value")
                
                if operator == "equals" and value != expected:
                    return False
                elif operator == "not_equals" and value == expected:
                    return False
                elif operator == "greater_than" and value <= expected:
                    return False
                elif operator == "less_than" and value >= expected:
                    return False
                elif operator == "contains" and expected not in str(value):
                    return False
                elif operator == "regex":
                    if not re.match(expected, str(value)):
                        return False
            else:
                # Simple equality check
                if value != condition:
                    return False
        
        return True
    
    async def _apply_map(self, data: Dict[str, Any], rule: TransformationRule) -> Dict[str, Any]:
        """Apply mapping transformation"""
        result = data.copy()
        
        if rule.expression:
            # Use Jinja2 template for expression
            template = self.jinja_env.from_string(rule.expression)
            
            # Prepare context with source fields
            context = {}
            for field in rule.source_fields:
                context[field.replace(".", "_")] = self._get_nested_value(data, field)
            
            # Add custom functions to context
            context.update(self.custom_functions)
            
            # Evaluate expression
            value = template.render(**context)
            
            # Try to parse result
            try:
                value = json.loads(value)
            except:
                pass  # Keep as string
            
            # Set target field
            self._set_nested_value(result, rule.target_field, value)
        else:
            # Simple field mapping
            if len(rule.source_fields) == 1:
                value = self._get_nested_value(data, rule.source_fields[0])
                self._set_nested_value(result, rule.target_field, value)
        
        return result
    
    async def _apply_filter(self, data: Dict[str, Any], rule: TransformationRule) -> bool:
        """Apply filter transformation"""
        if rule.expression:
            template = self.jinja_env.from_string(rule.expression)
            
            context = {}
            for field in rule.source_fields:
                context[field.replace(".", "_")] = self._get_nested_value(data, field)
            
            result = template.render(**context)
            
            # Convert to boolean
            return result.lower() in ["true", "1", "yes"]
        
        return True
    
    async def _apply_aggregate(self, data: Dict[str, Any], rule: TransformationRule) -> Dict[str, Any]:
        """Apply aggregation transformation"""
        result = data.copy()
        
        # Get values to aggregate
        values = []
        for field in rule.source_fields:
            value = self._get_nested_value(data, field)
            if value is not None:
                values.append(value)
        
        if not values:
            return result
        
        # Apply aggregation based on parameters
        agg_type = rule.parameters.get("type", "sum") if rule.parameters else "sum"
        
        if agg_type == "sum":
            agg_value = sum(values)
        elif agg_type == "avg":
            agg_value = sum(values) / len(values)
        elif agg_type == "min":
            agg_value = min(values)
        elif agg_type == "max":
            agg_value = max(values)
        elif agg_type == "count":
            agg_value = len(values)
        elif agg_type == "concat":
            separator = rule.parameters.get("separator", "") if rule.parameters else ""
            agg_value = separator.join(str(v) for v in values)
        else:
            agg_value = values
        
        if rule.target_field:
            self._set_nested_value(result, rule.target_field, agg_value)
        
        return result
    
    async def _apply_custom(self, data: Dict[str, Any], rule: TransformationRule) -> Dict[str, Any]:
        """Apply custom transformation"""
        func_name = rule.parameters.get("function") if rule.parameters else None
        
        if func_name and func_name in self.custom_functions:
            func = self.custom_functions[func_name]
            return await func(data, rule) if asyncio.iscoroutinefunction(func) else func(data, rule)
        
        return data
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dict using dot notation"""
        keys = path.split(".")
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value


class SchemaEvolution:
    """Handle schema evolution and compatibility"""
    
    def __init__(self):
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.compatibility_mode = "BACKWARD"  # BACKWARD, FORWARD, FULL, NONE
    
    def register_schema(self, name: str, version: int, schema: Dict[str, Any]):
        """Register a schema version"""
        if name not in self.schemas:
            self.schemas[name] = {}
        
        self.schemas[name][version] = schema
        logger.info(f"Registered schema", name=name, version=version)
    
    def check_compatibility(self, name: str, new_schema: Dict[str, Any]) -> bool:
        """Check if new schema is compatible"""
        if name not in self.schemas or not self.schemas[name]:
            return True  # No existing schema
        
        # Get latest version
        latest_version = max(self.schemas[name].keys())
        latest_schema = self.schemas[name][latest_version]
        
        if self.compatibility_mode == "NONE":
            return True
        elif self.compatibility_mode == "BACKWARD":
            return self._check_backward_compatibility(latest_schema, new_schema)
        elif self.compatibility_mode == "FORWARD":
            return self._check_forward_compatibility(latest_schema, new_schema)
        elif self.compatibility_mode == "FULL":
            return (self._check_backward_compatibility(latest_schema, new_schema) and
                   self._check_forward_compatibility(latest_schema, new_schema))
        
        return False
    
    def _check_backward_compatibility(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> bool:
        """Check if new schema can read old data"""
        # Simplified check: all required fields in old schema must exist in new
        old_required = old_schema.get("required", [])
        new_properties = new_schema.get("properties", {})
        
        for field in old_required:
            if field not in new_properties:
                return False
        
        return True
    
    def _check_forward_compatibility(self, old_schema: Dict[str, Any], new_schema: Dict[str, Any]) -> bool:
        """Check if old schema can read new data"""
        # Simplified check: all required fields in new schema must exist in old
        new_required = new_schema.get("required", [])
        old_properties = old_schema.get("properties", {})
        
        for field in new_required:
            if field not in old_properties:
                return False
        
        return True
    
    def evolve_data(self, data: Dict[str, Any], from_version: int, to_version: int, schema_name: str) -> Dict[str, Any]:
        """Evolve data from one schema version to another"""
        if from_version == to_version:
            return data
        
        result = data.copy()
        
        # Apply migrations between versions
        if from_version < to_version:
            # Forward migration
            for version in range(from_version + 1, to_version + 1):
                result = self._migrate_forward(result, schema_name, version)
        else:
            # Backward migration
            for version in range(from_version, to_version, -1):
                result = self._migrate_backward(result, schema_name, version)
        
        return result
    
    def _migrate_forward(self, data: Dict[str, Any], schema_name: str, version: int) -> Dict[str, Any]:
        """Migrate data forward to newer version"""
        # Add default values for new fields
        if schema_name in self.schemas and version in self.schemas[schema_name]:
            schema = self.schemas[schema_name][version]
            properties = schema.get("properties", {})
            
            for field, field_schema in properties.items():
                if field not in data and "default" in field_schema:
                    data[field] = field_schema["default"]
        
        return data
    
    def _migrate_backward(self, data: Dict[str, Any], schema_name: str, version: int) -> Dict[str, Any]:
        """Migrate data backward to older version"""
        # Remove fields not in older schema
        if schema_name in self.schemas and version in self.schemas[schema_name]:
            schema = self.schemas[schema_name][version]
            properties = schema.get("properties", {})
            
            # Keep only fields that exist in target schema
            return {k: v for k, v in data.items() if k in properties}
        
        return data


class DataQualityChecker:
    """Check data quality"""
    
    def __init__(self):
        self.rules: List[Dict[str, Any]] = []
        self.statistics: Dict[str, int] = {
            "total_checked": 0,
            "total_passed": 0,
            "total_failed": 0
        }
    
    def add_rule(self, rule: Dict[str, Any]):
        """Add quality check rule"""
        self.rules.append(rule)
    
    async def check(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Check data quality"""
        issues = []
        self.statistics["total_checked"] += 1
        
        for rule in self.rules:
            rule_type = rule.get("type")
            
            if rule_type == "required":
                field = rule.get("field")
                if not self._has_value(data, field):
                    issues.append(f"Required field missing: {field}")
            
            elif rule_type == "type":
                field = rule.get("field")
                expected_type = rule.get("expected")
                actual_value = self._get_value(data, field)
                
                if actual_value is not None:
                    if expected_type == "integer" and not isinstance(actual_value, int):
                        issues.append(f"Field {field} should be integer")
                    elif expected_type == "string" and not isinstance(actual_value, str):
                        issues.append(f"Field {field} should be string")
                    elif expected_type == "number" and not isinstance(actual_value, (int, float)):
                        issues.append(f"Field {field} should be number")
            
            elif rule_type == "range":
                field = rule.get("field")
                min_val = rule.get("min")
                max_val = rule.get("max")
                value = self._get_value(data, field)
                
                if value is not None:
                    if min_val is not None and value < min_val:
                        issues.append(f"Field {field} below minimum: {value} < {min_val}")
                    if max_val is not None and value > max_val:
                        issues.append(f"Field {field} above maximum: {value} > {max_val}")
            
            elif rule_type == "pattern":
                field = rule.get("field")
                pattern = rule.get("pattern")
                value = self._get_value(data, field)
                
                if value is not None and not re.match(pattern, str(value)):
                    issues.append(f"Field {field} doesn't match pattern: {pattern}")
            
            elif rule_type == "unique":
                # Would need to track seen values
                pass
        
        if issues:
            self.statistics["total_failed"] += 1
            return False, issues
        else:
            self.statistics["total_passed"] += 1
            return True, []
    
    def _has_value(self, data: Dict[str, Any], field: str) -> bool:
        """Check if field has a value"""
        value = self._get_value(data, field)
        return value is not None and value != ""
    
    def _get_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get field value from data"""
        keys = field.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value


import asyncio
from typing import Tuple