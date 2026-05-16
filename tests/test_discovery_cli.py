import pytest
import sys
from unittest.mock import Mock, patch
from src.main import main

@pytest.fixture
def mock_automation():
    with patch("src.main.CertificationAutomation") as mock_auth:
        auth_inst = mock_auth.return_value
        auth_inst.browser = Mock()
        auth_inst.course = Mock()
        auth_inst.monitor = Mock()
        auth_inst.metrics = Mock()
        auth_inst.db = Mock()
        auth_inst.discovery = Mock()
        auth_inst.__enter__.return_value = auth_inst
        yield auth_inst

def test_discovery_flag(mock_automation):
    """Test that --discover flag calls discover_free_courses"""
    test_args = ["src/main.py", "--discover"]

    with patch.object(sys, 'argv', test_args), \
         patch("src.main.load_config", return_value={}), \
         pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    mock_automation.discover_free_courses.assert_called_once()

def test_discovery_and_run(mock_automation):
    """Test that discovery can be followed by an automation run"""
    test_args = [
        "src/main.py",
        "--discover",
        "--urls", "http://test.com",
        "--email", "t", "--password", "p"
    ]

    mock_automation.run_multi_course.return_value = True

    with patch.object(sys, 'argv', test_args), \
         patch("src.main.load_config", return_value={}), \
         pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    mock_automation.discover_free_courses.assert_called_once()
    mock_automation.run_multi_course.assert_called_once()
