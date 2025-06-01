"""Extended logger module"""

import logging
import os
import yaml
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, Callable
from pathlib import Path
import traceback
import sys
import threading
import atexit
from .base_logger import logger as base_logger, log_error_with_context, log_event
from .log_rotation import LogRotationManager
import time
import functools

# Load config
config_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'config',
    'courses.yaml'
)
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Create logs directory if it doesn't exist
log_dir = config['logging']['log_dir']
os.makedirs(log_dir, exist_ok=True)

# Create archive directory for old logs
ARCHIVE_DIR = Path(log_dir) / "archive"
ARCHIVE_DIR.mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "level": "%(levelname)s",
    "message": "%(message)s",
    "module": "%(module)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d"
}

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON
        
        Args:
            record: Log record to format
        
        Returns:
            JSON formatted log string
        """
        # Get the original format
        message = super().format(record)
        
        # Create JSON log object
        log_obj = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": message
        }
        
        # Add extra fields from record
        if hasattr(record, "module"):
            log_obj["module"] = record.module
        if hasattr(record, "function"):
            log_obj["function"] = record.function
        if hasattr(record, "error"):
            log_obj["error"] = record.error
        
        # Add any additional fields from record.__dict__
        for key, value in record.__dict__.items():
            if key not in ["timestamp", "level", "message", "module", "function", "error",
                          "args", "exc_info", "exc_text", "msg", "created",
                          "msecs", "relativeCreated", "levelname", "levelno",
                          "pathname", "filename", "module", "funcName", "lineno",
                          "processName", "process", "threadName", "thread"]:
                log_obj[key] = value
        
        return json.dumps(log_obj)

class LoggerMetrics:
    """Track logging metrics for debugging"""
    def __init__(self):
        self.error_counts = {}
        self.warning_counts = {}
        self.last_errors = {}
        self.lock = threading.Lock()

    def increment_error(self, module: str, error_type: str):
        with self.lock:
            key = f"{module}:{error_type}"
            self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def increment_warning(self, module: str, warning_type: str):
        with self.lock:
            key = f"{module}:{warning_type}"
            self.warning_counts[key] = self.warning_counts.get(key, 0) + 1

    def record_last_error(self, module: str, error: Exception):
        with self.lock:
            self.last_errors[module] = {
                'type': type(error).__name__,
                'message': str(error),
                'timestamp': datetime.now().isoformat(),
                'traceback': traceback.format_exc()
            }

    def get_metrics(self) -> Dict[str, Any]:
        with self.lock:
            return {
                'error_counts': dict(self.error_counts),
                'warning_counts': dict(self.warning_counts),
                'last_errors': dict(self.last_errors)
            }

class CustomLogger:
    _instances = []

    def __init__(self, name="cert_automation"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.config = self._load_config()
        self.logger = self._setup_logger()
        self.metrics = LoggerMetrics()
        self.rotation_manager = LogRotationManager()
        self.rotation_manager.start_rotation()
        self._instances.append(self)
        
    @classmethod
    def cleanup_all(cls):
        """Clean up all logger instances"""
        for instance in cls._instances:
            instance.cleanup()
        cls._instances.clear()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'rotation_manager'):
            self.rotation_manager.stop_rotation()
            delattr(self, 'rotation_manager')
        
        if hasattr(self, 'logger'):
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore errors during cleanup

    def _load_config(self):
        """Load logging configuration from courses.yaml"""
        try:
            with open("config/courses.yaml", 'r') as f:
                config = yaml.safe_load(f)
                return config.get('logging', {})
        except Exception as e:
            # Use default values if config file not found
            return {
                'log_dir': 'logs',
                'max_size': 10485760,  # 10MB
                'backup_count': 5,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'date_format': '%Y-%m-%d %H:%M:%S'
            }

    def _setup_logger(self):
        """Set up logger with both file and console handlers"""
        logger = base_logger
        logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)

        # Create formatters
        formatter = logging.Formatter(
            fmt=self.config.get('format'),
            datefmt=self.config.get('date_format')
        )

        # File handler for general logs
        general_log = self.log_dir / f"{self.name}.log"
        file_handler = RotatingFileHandler(
            general_log,
            maxBytes=self.config.get('max_size'),
            backupCount=self.config.get('backup_count')
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # File handler for errors
        error_log = self.log_dir / f"{self.name}_error.log"
        error_handler = RotatingFileHandler(
            error_log,
            maxBytes=self.config.get('max_size'),
            backupCount=self.config.get('backup_count')
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # File handler for debug logs
        debug_log = self.log_dir / f"{self.name}_debug.log"
        debug_handler = RotatingFileHandler(
            debug_log,
            maxBytes=self.config.get('max_size'),
            backupCount=self.config.get('backup_count')
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
        logger.addHandler(debug_handler)

        return logger

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for logging"""
        try:
            return json.dumps(context, default=str)
        except Exception:
            return str(context)

    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        module = kwargs.pop('module', '')
        context = self._format_context(kwargs)
        self.logger.debug(f"{message} | Module: {module} | Context: {context}")

    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        module = kwargs.pop('module', '')
        context = self._format_context(kwargs)
        self.logger.info(f"{message} | Module: {module} | Context: {context}")

    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        module = kwargs.pop('module', '')
        warning_type = kwargs.pop('warning_type', 'general')
        context = self._format_context(kwargs)
        self.metrics.increment_warning(module, warning_type)
        self.logger.warning(f"{message} | Module: {module} | Context: {context}")

    def error(self, message: str, **kwargs):
        """Log error message with optional context and exception info"""
        module = kwargs.pop('module', '')
        error_type = kwargs.pop('error_type', 'general')
        exc_info = kwargs.pop('exc_info', sys.exc_info())
        context = self._format_context(kwargs)
        
        if exc_info and exc_info[0]:
            self.metrics.record_last_error(module, exc_info[1])
        
        self.metrics.increment_error(module, error_type)
        self.logger.error(
            f"{message} | Module: {module} | Context: {context}",
            exc_info=exc_info if exc_info and exc_info[0] else None
        )

    def critical(self, message: str, **kwargs):
        """Log critical message with optional context and exception info"""
        module = kwargs.pop('module', '')
        error_type = kwargs.pop('error_type', 'critical')
        exc_info = kwargs.pop('exc_info', sys.exc_info())
        context = self._format_context(kwargs)
        
        if exc_info and exc_info[0]:
            self.metrics.record_last_error(module, exc_info[1])
        
        self.metrics.increment_error(module, error_type)
        self.logger.critical(
            f"{message} | Module: {module} | Context: {context}",
            exc_info=exc_info if exc_info and exc_info[0] else None
        )

    def get_metrics(self) -> Dict[str, Any]:
        """Get current logging metrics"""
        return self.metrics.get_metrics()

