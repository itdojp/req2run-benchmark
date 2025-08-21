"""Data models for RBAC/ABAC hybrid authorization system"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field, validator
import uuid


class Effect(str, Enum):
    """Policy effect enumeration"""
    ALLOW = "allow"
    DENY = "deny"


class ConflictResolution(str, Enum):
    """Policy conflict resolution strategies"""
    DENY_OVERRIDES = "deny_overrides"
    ALLOW_OVERRIDES = "allow_overrides"
    FIRST_MATCH = "first_match"
    PRIORITY_BASED = "priority_based"


class PolicyType(str, Enum):
    """Policy type enumeration"""
    RBAC = "rbac"
    ABAC = "abac"
    HYBRID = "hybrid"


class Role(BaseModel):
    """Role model for RBAC"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    parent_roles: List[str] = Field(default_factory=list)  # For role hierarchy
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Role name must be alphanumeric with underscores/hyphens')
        return v


class User(BaseModel):
    """User model with roles and attributes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    roles: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    delegated_permissions: Dict[str, List[str]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True


class Resource(BaseModel):
    """Resource model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    identifier: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    owner: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Action(BaseModel):
    """Action model"""
    name: str
    resource_type: str
    description: Optional[str] = None


class Policy(BaseModel):
    """Base policy model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: PolicyType
    priority: int = Field(default=0, ge=0, le=1000)
    enabled: bool = True
    effect: Effect
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RBACPolicy(Policy):
    """RBAC-specific policy"""
    type: PolicyType = PolicyType.RBAC
    roles: List[str]
    permissions: List[str]
    resources: Optional[List[str]] = None


class ABACPolicy(Policy):
    """ABAC-specific policy with attribute conditions"""
    type: PolicyType = PolicyType.ABAC
    subject_attributes: Dict[str, Any] = Field(default_factory=dict)
    resource_attributes: Dict[str, Any] = Field(default_factory=dict)
    action_attributes: Dict[str, Any] = Field(default_factory=dict)
    environment_attributes: Dict[str, Any] = Field(default_factory=dict)
    conditions: Optional[str] = None  # JSONPATH or custom DSL expression


class TimeBasedPolicy(Policy):
    """Time-based policy with temporal constraints"""
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    time_constraints: Optional[Dict[str, Any]] = None  # e.g., {"weekdays": [1,2,3,4,5], "hours": [9,17]}


class AuthorizationRequest(BaseModel):
    """Authorization request model"""
    subject: str  # User ID or principal
    action: str
    resource: str
    context: Dict[str, Any] = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuthorizationDecision(BaseModel):
    """Authorization decision model"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    allowed: bool
    effect: Effect
    matched_policies: List[str] = Field(default_factory=list)
    evaluation_time_ms: float
    reasons: List[str] = Field(default_factory=list)
    obligations: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    """Audit log entry for authorization decisions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request: AuthorizationRequest
    decision: AuthorizationDecision
    user_id: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PolicySet(BaseModel):
    """Collection of policies with composition rules"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    policies: List[str] = Field(default_factory=list)
    conflict_resolution: ConflictResolution = ConflictResolution.DENY_OVERRIDES
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Permission(BaseModel):
    """Permission model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    resource_type: str
    actions: List[str]
    constraints: Optional[Dict[str, Any]] = None
    description: Optional[str] = None


class Delegation(BaseModel):
    """Permission delegation model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    delegator: str  # User who delegates
    delegate: str   # User who receives delegation
    permissions: List[str]
    constraints: Optional[Dict[str, Any]] = None
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    revoked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyEvaluationContext(BaseModel):
    """Context for policy evaluation"""
    user: User
    resource: Resource
    action: str
    environment: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthStatus(BaseModel):
    """Health check status"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    components: Dict[str, str] = Field(default_factory=dict)