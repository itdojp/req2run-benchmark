"""Cloud storage service for secure file uploads"""
import boto3
import hashlib
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from urllib.parse import urlparse
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import structlog

from models import UploadConfig


logger = structlog.get_logger()


class S3StorageService:
    """AWS S3 storage service for file uploads"""
    
    def __init__(self, 
                 bucket_name: str,
                 region_name: str = "us-east-1",
                 endpoint_url: Optional[str] = None,
                 aws_access_key_id: Optional[str] = None,
                 aws_secret_access_key: Optional[str] = None):
        
        self.bucket_name = bucket_name
        self.region_name = region_name
        
        # Configure S3 client
        config = Config(
            region_name=region_name,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        )
        
        session_kwargs = {}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs.update({
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key
            })
        
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            config=config,
            **session_kwargs
        )
        
        # Initialize bucket if it doesn't exist
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 bucket verified", bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.region_name == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region_name}
                        )
                    
                    # Configure bucket for security
                    self._configure_bucket_security()
                    logger.info("S3 bucket created", bucket=self.bucket_name)
                    
                except ClientError as create_error:
                    logger.error("Failed to create S3 bucket", 
                               bucket=self.bucket_name, error=str(create_error))
                    raise
            else:
                logger.error("Failed to access S3 bucket", 
                           bucket=self.bucket_name, error=str(e))
                raise
    
    def _configure_bucket_security(self):
        """Configure bucket security settings"""
        try:
            # Block public access
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': True,
                    'IgnorePublicAcls': True,
                    'BlockPublicPolicy': True,
                    'RestrictPublicBuckets': True
                }
            )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=self.bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Configure lifecycle rules
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration={
                    'Rules': [
                        {
                            'ID': 'QuarantineCleanup',
                            'Status': 'Enabled',
                            'Filter': {'Prefix': 'quarantine/'},
                            'Expiration': {'Days': UploadConfig.QUARANTINE_RETENTION_DAYS}
                        },
                        {
                            'ID': 'IncompleteMultipartCleanup',
                            'Status': 'Enabled',
                            'Filter': {},
                            'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 1}
                        }
                    ]
                }
            )
            
            logger.info("S3 bucket security configured", bucket=self.bucket_name)
            
        except ClientError as e:
            logger.warning("Failed to configure bucket security", 
                         bucket=self.bucket_name, error=str(e))
    
    def generate_object_key(self, upload_id: str, filename: str, quarantined: bool = False) -> str:
        """Generate S3 object key for uploaded file"""
        # Create date-based prefix
        now = datetime.utcnow()
        date_prefix = now.strftime("%Y/%m/%d")
        
        # Add quarantine prefix if needed
        prefix = "quarantine/" if quarantined else "uploads/"
        
        # Sanitize filename
        sanitized_filename = self._sanitize_filename(filename)
        
        return f"{prefix}{date_prefix}/{upload_id}/{sanitized_filename}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for S3 storage"""
        # Replace problematic characters
        filename = filename.replace(' ', '_')
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        return filename[:100]  # Limit length
    
    def generate_presigned_url(self, 
                             object_key: str, 
                             content_type: str,
                             expires_in: int = UploadConfig.PRESIGNED_URL_EXPIRY) -> Tuple[str, Dict[str, str]]:
        """Generate presigned URL for direct upload"""
        try:
            # Generate presigned POST
            conditions = [
                {"Content-Type": content_type},
                ["content-length-range", 1, UploadConfig.MAX_FILE_SIZE]
            ]
            
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=object_key,
                Fields={"Content-Type": content_type},
                Conditions=conditions,
                ExpiresIn=expires_in
            )
            
            logger.info("Presigned URL generated", 
                       object_key=object_key, expires_in=expires_in)
            
            return presigned_post['url'], presigned_post['fields']
            
        except ClientError as e:
            logger.error("Failed to generate presigned URL", 
                       object_key=object_key, error=str(e))
            raise
    
    def initiate_multipart_upload(self, 
                                 object_key: str, 
                                 content_type: str,
                                 metadata: Optional[Dict[str, str]] = None) -> str:
        """Initiate multipart upload"""
        try:
            kwargs = {
                'Bucket': self.bucket_name,
                'Key': object_key,
                'ContentType': content_type
            }
            
            if metadata:
                kwargs['Metadata'] = metadata
            
            response = self.s3_client.create_multipart_upload(**kwargs)
            upload_id = response['UploadId']
            
            logger.info("Multipart upload initiated", 
                       object_key=object_key, upload_id=upload_id)
            
            return upload_id
            
        except ClientError as e:
            logger.error("Failed to initiate multipart upload", 
                       object_key=object_key, error=str(e))
            raise
    
    def generate_presigned_upload_part_url(self, 
                                         object_key: str, 
                                         upload_id: str, 
                                         part_number: int,
                                         expires_in: int = UploadConfig.PRESIGNED_URL_EXPIRY) -> str:
        """Generate presigned URL for multipart upload part"""
        try:
            url = self.s3_client.generate_presigned_url(
                'upload_part',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key,
                    'UploadId': upload_id,
                    'PartNumber': part_number
                },
                ExpiresIn=expires_in
            )
            
            logger.debug("Presigned part URL generated", 
                        object_key=object_key, part_number=part_number)
            
            return url
            
        except ClientError as e:
            logger.error("Failed to generate presigned part URL", 
                       object_key=object_key, part_number=part_number, error=str(e))
            raise
    
    def complete_multipart_upload(self, 
                                 object_key: str, 
                                 upload_id: str, 
                                 parts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Complete multipart upload"""
        try:
            response = self.s3_client.complete_multipart_upload(
                Bucket=self.bucket_name,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            
            logger.info("Multipart upload completed", 
                       object_key=object_key, upload_id=upload_id)
            
            return {
                'location': response['Location'],
                'etag': response['ETag'],
                'version_id': response.get('VersionId')
            }
            
        except ClientError as e:
            logger.error("Failed to complete multipart upload", 
                       object_key=object_key, upload_id=upload_id, error=str(e))
            raise
    
    def abort_multipart_upload(self, object_key: str, upload_id: str):
        """Abort multipart upload"""
        try:
            self.s3_client.abort_multipart_upload(
                Bucket=self.bucket_name,
                Key=object_key,
                UploadId=upload_id
            )
            
            logger.info("Multipart upload aborted", 
                       object_key=object_key, upload_id=upload_id)
            
        except ClientError as e:
            logger.error("Failed to abort multipart upload", 
                       object_key=object_key, upload_id=upload_id, error=str(e))
            raise
    
    def get_object_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """Get object metadata"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'content_type': response.get('ContentType'),
                'content_length': response.get('ContentLength'),
                'last_modified': response.get('LastModified'),
                'etag': response.get('ETag'),
                'metadata': response.get('Metadata', {}),
                'version_id': response.get('VersionId')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            logger.error("Failed to get object info", 
                       object_key=object_key, error=str(e))
            raise
    
    def generate_download_url(self, 
                            object_key: str, 
                            expires_in: int = 3600,
                            filename: Optional[str] = None) -> str:
        """Generate presigned URL for download"""
        try:
            params = {
                'Bucket': self.bucket_name,
                'Key': object_key
            }
            
            # Add content disposition for download
            if filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'
            
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            
            logger.debug("Download URL generated", 
                        object_key=object_key, expires_in=expires_in)
            
            return url
            
        except ClientError as e:
            logger.error("Failed to generate download URL", 
                       object_key=object_key, error=str(e))
            raise
    
    def move_to_quarantine(self, object_key: str) -> str:
        """Move object to quarantine folder"""
        try:
            # Generate quarantine key
            quarantine_key = object_key.replace('uploads/', 'quarantine/')
            
            # Copy object to quarantine location
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': object_key},
                Key=quarantine_key
            )
            
            # Delete original object
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info("Object moved to quarantine", 
                       original_key=object_key, quarantine_key=quarantine_key)
            
            return quarantine_key
            
        except ClientError as e:
            logger.error("Failed to move object to quarantine", 
                       object_key=object_key, error=str(e))
            raise
    
    def delete_object(self, object_key: str):
        """Delete object from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            logger.info("Object deleted", object_key=object_key)
            
        except ClientError as e:
            logger.error("Failed to delete object", 
                       object_key=object_key, error=str(e))
            raise
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    def verify_upload_integrity(self, object_key: str, expected_hash: str) -> bool:
        """Verify uploaded file integrity using hash comparison"""
        try:
            # Download file content
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            content = response['Body'].read()
            actual_hash = self.calculate_file_hash(content)
            
            is_valid = actual_hash == expected_hash
            
            logger.info("Upload integrity verified", 
                       object_key=object_key, 
                       valid=is_valid,
                       expected_hash=expected_hash[:8],
                       actual_hash=actual_hash[:8])
            
            return is_valid
            
        except ClientError as e:
            logger.error("Failed to verify upload integrity", 
                       object_key=object_key, error=str(e))
            return False