# Register cleanup on exit
atexit.register(CustomLogger.cleanup_all)

# Create a global logger instance
logger = CustomLogger()

# Create an AI-specific logger instance
ai_logger = CustomLogger("ai_automation")

def archive_old_logs() -> None:
    """Archive logs older than 30 days"""
    current_time = time.time()
    for log_file in Path(log_dir).glob("*.log.*"):
        # Check if file is older than 30 days
        if (current_time - os.path.getmtime(log_file)) > (30 * 24 * 60 * 60):
            # Move to archive directory
            archive_path = ARCHIVE_DIR / log_file.name
            log_file.rename(archive_path)
            logger.info(
                f"Archived old log file",
                module="logger",
                source=str(log_file),
                destination=str(archive_path)
            )

def log_execution_time(func: Optional[Callable] = None, *, threshold_ms: int = 0):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                if execution_time > threshold_ms:
                    logger.info(
                        f"Function execution completed",
                        module="timing",
                        function=func.__name__,
                        execution_time_ms=execution_time
                    )
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.error(
                    f"Function execution failed",
                    module="timing",
                    function=func.__name__,
                    execution_time_ms=execution_time,
                    error=str(e)
                )
                raise
        return wrapper
    
    if func is None:
        return decorator
    return decorator(func)

def log_error_with_context(error: Exception, message: str, **kwargs):
    """Log error with additional context"""
    logger.error(
        message,
        error=str(error),
        error_type=type(error).__name__,
        traceback=traceback.format_exc(),
        **kwargs
    )

def log_ai_interaction(prompt: str, response: str, model: str, **kwargs):
    """Log AI model interactions"""
    ai_logger.info(
        "AI interaction",
        module="ai",
        prompt=prompt,
        response=response,
        model=model,
        **kwargs
    )

def log_monitor_event(event_type: str, **kwargs):
    """Log screen monitoring events"""
    logger.info(
        f"Monitor event: {event_type}",
        module="monitor",
        event_type=event_type,
        **kwargs
    )

def log_automation_event(event_type: str, **kwargs):
    """Log automation events"""
    logger.info(
        f"Automation event: {event_type}",
        module="automation",
        event_type=event_type,
        **kwargs
    )

# Example usage:
if __name__ == "__main__":
    # Test the logger
    logger.info("Starting application")
    try:
        raise ValueError("Test error")
    except Exception as e:
        logger.error(
            "An error occurred",
            module="main",
            function="test_function",
            error_type=type(e).__name__,
            custom_field="test"
        )

# Archive old logs on module import
archive_old_logs() 