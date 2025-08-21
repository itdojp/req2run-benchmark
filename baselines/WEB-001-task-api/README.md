# WEB-001-task-api: Task Management API with Rate Limiting
# タスク管理APIとレート制限機能

## Overview / 概要

A production-ready RESTful API for task management with JWT authentication, rate limiting, and data persistence. This implementation provides comprehensive CRUD operations for tasks with user authentication and IP-based rate limiting.

タスク管理のための本番環境対応RESTful APIで、JWT認証、レート制限、データ永続化機能を備えています。この実装は、ユーザー認証とIPベースのレート制限を備えたタスクの包括的なCRUD操作を提供します。

## Key Features / 主な機能

- **CRUD Operations**: Complete Create, Read, Update, Delete operations for tasks
- **JWT Authentication**: Secure token-based authentication system
- **Rate Limiting**: IP-based rate limiting (100 requests/minute per IP)
- **Data Persistence**: Support for SQLite, PostgreSQL, and MySQL
- **Pagination**: Efficient pagination for task listings
- **Permission Control**: User-specific task access control
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Structured error responses
- **Health Check**: Built-in health monitoring endpoint

## Architecture

```
┌─────────────────────────────────────────────┐
│              Client Application              │
└─────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────┐
│            FastAPI Application              │
├─────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Auth   │  │   Rate   │  │   CORS    │ │
│  │  Layer  │  │  Limiter │  │ Middleware│ │
│  └─────────┘  └──────────┘  └───────────┘ │
│                     │                       │
│  ┌─────────────────────────────────────┐  │
│  │         API Endpoints               │  │
│  │  /auth  /tasks  /health            │  │
│  └─────────────────────────────────────┘  │
│                     │                       │
│  ┌─────────────────────────────────────┐  │
│  │      SQLAlchemy ORM Layer          │  │
│  └─────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌──────────────┐          ┌──────────────┐
│   Database   │          │    Redis     │
│  (SQLite/    │          │ (Rate Limit) │
│  PostgreSQL) │          └──────────────┘
└──────────────┘
```

## Quick Start / クイックスタート

### Using Docker

```bash
# Build the image
docker build -t task-api .

# Run with SQLite (default)
docker run -p 3000:3000 task-api

# Run with PostgreSQL
docker run -p 3000:3000 \
  -e DATABASE_URL="postgresql://user:pass@postgres/taskdb" \
  -e REDIS_URL="redis://redis:6379" \
  -e JWT_SECRET="your-secret-key" \
  task-api
```

### Manual Setup

1. **Install dependencies / 依存関係のインストール:**
```bash
pip install -r requirements.txt
```

2. **Set environment variables / 環境変数の設定:**
```bash
export DATABASE_URL="sqlite:///./tasks.db"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="your-secret-key"
export PORT=3000
```

3. **Run the application / アプリケーションの実行:**
```bash
python src/main.py
```

4. **Access the API documentation / APIドキュメントへのアクセス:**
```bash
open http://localhost:3000/docs
```

## API Usage / API使用方法

### 1. Register User / ユーザー登録

```bash
curl -X POST "http://localhost:3000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123"
  }'

# Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 2. Login / ログイン

```bash
curl -X POST "http://localhost:3000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. Create Task / タスク作成

```bash
curl -X POST "http://localhost:3000/tasks" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deploy v2.0",
    "description": "Production deployment for version 2.0",
    "due_date": "2024-12-31T23:59:59Z"
  }'

# Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Deploy v2.0",
  "description": "Production deployment for version 2.0",
  "due_date": "2024-12-31T23:59:59Z",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 4. List Tasks with Pagination / ページネーション付きタスク一覧

```bash
curl -X GET "http://localhost:3000/tasks?page=1&limit=10" \
  -H "Authorization: Bearer <token>"

# Response:
{
  "tasks": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Deploy v2.0",
      "description": "Production deployment for version 2.0",
      "due_date": "2024-12-31T23:59:59Z",
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 42
  }
}
```

### 5. Get Specific Task / 特定タスクの取得

```bash
curl -X GET "http://localhost:3000/tasks/{task_id}" \
  -H "Authorization: Bearer <token>"
```

### 6. Update Task / タスク更新

```bash
curl -X PUT "http://localhost:3000/tasks/{task_id}" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Title",
    "status": "in_progress"
  }'
```

### 7. Delete Task / タスク削除

```bash
curl -X DELETE "http://localhost:3000/tasks/{task_id}" \
  -H "Authorization: Bearer <token>"
```

## Rate Limiting / レート制限

The API implements IP-based rate limiting:

- **Limit**: 100 requests per minute per IP address
- **Headers**: Rate limit information is included in response headers
- **Error Response**: HTTP 429 when limit exceeded

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded"
}
```

Response headers:
```
X-RateLimit-Remaining: 0
Retry-After: 60
```

## Security Features / セキュリティ機能

1. **JWT Authentication**: Secure token-based authentication
2. **Password Hashing**: Bcrypt password hashing
3. **Input Validation**: Pydantic schema validation
4. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
5. **XSS Protection**: JSON-only responses
6. **CORS Configuration**: Configurable CORS middleware
7. **Permission Control**: User-specific resource access

## Error Handling / エラー処理

The API returns structured error responses:

### Authentication Error (401)
```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token"
}
```

### Permission Error (403)
```json
{
  "error": "Forbidden",
  "message": "You don't have permission to modify this task"
}
```

### Rate Limit Error (429)
```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded"
}
```

## Performance Characteristics / パフォーマンス特性

- **Response Time**: P95 < 200ms (as per requirements)
- **Concurrent Connections**: Supports 1000+ concurrent connections
- **Database Pooling**: Connection pooling for optimal performance
- **Async Processing**: Non-blocking I/O with FastAPI

## Configuration / 設定

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./tasks.db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `JWT_SECRET` | Secret key for JWT signing | `your-secret-key-change-in-production` |
| `PORT` | Application port | `3000` |

### Database Support

The application supports multiple databases:

- **SQLite** (default): `sqlite:///./tasks.db`
- **PostgreSQL**: `postgresql://user:password@localhost/taskdb`
- **MySQL**: `mysql://user:password@localhost/taskdb`

## Testing / テスト

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests

```bash
pytest tests/integration/ -v
```

### Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 -H "Authorization: Bearer <token>" http://localhost:3000/tasks

# Using JMeter
jmeter -n -t tests/load/task_api_load_test.jmx
```

## Production Deployment / 本番環境デプロイ

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db/taskdb
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=taskdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: task-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: task-api
  template:
    metadata:
      labels:
        app: task-api
    spec:
      containers:
      - name: api
        image: task-api:latest
        ports:
        - containerPort: 3000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: jwt-secret
              key: secret
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Monitoring / モニタリング

The application provides health check endpoint:

```bash
curl http://localhost:3000/health

# Response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Troubleshooting / トラブルシューティング

### Database Connection Issues
- Verify DATABASE_URL is correct
- Check database server is running
- Ensure database credentials are valid

### Redis Connection Issues
- Verify REDIS_URL is correct
- Check Redis server is running
- Rate limiting will fall back to in-memory if Redis unavailable

### Authentication Issues
- Verify JWT_SECRET is set correctly
- Check token expiration (24 hours by default)
- Ensure Authorization header format: `Bearer <token>`

## License

MIT