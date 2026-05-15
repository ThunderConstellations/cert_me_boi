import pytest
import time
from unittest.mock import Mock, patch, call
from src.main import CertificationAutomation, process_course
from src.utils.error_handler import BrowserError

@pytest.fixture
def mock_db():
    with patch("src.main.DatabaseManager") as mock:
        db = mock.return_value
        yield db

@pytest.fixture
def mock_components():
    with patch("src.main.BrowserAutomation") as mock_browser, \
         patch("src.main.CourseAutomation") as mock_course, \
         patch("src.main.ScreenMonitor") as mock_monitor, \
         patch("src.main.RecoveryManager") as mock_recovery, \
         patch("src.main.MetricsCollector") as mock_metrics:
        
        # Setup mocks
        mock_browser_inst = mock_browser.return_value
        mock_course_inst = mock_course.return_value
        mock_monitor_inst = mock_monitor.return_value
        mock_recovery_inst = mock_recovery.return_value
        mock_metrics_inst = mock_metrics.return_value
        
        # Default behavior for setup
        mock_browser_inst.start.return_value = True
        mock_browser_inst.page = Mock()
        mock_course_inst.login_to_course.return_value = True
        mock_course_inst.start_automation.return_value = True
        
        yield {
            "browser": mock_browser_inst,
            "course": mock_course_inst,
            "monitor": mock_monitor_inst,
            "recovery": mock_recovery_inst,
            "metrics": mock_metrics_inst
        }

@pytest.fixture
def automation(mock_db, mock_components, temp_dir_structure):
    config_path = "config/courses.yaml"
    with patch("src.main.load_config") as mock_load:
        mock_load.return_value = {
            "platforms": {
                "coursera": {
                    "url": "https://coursera.org",
                    "selectors": {"login": "button"}
                }
            }
        }
        auth = CertificationAutomation(config_path)
        yield auth

def test_initialization(automation, mock_components):
    """Test successful initialization of components"""
    assert automation.browser == mock_components["browser"]
    assert automation.course == mock_components["course"]
    assert automation.monitor == mock_components["monitor"]
    mock_components["metrics"].start_collection.assert_called_once()
    mock_components["recovery"].initialize.assert_called_once()

def test_process_course_success(mock_components):
    """Test process_course logic flow"""
    browser = mock_components["browser"]
    course = mock_components["course"]
    monitor = mock_components["monitor"]
    recovery = mock_components["recovery"]

    course.start_automation.return_value = True
    course.download_certificate.return_value = "/path/to/cert.pdf"

    result = process_course(browser, course, monitor, recovery, "http://url", "coursera", "email", "pass")

    assert result is True
    course.start_automation.assert_called_once()
    course.download_certificate.assert_called_once()

def test_process_course_failure_on_automation(mock_components):
    """Test process_course logic flow on automation failure"""
    browser = mock_components["browser"]
    course = mock_components["course"]
    monitor = mock_components["monitor"]
    recovery = mock_components["recovery"]

    course.start_automation.return_value = False

    result = process_course(browser, course, monitor, recovery, "http://url", "coursera", "email", "pass")

    assert result is False
    course.start_automation.assert_called_once()
    # Should not attempt to download cert if automation failed
    course.download_certificate.assert_not_called()

def test_run_multi_course_db_tracking(automation, mock_components, mock_db):
    """Test that automation correctly tracks status in DB"""
    credentials = {
        "email": "test@example.com",
        "password": "password123"
    }
    urls = ["https://course.url"]

    with patch("src.main.process_course", return_value=True):
        automation.run_multi_course(urls, "coursera", credentials)
        
        mock_db.update_course_status.assert_any_call("https://course.url", "coursera", "STARTED")
        mock_db.update_course_status.assert_any_call("https://course.url", "coursera", "COMPLETED")

def test_cleanup_on_exit(mock_db, mock_components):
    """Test that context manager calls cleanup"""
    config_path = "config/courses.yaml"
    with patch("src.main.load_config") as mock_load:
        mock_load.return_value = {}
        with CertificationAutomation(config_path) as auth:
            pass
        
        mock_components["browser"].cleanup.assert_called_once()
        mock_components["course"].cleanup.assert_called_once()
        mock_components["monitor"].cleanup.assert_called_once()
