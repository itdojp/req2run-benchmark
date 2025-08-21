"""Database service for file upload management"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import structlog

from models import Base, FileUpload, UploadStatus, ScanStatus


logger = structlog.get_logger()


class DatabaseService:
    """Database service for managing file uploads"""
    
    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        
        # Create engine
        self.engine = create_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False
        )
        
        # Create tables
        self._create_tables()
        
        logger.info("Database service initialized", database_url=database_url[:50])
    
    def _create_tables(self):
        """Create database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
        except SQLAlchemyError as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    async def create_upload_record(self, 
                                 upload_id: str,
                                 filename: str,
                                 original_filename: str,
                                 content_type: str,
                                 size_bytes: int,
                                 user_id: Optional[str] = None,
                                 client_ip: Optional[str] = None,
                                 user_agent: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> FileUpload:
        """Create new upload record"""
        
        def _create_record():
            with self.get_session() as session:
                try:
                    upload = FileUpload(
                        id=upload_id,
                        filename=filename,
                        original_filename=original_filename,
                        content_type=content_type,
                        size_bytes=size_bytes,
                        status=UploadStatus.PENDING,
                        scan_status=ScanStatus.PENDING,
                        user_id=user_id,
                        client_ip=client_ip,
                        user_agent=user_agent,
                        metadata=metadata or {},
                        expires_at=datetime.utcnow() + timedelta(hours=24)
                    )
                    
                    session.add(upload)
                    session.commit()
                    session.refresh(upload)
                    
                    logger.info("Upload record created", 
                               upload_id=upload_id, 
                               filename=filename)
                    
                    return upload
                
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error("Failed to create upload record", 
                               upload_id=upload_id, error=str(e))
                    raise
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _create_record)
    
    async def get_upload_by_id(self, upload_id: str) -> Optional[FileUpload]:
        """Get upload record by ID"""
        
        def _get_upload():
            with self.get_session() as session:
                try:
                    upload = session.query(FileUpload).filter(
                        FileUpload.id == upload_id
                    ).first()
                    
                    if upload:
                        # Detach from session to use outside
                        session.expunge(upload)
                    
                    return upload
                
                except SQLAlchemyError as e:
                    logger.error("Failed to get upload record", 
                               upload_id=upload_id, error=str(e))
                    return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_upload)
    
    async def update_upload_status(self, 
                                 upload_id: str, 
                                 status: UploadStatus,
                                 progress_percentage: Optional[int] = None,
                                 upload_url: Optional[str] = None,
                                 bucket_name: Optional[str] = None,
                                 object_key: Optional[str] = None,
                                 multipart_upload_id: Optional[str] = None) -> bool:
        """Update upload status"""
        
        def _update_status():
            with self.get_session() as session:
                try:
                    upload = session.query(FileUpload).filter(
                        FileUpload.id == upload_id
                    ).first()
                    
                    if not upload:
                        return False
                    
                    # Update fields
                    upload.status = status
                    
                    if progress_percentage is not None:
                        upload.progress_percentage = progress_percentage
                    
                    if upload_url is not None:
                        upload.upload_url = upload_url
                    
                    if bucket_name is not None:
                        upload.bucket_name = bucket_name
                    
                    if object_key is not None:
                        upload.object_key = object_key
                    
                    if multipart_upload_id is not None:
                        upload.upload_id = multipart_upload_id
                    
                    # Update timestamps
                    if status == UploadStatus.UPLOADING and not upload.uploaded_at:
                        upload.uploaded_at = datetime.utcnow()
                    elif status == UploadStatus.COMPLETED:
                        upload.uploaded_at = datetime.utcnow()
                        upload.progress_percentage = 100
                    
                    session.commit()
                    
                    logger.info("Upload status updated", 
                               upload_id=upload_id, 
                               status=status.value,
                               progress=progress_percentage)
                    
                    return True
                
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error("Failed to update upload status", 
                               upload_id=upload_id, error=str(e))
                    return False
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _update_status)
    
    async def update_scan_result(self, 
                               upload_id: str,
                               scan_status: ScanStatus,
                               scan_result: Optional[Dict[str, Any]] = None,
                               quarantine_reason: Optional[str] = None) -> bool:
        """Update scan results"""
        
        def _update_scan():
            with self.get_session() as session:
                try:
                    upload = session.query(FileUpload).filter(
                        FileUpload.id == upload_id
                    ).first()
                    
                    if not upload:
                        return False
                    
                    upload.scan_status = scan_status
                    upload.scanned_at = datetime.utcnow()
                    
                    if scan_result is not None:
                        upload.scan_result = scan_result
                    
                    if quarantine_reason is not None:
                        upload.quarantine_reason = quarantine_reason
                    
                    # Update overall status if needed
                    if scan_status == ScanStatus.INFECTED:
                        upload.status = UploadStatus.QUARANTINED
                    elif scan_status == ScanStatus.CLEAN and upload.status == UploadStatus.PROCESSING:
                        upload.status = UploadStatus.COMPLETED
                    
                    session.commit()
                    
                    logger.info("Scan result updated", 
                               upload_id=upload_id, 
                               scan_status=scan_status.value)
                    
                    return True
                
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error("Failed to update scan result", 
                               upload_id=upload_id, error=str(e))
                    return False
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _update_scan)
    
    async def update_file_hash(self, upload_id: str, checksum_sha256: str) -> bool:
        """Update file hash after upload"""
        
        def _update_hash():
            with self.get_session() as session:
                try:
                    upload = session.query(FileUpload).filter(
                        FileUpload.id == upload_id
                    ).first()
                    
                    if not upload:
                        return False
                    
                    upload.checksum_sha256 = checksum_sha256
                    session.commit()
                    
                    logger.debug("File hash updated", 
                               upload_id=upload_id, 
                               hash=checksum_sha256[:16])
                    
                    return True
                
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error("Failed to update file hash", 
                               upload_id=upload_id, error=str(e))
                    return False
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _update_hash)
    
    async def list_uploads(self, 
                         user_id: Optional[str] = None,
                         status: Optional[UploadStatus] = None,
                         scan_status: Optional[ScanStatus] = None,
                         page: int = 1,
                         page_size: int = 20) -> Dict[str, Any]:
        """List uploads with pagination"""
        
        def _list_uploads():
            with self.get_session() as session:
                try:
                    query = session.query(FileUpload)
                    
                    # Apply filters
                    if user_id:
                        query = query.filter(FileUpload.user_id == user_id)
                    
                    if status:
                        query = query.filter(FileUpload.status == status)
                    
                    if scan_status:
                        query = query.filter(FileUpload.scan_status == scan_status)
                    
                    # Get total count
                    total_count = query.count()
                    
                    # Apply pagination
                    offset = (page - 1) * page_size
                    uploads = query.order_by(desc(FileUpload.created_at))\
                                 .offset(offset)\
                                 .limit(page_size)\
                                 .all()
                    
                    # Detach from session
                    for upload in uploads:
                        session.expunge(upload)
                    
                    return {
                        'uploads': uploads,
                        'total_count': total_count,
                        'page': page,
                        'page_size': page_size,
                        'has_more': total_count > (page * page_size)
                    }
                
                except SQLAlchemyError as e:
                    logger.error("Failed to list uploads", error=str(e))
                    return {
                        'uploads': [],
                        'total_count': 0,
                        'page': page,
                        'page_size': page_size,
                        'has_more': False
                    }
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _list_uploads)
    
    async def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics"""
        
        def _get_stats():
            with self.get_session() as session:
                try:
                    # Count by status
                    status_counts = {}
                    for status in UploadStatus:
                        count = session.query(FileUpload).filter(
                            FileUpload.status == status
                        ).count()
                        status_counts[status.value] = count
                    
                    # Count by scan status
                    scan_status_counts = {}
                    for scan_status in ScanStatus:
                        count = session.query(FileUpload).filter(
                            FileUpload.scan_status == scan_status
                        ).count()
                        scan_status_counts[scan_status.value] = count
                    
                    # Total size
                    total_size = session.query(func.sum(FileUpload.size_bytes)).scalar() or 0
                    
                    # Upload count by date (last 30 days)
                    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
                    recent_uploads = session.query(FileUpload).filter(
                        FileUpload.created_at >= thirty_days_ago
                    ).count()
                    
                    return {
                        'status_counts': status_counts,
                        'scan_status_counts': scan_status_counts,
                        'total_files': sum(status_counts.values()),
                        'total_size_bytes': total_size,
                        'recent_uploads_30d': recent_uploads
                    }
                
                except SQLAlchemyError as e:
                    logger.error("Failed to get upload statistics", error=str(e))
                    return {}
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_stats)
    
    async def cleanup_expired_uploads(self) -> int:
        """Clean up expired upload records"""
        
        def _cleanup():
            with self.get_session() as session:
                try:
                    # Find expired uploads
                    now = datetime.utcnow()
                    expired_uploads = session.query(FileUpload).filter(
                        and_(
                            FileUpload.expires_at < now,
                            or_(
                                FileUpload.status == UploadStatus.PENDING,
                                FileUpload.status == UploadStatus.FAILED
                            )
                        )
                    ).all()
                    
                    # Delete expired records
                    deleted_count = 0
                    for upload in expired_uploads:
                        session.delete(upload)
                        deleted_count += 1
                    
                    session.commit()
                    
                    if deleted_count > 0:
                        logger.info("Cleaned up expired uploads", count=deleted_count)
                    
                    return deleted_count
                
                except SQLAlchemyError as e:
                    session.rollback()
                    logger.error("Failed to cleanup expired uploads", error=str(e))
                    return 0
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _cleanup)
    
    async def get_pending_scans(self, limit: int = 10) -> List[FileUpload]:
        """Get uploads pending malware scan"""
        
        def _get_pending():
            with self.get_session() as session:
                try:
                    uploads = session.query(FileUpload).filter(
                        and_(
                            FileUpload.status == UploadStatus.PROCESSING,
                            FileUpload.scan_status == ScanStatus.PENDING
                        )
                    ).order_by(FileUpload.created_at)\
                     .limit(limit)\
                     .all()
                    
                    # Detach from session
                    for upload in uploads:
                        session.expunge(upload)
                    
                    return uploads
                
                except SQLAlchemyError as e:
                    logger.error("Failed to get pending scans", error=str(e))
                    return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_pending)