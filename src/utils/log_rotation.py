"""Log rotation manager module"""

import os
import time
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import shutil

class LogRotationManager:
    """Manages log file rotation and archival"""
    
    def __init__(self, 
                 rotation_interval: int = 3600,  # 1 hour
                 max_size: int = 10485760,  # 10MB
                 max_days: int = 30,
                 backup_count: int = 5,
                 compress: bool = True):
        """Initialize log rotation manager
        
        Args:
            rotation_interval: Interval between rotation checks in seconds
            max_size: Maximum log file size in bytes
            max_days: Maximum age of log files in days
            backup_count: Number of backup files to keep
            compress: Whether to compress archived logs
        """
        self.rotation_interval = rotation_interval
        self.max_size = max_size
        self.max_days = max_days
        self.backup_count = backup_count
        self.compress = compress
        
        self.running = False
        self.rotation_thread: Optional[threading.Thread] = None
        self.last_rotation = datetime.now()

    def start_rotation(self) -> None:
        """Start log rotation thread"""
        if not self.running:
            self.running = True
            self.rotation_thread = threading.Thread(
                target=self._rotation_loop,
                daemon=True
            )
            self.rotation_thread.start()

    def stop_rotation(self) -> None:
        """Stop log rotation thread"""
        self.running = False
        if self.rotation_thread:
            self.rotation_thread.join(timeout=5.0)
            self.rotation_thread = None

    def _rotation_loop(self) -> None:
        """Main rotation loop"""
        while self.running:
            try:
                self._check_and_rotate()
                time.sleep(self.rotation_interval)
            except Exception as e:
                print(f"Error in log rotation: {str(e)}")  # Basic error handling

    def _check_and_rotate(self) -> None:
        """Check log files and rotate if needed"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return
        
        # Create archive directory if needed
        archive_dir = log_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        # Check all log files
        for log_file in log_dir.glob("*.log"):
            try:
                self._rotate_if_needed(log_file, archive_dir)
            except Exception as e:
                print(f"Error rotating {log_file}: {str(e)}")  # Basic error handling

    def _rotate_if_needed(self, log_file: Path, archive_dir: Path) -> None:
        """Rotate a single log file if needed"""
        # Check file size
        if log_file.stat().st_size > self.max_size:
            self._rotate_file(log_file, archive_dir)
            return
        
        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_age > timedelta(days=self.max_days):
            self._archive_file(log_file, archive_dir)

    def _rotate_file(self, log_file: Path, archive_dir: Path) -> None:
        """Rotate a log file"""
        # Get existing backups
        base_name = log_file.stem
        backups = sorted([
            f for f in log_file.parent.glob(f"{base_name}.*")
            if f.suffix.isdigit()
        ], reverse=True)
        
        # Remove old backups
        while len(backups) >= self.backup_count:
            oldest = backups.pop()
            oldest.unlink()
        
        # Rotate backups
        for i, backup in enumerate(backups):
            new_number = len(backups) - i + 1
            backup.rename(log_file.with_suffix(f".{new_number}"))
        
        # Rotate current file
        log_file.rename(log_file.with_suffix(".1"))
        
        # Create new empty file
        log_file.touch()

    def _archive_file(self, log_file: Path, archive_dir: Path) -> None:
        """Archive an old log file"""
        # Create archive filename with timestamp
        timestamp = datetime.fromtimestamp(log_file.stat().st_mtime)
        archive_name = f"{log_file.stem}_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        archive_path = archive_dir / archive_name
        
        # Move file to archive
        shutil.move(str(log_file), str(archive_path))
        
        # Compress if enabled
        if self.compress:
            try:
                import gzip
                with open(archive_path, 'rb') as f_in:
                    with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                archive_path.unlink()  # Remove uncompressed file
            except ImportError:
                pass  # Skip compression if gzip not available 