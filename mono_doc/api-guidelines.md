# Hebbia Platform API Guidelines

## Overview

This document defines the API design standards and conventions for the Hebbia platform. All APIs must follow these guidelines to ensure consistency, reliability, and ease of use across the platform.

## Design Principles

### 1. Consistency Over Cleverness
- Follow established HTTP semantics and REST conventions
- Use consistent naming patterns across all endpoints
- Maintain uniform response structures

### 2. Least Privilege Security
- Choose the simplest authentication scheme that meets security requirements
- Apply principle of least privilege for all access controls
- Default to secure configurations

### 3. Explicit Error Handling
- Use RFC 9457 (Problem Details for HTTP APIs) error format
- Provide clear, actionable error messages
- Include relevant context without exposing sensitive information

### 4. Documentation by Example
- Include comprehensive request/response examples
- Provide clear descriptions for all parameters
- Document expected behavior and edge cases

## API Structure

### Base URLs

- **Production**: `https://api.hebbia.ai`
- **Staging**: `https://api-staging.hebbia.ai`
- **Development**: `http://localhost:8000`

### Service Prefixes

Each microservice has a dedicated prefix to organize endpoints logically:

| Service | Prefix | Purpose |
|---------|--------|---------|
| Brain | `/v2/` | Core platform management (users, orgs, tenants) |
| Document Manager | `/docs/` | Document storage and search |
| Agents | `/agents/` | AI chat and research agents |
| Sheets | `/sheets/` | Collaborative spreadsheets |
| Artifacts | `/artifacts/` | Document templates and generation |
| FlashDocs | `/v1/`, `/v2/`, `/v3/` | Presentation generation |

## Authentication

### Bearer Token (Primary)
```http
Authorization: Bearer <jwt_token>
```

- OAuth 2.0 JWT tokens issued via Auth0
- Used for user session authentication
- Tokens contain user context and permissions

### API Key (Server-to-Server)
```http
X-API-Key: <api_key>
```

- For programmatic access and integrations
- Organization-scoped with specific permissions
- Contact support for provisioning

### Hybrid Authentication
Many endpoints support both authentication methods:
```python
# FastAPI dependency pattern
async def allows_login_or_api(
    session: Session = Depends(apply_session),
    token: Optional[HTTPAuthorizationCredentials] = Depends(token_auth_scheme),
    x_api_key: Optional[str] = Header(None),
) -> LoginResponse:
```

## Versioning Strategy

### URI Versioning
- Use `/v{major}` prefix for breaking changes
- Current version: `v2` for core services
- Version in URI path, not headers or query parameters

### Backward Compatibility
- Maintain at least 2 major versions simultaneously
- Provide 6-month deprecation notice for version retirement
- Use feature flags for gradual rollouts

### Example:
```
/v1/users/{id}    # Legacy (deprecated)
/v2/users/{id}    # Current
/v3/users/{id}    # Future
```

## Request/Response Format

### Content Type
- **Request**: `application/json` (default)
- **Response**: `application/json` with ORJSON serialization
- **File uploads**: `multipart/form-data`
- **Streaming**: `text/event-stream` for SSE

### Request Structure
```json
{
  "data": {
    // Primary request payload
  },
  "metadata": {
    // Optional metadata
  }
}
```

### Response Structure
```json
{
  "data": {
    // Primary response data
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z",
    "processing_time_ms": 150
  }
}
```

### List Responses
```json
{
  "items": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTIzLCJ0cyI6MTY5...",
    "has_more": true,
    "limit": 50
  },
  "metadata": {
    "total_count": 1250,
    "search_time_ms": 45
  }
}
```

## Pagination

### Cursor-Based Pagination
Use cursor-based pagination for consistent results:

**Request:**
```http
GET /v2/users?cursor=eyJpZCI6MTIzfQ&limit=50
```

