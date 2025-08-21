"""Main FastAPI application for RBAC/ABAC hybrid authorization system"""
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog
import yaml
from decouple import config as env_config

from models import (
    User, Role, Resource, Policy, RBACPolicy, ABACPolicy,
    AuthorizationRequest, AuthorizationDecision, AuditLog,
    PolicySet, Permission, Delegation, HealthStatus,
    Effect, PolicyType, TimeBasedPolicy
)
from policy_engine import PolicyEngine
from audit import AuditManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global instances
policy_engine: Optional[PolicyEngine] = None
audit_manager: Optional[AuditManager] = None
users_db: Dict[str, User] = {}
resources_db: Dict[str, Resource] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global policy_engine, audit_manager
    
    # Startup
    logger.info("Starting authorization service")
    
    # Initialize components
    policy_engine = PolicyEngine()
    audit_manager = AuditManager()
    
    # Load initial configuration
    await load_configuration()
    
    # Start background tasks
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    yield
    
    # Shutdown
    logger.info("Shutting down authorization service")
    
    # Cancel background tasks
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title="RBAC/ABAC Hybrid Authorization System",
    description="High-performance authorization service with role and attribute-based access control",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def load_configuration():
    """Load initial configuration from files"""
    try:
        # Load RBAC configuration
        with open("config/rbac.yaml", "r") as f:
            rbac_config = yaml.safe_load(f)
            await load_rbac_config(rbac_config)
    except FileNotFoundError:
        logger.warning("RBAC configuration file not found")
    
    try:
        # Load ABAC configuration
        with open("config/abac.yaml", "r") as f:
            abac_config = yaml.safe_load(f)
            await load_abac_config(abac_config)
    except FileNotFoundError:
        logger.warning("ABAC configuration file not found")
    
    try:
        # Load policies
        with open("config/policies.yaml", "r") as f:
            policies_config = yaml.safe_load(f)
            await load_policies(policies_config)
    except FileNotFoundError:
        logger.warning("Policies configuration file not found")
    
    # Create default demo data
    await create_demo_data()


async def load_rbac_config(config: Dict[str, Any]):
    """Load RBAC configuration"""
    if not config:
        return
    
    # Load roles
    for role_data in config.get('roles', []):
        role = Role(**role_data)
        await policy_engine.add_role(role)
    
    logger.info("Loaded RBAC configuration", roles_count=len(config.get('roles', [])))


async def load_abac_config(config: Dict[str, Any]):
    """Load ABAC configuration"""
    if not config:
        return
    
    # Load attribute definitions and policies
    logger.info("Loaded ABAC configuration")


async def load_policies(config: Dict[str, Any]):
    """Load policies from configuration"""
    if not config:
        return
    
    for policy_data in config.get('policies', []):
        policy_type = policy_data.get('type', 'rbac')
        
        if policy_type == 'rbac':
            policy = RBACPolicy(**policy_data)
        elif policy_type == 'abac':
            policy = ABACPolicy(**policy_data)
        elif policy_type == 'time_based':
            policy = TimeBasedPolicy(**policy_data)
        else:
            policy = Policy(**policy_data)
        
        await policy_engine.add_policy(policy)
    
    logger.info("Loaded policies", count=len(config.get('policies', [])))


async def create_demo_data():
    """Create demo users, roles, and policies"""
    # Create demo roles
    admin_role = Role(
        id="role_admin",
        name="admin",
        permissions=["read", "write", "delete", "admin"],
        description="Administrator role with full access"
    )
    
    user_role = Role(
        id="role_user",
        name="user",
        permissions=["read"],
        description="Basic user role with read access"
    )
    
    editor_role = Role(
        id="role_editor",
        name="editor",
        permissions=["read", "write"],
        parent_roles=["role_user"],
        description="Editor role with read and write access"
    )
    
    await policy_engine.add_role(admin_role)
    await policy_engine.add_role(user_role)
    await policy_engine.add_role(editor_role)
    
    # Create demo users
    admin_user = User(
        id="user_admin",
        username="admin",
        email="admin@example.com",
        roles=["role_admin"],
        attributes={"department": "IT", "clearance": "high"}
    )
    
    regular_user = User(
        id="user_john",
        username="john",
        email="john@example.com",
        roles=["role_user"],
        attributes={"department": "Sales", "clearance": "low"}
    )
    
    editor_user = User(
        id="user_jane",
        username="jane",
        email="jane@example.com",
        roles=["role_editor"],
        attributes={"department": "Marketing", "clearance": "medium"}
    )
    
    users_db[admin_user.id] = admin_user
    users_db[regular_user.id] = regular_user
    users_db[editor_user.id] = editor_user
    
    # Create demo resources
    public_resource = Resource(
        id="res_public",
        type="document",
        identifier="/documents/public",
        attributes={"classification": "public", "owner": "system"}
    )
    
    private_resource = Resource(
        id="res_private",
        type="document",
        identifier="/documents/private",
        attributes={"classification": "private", "owner": "user_admin"}
    )
    
    resources_db[public_resource.id] = public_resource
    resources_db[private_resource.id] = private_resource
    
    # Create demo policies
    rbac_policy = RBACPolicy(
        id="policy_rbac_1",
        name="Admin Full Access",
        type=PolicyType.RBAC,
        effect=Effect.ALLOW,
        roles=["role_admin"],
        permissions=["read", "write", "delete"],
        priority=100
    )
    
    abac_policy = ABACPolicy(
        id="policy_abac_1",
        name="Department Access Control",
        type=PolicyType.ABAC,
        effect=Effect.ALLOW,
        subject_attributes={"department": "IT"},
        resource_attributes={"classification": "private"},
        conditions="$.user.attributes.clearance == 'high'"
    )
    
    time_policy = TimeBasedPolicy(
        id="policy_time_1",
        name="Business Hours Only",
        type=PolicyType.RBAC,
        effect=Effect.ALLOW,
        roles=["role_user"],
        permissions=["read"],
        time_constraints={"weekdays": [0, 1, 2, 3, 4], "hours": [9, 17]}
    )
    
    await policy_engine.add_policy(rbac_policy)
    await policy_engine.add_policy(abac_policy)
    await policy_engine.add_policy(time_policy)
    
    logger.info("Created demo data")


