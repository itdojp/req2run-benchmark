# WEB-011: Secure File Upload with Presigned URLs

A production-grade secure file upload system featuring presigned URLs, malware scanning, multipart uploads, and comprehensive progress tracking.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI API    │───▶│  S3 Storage     │
│                 │    │                  │    │                 │
│ • Upload UI     │    │ • Presigned URLs │    │ • Secure Bucket │
│ • Progress      │    │ • Validation     │    │ • Versioning    │
│ • File Preview  │    │ • Progress Track │    │ • Lifecycle     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   Database       │    │ Malware Scanner │
                       │                  │    │                 │
                       │ • Upload Records │    │ • ClamAV        │
                       │ • Progress       │    │ • Hash Check    │
                       │ • Scan Results   │    │ • Quarantine    │
                       └──────────────────┘    └─────────────────┘
```

## Key Features

### 🔐 Secure Upload Process
- **Presigned URLs**: Direct client-to-S3 upload without exposing credentials
- **Content Type Validation**: Strict MIME type and extension matching
- **File Size Limits**: Configurable upload size restrictions
- **Input Sanitization**: Filename and metadata validation

### 🚀 Upload Performance
- **Multipart Uploads**: Parallel upload of large files (>100MB)
- **Progress Tracking**: Real-time upload progress monitoring
- **Resume Support**: Ability to resume interrupted uploads
- **Concurrent Uploads**: Multiple files upload simultaneously

### 🛡️ Security & Scanning
- **Malware Detection**: ClamAV integration with hash-based fallback
- **Quarantine System**: Automatic isolation of infected files
- **Content Verification**: SHA-256 integrity checking
- **Access Control**: API key authentication and authorization

### 📊 Monitoring & Management
- **Upload Statistics**: Comprehensive metrics and reporting
- **File Lifecycle**: Automated cleanup and retention policies
- **Audit Trail**: Complete upload and scan history
- **Health Monitoring**: Service health checks and diagnostics

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL/MySQL/SQLite database
- AWS S3 or MinIO storage
- ClamAV (optional, for malware scanning)

### Installation

```bash
# Clone and setup
cd baselines/WEB-011
pip install -r requirements.txt

# Configure environment
cp config/app.env .env
# Edit .env with your settings

# Initialize database
python -c "from src.database import DatabaseService; DatabaseService('sqlite:///./uploads.db')"
```

### Running the Service

```bash
# Development mode
python src/main.py

# Production mode with Gunicorn
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker deployment
docker build -t secure-upload .
docker run -p 8000:8000 -v $(pwd)/data:/app/data secure-upload
```

## API Reference

### Authentication

All endpoints require an `Authorization: Bearer {API_KEY}` header.

### Core Endpoints

#### Generate Presigned URL

```http
POST /api/v1/upload/presign
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "metadata": {
    "description": "Important document",
    "category": "reports"
  },
  "multipart": false
}
```

Response:
```json
{
  "upload_id": "uuid-here",
  "upload_url": "https://s3.amazonaws.com/bucket/...",
  "expires_in": 3600,
  "fields": {
    "key": "uploads/2024/01/21/uuid/document.pdf",
    "Content-Type": "application/pdf",
    "policy": "...",
    "x-amz-credential": "...",
    "x-amz-algorithm": "AWS4-HMAC-SHA256",
    "x-amz-date": "20240121T120000Z",
    "x-amz-signature": "..."
  }
}
```

#### Upload Progress Update

```http
POST /api/v1/upload/{upload_id}/progress
Content-Type: application/json

{
  "upload_id": "uuid-here",
  "progress_percentage": 45,
  "bytes_uploaded": 471859
}
```

#### Get Upload Information

```http
GET /api/v1/upload/{upload_id}
Authorization: Bearer your-api-key
```

Response:
```json
{
  "id": "uuid-here",
  "filename": "document.pdf",
  "original_filename": "document.pdf",
  "content_type": "application/pdf",
  "size_bytes": 1048576,
  "status": "completed",
  "scan_status": "clean",
  "progress_percentage": 100,
  "created_at": "2024-01-21T12:00:00Z",
  "uploaded_at": "2024-01-21T12:05:00Z",
  "expires_at": "2024-01-22T12:00:00Z",
  "download_url": "https://s3.amazonaws.com/...",
  "metadata": {
    "description": "Important document"
  }
}
```

### Multipart Upload

For large files (>100MB), use multipart upload:

1. **Request multipart presigned URL** with `"multipart": true`
2. **Get part URLs**: `GET /api/v1/upload/{upload_id}/parts?parts=10`
3. **Upload parts** using the provided URLs
4. **Complete upload**: `POST /api/v1/upload/{upload_id}/complete`

#### Get Multipart Part URLs

```http
GET /api/v1/upload/{upload_id}/parts?parts=5
Authorization: Bearer your-api-key
```

Response:
```json
{
  "parts": [
    {
      "part_number": 1,
      "upload_url": "https://s3.amazonaws.com/bucket/...",
      "expires_in": 3600
    },
    // ... more parts
  ]
}
```

#### Complete Multipart Upload

```http
POST /api/v1/upload/{upload_id}/complete
Content-Type: application/json