**Response:**
```json
{
  "items": [...],
  "pagination": {
    "cursor": "eyJpZCI6MTczfQ",  // Next page cursor
    "has_more": true,
    "limit": 50
  }
}
```

### Parameters
- `cursor`: Opaque pagination token (base64-encoded JSON)
- `limit`: Results per page (1-100, default: 50)
- `has_more`: Boolean indicating if more results exist

### Implementation
```python
# Example cursor structure
cursor_data = {
    "id": last_item_id,
    "timestamp": last_item_timestamp,
    "sort_field": last_sort_value
}
cursor = base64.b64encode(json.dumps(cursor_data).encode()).decode()
```

## Error Handling

### Error Response Format (RFC 9457)
```json
{
  "detail": "Resource not found",
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "instance": "/docs/documents/123",
  "context": {
    "resource_type": "document",
    "resource_id": "123"
  }
}
```

### Standard HTTP Status Codes

| Code | Usage | Description |
|------|-------|-------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 204 | No Content | Success with no response body |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 422 | Validation Error | Request validation failed |
| 429 | Rate Limited | Too many requests |
| 500 | Internal Error | Unexpected server error |

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "age"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ],
  "status": 422
}
```

## Rate Limiting

### Default Limits
- **User sessions**: 600 requests per minute
- **API keys**: Custom limits based on usage tier
- **Anonymous requests**: 60 requests per hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 600
X-RateLimit-Remaining: 599
X-RateLimit-Reset: 1642261800
X-RateLimit-Window: 60
```

### Rate Limit Response
```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds.",
  "status": 429,
  "retry_after": 30
}
```

## Security Headers

### Required Headers
```http
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://search.hebbia.ai"],
    allow_origin_regex=r"^https?://.*\.vercel\.app|^http?://localhost:.*|^https?://.*\.hebbia\.ai",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=86400,
)
```

## Naming Conventions

### REST Resource Naming
- Use plural nouns for collections: `/users`, `/documents`
- Use kebab-case for multi-word resources: `/document-lists`
- Avoid verbs in resource names
- Use sub-resources for relationships: `/users/{id}/organizations`

### JSON Field Naming
- Use snake_case for field names: `created_at`, `user_id`
- Use descriptive names: `document_count` not `doc_cnt`
- Boolean fields use `is_` prefix: `is_active`, `is_public`
- Timestamps end with `_at`: `created_at`, `updated_at`

### Query Parameters
- Use snake_case: `created_after`, `document_type`
- Boolean parameters: `is_public=true`
- Arrays: `tags=tag1,tag2` or `tags[]=tag1&tags[]=tag2`

## File Handling

### File Uploads
```http
POST /docs/documents
Content-Type: multipart/form-data

file: <binary_data>
document_list_id: uuid
metadata: {"title": "Custom Title"}
```

### File Size Limits
- **Documents**: 100MB per file
- **Images**: 10MB per file
- **Total request**: 500MB maximum

### Supported File Types
- **Documents**: PDF, DOCX, XLSX, PPTX, TXT, HTML, CSV
- **Images**: JPEG, PNG, GIF, WebP
- **Archives**: ZIP (with extraction)

### File Response Headers
```http
Content-Type: application/pdf
Content-Length: 1048576
Content-Disposition: attachment; filename="document.pdf"
ETag: "abc123"
Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT
```

## Streaming Responses

### Server-Sent Events
For real-time AI responses:
```http
GET /agents/multi-doc-chat/{id}/stream
Accept: text/event-stream

data: {"type": "message_start", "content": ""}
data: {"type": "content_delta", "content": "Hello"}
data: {"type": "content_delta", "content": " world"}
data: {"type": "message_end", "content": "Hello world"}
```

### Chunked Responses
```http
Transfer-Encoding: chunked
Content-Type: application/json

{"partial": "data"}
{"more": "data"}
{"final": "data"}
```

## Monitoring and Observability

