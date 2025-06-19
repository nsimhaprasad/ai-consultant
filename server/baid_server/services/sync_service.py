"""Sync service for baid-sync functionality."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict
from google.cloud import storage
from baid_server.config import settings

logger = logging.getLogger(__name__)


class SyncService:
    """Service for handling directory synchronization to Google Cloud Storage."""

    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = getattr(settings, 'GCS_SYNC_BUCKET', 'baid-sync-storage')
        self.url_expiration_hours = 1  # URLs expire in 1 hour

    def generate_signed_url(
        self, 
        filename: str,
        content_type: str,
        user_id: str
    ) -> str:
        """Generate a signed URL for uploading compressed archive to Google Cloud Storage.
        
        Args:
            filename: Name of the file to upload (e.g., "project_20230101_120000.tar.gz")
            content_type: MIME type of the file (e.g., "application/gzip")
            user_id: User ID for organizing storage
            
        Returns:
            Signed URL for uploading the file
        """
        try:
            bucket = self.client.bucket(self.bucket_name)
            
            # Create expiration time
            expiration = datetime.now(timezone.utc) + timedelta(hours=self.url_expiration_hours)
            
            # Create GCS object path: users/{user_id}/archives/{filename}
            object_path = f"users/{user_id}/archives/{filename}"
            
            # Get blob reference
            blob = bucket.blob(object_path)
            
            # Generate signed URL for uploading
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=expiration,
                method="PUT",
                content_type=content_type
            )
            
            logger.info(f"Generated signed URL for file {filename} for user {user_id}")
            return signed_url
            
        except Exception as e:
            logger.error(f"Error generating signed URL: {str(e)}")
            raise Exception(f"Failed to generate signed URL: {str(e)}")

    def validate_sync_request(
        self, 
        filename: str,
        content_type: str
    ) -> None:
        """Validate sync request parameters.
        
        Args:
            filename: Filename to validate
            content_type: Content type to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not filename or len(filename.strip()) == 0:
            raise ValueError("Filename is required")
            
        if not content_type or len(content_type.strip()) == 0:
            raise ValueError("Content type is required")
            
        # Validate filename doesn't contain path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename - path traversal not allowed")
            
        # Validate content type for compressed archives
        allowed_content_types = [
            "application/gzip",
            "application/x-gzip", 
            "application/x-tar",
            "application/x-compressed-tar"
        ]
        
        if content_type not in allowed_content_types:
            raise ValueError(f"Invalid content type. Allowed types: {', '.join(allowed_content_types)}")

    def get_bucket_info(self) -> Dict[str, str]:
        """Get information about the configured storage bucket.
        
        Returns:
            Dictionary with bucket information
        """
        try:
            bucket = self.client.bucket(self.bucket_name)
            return {
                "bucket_name": self.bucket_name,
                "location": bucket.location or "unknown",
                "storage_class": bucket.storage_class or "unknown"
            }
        except Exception as e:
            logger.error(f"Error getting bucket info: {str(e)}")
            return {
                "bucket_name": self.bucket_name,
                "location": "unknown",
                "storage_class": "unknown",
                "error": str(e)
            }