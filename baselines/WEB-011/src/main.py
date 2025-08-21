"""
WEB-011: Secure File Upload with Presigned URLs
Main FastAPI application
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from decouple import config
import structlog

from models import (
    PresignedUrlRequest, PresignedUrlResponse, MultipartUploadInitResponse,
    MultipartUploadCompleteRequest, UploadProgressUpdate, FileInfo,
    FileListResponse, ScanResult, UploadStatus, ScanStatus,
    ContentTypeValidator, UploadConfig
)
from database import DatabaseService
from storage import S3StorageService
from scanner import CompositeMalwareScanner


# Setup logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration
DATABASE_URL = config('DATABASE_URL', default='sqlite:///./uploads.db')
S3_BUCKET_NAME = config('S3_BUCKET_NAME', default='secure-uploads')
S3_REGION = config('S3_REGION', default='us-east-1')
S3_ENDPOINT_URL = config('S3_ENDPOINT_URL', default=None)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)

CLAMAV_HOST = config('CLAMAV_HOST', default='localhost')
CLAMAV_PORT = config('CLAMAV_PORT', default=3310, cast=int)
CLAMAV_SOCKET = config('CLAMAV_SOCKET', default=None)

API_KEY = config('API_KEY', default='test-api-key')

# Initialize services
db_service = DatabaseService(DATABASE_URL)
storage_service = S3StorageService(
    bucket_name=S3_BUCKET_NAME,
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
scanner_service = CompositeMalwareScanner(
    enable_clamav=True,
    enable_hash_scanner=True,
    clamd_socket=CLAMAV_SOCKET,
    clamd_host=CLAMAV_HOST,
    clamd_port=CLAMAV_PORT
)

# Security
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="Secure File Upload Service",
    description="Secure file upload system with presigned URLs, malware scanning, and progress tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify API key"""
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials


def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent", ""),
        "user_id": request.headers.get("x-user-id")  # Optional user ID header
    }


@app.on_event("startup")
async def startup_event():
    """Initialize application"""
    logger.info("Starting Secure File Upload Service")
    
    # Test services
    scanner_available = scanner_service.is_available()
    logger.info("Service status", 
               database="initialized",
               storage="initialized", 
               scanner=scanner_available)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Secure File Upload Service")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "ok",
            "storage": "ok",
            "scanner": "ok" if scanner_service.is_available() else "degraded"
        }
    }


@app.post("/api/v1/upload/presign", response_model=PresignedUrlResponse)
async def generate_presigned_url(
    request: PresignedUrlRequest,
    background_tasks: BackgroundTasks,
    client_info: Dict[str, str] = Depends(get_client_info),
    api_key: str = Depends(verify_api_key)
):
    """Generate presigned URL for secure file upload"""
    
    try:
        # Validate content type with filename
        if not ContentTypeValidator.validate_content_type_with_extension(
            request.filename, request.content_type
        ):
            raise HTTPException(
                status_code=400,
                detail="Content type does not match file extension"
            )
        
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Create database record
        await db_service.create_upload_record(
            upload_id=upload_id,
            filename=request.filename,
            original_filename=request.filename,
            content_type=request.content_type,
            size_bytes=request.size_bytes,
            user_id=client_info.get("user_id"),
            client_ip=client_info.get("client_ip"),
            user_agent=client_info.get("user_agent"),
            metadata=request.metadata
        )
        
        # Generate S3 object key
        object_key = storage_service.generate_object_key(upload_id, request.filename)
        
        # Check if multipart upload is needed
        if request.multipart or UploadConfig.should_use_multipart(request.size_bytes):
            return await _handle_multipart_upload(
                upload_id, object_key, request, background_tasks
            )
        else:
            return await _handle_single_upload(
                upload_id, object_key, request, background_tasks
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate presigned URL", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def _handle_single_upload(
    upload_id: str,
    object_key: str,
    request: PresignedUrlRequest,
    background_tasks: BackgroundTasks
) -> PresignedUrlResponse:
    """Handle single-part upload"""
    
    # Generate presigned URL
    upload_url, fields = storage_service.generate_presigned_url(
        object_key=object_key,
        content_type=request.content_type,
        expires_in=UploadConfig.PRESIGNED_URL_EXPIRY
    )
    
    # Update database with upload info
    await db_service.update_upload_status(
        upload_id=upload_id,
        status=UploadStatus.PENDING,
        upload_url=upload_url,
        bucket_name=storage_service.bucket_name,
        object_key=object_key
    )
    
    # Schedule post-upload processing
    background_tasks.add_task(
        _schedule_upload_processing,
        upload_id,
        object_key,
        request.checksum_sha256
    )
    
    logger.info("Single upload presigned URL generated", 
               upload_id=upload_id, filename=request.filename)
    
    return PresignedUrlResponse(
        upload_id=upload_id,
        upload_url=upload_url,
        expires_in=UploadConfig.PRESIGNED_URL_EXPIRY,
        fields=fields
    )


