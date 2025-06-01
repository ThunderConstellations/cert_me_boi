import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from src.utils.error_handler import (
    AutomationError,
    BrowserError,
    MonitorError,
    AIError,
    NetworkError,
    retry_on_exception,
    handle_browser_errors,
    handle_monitor_errors,
    handle_ai_errors,
    handle_network_errors,
    safe_execute
)
from src.utils.recovery_manager import (
    RecoveryManager,
    RecoveryStrategy,
    BrowserRecoveryStrategy,
    MonitorRecoveryStrategy,
    AIRecoveryStrategy
)
from src.utils.metrics_collector import MetricsCollector
from src.utils.logger import logger

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_browser = Mock()
        self.mock_monitor = Mock()
        self.mock_ai = Mock()
        
        # Initialize recovery manager with mock components
        self.recovery_manager = RecoveryManager()
        self.recovery_manager.initialize(
            browser_instance=self.mock_browser,
            monitor_instance=self.mock_monitor,
            ai_instance=self.mock_ai
        )
        
        # Initialize metrics collector
        self.metrics_collector = MetricsCollector()

    def test_retry_decorator(self):
        """Test retry decorator with exponential backoff"""
        attempts = []
        
        @retry_on_exception(
            exceptions=(NetworkError,),
            max_attempts=3,
            backoff_factor=0.1  # Small factor for faster tests
        )
        def test_function():
            attempts.append(time.time())
            raise NetworkError("Test error")
        
        with self.assertRaises(NetworkError):
            test_function()
        
        self.assertEqual(len(attempts), 3)
        
        # Check backoff intervals
        intervals = [attempts[i+1] - attempts[i] for i in range(len(attempts)-1)]
        self.assertTrue(all(intervals[i] > intervals[i-1] for i in range(1, len(intervals))))

    def test_error_handlers(self):
        """Test error handler decorators"""
        # Test browser error handler
        @handle_browser_errors
        def browser_function():
            raise Exception("Browser error")
        
        with self.assertRaises(BrowserError):
            browser_function()
        
        # Test monitor error handler
        @handle_monitor_errors
        def monitor_function():
            raise Exception("Monitor error")
        
        with self.assertRaises(MonitorError):
            monitor_function()
        
        # Test AI error handler
        @handle_ai_errors
        def ai_function():
            raise Exception("AI error")
        
        with self.assertRaises(AIError):
            ai_function()

    def test_safe_execute(self):
        """Test safe execution wrapper"""
        def error_function():
            raise ValueError("Test error")
        
        # Test with default value
        result = safe_execute(error_function, default_value="default")
        self.assertEqual(result, "default")
        
        # Test with custom error handler
        handler_called = False
        def custom_handler(e):
            nonlocal handler_called
            handler_called = True
            return "handled"
        
        result = safe_execute(error_function, error_handler=custom_handler)
        self.assertEqual(result, "handled")
        self.assertTrue(handler_called)

    def test_recovery_strategies(self):
        """Test recovery strategies"""
        # Test browser recovery
        browser_strategy = BrowserRecoveryStrategy(
            "test_browser",
            max_attempts=2,
            browser_instance=self.mock_browser
        )
        
        self.mock_browser.refresh.return_value = True
        self.assertTrue(browser_strategy.execute({}))
        self.mock_browser.refresh.assert_called_once()
        
        # Test monitor recovery
        monitor_strategy = MonitorRecoveryStrategy(
            "test_monitor",
            max_attempts=2,
            monitor_instance=self.mock_monitor
        )
        
        self.mock_monitor.recapture.return_value = True
        self.assertTrue(monitor_strategy.execute({}))
        self.mock_monitor.recapture.assert_called_once()
        
        # Test AI recovery
        ai_strategy = AIRecoveryStrategy(
            "test_ai",
            max_attempts=2,
            ai_instance=self.mock_ai
        )
        
        self.mock_ai.retry_request.return_value = True
        self.assertTrue(ai_strategy.execute({"request": "test"}))
        self.mock_ai.retry_request.assert_called_once()

    def test_recovery_manager(self):
        """Test recovery manager error handling"""
        # Test browser error recovery
        error = BrowserError("Test error")
        self.assertTrue(
            self.recovery_manager.handle_error(
                error,
                "browser",
                {"action": "click"}
            )
        )
        
        # Test monitor error recovery
        error = MonitorError("Test error")
        self.assertTrue(
            self.recovery_manager.handle_error(
                error,
                "monitor",
                {"region": "test"}
            )
        )
        
        # Test AI error recovery
        error = AIError("Test error")
        self.assertTrue(
            self.recovery_manager.handle_error(
                error,
                "ai",
                {"request": "test"}
            )
        )

    def test_metrics_collection(self):
        """Test metrics collection during error handling"""
        # Record some test metrics
        self.metrics_collector.record_operation("browser", "click", False, 100.0)
        self.metrics_collector.record_error("browser", "ElementNotFoundError")
        
        # Get metrics summary
        summary = self.metrics_collector.get_metrics_summary()
        
        self.assertEqual(summary['error_counts']['browser'], 1)
        self.assertEqual(summary['total_operations']['browser'], 1)
        self.assertEqual(summary['error_rates']['browser'], 1.0)
        
        # Check performance metrics
        self.assertIn('browser', summary['performance'])
        self.assertIn('click', summary['performance']['browser'])
        self.assertEqual(summary['performance']['browser']['click']['avg_duration'], 100.0)

    def test_error_recovery_integration(self):
        """Test integration of error handling components"""
        # Mock browser operation that fails twice then succeeds
        operation_count = 0
        def browser_operation():
            nonlocal operation_count
            operation_count += 1
            if operation_count < 3:
                raise BrowserError("Test error")
            return True

        # Create decorated test function
        @retry_on_exception(
            exceptions=(BrowserError,),
            max_attempts=3,
            backoff_factor=0.1
        )
        @handle_browser_errors
        def test_operation():
            return browser_operation()

        # Execute operation
        start_time = time.time()
        result = test_operation()
        duration = time.time() - start_time

        # Verify results
        self.assertTrue(result)
        self.assertEqual(operation_count, 3)
        
        # Check metrics
        summary = self.metrics_collector.get_metrics_summary()
        self.assertGreater(duration, 0.2)  # Account for backoff delays

    def test_concurrent_error_handling(self):
        """Test error handling under concurrent operations"""
        import threading
        import random
        
        # Simulate concurrent operations
        def worker(worker_id):
            for _ in range(10):
                try:
                    if random.random() < 0.5:
                        raise BrowserError(f"Error in worker {worker_id}")
                    self.metrics_collector.record_operation(
                        "browser",
                        f"worker_{worker_id}",
                        True,
                        random.random() * 100
                    )
                except Exception as e:
                    self.metrics_collector.record_error(
                        "browser",
                        type(e).__name__
                    )
                time.sleep(random.random() * 0.1)

        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify metrics were collected correctly
        summary = self.metrics_collector.get_metrics_summary()
        self.assertGreater(len(summary['error_counts']), 0)
        self.assertGreater(len(summary['total_operations']), 0)

if __name__ == '__main__':
    unittest.main() 