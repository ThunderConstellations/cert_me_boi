"""Test configuration and fixtures"""

import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from playwright.sync_api import Page, Browser, BrowserContext
from typing import Dict, Any, Generator

# Import components for fixtures
from src.automation.course_automation import CourseAutomation
from src.monitor.video_monitor import VideoMonitor
from src.utils.logger import logger, ai_logger, log_ai_interaction, log_error_with_context
from src.utils.error_handler import AutomationError, MonitorError

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration"""
    config_path = Path("config/courses.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="session")
def test_credentials() -> Dict[str, str]:
    """Test credentials"""
    return {
        "email": "test@example.com",
        "password": "password123"
    }

@pytest.fixture
def mock_browser():
    """Mock browser instance"""
    browser = Mock(spec=Browser)
    context = Mock(spec=BrowserContext)
    page = Mock(spec=Page)
    
    # Configure browser behavior
    browser.new_context.return_value = context
    context.new_page.return_value = page
    
    # Configure page behavior
    page.goto.return_value = None
    page.fill.return_value = None
    page.click.return_value = None
    page.wait_for_load_state.return_value = None
    page.wait_for_selector.return_value = Mock()
    page.screenshot.return_value = None
    
    return browser

@pytest.fixture
def mock_page(mock_browser):
    """Mock page instance"""
    return mock_browser.new_context().new_page()

@pytest.fixture
def course_automation(tmp_path):
    """Course automation instance"""
    with patch('src.automation.course_automation.yaml.safe_load') as mock_load:
        mock_load.return_value = {
            'certificates': {
                'save_dir': str(tmp_path / 'certificates'),
                'verify_text': True,
                'min_confidence': 0.8
            },
            'courses': {
                'default': {
                    'selectors': {
                        'login_button': '#login-button',
                        'email_field': '#email',
                        'password_field': '#password',
                        'certificate_container': '#certificate-container',
                        'progress_bar': '.progress-bar',
                        'video_player': '.video-player'
                    },
                    'timeouts': {
                        'navigation': 30000,
                        'element': 5000,
                        'certificate': 10000
                    }
                }
            }
        }
        automation = CourseAutomation()
        return automation

@pytest.fixture
def video_monitor(tmp_path):
    """Video monitor instance"""
    with patch('src.monitor.video_monitor.yaml.safe_load') as mock_load:
        mock_load.return_value = {
            'frame_analysis': {
                'buffer_size': 10,
                'motion_threshold': 1000,
                'progress_threshold': 0.9,
                'blur_threshold': 100
            },
            'progress_bar': {
                'color_ranges': {
                    'white': {
                        'lower': [0, 0, 200],
                        'upper': [180, 30, 255]
                    },
                    'gray': {
                        'lower': [0, 0, 100],
                        'upper': [180, 30, 200]
                    }
                },
                'roi': {
                    'top_percent': 0.8,
                    'height_percent': 0.1
                },
                'min_width_percent': 0.3,
                'min_height_pixels': 5
            },
            'template_matching': {
                'threshold': 0.8,
                'scale_range': [0.8, 1.2],
                'scale_steps': 5
            },
            'screenshots': {
                'max_per_session': 100,
                'jpeg_quality': 95,
                'png_compression': 9
            },
            'logging': {
                'frame_metrics': True
            }
        }
        monitor = VideoMonitor()
        return monitor

@pytest.fixture
def temp_dir_structure(tmp_path):
    """Create temporary directory structure"""
    # Create directories
    (tmp_path / 'certificates').mkdir()
    (tmp_path / 'screenshots').mkdir()
    (tmp_path / 'templates').mkdir()
    (tmp_path / 'logs').mkdir()
    
    # Set environment variables
    os.environ['CERT_DIR'] = str(tmp_path / 'certificates')
    os.environ['SCREENSHOT_DIR'] = str(tmp_path / 'screenshots')
    os.environ['TEMPLATE_DIR'] = str(tmp_path / 'templates')
    os.environ['LOG_DIR'] = str(tmp_path / 'logs')
    
    yield tmp_path
    
    # Clean up environment variables
    for var in ['CERT_DIR', 'SCREENSHOT_DIR', 'TEMPLATE_DIR', 'LOG_DIR']:
        if var in os.environ:
            del os.environ[var]

@pytest.fixture
def error_factory() -> Dict[str, Exception]:
    """Factory for creating test errors"""
    return {
        "automation": AutomationError("Test automation error"),
        "monitor": MonitorError("Test monitor error")
    }

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "monitor: marks tests as monitor tests")
    config.addinivalue_line("markers", "automation: marks tests as automation tests")

@pytest.fixture(autouse=True)
def setup_logging(temp_dir_structure):
    """Set up logging for tests"""
    log_dir = temp_dir_structure / 'logs'
    os.environ['LOG_DIR'] = str(log_dir)
    yield
    del os.environ['LOG_DIR']

@pytest.fixture(autouse=True)
def cleanup_temp_files(tmp_path):
    """Clean up temporary files after tests"""
    yield
    for pattern in ['*.log', '*.png', '*.json']:
        for file in tmp_path.glob(pattern):
            try:
                file.unlink()
            except Exception:
                pass

@pytest.fixture
def assert_logs_contain():
    """Assert that logs contain expected text"""
    def _assert_logs_contain(log_file: Path, expected_text: str):
        assert log_file.exists(), f"Log file {log_file} does not exist"
        content = log_file.read_text()
        assert expected_text in content, f"Expected text '{expected_text}' not found in log file"
    return _assert_logs_contain 