{
  "upload_id": "uuid-here",
  "parts": [
    {"PartNumber": 1, "ETag": "\"etag1\""},
    {"PartNumber": 2, "ETag": "\"etag2\""}
  ]
}
```

### File Management

#### List Uploads

```http
GET /api/v1/uploads?user_id=user123&status=completed&page=1&page_size=20
Authorization: Bearer your-api-key
```

#### Upload Statistics

```http
GET /api/v1/stats
Authorization: Bearer your-api-key
```

Response:
```json
{
  "status_counts": {
    "pending": 5,
    "completed": 150,
    "failed": 2,
    "quarantined": 1
  },
  "scan_status_counts": {
    "clean": 148,
    "infected": 1,
    "pending": 5,
    "error": 1
  },
  "total_files": 158,
  "total_size_bytes": 5368709120,
  "recent_uploads_30d": 45
}
```

## Client Implementation

### JavaScript/TypeScript Example

```typescript
class SecureUploadClient {
  constructor(private apiBaseUrl: string, private apiKey: string) {}

  async uploadFile(file: File, metadata?: any): Promise<string> {
    // 1. Calculate file hash
    const checksum = await this.calculateSHA256(file);
    
    // 2. Request presigned URL
    const response = await fetch(`${this.apiBaseUrl}/api/v1/upload/presign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        filename: file.name,
        content_type: file.type,
        size_bytes: file.size,
        checksum_sha256: checksum,
        metadata,
        multipart: file.size > 100 * 1024 * 1024 // 100MB
      })
    });

    const uploadInfo = await response.json();
    
    if (uploadInfo.multipart_upload_id) {
      return await this.uploadMultipart(file, uploadInfo);
    } else {
      return await this.uploadSingle(file, uploadInfo);
    }
  }

  private async uploadSingle(file: File, uploadInfo: any): Promise<string> {
    // Create form data for S3 POST
    const formData = new FormData();
    
    // Add fields from presigned URL
    for (const [key, value] of Object.entries(uploadInfo.fields)) {
      formData.append(key, value as string);
    }
    
    formData.append('file', file);
    
    // Upload to S3
    const uploadResponse = await fetch(uploadInfo.upload_url, {
      method: 'POST',
      body: formData
    });
    
    if (!uploadResponse.ok) {
      throw new Error('Upload failed');
    }
    
    return uploadInfo.upload_id;
  }

  private async uploadMultipart(file: File, uploadInfo: any): Promise<string> {
    const partSize = 5 * 1024 * 1024; // 5MB
    const numParts = Math.ceil(file.size / partSize);
    
    // Get part URLs
    const partsResponse = await fetch(
      `${this.apiBaseUrl}/api/v1/upload/${uploadInfo.upload_id}/parts?parts=${numParts}`,
      {
        headers: { 'Authorization': `Bearer ${this.apiKey}` }
      }
    );
    
    const partsData = await partsResponse.json();
    
    // Upload parts in parallel
    const uploadPromises = partsData.parts.map(async (part: any) => {
      const start = (part.part_number - 1) * partSize;
      const end = Math.min(start + partSize, file.size);
      const chunk = file.slice(start, end);
      
      const response = await fetch(part.upload_url, {
        method: 'PUT',
        body: chunk
      });
      
      return {
        PartNumber: part.part_number,
        ETag: response.headers.get('ETag')
      };
    });
    
    const parts = await Promise.all(uploadPromises);
    
    // Complete multipart upload
    await fetch(`${this.apiBaseUrl}/api/v1/upload/${uploadInfo.upload_id}/complete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        upload_id: uploadInfo.upload_id,
        parts
      })
    });
    
    return uploadInfo.upload_id;
  }

  private async calculateSHA256(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  async trackProgress(uploadId: string, onProgress: (progress: number) => void) {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${this.apiBaseUrl}/api/v1/upload/${uploadId}`, {
          headers: { 'Authorization': `Bearer ${this.apiKey}` }
        });
        const info = await response.json();
        
        onProgress(info.progress_percentage);
        
        if (info.status === 'completed' || info.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Progress tracking error:', error);
        clearInterval(interval);
      }
    }, 1000);
  }
}

// Usage
const client = new SecureUploadClient('http://localhost:8000', 'your-api-key');

const fileInput = document.querySelector('#file-input') as HTMLInputElement;
fileInput.addEventListener('change', async (event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  
  try {
    const uploadId = await client.uploadFile(file, {
      category: 'documents',
      uploaded_by: 'user123'
    });
    
    console.log('Upload started:', uploadId);
    
    // Track progress
    client.trackProgress(uploadId, (progress) => {
      console.log(`Upload progress: ${progress}%`);
    });
    
  } catch (error) {
    console.error('Upload error:', error);
  }
});
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/uploads
# DATABASE_URL=sqlite:///./uploads.db

# S3 Storage
S3_BUCKET_NAME=secure-uploads
S3_REGION=us-east-1
S3_ENDPOINT_URL=https://s3.amazonaws.com  # or MinIO endpoint
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# ClamAV Scanner
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl  # Alternative to TCP

# Security
API_KEY=your-secure-api-key

# Upload Limits
UPLOAD_MAX_SIZE=10737418240  # 10GB
MULTIPART_THRESHOLD=104857600  # 100MB
PRESIGNED_URL_EXPIRY=3600  # 1 hour
```

### Allowed File Types

The system supports these file types by default:

- **Images**: JPEG, PNG, GIF, WebP
- **Documents**: PDF, Word (.doc, .docx), Excel (.xls, .xlsx), Plain text, CSV
- **Archives**: ZIP
- **Media**: MP4, QuickTime, AVI, MP3, WAV

To modify allowed types, update the `MIME_TO_EXTENSIONS` mapping in `src/models.py`.

## Security Features

### Upload Security

- **Presigned URL Expiry**: URLs expire after configured time (default: 1 hour)
- **Content-Type Enforcement**: S3 policy enforces declared content type
- **File Size Limits**: Both client and server-side size validation
- **Filename Sanitization**: Removes dangerous characters from filenames

### Malware Scanning

- **ClamAV Integration**: Industry-standard antivirus scanning
- **Hash-based Detection**: Known malware hash comparison
- **Quarantine System**: Infected files moved to quarantine bucket
- **Scan Result Tracking**: Complete audit trail of scan results

### Access Control

- **API Key Authentication**: Bearer token authentication
- **User Context**: Optional user ID tracking
- **IP Logging**: Client IP address recording
- **Rate Limiting**: (Configure with reverse proxy)

## Production Deployment

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/uploads
      - S3_BUCKET_NAME=production-uploads
      - API_KEY=${API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=uploads
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: secure-upload-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: secure-upload-api
  template:
    metadata:
      labels:
        app: secure-upload-api
    spec:
      containers:
      - name: api
        image: secure-upload:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Monitoring & Maintenance

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/api/v1/stats
```

### Database Maintenance

```python
# Cleanup expired uploads (run periodically)
from src.database import DatabaseService

db = DatabaseService("postgresql://...")
deleted_count = await db.cleanup_expired_uploads()
print(f"Cleaned up {deleted_count} expired uploads")
```

### Log Monitoring

The application uses structured logging. Key log patterns to monitor:

- `"File scan found threats"` - Malware detection
- `"Upload integrity check failed"` - Corrupted uploads
- `"Failed to generate presigned URL"` - S3 issues
- `"Database connection error"` - Database issues

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_uploads_user_status ON file_uploads(user_id, status);
CREATE INDEX idx_uploads_scan_status ON file_uploads(scan_status);
CREATE INDEX idx_uploads_created_at ON file_uploads(created_at DESC);

-- Partition large tables by date
CREATE TABLE file_uploads_2024_01 PARTITION OF file_uploads
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### S3 Configuration

```json
{
  "Rules": [
    {
      "ID": "TransitionToIA",
      "Status": "Enabled",
      "Transition": {
        "Days": 30,
        "StorageClass": "STANDARD_IA"
      }
    },
    {
      "ID": "ArchiveOldFiles",
      "Status": "Enabled",
      "Transition": {
        "Days": 365,
        "StorageClass": "GLACIER"
      }
    }
  ]
}
```

## Testing

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Test specific module
pytest tests/test_storage.py -v

# Coverage report
pytest tests/ --cov=src --cov-report=html
```

### Integration Tests

```bash
# Test with real S3 (requires credentials)
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
pytest tests/integration/ -v

# Test with localstack
docker run -p 4566:4566 localstack/localstack
pytest tests/integration/ -v
```

### Load Testing

```bash
# Install k6
curl https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz -L | tar xvz --strip-components 1

# Run upload load test
k6 run tests/load/upload_test.js
```

## License

This implementation is part of the Req2Run benchmark suite.