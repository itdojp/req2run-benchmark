"""Data models for secure file upload system"""
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, List, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import magic


Base = declarative_base()


class UploadStatus(str, Enum):
    """Upload status enumeration"""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    CANCELLED = "cancelled"


class ScanStatus(str, Enum):
    """Malware scan status"""
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"


class FileUpload(Base):
    """Database model for file uploads"""
    __tablename__ = "file_uploads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    
    # Upload metadata
    upload_url = Column(Text)
    upload_id = Column(String(255))  # For multipart uploads
    bucket_name = Column(String(100))
    object_key = Column(String(500))
    
    # Status tracking
    status = Column(String(20), default=UploadStatus.PENDING)
    scan_status = Column(String(20), default=ScanStatus.PENDING)
    progress_percentage = Column(Integer, default=0)
    
    # Security
    checksum_sha256 = Column(String(64))
    scan_result = Column(JSON)
    quarantine_reason = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime)
    scanned_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # User context
    user_id = Column(String(100))
    client_ip = Column(String(45))
    user_agent = Column(Text)
    
    # Additional metadata
    metadata = Column(JSON)


class PresignedUrlRequest(BaseModel):
    """Request model for presigned URL generation"""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., min_length=1, max_length=100)
    size_bytes: int = Field(..., gt=0, le=10 * 1024 * 1024 * 1024)  # Max 10GB
    checksum_sha256: Optional[str] = Field(None, regex=r'^[a-fA-F0-9]{64}$')
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    multipart: Optional[bool] = Field(default=False)
    
    @validator('filename')
    def validate_filename(cls, v):
        # Basic filename validation
        forbidden_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in v for char in forbidden_chars):
            raise ValueError(f'Filename contains forbidden characters: {forbidden_chars}')
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        # Allowed MIME types
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv',
            'application/zip', 'application/x-zip-compressed',
            'video/mp4', 'video/quicktime', 'video/x-msvideo',
            'audio/mpeg', 'audio/wav', 'audio/x-wav'
        ]
        
        if v not in allowed_types:
            raise ValueError(f'Content type {v} not allowed')
        return v


class PresignedUrlResponse(BaseModel):
    """Response model for presigned URL"""
    upload_id: str
    upload_url: str
    expires_in: int  # seconds
    fields: Optional[Dict[str, str]] = None  # For POST uploads
    headers: Optional[Dict[str, str]] = None  # For PUT uploads
    multipart_upload_id: Optional[str] = None  # For multipart uploads


class MultipartUploadPart(BaseModel):
    """Model for multipart upload part"""
    part_number: int = Field(..., ge=1, le=10000)
    upload_url: str
    expires_in: int


class MultipartUploadInitResponse(BaseModel):
    """Response for multipart upload initialization"""
    upload_id: str
    multipart_upload_id: str
    parts: List[MultipartUploadPart]


class MultipartUploadCompleteRequest(BaseModel):
    """Request to complete multipart upload"""
    upload_id: str
    parts: List[Dict[str, Any]]  # [{PartNumber: int, ETag: str}]


class UploadProgressUpdate(BaseModel):
    """Upload progress update model"""
    upload_id: str
    progress_percentage: int = Field(..., ge=0, le=100)
    bytes_uploaded: int = Field(..., ge=0)


class FileInfo(BaseModel):
    """File information response"""
    id: str
    filename: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: UploadStatus
    scan_status: ScanStatus
    progress_percentage: int
    created_at: datetime
    uploaded_at: Optional[datetime]
    expires_at: Optional[datetime]
    download_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FileListResponse(BaseModel):
    """Response for file listing"""
    files: List[FileInfo]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class ScanResult(BaseModel):
    """Malware scan result"""
    upload_id: str
    status: ScanStatus
    scan_engine: str
    scanned_at: datetime
    threats_found: List[str] = Field(default_factory=list)
    scan_details: Optional[Dict[str, Any]] = None


class UploadConfig:
    """Configuration constants for uploads"""
    
    # File size limits (bytes)
    MIN_FILE_SIZE = 1  # 1 byte
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB
    MAX_MULTIPART_THRESHOLD = 100 * 1024 * 1024  # 100MB
    
    # Multipart configuration
    MULTIPART_PART_SIZE = 5 * 1024 * 1024  # 5MB minimum
    MAX_PARTS = 10000
    
    # Security settings
    PRESIGNED_URL_EXPIRY = 3600  # 1 hour
    UPLOAD_TOKEN_EXPIRY = 24 * 3600  # 24 hours
    
    # Quarantine settings
    QUARANTINE_RETENTION_DAYS = 30
    
    # Progress tracking
    PROGRESS_UPDATE_INTERVAL = 5  # seconds
    
    @classmethod
    def get_multipart_part_count(cls, file_size: int) -> int:
        """Calculate number of parts for multipart upload"""
        if file_size <= cls.MULTIPART_PART_SIZE:
            return 1
        
        part_count = (file_size + cls.MULTIPART_PART_SIZE - 1) // cls.MULTIPART_PART_SIZE
        return min(part_count, cls.MAX_PARTS)
    
    @classmethod
    def should_use_multipart(cls, file_size: int) -> bool:
        """Determine if multipart upload should be used"""
        return file_size > cls.MAX_MULTIPART_THRESHOLD


class ContentTypeValidator:
    """Utility for content type validation"""
    
    ALLOWED_EXTENSIONS = {
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv',
        # Archives
        '.zip',
        # Media
        '.mp4', '.mov', '.avi', '.mp3', '.wav'
    }
    
    MIME_TO_EXTENSIONS = {
        'image/jpeg': ['.jpg', '.jpeg'],
        'image/png': ['.png'],
        'image/gif': ['.gif'],
        'image/webp': ['.webp'],
        'application/pdf': ['.pdf'],
        'application/msword': ['.doc'],
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
        'application/vnd.ms-excel': ['.xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
        'text/plain': ['.txt'],
        'text/csv': ['.csv'],
        'application/zip': ['.zip'],
        'video/mp4': ['.mp4'],
        'video/quicktime': ['.mov'],
        'video/x-msvideo': ['.avi'],
        'audio/mpeg': ['.mp3'],
        'audio/wav': ['.wav']
    }
    
    @classmethod
    def validate_content_type_with_extension(cls, filename: str, content_type: str) -> bool:
        """Validate that content type matches file extension"""
        import os
        
        ext = os.path.splitext(filename.lower())[1]
        
        if ext not in cls.ALLOWED_EXTENSIONS:
            return False
        
        expected_extensions = cls.MIME_TO_EXTENSIONS.get(content_type, [])
        return ext in expected_extensions
    
    @classmethod
    def detect_content_type_from_content(cls, file_content: bytes) -> str:
        """Detect content type from file content using python-magic"""
        try:
            mime = magic.Magic(mime=True)
            detected_type = mime.from_buffer(file_content)
            return detected_type
        except Exception:
            return 'application/octet-stream'
    
    @classmethod
    def is_allowed_content_type(cls, content_type: str) -> bool:
        """Check if content type is in allowed list"""
        return content_type in cls.MIME_TO_EXTENSIONS