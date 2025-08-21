"""Policy evaluation engine for RBAC/ABAC hybrid authorization"""
import time
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import json
from jsonpath_ng import parse
import structlog

from models import (
    User, Role, Resource, Policy, RBACPolicy, ABACPolicy,
    TimeBasedPolicy, AuthorizationRequest, AuthorizationDecision,
    Effect, ConflictResolution, PolicySet, PolicyEvaluationContext,
    PolicyType, Delegation
)

logger = structlog.get_logger()


class PolicyEngine:
    """Core policy evaluation engine"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.policies: Dict[str, Policy] = {}
        self.policy_sets: Dict[str, PolicySet] = {}
        self.permissions: Dict[str, Set[str]] = {}  # role -> permissions
        self.delegations: Dict[str, List[Delegation]] = {}
        self.cache: Dict[str, AuthorizationDecision] = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def evaluate(
        self,
        request: AuthorizationRequest,
        user: User,
        resource: Resource
    ) -> AuthorizationDecision:
        """Evaluate authorization request against all policies"""
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(request)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.utcnow() - cached.timestamp).seconds < self.cache_ttl:
                logger.debug("Cache hit", request_id=request.subject)
                return cached
        
        # Create evaluation context
        context = PolicyEvaluationContext(
            user=user,
            resource=resource,
            action=request.action,
            environment=request.context,
            timestamp=request.timestamp
        )
        
        # Collect all applicable policies
        applicable_policies = await self._get_applicable_policies(context)
        
        # Evaluate policies
        decisions = []
        matched_policies = []
        reasons = []
        
        for policy in applicable_policies:
            decision = await self._evaluate_policy(policy, context)
            if decision is not None:
                decisions.append((policy, decision))
                if decision:
                    matched_policies.append(policy.id)
                    reasons.append(f"Policy {policy.name} allows action")
                else:
                    reasons.append(f"Policy {policy.name} denies action")
        
        # Resolve conflicts
        final_effect = self._resolve_conflicts(decisions)
        
        # Check delegations
        delegated_permissions = await self._check_delegations(user, request)
        if delegated_permissions:
            reasons.append(f"Delegated permissions: {delegated_permissions}")
            if request.action in delegated_permissions:
                final_effect = Effect.ALLOW
        
        # Create decision
        evaluation_time = (time.time() - start_time) * 1000
        decision = AuthorizationDecision(
            allowed=final_effect == Effect.ALLOW,
            effect=final_effect,
            matched_policies=matched_policies,
            evaluation_time_ms=evaluation_time,
            reasons=reasons,
            timestamp=datetime.utcnow()
        )
        
        # Cache decision
        self.cache[cache_key] = decision
        
        logger.info("Authorization decision",
                   allowed=decision.allowed,
                   user=user.username,
                   action=request.action,
                   resource=request.resource,
                   time_ms=evaluation_time)
        
        return decision
    
    async def _get_applicable_policies(
        self,
        context: PolicyEvaluationContext
    ) -> List[Policy]:
        """Get all policies applicable to the context"""
        applicable = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            # Check time-based constraints
            if isinstance(policy, TimeBasedPolicy):
                if not self._check_time_constraints(policy, context.timestamp):
                    continue
            
            # Check policy type applicability
            if policy.type == PolicyType.RBAC:
                if await self._is_rbac_applicable(policy, context):
                    applicable.append(policy)
            elif policy.type == PolicyType.ABAC:
                if await self._is_abac_applicable(policy, context):
                    applicable.append(policy)
            elif policy.type == PolicyType.HYBRID:
                # Hybrid policies are always evaluated
                applicable.append(policy)
        
        # Sort by priority
        applicable.sort(key=lambda p: p.priority, reverse=True)
        
        return applicable
    
    async def _is_rbac_applicable(
        self,
        policy: RBACPolicy,
        context: PolicyEvaluationContext
    ) -> bool:
        """Check if RBAC policy applies to context"""
        # Get user's effective roles (including inherited)
        effective_roles = await self._get_effective_roles(context.user)
        
        # Check if any user role matches policy roles
        for role in policy.roles:
            if role in effective_roles:
                # Check if action matches permissions
                if context.action in policy.permissions:
                    # Check resource constraints if specified
                    if policy.resources:
                        if context.resource.identifier in policy.resources:
                            return True
                    else:
                        return True
        
        return False
    
    async def _is_abac_applicable(
        self,
        policy: ABACPolicy,
        context: PolicyEvaluationContext
    ) -> bool:
        """Check if ABAC policy applies to context"""
        # Check subject attributes
        if not self._match_attributes(
            context.user.attributes,
            policy.subject_attributes
        ):
            return False
        
        # Check resource attributes
        if not self._match_attributes(
            context.resource.attributes,
            policy.resource_attributes
        ):
            return False
        
        # Check action attributes
        if policy.action_attributes:
            action_attrs = {"name": context.action}
            if not self._match_attributes(action_attrs, policy.action_attributes):
                return False
        
        # Check environment attributes
        if not self._match_attributes(
            context.environment,
            policy.environment_attributes
        ):
            return False
        
        # Evaluate custom conditions if present
        if policy.conditions:
            return self._evaluate_conditions(policy.conditions, context)
        
        return True
    
    def _match_attributes(
        self,
        actual: Dict[str, Any],
        required: Dict[str, Any]
    ) -> bool:
        """Match attributes using various operators"""
        for key, value in required.items():
            if isinstance(value, dict):
                # Complex matching with operators
                operator = value.get('operator', 'equals')
                expected = value.get('value')
                
                if operator == 'equals':
                    if actual.get(key) != expected:
                        return False
                elif operator == 'contains':
                    if expected not in actual.get(key, []):
                        return False
                elif operator == 'greater_than':
                    if actual.get(key, 0) <= expected:
                        return False
                elif operator == 'less_than':
                    if actual.get(key, float('inf')) >= expected:
                        return False
                elif operator == 'in':
                    if actual.get(key) not in expected:
                        return False
                elif operator == 'regex':
                    import re
                    if not re.match(expected, str(actual.get(key, ''))):
                        return False
            else:
                # Simple equality check
                if actual.get(key) != value:
                    return False
        
        return True
    
    def _evaluate_conditions(
        self,
        conditions: str,
        context: PolicyEvaluationContext
    ) -> bool:
        """Evaluate custom conditions using JSONPath"""
        try:
            # Create context dict for JSONPath evaluation
            ctx_dict = {
                "user": context.user.dict(),
                "resource": context.resource.dict(),
                "action": context.action,
                "environment": context.environment
            }
            
            # Parse and evaluate JSONPath expression
            jsonpath_expr = parse(conditions)
            matches = jsonpath_expr.find(ctx_dict)
            
            # If matches found, condition is true
            return len(matches) > 0
        except Exception as e:
            logger.error("Condition evaluation failed", error=str(e))
            return False
    
    async def _evaluate_policy(
        self,
        policy: Policy,
        context: PolicyEvaluationContext
    ) -> Optional[bool]:
        """Evaluate a single policy"""
        if policy.type == PolicyType.RBAC:
            result = await self._evaluate_rbac_policy(policy, context)
        elif policy.type == PolicyType.ABAC:
            result = await self._evaluate_abac_policy(policy, context)
        else:
            # Hybrid evaluation
            result = await self._evaluate_hybrid_policy(policy, context)
        
        if result:
            return policy.effect == Effect.ALLOW
        
        return None
    
    async def _evaluate_rbac_policy(
        self,
        policy: RBACPolicy,
        context: PolicyEvaluationContext
    ) -> bool:
        """Evaluate RBAC policy"""
        effective_roles = await self._get_effective_roles(context.user)
        
        for role in policy.roles:
            if role in effective_roles:
                if context.action in policy.permissions:
                    if policy.resources:
                        return context.resource.identifier in policy.resources
                    return True
        
        return False
    
    async def _evaluate_abac_policy(
        self,
        policy: ABACPolicy,
        context: PolicyEvaluationContext
    ) -> bool:
        """Evaluate ABAC policy"""
        # Already checked applicability, so if we're here, it matches
        return True
    
    async def _evaluate_hybrid_policy(
        self,
        policy: Policy,
        context: PolicyEvaluationContext
    ) -> bool:
        """Evaluate hybrid RBAC/ABAC policy"""
        # Combine both RBAC and ABAC evaluation
        # This is a simplified implementation
        return True
    
    async def _get_effective_roles(self, user: User) -> Set[str]:
        """Get all effective roles including inherited ones"""
        effective_roles = set(user.roles)
        
        # Add inherited roles
        to_process = list(user.roles)
        processed = set()
        
        while to_process:
            role_id = to_process.pop(0)
            if role_id in processed:
                continue
            
            processed.add(role_id)
            
            if role_id in self.roles:
                role = self.roles[role_id]
                for parent in role.parent_roles:
                    if parent not in effective_roles:
                        effective_roles.add(parent)
                        to_process.append(parent)
        
        return effective_roles
    
    async def _check_delegations(
        self,
        user: User,
        request: AuthorizationRequest
    ) -> Set[str]:
        """Check delegated permissions"""
        delegated_perms = set()
        
        # Check if user has any delegations
        if user.id in self.delegations:
            for delegation in self.delegations[user.id]:
                if delegation.revoked:
                    continue
                
                # Check time validity
                now = datetime.utcnow()
                if delegation.valid_until and now > delegation.valid_until:
                    continue
                
                if now >= delegation.valid_from:
                    delegated_perms.update(delegation.permissions)
        
        return delegated_perms
    
    def _resolve_conflicts(
        self,
        decisions: List[Tuple[Policy, bool]]
    ) -> Effect:
        """Resolve policy conflicts based on conflict resolution strategy"""
        if not decisions:
            return Effect.DENY  # Default deny
        
        # Get conflict resolution strategy (default: deny_overrides)
        strategy = ConflictResolution.DENY_OVERRIDES
        
        allows = [p for p, d in decisions if d]
        denies = [p for p, d in decisions if not d]
        
        if strategy == ConflictResolution.DENY_OVERRIDES:
            return Effect.DENY if denies else Effect.ALLOW
        elif strategy == ConflictResolution.ALLOW_OVERRIDES:
            return Effect.ALLOW if allows else Effect.DENY
        elif strategy == ConflictResolution.FIRST_MATCH:
            return Effect.ALLOW if decisions[0][1] else Effect.DENY
        elif strategy == ConflictResolution.PRIORITY_BASED:
            # Already sorted by priority
            return Effect.ALLOW if decisions[0][1] else Effect.DENY
        
        return Effect.DENY
    
    def _check_time_constraints(
        self,
        policy: TimeBasedPolicy,
        timestamp: datetime
    ) -> bool:
        """Check if policy is valid at given time"""
        if policy.valid_from and timestamp < policy.valid_from:
            return False
        
        if policy.valid_until and timestamp > policy.valid_until:
            return False
        
        if policy.time_constraints:
            # Check weekday constraints
            if 'weekdays' in policy.time_constraints:
                if timestamp.weekday() not in policy.time_constraints['weekdays']:
                    return False
            
            # Check hour constraints
            if 'hours' in policy.time_constraints:
                hour_range = policy.time_constraints['hours']
                current_hour = timestamp.hour
                if len(hour_range) == 2:
                    if not (hour_range[0] <= current_hour < hour_range[1]):
                        return False
        
        return True
    
    def _get_cache_key(self, request: AuthorizationRequest) -> str:
        """Generate cache key for request"""
        return f"{request.subject}:{request.action}:{request.resource}"
    
    async def add_policy(self, policy: Policy):
        """Add or update a policy"""
        self.policies[policy.id] = policy
        logger.info("Policy added/updated", policy_id=policy.id, name=policy.name)
    
    async def remove_policy(self, policy_id: str):
        """Remove a policy"""
        if policy_id in self.policies:
            del self.policies[policy_id]
            logger.info("Policy removed", policy_id=policy_id)
    
    async def add_role(self, role: Role):
        """Add or update a role"""
        self.roles[role.id] = role
        logger.info("Role added/updated", role_id=role.id, name=role.name)
    
    async def add_delegation(self, delegation: Delegation):
        """Add a delegation"""
        if delegation.delegate not in self.delegations:
            self.delegations[delegation.delegate] = []
        
        self.delegations[delegation.delegate].append(delegation)
        logger.info("Delegation added", 
                   delegator=delegation.delegator,
                   delegate=delegation.delegate)
    
    def clear_cache(self):
        """Clear the decision cache"""
        self.cache.clear()
        logger.info("Cache cleared")