### Request IDs
Every request gets a unique ID for tracing:
```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

### Logging Structure
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "doc_manager",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "org_id": "789e0123-e45f-67d8-a901-234567890123",
  "method": "GET",
  "path": "/docs/documents",
  "status_code": 200,
  "response_time_ms": 150,
  "message": "Document search completed"
}
```

### Health Checks
```http
GET /health

{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": {"status": "healthy", "response_time_ms": 5},
    "redis": {"status": "healthy", "response_time_ms": 2},
    "elasticsearch": {"status": "degraded", "response_time_ms": 1500}
  }
}
```

## Implementation Guidelines

### FastAPI Best Practices

#### Dependency Injection
```python
# Authentication
@router.get("/users/{user_id}")
async def get_user(
    user_id: str = Path(..., description="User ID"),
    current_user: UserWithOrgsDict = Depends(requires_login),
    session: AsyncSession = Depends(async_apply_session),
):
    # Implementation
```

#### Request/Response Models
```python
# Always use Pydantic models
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True  # For SQLAlchemy integration
```

#### Error Handling
```python
# Custom exceptions
class ResourceNotFoundError(HTTPException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=404,
            detail=f"{resource_type} not found",
            headers={"X-Error-Code": "RESOURCE_NOT_FOUND"}
        )

# Global exception handler
@app.exception_handler(ResourceNotFoundError)
async def not_found_handler(request: Request, exc: ResourceNotFoundError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status": exc.status_code}
    )
```

### Database Integration

#### SQLAlchemy Models
```python
class User(DeclarativeBase):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(VARCHAR(), nullable=False)
    email = Column(VARCHAR(), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Async Queries
```python
async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```

## Testing Guidelines

### Unit Tests
```python
@pytest.mark.asyncio
async def test_create_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/v2/users",
            json={"name": "Test User", "email": "test@example.com"},
            headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Test User"
```

### Integration Tests
```python
@pytest.mark.integration
async def test_document_upload_flow():
    # Test complete upload and processing flow
    with open("test_document.pdf", "rb") as f:
        response = await client.post(
            "/docs/documents",
            files={"file": f},
            data={"document_list_id": str(document_list.id)}
        )

    assert response.status_code == 201
    document_id = response.json()["id"]

    # Wait for processing
    await wait_for_document_processing(document_id)

    # Verify content extraction
    content_response = await client.get(f"/docs/documents/{document_id}/content")
    assert content_response.status_code == 200
```

## Deployment Considerations

### Environment Configuration
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - RATE_LIMIT_REDIS_URL=${REDIS_URL}
```

### Health Check Configuration
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### Load Balancer Configuration
```nginx
upstream api_servers {
    least_conn;
    server api1:8000 max_fails=3 fail_timeout=30s;
    server api2:8000 max_fails=3 fail_timeout=30s;
    server api3:8000 max_fails=3 fail_timeout=30s;
}

server {
    location /api/ {
        proxy_pass http://api_servers;
        proxy_set_header X-Request-ID $request_id;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Migration and Backwards Compatibility

### Breaking Changes
- Always introduce in new major version
- Provide migration guide and tooling
- Maintain previous version for minimum 6 months

### Non-Breaking Changes
- New optional fields
- New endpoints
- Additional response fields
- More permissive validation

### Deprecation Process
1. **Announce**: Add deprecation notice in documentation
2. **Warn**: Include deprecation headers in responses
3. **Migrate**: Provide migration tools and support
4. **Remove**: Remove after deprecation period

```http
# Deprecation warning
Deprecation: version="v1" date="2024-06-01" link="https://docs.hebbia.ai/migration/v2"
```

## Additional Resources

- [OpenAPI 3.1.1 Specification](https://swagger.io/specification/)
- [RFC 9457: Problem Details for HTTP APIs](https://tools.ietf.org/rfc/rfc9457.txt)
- [REST API Design Best Practices](https://restfulapi.net/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