async def _handle_multipart_upload(
    upload_id: str,
    object_key: str,
    request: PresignedUrlRequest,
    background_tasks: BackgroundTasks
) -> PresignedUrlResponse:
    """Handle multipart upload"""
    
    # Initiate multipart upload
    multipart_upload_id = storage_service.initiate_multipart_upload(
        object_key=object_key,
        content_type=request.content_type,
        metadata={"upload_id": upload_id}
    )
    
    # Update database
    await db_service.update_upload_status(
        upload_id=upload_id,
        status=UploadStatus.PENDING,
        bucket_name=storage_service.bucket_name,
        object_key=object_key,
        multipart_upload_id=multipart_upload_id
    )
    
    logger.info("Multipart upload initiated", 
               upload_id=upload_id, 
               multipart_upload_id=multipart_upload_id)
    
    return PresignedUrlResponse(
        upload_id=upload_id,
        upload_url="",  # Not needed for multipart
        expires_in=UploadConfig.PRESIGNED_URL_EXPIRY,
        multipart_upload_id=multipart_upload_id
    )


@app.get("/api/v1/upload/{upload_id}/parts")
async def get_multipart_upload_urls(
    upload_id: str,
    parts: int,
    api_key: str = Depends(verify_api_key)
):
    """Get presigned URLs for multipart upload parts"""
    
    try:
        # Get upload record
        upload = await db_service.get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        if not upload.upload_id:  # multipart_upload_id
            raise HTTPException(status_code=400, detail="Not a multipart upload")
        
        # Validate part count
        if parts < 1 or parts > UploadConfig.MAX_PARTS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid part count. Must be between 1 and {UploadConfig.MAX_PARTS}"
            )
        
        # Generate URLs for each part
        part_urls = []
        for part_number in range(1, parts + 1):
            part_url = storage_service.generate_presigned_upload_part_url(
                object_key=upload.object_key,
                upload_id=upload.upload_id,
                part_number=part_number,
                expires_in=UploadConfig.PRESIGNED_URL_EXPIRY
            )
            
            part_urls.append({
                "part_number": part_number,
                "upload_url": part_url,
                "expires_in": UploadConfig.PRESIGNED_URL_EXPIRY
            })
        
        logger.info("Multipart URLs generated", 
                   upload_id=upload_id, parts=parts)
        
        return {"parts": part_urls}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate multipart URLs", 
                   upload_id=upload_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/upload/{upload_id}/complete")
