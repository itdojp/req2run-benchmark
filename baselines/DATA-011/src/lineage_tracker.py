"""Data Lineage Tracking"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import uuid

import structlog

logger = structlog.get_logger()


@dataclass
class DataAsset:
    """Represents a data asset in lineage"""
    asset_id: str
    name: str
    asset_type: str  # table, file, stream, api
    location: str
    schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "name": self.name,
            "asset_type": self.asset_type,
            "location": self.location,
            "schema": self.schema,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class LineageOperation:
    """Represents an operation in data lineage"""
    operation_id: str
    operation_type: str  # extract, transform, load, join, filter, aggregate
    description: str
    inputs: List[str]  # Asset IDs
    outputs: List[str]  # Asset IDs
    transformations: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    executed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "description": self.description,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "transformations": self.transformations,
            "metadata": self.metadata,
            "executed_at": self.executed_at.isoformat()
        }


class LineageTracker:
    """Track data lineage throughout the pipeline"""
    
    def __init__(self):
        self.assets: Dict[str, DataAsset] = {}
        self.operations: Dict[str, LineageOperation] = {}
        self.lineage_graph: Dict[str, Set[str]] = {}  # asset_id -> set of dependent asset_ids
        self.reverse_lineage: Dict[str, Set[str]] = {}  # asset_id -> set of source asset_ids
    
    def register_asset(self, asset: DataAsset) -> str:
        """Register a data asset"""
        if not asset.asset_id:
            asset.asset_id = str(uuid.uuid4())
        
        self.assets[asset.asset_id] = asset
        
        # Initialize graph nodes
        if asset.asset_id not in self.lineage_graph:
            self.lineage_graph[asset.asset_id] = set()
        if asset.asset_id not in self.reverse_lineage:
            self.reverse_lineage[asset.asset_id] = set()
        
        logger.info(f"Registered asset", asset_id=asset.asset_id, name=asset.name)
        return asset.asset_id
    
    def track_operation(self, operation: LineageOperation) -> str:
        """Track a data operation"""
        if not operation.operation_id:
            operation.operation_id = str(uuid.uuid4())
        
        self.operations[operation.operation_id] = operation
        
        # Update lineage graph
        for output_id in operation.outputs:
            if output_id not in self.lineage_graph:
                self.lineage_graph[output_id] = set()
            
            for input_id in operation.inputs:
                # Forward lineage: input -> output
                if input_id not in self.lineage_graph:
                    self.lineage_graph[input_id] = set()
                self.lineage_graph[input_id].add(output_id)
                
                # Reverse lineage: output -> input
                if output_id not in self.reverse_lineage:
                    self.reverse_lineage[output_id] = set()
                self.reverse_lineage[output_id].add(input_id)
        
        logger.info(f"Tracked operation", 
                   operation_id=operation.operation_id,
                   type=operation.operation_type,
                   inputs=len(operation.inputs),
                   outputs=len(operation.outputs))
        
        return operation.operation_id
    
    def get_downstream_lineage(self, asset_id: str, max_depth: int = -1) -> Dict[str, Any]:
        """Get downstream lineage for an asset"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        visited = set()
        lineage = self._trace_downstream(asset_id, visited, 0, max_depth)
        
        return {
            "root_asset": self.assets[asset_id].to_dict(),
            "downstream": lineage
        }
    
    def _trace_downstream(self, asset_id: str, visited: Set[str], depth: int, max_depth: int) -> List[Dict[str, Any]]:
        """Recursively trace downstream lineage"""
        if asset_id in visited or (max_depth >= 0 and depth >= max_depth):
            return []
        
        visited.add(asset_id)
        downstream = []
        
        for dependent_id in self.lineage_graph.get(asset_id, set()):
            if dependent_id in self.assets:
                asset_info = {
                    "asset": self.assets[dependent_id].to_dict(),
                    "depth": depth + 1,
                    "operations": self._get_operations_between(asset_id, dependent_id)
                }
                
                # Recursively get downstream
                asset_info["downstream"] = self._trace_downstream(
                    dependent_id, visited, depth + 1, max_depth
                )
                
                downstream.append(asset_info)
        
        return downstream
    
    def get_upstream_lineage(self, asset_id: str, max_depth: int = -1) -> Dict[str, Any]:
        """Get upstream lineage for an asset"""
        if asset_id not in self.assets:
            raise ValueError(f"Asset {asset_id} not found")
        
        visited = set()
        lineage = self._trace_upstream(asset_id, visited, 0, max_depth)
        
        return {
            "root_asset": self.assets[asset_id].to_dict(),
            "upstream": lineage
        }
    
    def _trace_upstream(self, asset_id: str, visited: Set[str], depth: int, max_depth: int) -> List[Dict[str, Any]]:
        """Recursively trace upstream lineage"""
        if asset_id in visited or (max_depth >= 0 and depth >= max_depth):
            return []
        
        visited.add(asset_id)
        upstream = []
        
        for source_id in self.reverse_lineage.get(asset_id, set()):
            if source_id in self.assets:
                asset_info = {
                    "asset": self.assets[source_id].to_dict(),
                    "depth": depth + 1,
                    "operations": self._get_operations_between(source_id, asset_id)
                }
                
                # Recursively get upstream
                asset_info["upstream"] = self._trace_upstream(
                    source_id, visited, depth + 1, max_depth
                )
                
                upstream.append(asset_info)
        
        return upstream
    
    def _get_operations_between(self, source_id: str, target_id: str) -> List[Dict[str, Any]]:
        """Get operations between two assets"""
        operations = []
        
        for op in self.operations.values():
            if source_id in op.inputs and target_id in op.outputs:
                operations.append(op.to_dict())
        
        return operations
    
    def get_impact_analysis(self, asset_id: str) -> Dict[str, Any]:
        """Analyze impact of changes to an asset"""
        downstream = self.get_downstream_lineage(asset_id)
        
        # Count affected assets
        affected_assets = set()
        
        def count_affected(lineage_data: List[Dict[str, Any]]):
            for item in lineage_data:
                affected_assets.add(item["asset"]["asset_id"])
                if "downstream" in item:
                    count_affected(item["downstream"])
        
        if "downstream" in downstream:
            count_affected(downstream["downstream"])
        
        # Categorize by type
        affected_by_type = {}
        for affected_id in affected_assets:
            if affected_id in self.assets:
                asset_type = self.assets[affected_id].asset_type
                if asset_type not in affected_by_type:
                    affected_by_type[asset_type] = []
                affected_by_type[asset_type].append(self.assets[affected_id].name)
        
        return {
            "source_asset": self.assets[asset_id].to_dict(),
            "total_affected": len(affected_assets),
            "affected_by_type": affected_by_type,
            "critical_paths": self._find_critical_paths(asset_id)
        }
    
    def _find_critical_paths(self, asset_id: str) -> List[List[str]]:
        """Find critical paths in lineage"""
        # Simplified: Find all paths from asset to leaf nodes
        paths = []
        
        def dfs(current_id: str, path: List[str]):
            path = path + [current_id]
            
            dependents = self.lineage_graph.get(current_id, set())
            if not dependents:
                # Leaf node
                paths.append(path)
            else:
                for dependent_id in dependents:
                    if dependent_id not in path:  # Avoid cycles
                        dfs(dependent_id, path)
        
        dfs(asset_id, [])
        
        # Return top 5 longest paths
        paths.sort(key=len, reverse=True)
        return paths[:5]
    
    def get_data_flow_diagram(self) -> Dict[str, Any]:
        """Generate data flow diagram representation"""
        nodes = []
        edges = []
        
        # Add asset nodes
        for asset_id, asset in self.assets.items():
            nodes.append({
                "id": asset_id,
                "label": asset.name,
                "type": asset.asset_type,
                "metadata": asset.metadata
            })
        
        # Add edges from lineage
        for source_id, targets in self.lineage_graph.items():
            for target_id in targets:
                # Find operations for this edge
                operations = self._get_operations_between(source_id, target_id)
                
                edges.append({
                    "source": source_id,
                    "target": target_id,
                    "operations": [op["operation_type"] for op in operations]
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": self.get_statistics()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get lineage statistics"""
        # Calculate connectivity metrics
        connected_assets = set()
        for source_id, targets in self.lineage_graph.items():
            connected_assets.add(source_id)
            connected_assets.update(targets)
        
        # Find isolated assets
        isolated_assets = set(self.assets.keys()) - connected_assets
        
        # Count by type
        assets_by_type = {}
        for asset in self.assets.values():
            if asset.asset_type not in assets_by_type:
                assets_by_type[asset.asset_type] = 0
            assets_by_type[asset.asset_type] += 1
        
        # Count operations by type
        operations_by_type = {}
        for op in self.operations.values():
            if op.operation_type not in operations_by_type:
                operations_by_type[op.operation_type] = 0
            operations_by_type[op.operation_type] += 1
        
        return {
            "total_assets": len(self.assets),
            "total_operations": len(self.operations),
            "connected_assets": len(connected_assets),
            "isolated_assets": len(isolated_assets),
            "assets_by_type": assets_by_type,
            "operations_by_type": operations_by_type,
            "average_dependencies": sum(len(deps) for deps in self.lineage_graph.values()) / max(len(self.lineage_graph), 1)
        }
    
    def export_lineage(self, format: str = "json") -> str:
        """Export lineage in specified format"""
        if format == "json":
            return json.dumps({
                "assets": {k: v.to_dict() for k, v in self.assets.items()},
                "operations": {k: v.to_dict() for k, v in self.operations.items()},
                "lineage_graph": {k: list(v) for k, v in self.lineage_graph.items()},
                "reverse_lineage": {k: list(v) for k, v in self.reverse_lineage.items()}
            }, indent=2)
        elif format == "dot":
            # GraphViz DOT format
            dot = "digraph DataLineage {\n"
            dot += "  rankdir=LR;\n"
            
            # Add nodes
            for asset_id, asset in self.assets.items():
                label = f"{asset.name}\\n({asset.asset_type})"
                dot += f'  "{asset_id}" [label="{label}"];\n'
            
            # Add edges
            for source_id, targets in self.lineage_graph.items():
                for target_id in targets:
                    dot += f'  "{source_id}" -> "{target_id}";\n'
            
            dot += "}\n"
            return dot
        else:
            raise ValueError(f"Unsupported format: {format}")