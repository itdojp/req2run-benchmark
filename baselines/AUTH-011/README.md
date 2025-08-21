# AUTH-011: RBAC/ABAC Hybrid Authorization System

## Overview

A high-performance, production-grade authorization system that combines Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) with advanced features including policy inheritance, time-based policies, permission delegation, and comprehensive audit logging.

## Key Features

### RBAC (Role-Based Access Control)
- Hierarchical role structure with inheritance
- Permission-based access control
- Role composition and parent roles
- Dynamic role assignment

### ABAC (Attribute-Based Access Control)
- Subject, resource, action, and environment attributes
- Complex attribute matching with operators
- JSONPath-based condition evaluation
- Dynamic attribute-based policies

### Hybrid Authorization
- Combines RBAC and ABAC for flexible access control
- Policy composition with multiple resolution strategies
- Priority-based policy evaluation
- Conflict resolution (deny_overrides, allow_overrides, first_match, priority_based)

### Advanced Features
- **Time-based Policies**: Restrict access based on time constraints
- **Permission Delegation**: Users can delegate their permissions temporarily
- **Policy Inheritance**: Policies can inherit from parent policies
- **Constant-time Evaluation**: Optimized for O(1) policy lookups
- **Dynamic Policy Updates**: Update policies without system restart
- **Comprehensive Audit Logging**: Track all authorization decisions

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Layer  │────▶│   Policy    │
│             │     │  (FastAPI)  │     │   Engine    │
└─────────────┘     └─────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Audit    │     │   Cache     │
                    │   Manager   │     │   Layer     │
                    └─────────────┘     └─────────────┘
```

## Quick Start

### Using Docker

```bash
# Build the image
docker build -t auth-system .

# Run the container
docker run -p 8000:8000 auth-system

# Health check
curl http://localhost:8000/health
```

### Manual Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the application:**
```bash
cd src
python main.py
```

## API Endpoints

### Authorization

- `POST /api/v1/authorize` - Main authorization endpoint
- `POST /api/v1/batch-authorize` - Batch authorization for multiple requests

### Policy Management

- `GET /api/v1/policies` - List all policies (admin only)
- `POST /api/v1/policies` - Create new policy (admin only)
- `PUT /api/v1/policies/{policy_id}` - Update policy (admin only)
- `DELETE /api/v1/policies/{policy_id}` - Delete policy (admin only)

### Role Management

- `GET /api/v1/roles` - List all roles
- `POST /api/v1/roles` - Create new role (admin only)

### Delegation

- `POST /api/v1/delegations` - Create permission delegation

### Audit

- `GET /api/v1/audit-logs` - Get audit logs (admin only)

### Health

- `GET /health` - Health check endpoint

## Usage Examples

### Basic Authorization Request

```bash
curl -X POST http://localhost:8000/api/v1/authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '{
    "subject": "user_john",
    "action": "read",
    "resource": "/documents/public",
    "context": {
      "ip": "192.168.1.1",
      "time": "2024-01-21T10:30:00Z"
    }
  }'
```

### Create RBAC Policy

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Developer Access",
    "type": "rbac",
    "effect": "allow",
    "priority": 70,
    "roles": ["role_developer"],
    "permissions": ["read", "write", "deploy"],
    "resources": ["/code/*", "/deployments/*"]
  }'
```

### Create ABAC Policy

```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "name": "Sensitive Data Protection",
    "type": "abac",
    "effect": "deny",
    "priority": 90,
    "subject_attributes": {
      "clearance": {
        "operator": "less_than",
        "value": "secret"
      }
    },
    "resource_attributes": {
      "classification": {
        "operator": "in",
        "value": ["secret", "top_secret"]
      }
    }
  }'
```

### Batch Authorization

```bash
curl -X POST http://localhost:8000/api/v1/batch-authorize \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_john" \
  -d '[
    {
      "subject": "user_john",
      "action": "read",
      "resource": "/documents/public"
    },
    {
      "subject": "user_john",
      "action": "write",
      "resource": "/documents/private"
    }
  ]'
```

### Create Permission Delegation

```bash
curl -X POST http://localhost:8000/api/v1/delegations \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_admin" \
  -d '{
    "delegator": "user_admin",
    "delegate": "user_john",
    "permissions": ["admin", "audit"],
    "valid_until": "2024-01-22T00:00:00Z"
  }'
```

## Configuration

### RBAC Configuration (`config/rbac.yaml`)

Define roles, permissions, and hierarchies:

```yaml
roles:
  - id: role_admin
    name: admin
    permissions:
      - read
      - write
      - delete
      - admin
    parent_roles: []
```

### ABAC Configuration (`config/abac.yaml`)

Define attributes and attribute-based policies:

```yaml
attributes:
  subject:
    - name: department
      type: string
      values: [IT, HR, Finance]
    - name: clearance
      type: string
      values: [public, confidential, secret]
```

### Policies Configuration (`config/policies.yaml`)

Define authorization policies:

```yaml
policies:
  - id: policy_1
    name: Admin Access
    type: rbac
    effect: allow
    priority: 100
    roles: [role_admin]
    permissions: ["*"]
```

## Policy Evaluation

### Evaluation Order

1. Time-based constraints check
2. RBAC policy evaluation
3. ABAC policy evaluation
4. Delegation check
5. Conflict resolution
6. Final decision

### Conflict Resolution Strategies

- **deny_overrides**: Any deny policy overrides allow policies
- **allow_overrides**: Any allow policy overrides deny policies
- **first_match**: First matching policy determines the outcome
- **priority_based**: Highest priority policy determines the outcome

## Performance

- **Policy Evaluation**: < 5ms P99 latency
- **Throughput**: > 10,000 requests per second
- **Cache Hit Rate**: > 90% for repeated requests
- **Memory Usage**: < 2GB under normal load

## Security Considerations

1. **Authentication**: Ensure proper authentication before authorization
2. **TLS**: Always use HTTPS in production
3. **API Keys**: Rotate admin API keys regularly
4. **Audit Logs**: Monitor audit logs for suspicious activity
5. **Policy Review**: Regularly review and update policies
6. **Least Privilege**: Follow principle of least privilege

## Monitoring

### Metrics

- Authorization request rate
- Decision latency (P50, P95, P99)
- Policy hit rate
- Cache effectiveness
- Audit log volume

### Health Checks

The `/health` endpoint provides:
- System status
- Component health
- Version information

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Performance Tests

```bash
pytest tests/performance/ -v --benchmark-only
```

## License

MIT