async def complete_multipart_upload(
    upload_id: str,
    request: MultipartUploadCompleteRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Complete multipart upload"""
    
    try:
        # Get upload record
        upload = await db_service.get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        if not upload.upload_id:  # multipart_upload_id
            raise HTTPException(status_code=400, detail="Not a multipart upload")
        
        # Complete multipart upload
        result = storage_service.complete_multipart_upload(
            object_key=upload.object_key,
            upload_id=upload.upload_id,
            parts=request.parts
        )
        
        # Update database
        await db_service.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.PROCESSING,
            progress_percentage=100
        )
        
        # Schedule post-upload processing
        background_tasks.add_task(
            _process_uploaded_file,
            upload_id,
            upload.object_key
        )
        
        logger.info("Multipart upload completed", 
                   upload_id=upload_id, location=result['location'])
        
        return {
            "upload_id": upload_id,
            "status": "completed",
            "location": result['location']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to complete multipart upload", 
                   upload_id=upload_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v1/upload/{upload_id}/progress")
async def update_upload_progress(
    upload_id: str,
    progress: UploadProgressUpdate,
    api_key: str = Depends(verify_api_key)
):
    """Update upload progress"""
    
    try:
        success = await db_service.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.UPLOADING,
            progress_percentage=progress.progress_percentage
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        logger.debug("Upload progress updated", 
                    upload_id=upload_id, 
                    progress=progress.progress_percentage)
        
        return {"status": "updated"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update progress", 
                   upload_id=upload_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/upload/{upload_id}", response_model=FileInfo)
async def get_upload_info(
    upload_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get upload information"""
    
    try:
        upload = await db_service.get_upload_by_id(upload_id)
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Generate download URL if file is clean and completed
        download_url = None
        if (upload.status == UploadStatus.COMPLETED and 
            upload.scan_status == ScanStatus.CLEAN and 
            upload.object_key):
            
            download_url = storage_service.generate_download_url(
                object_key=upload.object_key,
                expires_in=3600,
                filename=upload.original_filename
            )
        
        return FileInfo(
            id=str(upload.id),
            filename=upload.filename,
            original_filename=upload.original_filename,
            content_type=upload.content_type,
            size_bytes=upload.size_bytes,
            status=upload.status,
            scan_status=upload.scan_status,
            progress_percentage=upload.progress_percentage,
            created_at=upload.created_at,
            uploaded_at=upload.uploaded_at,
            expires_at=upload.expires_at,
            download_url=download_url,
            metadata=upload.metadata
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get upload info", 
                   upload_id=upload_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/uploads", response_model=FileListResponse)
async def list_uploads(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    """List uploads with pagination"""
    
    try:
        # Validate parameters
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        upload_status = None
        if status:
            try:
                upload_status = UploadStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status")
        
        # Get uploads from database
        result = await db_service.list_uploads(
            user_id=user_id,
            status=upload_status,
            page=page,
            page_size=page_size
        )
        
        # Convert to FileInfo objects
        files = []
        for upload in result['uploads']:
            download_url = None
            if (upload.status == UploadStatus.COMPLETED and 
                upload.scan_status == ScanStatus.CLEAN and 
                upload.object_key):
                
                download_url = storage_service.generate_download_url(
                    object_key=upload.object_key,
                    expires_in=3600,
                    filename=upload.original_filename
                )
            
            files.append(FileInfo(
                id=str(upload.id),
                filename=upload.filename,
                original_filename=upload.original_filename,
                content_type=upload.content_type,
                size_bytes=upload.size_bytes,
                status=upload.status,
                scan_status=upload.scan_status,
                progress_percentage=upload.progress_percentage,
                created_at=upload.created_at,
                uploaded_at=upload.uploaded_at,
                expires_at=upload.expires_at,
                download_url=download_url,
                metadata=upload.metadata
            ))
        
        return FileListResponse(
            files=files,
            total_count=result['total_count'],
            page=result['page'],
            page_size=result['page_size'],
            has_more=result['has_more']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list uploads", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/stats")
async def get_upload_statistics(api_key: str = Depends(verify_api_key)):
    """Get upload statistics"""
    
    try:
        stats = await db_service.get_upload_statistics()
        return stats
    
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


async def _schedule_upload_processing(
    upload_id: str, 
    object_key: str, 
    expected_hash: Optional[str] = None
):
    """Schedule post-upload processing"""
    # Wait a bit for upload to complete
    await asyncio.sleep(2)
    
    # Check if file exists and process
    await _process_uploaded_file(upload_id, object_key, expected_hash)


async def _process_uploaded_file(
    upload_id: str, 
    object_key: str, 
    expected_hash: Optional[str] = None
):
    """Process uploaded file (integrity check and malware scan)"""
    
    try:
        logger.info("Processing uploaded file", upload_id=upload_id)
        
        # Update status to processing
        await db_service.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.PROCESSING
        )
        
        # Get object info
        object_info = storage_service.get_object_info(object_key)
        if not object_info:
            await db_service.update_upload_status(
                upload_id=upload_id,
                status=UploadStatus.FAILED
            )
            logger.error("Uploaded file not found", upload_id=upload_id)
            return
        
        # Verify integrity if hash provided
        if expected_hash:
            is_valid = storage_service.verify_upload_integrity(object_key, expected_hash)
            if not is_valid:
                await db_service.update_upload_status(
                    upload_id=upload_id,
                    status=UploadStatus.FAILED
                )
                logger.error("File integrity check failed", upload_id=upload_id)
                return
            
            await db_service.update_file_hash(upload_id, expected_hash)
        
        # Perform malware scan
        await _scan_uploaded_file(upload_id, object_key)
        
    except Exception as e:
        logger.error("File processing failed", upload_id=upload_id, error=str(e))
        await db_service.update_upload_status(
            upload_id=upload_id,
            status=UploadStatus.FAILED
        )


async def _scan_uploaded_file(upload_id: str, object_key: str):
    """Scan uploaded file for malware"""
    
    try:
        logger.info("Scanning file for malware", upload_id=upload_id)
        
        # Update scan status
        await db_service.update_scan_result(
            upload_id=upload_id,
            scan_status=ScanStatus.SCANNING
        )
        
        # Download file content for scanning (for small files)
        # In production, you might want to scan directly from S3 or use a streaming approach
        import boto3
        s3_client = storage_service.s3_client
        
        try:
            response = s3_client.get_object(
                Bucket=storage_service.bucket_name,
                Key=object_key
            )
            file_content = response['Body'].read()
        except Exception as e:
            logger.error("Failed to download file for scanning", 
                       upload_id=upload_id, error=str(e))
            await db_service.update_scan_result(
                upload_id=upload_id,
                scan_status=ScanStatus.ERROR
            )
            return
        
        # Perform scan
        scan_results = await scanner_service.scan_file_content(
            file_content=file_content,
            filename=object_key
        )
        
        # Get composite result
        final_result = scanner_service.get_composite_result(scan_results)
        
        # Process scan result
        if final_result.status == ScanStatus.INFECTED:
            # Move to quarantine
            quarantine_key = storage_service.move_to_quarantine(object_key)
            
            await db_service.update_scan_result(
                upload_id=upload_id,
                scan_status=ScanStatus.INFECTED,
                scan_result={
                    "threats": final_result.threats,
                    "scan_engine": final_result.scan_engine,
                    "scan_details": final_result.scan_details
                },
                quarantine_reason=f"Threats found: {', '.join(final_result.threats)}"
            )
            
            logger.warning("File quarantined due to threats", 
                         upload_id=upload_id, 
                         threats=final_result.threats)
            
        elif final_result.status == ScanStatus.CLEAN:
            # File is clean
            await db_service.update_scan_result(
                upload_id=upload_id,
                scan_status=ScanStatus.CLEAN,
                scan_result={
                    "scan_engine": final_result.scan_engine,
                    "scan_details": final_result.scan_details
                }
            )
            
            # Update overall status to completed
            await db_service.update_upload_status(
                upload_id=upload_id,
                status=UploadStatus.COMPLETED
            )
            
            logger.info("File scan completed - clean", upload_id=upload_id)
            
        else:
            # Scan error
            await db_service.update_scan_result(
                upload_id=upload_id,
                scan_status=ScanStatus.ERROR,
                scan_result={
                    "error": "Scan failed",
                    "scan_details": final_result.scan_details
                }
            )
            
            logger.error("File scan failed", upload_id=upload_id)
        
    except Exception as e:
        logger.error("Malware scan failed", upload_id=upload_id, error=str(e))
        await db_service.update_scan_result(
            upload_id=upload_id,
            scan_status=ScanStatus.ERROR
        )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )