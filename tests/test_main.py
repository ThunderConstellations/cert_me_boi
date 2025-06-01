import pytest
import time
from unittest.mock import Mock, patch, call
from pathlib import Path
from src.main import CertificationAutomation
from src.utils.error_handler import (
    AutomationError,
    BrowserError,
    MonitorError,
    AIError,
    NetworkError
)

@pytest.mark.integration
class TestCertificationAutomation:
    @pytest.fixture
    def automation(
        self,
        mock_browser,
        mock_monitor,
        mock_ai,
        recovery_manager,
        metrics_collector,
        temp_log_dir,
        temp_config_dir
    ):
        """Create automation instance with mocked components"""
        with patch("src.main.BrowserAutomation", return_value=mock_browser), \
             patch("src.main.ScreenMonitor", return_value=mock_monitor), \
             patch("src.main.ModelHandler", return_value=mock_ai), \
             patch("src.main.RecoveryManager", return_value=recovery_manager), \
             patch("src.main.MetricsCollector", return_value=metrics_collector):
            automation = CertificationAutomation()
            yield automation

    def test_initialization(self, automation, mock_browser, mock_monitor, mock_ai):
        """Test successful initialization of components"""
        assert automation.initialize_components()
        mock_browser.start.assert_called_once()
        mock_ai.load_model.assert_called_once()

    def test_initialization_failure(self, automation, mock_browser):
        """Test handling of initialization failures"""
        mock_browser.start.side_effect = BrowserError("Failed to start browser")
        
        with pytest.raises(BrowserError):
            automation.initialize_components()

    @pytest.mark.parametrize("video_state,expected_action", [
        ("paused", "play_button"),
        ("ended", "next_button")
    ])
    def test_handle_video_lecture(
        self,
        automation,
        mock_browser,
        mock_monitor,
        video_state,
        expected_action
    ):
        """Test video lecture handling"""
        automation.initialize_components()
        automation.handle_video_lecture(video_state)
        
        # Verify correct button was clicked
        mock_browser.click_element.assert_called_with(
            automation.config['platforms']['coursera']['selectors'][expected_action]
        )
        
        # Verify progress was checked
        mock_monitor.check_video_progress.assert_called_once()

    def test_handle_quiz(self, automation, mock_browser, mock_ai):
        """Test quiz handling"""
        automation.initialize_components()
        quiz_text = "Test quiz question"
        
        automation.handle_quiz(quiz_text)
        
        # Verify AI generated an answer
        mock_ai.generate_text.assert_called_with(
            f"Answer this quiz question: {quiz_text}"
        )
        
        # Verify answer was submitted
        mock_browser.fill_input.assert_called_once()

    def test_handle_assignment(self, automation, mock_browser, mock_ai):
        """Test assignment handling"""
        automation.initialize_components()
        assignment_text = "Test assignment"
        
        automation.handle_assignment(assignment_text)
        
        # Verify AI generated a solution
        mock_ai.generate_text.assert_called_with(
            f"Complete this assignment: {assignment_text}",
            max_length=1000
        )
        
        # Verify solution was submitted
        mock_browser.fill_input.assert_called_once()
        mock_browser.click_element.assert_called_once()

    def test_monitor_callback(self, automation, mock_monitor):
        """Test monitor callback handling"""
        automation.initialize_components()
        
        # Test video player callback
        automation.monitor_callback("video_player", None)
        mock_monitor.detect_video_state.assert_called_once()
        
        # Test quiz callback
        automation.monitor_callback("quiz", None)
        mock_monitor.save_screenshot.assert_called_with(None, "quiz")
        
        # Test assignment callback
        automation.monitor_callback("assignment", None)
        mock_monitor.save_screenshot.assert_called_with(None, "assignment")

    @pytest.mark.parametrize("success", [True, False])
    def test_login_to_platform(self, automation, mock_browser, success):
        """Test platform login"""
        automation.initialize_components()
        mock_browser.login.return_value = success
        credentials = {"email": "test@example.com", "password": "password123"}
        
        if success:
            assert automation.login_to_platform("coursera", credentials)
        else:
            with pytest.raises(NetworkError):
                automation.login_to_platform("coursera", credentials)

    def test_error_recovery(self, automation, mock_browser, recovery_manager):
        """Test error recovery during operations"""
        automation.initialize_components()
        
        # Simulate browser error with successful recovery
        mock_browser.click_element.side_effect = [
            BrowserError("Click failed"),
            True
        ]
        
        automation.handle_video_lecture("paused")
        
        # Verify recovery was attempted
        assert mock_browser.click_element.call_count == 2

    def test_metrics_collection(self, automation, metrics_collector):
        """Test metrics collection during operations"""
        automation.initialize_components()
        
        # Simulate successful operation
        automation.handle_video_lecture("paused")
        
        # Verify metrics were recorded
        summary = metrics_collector.get_metrics_summary()
        assert "browser" in summary["total_operations"]
        assert "video_lecture" in str(summary["performance"])

    def test_cleanup(self, automation, mock_browser, mock_monitor, mock_ai, metrics_collector):
        """Test cleanup of resources"""
        automation.initialize_components()
        automation.cleanup()
        
        # Verify all components were cleaned up
        mock_browser.cleanup.assert_called_once()
        mock_monitor.cleanup.assert_called_once()
        mock_ai.cleanup.assert_called_once()
        
        # Verify metrics collection was stopped
        assert not metrics_collector.is_collecting

    def test_context_manager(self, automation, mock_browser, mock_monitor, mock_ai):
        """Test context manager functionality"""
        with automation as auto:
            auto.initialize_components()
            # Simulate some operation
            auto.handle_video_lecture("paused")
        
        # Verify cleanup was called
        mock_browser.cleanup.assert_called_once()
        mock_monitor.cleanup.assert_called_once()
        mock_ai.cleanup.assert_called_once()

    @pytest.mark.parametrize("error_type,expected_error", [
        (BrowserError, "Browser error"),
        (MonitorError, "Monitor error"),
        (AIError, "AI error"),
        (NetworkError, "Network error")
    ])
    def test_error_handling(
        self,
        automation,
        mock_browser,
        mock_monitor,
        mock_ai,
        error_type,
        expected_error
    ):
        """Test handling of different error types"""
        automation.initialize_components()
        
        # Simulate error in browser operation
        mock_browser.click_element.side_effect = error_type(expected_error)
        
        with pytest.raises(error_type) as exc_info:
            automation.handle_video_lecture("paused")
        
        assert str(exc_info.value) == expected_error

    def test_concurrent_operations(self, automation):
        """Test handling of concurrent operations"""
        import threading
        import queue
        
        automation.initialize_components()
        results = queue.Queue()
        errors = queue.Queue()
        
        def worker(operation):
            try:
                if operation == "video":
                    automation.handle_video_lecture("paused")
                elif operation == "quiz":
                    automation.handle_quiz("test quiz")
                elif operation == "assignment":
                    automation.handle_assignment("test assignment")
                results.put(operation)
            except Exception as e:
                errors.put((operation, e))
        
        # Start concurrent operations
        threads = []
        operations = ["video", "quiz", "assignment"] * 3
        
        for op in operations:
            thread = threading.Thread(target=worker, args=(op,))
            threads.append(thread)
            thread.start()
        
        # Wait for all operations to complete
        for thread in threads:
            thread.join()
        
        # Check results
        completed = []
        while not results.empty():
            completed.append(results.get())
        
        failed = []
        while not errors.empty():
            failed.append(errors.get())
        
        assert len(completed) + len(failed) == len(operations)

    def test_performance_monitoring(self, automation, metrics_collector):
        """Test performance monitoring of operations"""
        automation.initialize_components()
        
        # Simulate operations with different durations
        start_time = time.time()
        automation.handle_video_lecture("paused")
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Check metrics
        summary = metrics_collector.get_metrics_summary()
        assert "browser" in summary["performance"]
        assert duration > 0

    @pytest.mark.slow
    def test_long_running_operation(self, automation, mock_browser):
        """Test handling of long-running operations"""
        automation.initialize_components()
        
        # Simulate slow browser operation
        def slow_operation(*args, **kwargs):
            time.sleep(2)
            return True
        
        mock_browser.click_element.side_effect = slow_operation
        
        start_time = time.time()
        automation.handle_video_lecture("paused")
        duration = time.time() - start_time
        
        assert duration >= 2  # Verify operation took at least 2 seconds

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 