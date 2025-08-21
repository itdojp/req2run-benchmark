# WEB-010: Search + CRUD with Paging, Sort, and Filter - Baseline Implementation

## Overview

This baseline implementation provides a comprehensive REST API with advanced search, filtering, sorting, and pagination features. It demonstrates best practices for building scalable, performant APIs with complex query capabilities.

## Features Implemented

### Core Features (MUST)
- ✅ Full CRUD operations for resources
- ✅ Full-text search across all fields
- ✅ Cursor-based pagination
- ✅ Multi-field sorting
- ✅ Complex filtering with operators
- ✅ Input validation
- ✅ Proper HTTP status codes

### Additional Features (SHOULD/MAY)
- ✅ Bulk operations
- ✅ Search result highlighting
- ⚠️ Saved searches (partial)

## API Endpoints

### CRUD Operations
- `GET /api/v1/items` - List items with filtering
- `GET /api/v1/items/{id}` - Get single item
- `POST /api/v1/items` - Create new item
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item
- `POST /api/v1/items/bulk` - Bulk operations

### Search
- `GET /api/v1/items/search` - Full-text search
- `POST /api/v1/items/search/advanced` - Advanced search with complex queries

### Query Parameters

#### Pagination
- `cursor` - Cursor for pagination
- `limit` - Number of results (default: 20, max: 100)

#### Sorting
- `sort` - Comma-separated fields with direction (e.g., `name:asc,created_at:desc`)

#### Filtering
- `filter[field][operator]` - Filter syntax
  - Operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `like`, `in`, `between`
  - Example: `filter[price][gte]=100&filter[category][in]=electronics,books`

#### Search
- `q` - Search query
- `fields` - Fields to search (comma-separated)
- `highlight` - Enable result highlighting (true/false)

## Example Requests

### Search with Pagination and Sorting
```http
GET /api/v1/items/search?q=laptop&sort=price:asc&limit=20&cursor=eyJpZCI6MTAwfQ==
```

### Complex Filtering
```http
GET /api/v1/items?filter[price][between]=100,500&filter[category][eq]=electronics&sort=rating:desc
```

### Bulk Update
```http
POST /api/v1/items/bulk
Content-Type: application/json

{
  "operations": [
    {"op": "update", "id": 1, "data": {"price": 299.99}},
    {"op": "delete", "id": 2},
    {"op": "create", "data": {"name": "New Item", "price": 199.99}}
  ]
}
```

## Performance Characteristics

- Search latency: P95 < 100ms, P99 < 200ms
- Throughput: 1000+ requests/second
- Supports datasets with millions of records
- Efficient cursor pagination (no offset performance degradation)

## Technology Stack

- **Framework**: FastAPI (Python) / Express (Node.js)
- **Database**: PostgreSQL with full-text search
- **Search Engine**: Elasticsearch (optional)
- **Caching**: Redis

## Running the Baseline

### Docker
```bash
docker build -t web-010-baseline .
docker run -p 8000:8000 web-010-baseline
```

### Local Development
```bash
pip install -r requirements.txt
python src/main.py
```

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Load testing
locust -f tests/performance/locustfile.py
```

## Configuration

See `config/api.yaml` for configuration options:

```yaml
api:
  max_page_size: 100
  default_page_size: 20
  search_timeout_ms: 5000
  
database:
  connection_pool_size: 20
  query_timeout_ms: 3000
  
search:
  min_query_length: 2
  max_query_terms: 10
  highlight_enabled: true
```

## License

MIT