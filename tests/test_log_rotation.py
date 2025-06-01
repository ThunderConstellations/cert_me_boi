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
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def mock_config():
    """Create mock configuration"""
    return {
        'logging': {
            'log_dir': 'logs',
            'rotation': {
                'max_size': 1024,  # 1KB for testing
                'max_days': 7,
                'compress': True,
                'interval': 1,  # 1 second for testing
                'backup_count': 3
            }
        }
    }

@pytest.fixture
def rotation_manager(temp_log_dir, mock_config):
    """Create a test rotation manager instance"""
    with patch('src.utils.log_rotation.LogRotationManager._load_config') as mock_load:
        mock_load.return_value = mock_config
        manager = LogRotationManager()
        manager.log_dir = temp_log_dir
        manager.archive_dir = temp_log_dir / "archive"
        manager.archive_dir.mkdir()
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
        assert not rotation_manager.is_running
        assert rotation_manager.rotation_thread is None

    def test_rotation_on_size(self, rotation_manager, temp_log_dir):
        """Test log file rotation based on size"""
        # Create a large log file
        log_file = temp_log_dir / "test.log"
        create_test_log(log_file, 2048)  # 2KB

        # Start rotation
        rotation_manager.start_rotation()
        time.sleep(2)  # Wait for rotation to occur
        
        # Check that original file was rotated
        assert log_file.exists()
        assert log_file.stat().st_size == 0
        
        # Check that backup was created
        backup = log_file.with_suffix(".log.1")
        assert backup.exists()
        assert backup.stat().st_size == 2048

    def test_compression(self, rotation_manager, temp_log_dir):
        """Test log file compression"""
        # Create test file
        test_file = temp_log_dir / "compress_test.log"
        test_data = "test" * 1000
        test_file.write_text(test_data)

        # Compress file
        rotation_manager._compress_file(test_file)
        
        # Check compressed file
        compressed_file = rotation_manager.archive_dir / f"{test_file.name}.gz"
        assert compressed_file.exists()
        
        # Verify content
        with gzip.open(compressed_file, 'rt') as f:
            content = f.read()
            assert content == test_data

    def test_cleanup_old_files(self, rotation_manager, temp_log_dir):
        """Test cleanup of old files"""
        # Create old and new files
        old_date = datetime.now() - timedelta(days=10)
        new_date = datetime.now()

        old_file = temp_log_dir / "old_test.log.1"
        new_file = temp_log_dir / "new_test.log.1"
        
        create_test_log(old_file, 100)
        create_test_log(new_file, 100)
        
        os.utime(str(old_file), (old_date.timestamp(), old_date.timestamp()))
        os.utime(str(new_file), (new_date.timestamp(), new_date.timestamp()))

        # Run cleanup
        rotation_manager._cleanup_old_files()
        
        # Check results
        assert not old_file.exists()
        assert new_file.exists()

    def test_background_rotation(self, rotation_manager, temp_log_dir):
        """Test background rotation task"""
        # Create test log file
        log_file = temp_log_dir / "background_test.log"
        create_test_log(log_file, 2048)  # 2KB

        # Start rotation
        rotation_manager.start_rotation()
        assert rotation_manager.is_running
        assert rotation_manager.rotation_thread is not None
        
        # Wait for rotation
        time.sleep(2)
        
        # Check results
        assert log_file.exists()
        assert log_file.stat().st_size == 0
        assert log_file.with_suffix(".log.1").exists()
        
        # Stop rotation
        rotation_manager.stop_rotation()
        assert not rotation_manager.is_running

    def test_error_handling(self, rotation_manager, temp_log_dir):
        """Test error handling in rotation operations"""
        # Create an unreadable log file
        log_file = temp_log_dir / "error_test.log"
        create_test_log(log_file, 2048)
        os.chmod(log_file, 0o000)  # Remove all permissions

        # Start rotation
        rotation_manager.start_rotation()
        time.sleep(2)
        
        # Cleanup
        os.chmod(log_file, 0o666)
        log_file.unlink()

    def test_concurrent_rotation(self, rotation_manager, temp_log_dir):
        """Test concurrent access to rotation operations"""
        import threading
        
        # Create test files
        files = []
        for i in range(5):
            log_file = temp_log_dir / f"concurrent_test_{i}.log"
            create_test_log(log_file, 2048)
            files.append(log_file)

        # Start rotation
        rotation_manager.start_rotation()
        time.sleep(2)

        # Check results
        for file in files:
            assert file.exists()
            assert file.stat().st_size == 0
            assert file.with_suffix(".log.1").exists()

    def test_rotation_with_missing_directory(self, rotation_manager):
        """Test rotation when directories are missing"""
        # Remove directories
        shutil.rmtree(rotation_manager.log_dir)
        
        # Start rotation
        rotation_manager.start_rotation()
        time.sleep(1)
        
        # Check that directories were recreated
        assert rotation_manager.log_dir.exists()
        assert rotation_manager.archive_dir.exists()

    def test_stop_without_start(self, rotation_manager):
        """Test stopping rotation when not started"""
        rotation_manager.stop_rotation()
        assert not rotation_manager.is_running
        assert rotation_manager.rotation_thread is None

    def test_multiple_starts(self, rotation_manager):
        """Test starting rotation multiple times"""
        rotation_manager.start_rotation()
        first_thread = rotation_manager.rotation_thread
        
        rotation_manager.start_rotation()
        second_thread = rotation_manager.rotation_thread
        
        assert first_thread is second_thread
        
        rotation_manager.stop_rotation() 