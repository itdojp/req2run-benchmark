# WEB-001: Todo REST API Baseline Implementation

This is the baseline (reference) implementation for the WEB-001 problem: Todo REST API with JWT Authentication.

## Expected Score

- **Total Score**: 85.2%
- **Grade**: Silver
- **Breakdown**:
  - Functional Coverage: 100% (weight: 0.35) → 35.0
  - Test Pass Rate: 92% (weight: 0.25) → 23.0  
  - Performance Score: 78% (weight: 0.15) → 11.7
  - Code Quality: 85% (weight: 0.15) → 12.75
  - Security Score: 90% (weight: 0.10) → 9.0

## Implementation Overview

This baseline implementation uses:
- **Framework**: FastAPI (Python 3.11)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Validation**: Pydantic models
- **Testing**: pytest with httpx

## Directory Structure

```
baselines/WEB-001/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container definition
├── src/
│   ├── main.py       # FastAPI application entry point
│   ├── models.py     # SQLAlchemy models
│   ├── schemas.py    # Pydantic schemas
│   ├── database.py   # Database configuration
│   ├── auth.py       # JWT authentication
│   ├── crud.py       # CRUD operations
│   └── config.py     # Application configuration
├── tests/
│   ├── test_unit.py       # Unit tests
│   ├── test_integration.py # Integration tests
│   ├── test_performance.py # Performance tests
│   ├── test_security.py    # Security tests
│   └── test_property.py    # Property-based tests
└── docs/
    └── setup.md      # Setup instructions

```

## Running the Implementation

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v --cov=src --cov-report=html
```

### Docker Deployment

```bash
# Build the image
docker build -t web-001-baseline .

# Run the container
docker run -p 8000:8000 web-001-baseline

# Run with resource limits (as per problem constraints)
docker run -p 8000:8000 \
  --cpus="1.0" \
  --memory="512m" \
  web-001-baseline
```

## API Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and receive JWT token
- `GET /todos` - List all todos (paginated)
- `POST /todos` - Create a new todo
- `GET /todos/{id}` - Get a specific todo
- `PUT /todos/{id}` - Update a todo
- `DELETE /todos/{id}` - Delete a todo
- `GET /health` - Health check endpoint

## Performance Characteristics

- **P95 Latency**: ~95ms (requirement: 120ms)
- **P99 Latency**: ~150ms (requirement: 200ms)
- **Throughput**: ~65 RPS (requirement: 50 RPS)
- **Memory Usage**: ~450MB under load (limit: 512MB)
- **CPU Usage**: ~0.8 cores under load (limit: 1.0 core)

## Security Features

- JWT-based authentication with token expiration
- Password hashing with bcrypt
- Input validation via Pydantic
- SQL injection prevention via SQLAlchemy ORM
- No hardcoded secrets (uses environment variables)
- Rate limiting on authentication endpoints

## Code Quality Metrics

- **Test Coverage**: 92%
- **Cyclomatic Complexity**: Average 4.2, Max 8
- **Type Hints**: 100% coverage
- **Documentation**: All public functions documented
- **Linting**: Passes flake8 and black formatting

## Known Limitations

1. Uses SQLite instead of a production database (acceptable per requirements)
2. No distributed caching (single-instance deployment)
3. Basic rate limiting (in-memory, not distributed)

## Improvement Opportunities

While this baseline meets all requirements, potential improvements include:
- PostgreSQL for production deployment
- Redis for caching and distributed rate limiting
- OpenTelemetry for observability
- Alembic for database migrations