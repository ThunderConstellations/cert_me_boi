import os
import time
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.utils.log_rotation import LogRotationManager

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for logs"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir

@pytest.fixture
def rotation_manager(temp_log_dir):
    """Create a test rotation manager instance"""
    # Initialize with small thresholds for testing
    manager = LogRotationManager(
        rotation_interval=0.1,
        max_size=1024,
        max_days=7,
        backup_count=3,
        compress=True
    )
    # Patch Path to use temp_log_dir instead of "logs"
    with patch('src.utils.log_rotation.Path', return_value=temp_log_dir):
        manager.log_dir = temp_log_dir
        manager.archive_dir = temp_log_dir / "archive"
        manager.archive_dir.mkdir(exist_ok=True)
        yield manager
        manager.stop_rotation()

def create_test_log(path: Path, size_bytes: int) -> Path:
    """Create a test log file of specified size"""
    with open(path, 'w') as f:
        f.write('x' * size_bytes)
    return path

class TestLogRotationManager:
    """Test cases for LogRotationManager"""

    def test_initialization(self, rotation_manager, temp_log_dir):
        """Test manager initialization"""
        assert rotation_manager.log_dir == temp_log_dir
        assert rotation_manager.archive_dir.exists()
        assert not rotation_manager.running
        assert rotation_manager.rotation_thread is None

    def test_rotation_on_size(self, rotation_manager, temp_log_dir):
        """Test log file rotation based on size"""
        # Create a large log file
        log_file = temp_log_dir / "test.log"
        create_test_log(log_file, 2048)  # 2KB

        # Manually trigger rotation check
        with patch('src.utils.log_rotation.Path.exists', return_value=True),              patch('src.utils.log_rotation.Path.glob', return_value=[log_file]):
            rotation_manager._check_and_rotate()
        
        # Check that backup was created (manually call _rotate_if_needed to be sure of paths)
        rotation_manager._rotate_if_needed(log_file, rotation_manager.archive_dir)

        # Original file should be replaced by empty one
        assert log_file.exists()
        assert log_file.stat().st_size == 0
        
        # Backup should exist
        backup = log_file.with_suffix(".1")
        assert backup.exists()
        assert backup.stat().st_size == 2048

    def test_compression(self, rotation_manager, temp_log_dir):
        """Test log file archival and compression"""
        # Create test file
        test_file = temp_log_dir / "compress_test.log"
        test_data = "test" * 1000
        test_file.write_text(test_data)

        # Archive file (which compresses it)
        rotation_manager._archive_file(test_file, rotation_manager.archive_dir)
        
        # Check compressed file
        compressed_files = list(rotation_manager.archive_dir.glob("*.gz"))
        assert len(compressed_files) > 0
        
        # Verify content
        with gzip.open(compressed_files[0], 'rt') as f:
            content = f.read()
            assert content == test_data

    def test_cleanup_old_files(self, rotation_manager, temp_log_dir):
        """Test rotation based on age"""
        # Create old file
        old_date = datetime.now() - timedelta(days=10)
        log_file = temp_log_dir / "old_test.log"
        create_test_log(log_file, 100)
        
        # Set mtime to past
        os.utime(str(log_file), (old_date.timestamp(), old_date.timestamp()))

        # Check if age rotation triggers archival
        with patch.object(rotation_manager, '_archive_file') as mock_archive:
            rotation_manager._rotate_if_needed(log_file, rotation_manager.archive_dir)
            mock_archive.assert_called_once()

    def test_background_rotation(self, rotation_manager, temp_log_dir):
        """Test background rotation task"""
        # Create test log file
        log_file = temp_log_dir / "background_test.log"
        create_test_log(log_file, 2048)  # 2KB

        # Start rotation
        with patch('src.utils.log_rotation.Path', return_value=temp_log_dir):
            rotation_manager.start_rotation()
            assert rotation_manager.running
            assert rotation_manager.rotation_thread is not None

            # Wait for rotation
            time.sleep(0.5)
        
        # Stop rotation
        rotation_manager.stop_rotation()
        assert not rotation_manager.running

    def test_stop_without_start(self, rotation_manager):
        """Test stopping rotation when not started"""
        rotation_manager.stop_rotation()
        assert not rotation_manager.running
        assert rotation_manager.rotation_thread is None

    def test_multiple_starts(self, rotation_manager):
        """Test starting rotation multiple times"""
        rotation_manager.start_rotation()
        first_thread = rotation_manager.rotation_thread
        
        rotation_manager.start_rotation()
        second_thread = rotation_manager.rotation_thread
        
        assert first_thread is second_thread
        
        rotation_manager.stop_rotation()
