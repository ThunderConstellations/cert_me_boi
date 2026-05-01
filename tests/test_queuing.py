import pytest
import sys
from unittest.mock import Mock, patch, call
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
        auth_inst.__enter__.return_value = auth_inst
        # Mock run_multi_course behavior
        def mock_run(urls, platform, credentials):
             # Simulate process for each url
             for url in urls:
                  auth_inst.db.update_course_status(url, platform, "STARTED")
                  auth_inst.db.update_course_status(url, platform, "COMPLETED")
             return True
        auth_inst.run_multi_course = Mock(side_effect=mock_run)
        yield auth_inst

def test_multi_course_queuing(mock_automation):
    """Test that main() correctly iterates over multiple URLs via run_multi_course"""
    urls = "http://course1.com,http://course2.com"
    test_args = [
        "src/main.py",
        "--urls", urls,
        "--email", "test@test.com",
        "--password", "pass",
        "--platform", "coursera"
    ]

    with patch.object(sys, 'argv', test_args), \
         patch("src.main.load_config", return_value={}), \
         pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 0
    mock_automation.run_multi_course.assert_called_once()
    # Check that URLs were parsed correctly
    call_args = mock_automation.run_multi_course.call_args[0]
    assert call_args[0] == ["http://course1.com", "http://course2.com"]

def test_multi_course_queuing_partial_failure(mock_automation):
    """Test that main() correctly reports failure from run_multi_course"""
    urls = "http://fail.com"
    test_args = [
        "src/main.py",
        "--urls", urls,
        "--email", "test@test.com",
        "--password", "pass"
    ]

    mock_automation.run_multi_course.side_effect = None
    mock_automation.run_multi_course.return_value = False

    with patch.object(sys, 'argv', test_args), \
         patch("src.main.load_config", return_value={}), \
         pytest.raises(SystemExit) as excinfo:
        main()

    assert excinfo.value.code == 1
