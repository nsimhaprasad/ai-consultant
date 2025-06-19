"""Core synchronization functionality for BAID-Sync

This module handles directory compression, uploading to Google Cloud Storage,
and the continuous sync loop functionality.
"""

import os
import time
import tarfile
import tempfile
import hashlib
import logging
from pathlib import Path
from typing import Optional, List
import requests
from datetime import datetime
from .auth import BASE_URL

logger = logging.getLogger("baid-sync")

# Default ignore patterns
DEFAULT_IGNORE_PATTERNS = [
    '.git',
    '.gitignore',
    '__pycache__',
    '*.pyc',
    '.DS_Store',
    'node_modules',
    '.env',
    '.venv',
    'venv',
    '.pytest_cache',
    '.coverage',
    'dist',
    'build',
    '*.egg-info',
    '.mypy_cache',
    '.idea',
    '.vscode'
]


class DirectorySync:
    """Handles directory synchronization to Google Cloud Storage"""

    def __init__(self, config, directory_path: str, ignore_patterns: Optional[List[str]] = None):
        self.config = config
        self.directory_path = Path(directory_path).resolve()
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self.last_sync_hash = None
        
        if not self.directory_path.exists():
            raise ValueError(f"Directory does not exist: {self.directory_path}")
        
        if not self.directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory_path}")

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on ignore patterns"""
        path_str = str(path)
        relative_path = path.relative_to(self.directory_path)
        relative_str = str(relative_path)
        
        for pattern in self.ignore_patterns:
            if pattern.startswith('*.'):
                # Handle file extensions
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in relative_str or pattern == relative_path.name:
                return True
        return False

    def get_files_to_sync(self) -> List[Path]:
        """Get list of files that should be synchronized"""
        files = []
        for root, dirs, filenames in os.walk(self.directory_path):
            root_path = Path(root)
            
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
            
            for filename in filenames:
                file_path = root_path / filename
                if not self.should_ignore(file_path):
                    files.append(file_path)
        
        return files

    def calculate_directory_hash(self) -> str:
        """Calculate a hash of the directory contents to detect changes"""
        hasher = hashlib.sha256()
        
        files = sorted(self.get_files_to_sync())
        for file_path in files:
            try:
                # Add relative path to hash
                relative_path = file_path.relative_to(self.directory_path)
                hasher.update(str(relative_path).encode('utf-8'))
                
                # Add file modification time and size
                stat = file_path.stat()
                hasher.update(str(stat.st_mtime).encode('utf-8'))
                hasher.update(str(stat.st_size).encode('utf-8'))
                
            except (OSError, IOError) as e:
                logger.warning(f"Error reading file {file_path}: {e}")
                continue
        
        return hasher.hexdigest()

    def has_changes(self) -> bool:
        """Check if directory has changes since last sync"""
        current_hash = self.calculate_directory_hash()
        if self.last_sync_hash is None or current_hash != self.last_sync_hash:
            return True
        return False

    def create_archive(self) -> str:
        """Create a compressed archive of the directory"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
            archive_path = temp_file.name

        try:
            with tarfile.open(archive_path, 'w:gz') as tar:
                files = self.get_files_to_sync()
                
                for file_path in files:
                    try:
                        # Use relative path within archive
                        arcname = file_path.relative_to(self.directory_path)
                        tar.add(file_path, arcname=arcname)
                    except (OSError, IOError) as e:
                        logger.warning(f"Error adding file {file_path} to archive: {e}")
                        continue

            logger.info(f"Created archive: {archive_path} ({len(files)} files)")
            return archive_path

        except Exception as e:
            # Clean up on error
            if os.path.exists(archive_path):
                os.unlink(archive_path)
            raise e

    def get_signed_upload_url(self) -> Optional[str]:
        """Get signed URL for uploading to Google Cloud Storage"""
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            directory_name = self.directory_path.name
            filename = f"{directory_name}_{timestamp}.tar.gz"
            
            response = requests.post(
                f"{BASE_URL}/api/sync/signed-url",
                headers={
                    "Authorization": f"Bearer {self.config.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "filename": filename,
                    "content_type": "application/gzip"
                },
                timeout=30
            )

            if response.status_code != 200:
                logger.error(f"Failed to get signed URL: {response.status_code} - {response.text}")
                return None

            data = response.json()
            return data.get("signed_url")

        except Exception as e:
            logger.error(f"Error getting signed URL: {e}")
            return None

    def upload_to_gcs(self, archive_path: str, signed_url: str) -> bool:
        """Upload archive to Google Cloud Storage using signed URL"""
        try:
            with open(archive_path, 'rb') as f:
                response = requests.put(
                    signed_url,
                    data=f,
                    headers={
                        'Content-Type': 'application/gzip'
                    },
                    timeout=300  # 5 minutes timeout for upload
                )

            if response.status_code in [200, 204]:
                logger.info("Successfully uploaded to Google Cloud Storage")
                return True
            else:
                logger.error(f"Upload failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error uploading to GCS: {e}")
            return False

    def sync_directory(self) -> bool:
        """Perform a complete sync of the directory"""
        try:
            # Check for changes
            if not self.has_changes():
                logger.info("No changes detected, skipping sync")
                return True

            logger.info(f"Syncing directory: {self.directory_path}")
            
            # Create archive
            archive_path = self.create_archive()
            
            try:
                # Get signed URL
                signed_url = self.get_signed_upload_url()
                if not signed_url:
                    return False

                # Upload to GCS
                success = self.upload_to_gcs(archive_path, signed_url)
                
                if success:
                    # Update last sync hash
                    self.last_sync_hash = self.calculate_directory_hash()
                    logger.info("Directory sync completed successfully")
                
                return success

            finally:
                # Clean up archive file
                if os.path.exists(archive_path):
                    os.unlink(archive_path)

        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return False

    def start_continuous_sync(self, interval_minutes: int = 5):
        """Start continuous sync loop with specified interval"""
        interval_seconds = interval_minutes * 60
        logger.info(f"Starting continuous sync every {interval_minutes} minutes")
        logger.info(f"Press Ctrl+C to stop")
        
        try:
            while True:
                try:
                    self.sync_directory()
                except Exception as e:
                    logger.error(f"Sync error: {e}")
                
                logger.info(f"Waiting {interval_minutes} minutes until next sync...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Sync stopped by user")
        except Exception as e:
            logger.error(f"Unexpected error in sync loop: {e}")
            raise