async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            
            # Clear old cache entries
            policy_engine.clear_cache()
            
            # Clean up old audit logs
            await audit_manager.cleanup_old_logs(days=30)
            
            logger.info("Periodic cleanup completed")
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("Cleanup task error", error=str(e))


def get_current_user(user_id: str = Header(None, alias="X-User-ID")) -> User:
    """Get current user from header"""
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    return users_db[user_id]


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    return HealthStatus(
        status="healthy",
        components={
            "policy_engine": "ok" if policy_engine else "error",
            "audit_manager": "ok" if audit_manager else "error"
        }
    )


@app.post("/api/v1/authorize", response_model=AuthorizationDecision)
async def authorize(
    request: AuthorizationRequest,
    user: User = Depends(get_current_user)
):
    """Main authorization endpoint"""
    # Get resource
    if request.resource not in resources_db:
        # Create dynamic resource
        resource = Resource(
            type="unknown",
            identifier=request.resource,
            attributes=request.attributes
        )
    else:
        resource = resources_db[request.resource]
    
    # Evaluate authorization
    decision = await policy_engine.evaluate(request, user, resource)
    
    # Audit log
    audit_log = AuditLog(
        request=request,
        decision=decision,
        user_id=user.id,
        metadata={"source": "api"}
    )
    await audit_manager.log(audit_log)
    
    return decision


@app.post("/api/v1/policies", response_model=Policy)
async def create_policy(
    policy_data: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    """Create a new policy (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Determine policy type and create appropriate instance
    policy_type = policy_data.get('type', 'rbac')
    
    if policy_type == 'rbac':
        policy = RBACPolicy(**policy_data)
    elif policy_type == 'abac':
        policy = ABACPolicy(**policy_data)
    else:
        policy = Policy(**policy_data)
    
    await policy_engine.add_policy(policy)
    
    return policy


@app.put("/api/v1/policies/{policy_id}")
async def update_policy(
    policy_id: str,
    policy_data: Dict[str, Any],
    user: User = Depends(get_current_user)
):
    """Update a policy (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if policy_id not in policy_engine.policies:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # Update policy
    policy_data['id'] = policy_id
    policy_type = policy_data.get('type', 'rbac')
    
    if policy_type == 'rbac':
        policy = RBACPolicy(**policy_data)
    elif policy_type == 'abac':
        policy = ABACPolicy(**policy_data)
    else:
        policy = Policy(**policy_data)
    
    await policy_engine.add_policy(policy)
    
    return {"status": "updated"}


@app.delete("/api/v1/policies/{policy_id}")
async def delete_policy(
    policy_id: str,
    user: User = Depends(get_current_user)
):
    """Delete a policy (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await policy_engine.remove_policy(policy_id)
    
    return {"status": "deleted"}


@app.get("/api/v1/policies")
async def list_policies(
    user: User = Depends(get_current_user)
):
    """List all policies (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return list(policy_engine.policies.values())


@app.post("/api/v1/roles", response_model=Role)
async def create_role(
    role: Role,
    user: User = Depends(get_current_user)
):
    """Create a new role (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await policy_engine.add_role(role)
    
    return role


@app.get("/api/v1/roles")
async def list_roles(
    user: User = Depends(get_current_user)
):
    """List all roles"""
    return list(policy_engine.roles.values())


@app.post("/api/v1/delegations", response_model=Delegation)
async def create_delegation(
    delegation: Delegation,
    user: User = Depends(get_current_user)
):
    """Create a permission delegation"""
    # Verify delegator is the current user
    if delegation.delegator != user.id:
        raise HTTPException(status_code=403, detail="Can only delegate own permissions")
    
    # Verify delegator has the permissions to delegate
    # (simplified check)
    
    await policy_engine.add_delegation(delegation)
    
    return delegation


@app.get("/api/v1/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    user: User = Depends(get_current_user)
):
    """Get audit logs (admin only)"""
    if "role_admin" not in user.roles:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await audit_manager.get_logs(limit=limit)
    
    return logs


@app.post("/api/v1/batch-authorize")
async def batch_authorize(
    requests: List[AuthorizationRequest],
    user: User = Depends(get_current_user)
):
    """Batch authorization for multiple requests"""
    decisions = []
    
    for request in requests:
        # Get resource
        if request.resource not in resources_db:
            resource = Resource(
                type="unknown",
                identifier=request.resource,
                attributes=request.attributes
            )
        else:
            resource = resources_db[request.resource]
        
        # Evaluate
        decision = await policy_engine.evaluate(request, user, resource)
        decisions.append(decision)
    
    return decisions


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )