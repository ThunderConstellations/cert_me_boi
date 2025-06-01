"""Test error handler module"""

import pytest
import time
from unittest.mock import Mock, patch
from src.utils.error_handler import (
    AutomationError,
    MonitorError,
    retry_on_error,
    safe_monitor_operation,
    handle_automation_error
)

def test_automation_error():
    """Test AutomationError exception"""
    with pytest.raises(AutomationError, match="Test error"):
        raise AutomationError("Test error")

def test_monitor_error():
    """Test MonitorError exception"""
    with pytest.raises(MonitorError, match="Test error"):
        raise MonitorError("Test error")

def test_retry_on_error_success():
    """Test retry_on_error decorator with successful function"""
    mock_func = Mock(return_value="success")
    decorated = retry_on_error()(mock_func)
    
    result = decorated()
    assert result == "success"
    assert mock_func.call_count == 1

def test_retry_on_error_retry_and_succeed():
    """Test retry_on_error decorator with function that fails then succeeds"""
    mock_func = Mock(side_effect=[ValueError("First try"), "success"])
    decorated = retry_on_error(max_attempts=2)(mock_func)
    
    result = decorated()
    assert result == "success"
    assert mock_func.call_count == 2

def test_retry_on_error_max_attempts():
    """Test retry_on_error decorator reaches max attempts"""
    mock_func = Mock(side_effect=ValueError("Error"))
    decorated = retry_on_error(max_attempts=3)(mock_func)
    
    with pytest.raises(ValueError, match="Error"):
        decorated()
    assert mock_func.call_count == 3

def test_retry_on_error_allowed_exceptions():
    """Test retry_on_error decorator with allowed exceptions"""
    mock_func = Mock(side_effect=ValueError("Allowed error"))
    decorated = retry_on_error(
        max_attempts=2,
        allowed_exceptions=(ValueError,)
    )(mock_func)
    
    with pytest.raises(ValueError, match="Allowed error"):
        decorated()
    assert mock_func.call_count == 2

def test_retry_on_error_unallowed_exception():
    """Test retry_on_error decorator with unallowed exception"""
    mock_func = Mock(side_effect=TypeError("Unallowed error"))
    decorated = retry_on_error(
        max_attempts=2,
        allowed_exceptions=(ValueError,)
    )(mock_func)
    
    with pytest.raises(TypeError, match="Unallowed error"):
        decorated()
    assert mock_func.call_count == 1

def test_safe_monitor_operation_success():
    """Test safe_monitor_operation decorator with successful function"""
    mock_func = Mock(return_value="success")
    decorated = safe_monitor_operation(mock_func)
    
    result = decorated()
    assert result == "success"
    assert mock_func.call_count == 1

def test_safe_monitor_operation_opencv_error():
    """Test safe_monitor_operation decorator with OpenCV error"""
    class MockOpenCVError(Exception):
        __module__ = 'cv2'
    
    mock_func = Mock(side_effect=MockOpenCVError("OpenCV error"))
    decorated = safe_monitor_operation(mock_func)
    
    with pytest.raises(MonitorError, match="OpenCV error in mock"):
        decorated()
    assert mock_func.call_count == 1

def test_safe_monitor_operation_other_error():
    """Test safe_monitor_operation decorator with other error"""
    mock_func = Mock(side_effect=ValueError("Other error"))
    decorated = safe_monitor_operation(mock_func)
    
    with pytest.raises(ValueError, match="Other error"):
        decorated()
    assert mock_func.call_count == 1

def test_handle_automation_error_success():
    """Test handle_automation_error decorator with successful function"""
    mock_func = Mock(return_value="success")
    decorated = handle_automation_error(mock_func)
    
    result = decorated()
    assert result == "success"
    assert mock_func.call_count == 1

def test_handle_automation_error_automation_error():
    """Test handle_automation_error decorator with AutomationError"""
    mock_func = Mock(side_effect=AutomationError("Automation error"))
    decorated = handle_automation_error(mock_func)
    
    with pytest.raises(AutomationError, match="Automation error"):
        decorated()
    assert mock_func.call_count == 1

def test_handle_automation_error_other_error():
    """Test handle_automation_error decorator with other error"""
    mock_func = Mock(side_effect=ValueError("Other error"))
    decorated = handle_automation_error(mock_func)
    
    with pytest.raises(AutomationError, match="Unexpected error in mock"):
        decorated()
    assert mock_func.call_count == 1

def test_retry_delay():
    """Test retry delay in retry_on_error decorator"""
    start_time = time.time()
    
    mock_func = Mock(side_effect=[ValueError("First"), ValueError("Second"), "success"])
    decorated = retry_on_error(max_attempts=3, retry_delay=0.1)(mock_func)
    
    result = decorated()
    elapsed_time = time.time() - start_time
    
    assert result == "success"
    assert mock_func.call_count == 3
    assert elapsed_time >= 0.3  # At least 0.1 + 0.2 seconds delay

def test_operation_timing():
    """Test operation timing in safe_monitor_operation decorator"""
    def slow_func():
        time.sleep(0.1)
        return "success"
    
    decorated = safe_monitor_operation(slow_func)
    
    with patch("src.utils.logger.logger.debug") as mock_debug:
        result = decorated()
        
        assert result == "success"
        assert mock_debug.call_count >= 2
        
        # Check that execution time was logged
        timing_call = mock_debug.call_args_list[1]
        assert "execution_time" in timing_call[1]
        assert timing_call[1]["execution_time"] >= 0.1 