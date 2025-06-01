"""Base logger module"""

import logging
import os
import yaml
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pathlib import Path
import traceback
from typing import Dict, Any, Optional

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

class CustomLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = None
        self.context = None

class CustomLogger(logging.Logger):
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info,
                  func=None, extra=None, sinfo=None, **kwargs):
        """Create a custom LogRecord instance"""
        record = CustomLogRecord(name, level, fn, lno, msg, args, exc_info, func, sinfo)
        if extra:
            for key, value in extra.items():
                setattr(record, key, value)
        return record

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             stacklevel=1, **kwargs):
        """Override _log to handle custom fields"""
        if extra is None:
            extra = {}
        extra.update(kwargs)
        super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel)

# Register custom logger class
logging.setLoggerClass(CustomLogger)

# Create formatters
class CustomFormatter(logging.Formatter):
    def format(self, record):
        """Format log record with custom fields"""
        # Format the basic message
        record.message = record.getMessage()
        
        # Add custom fields if present
        custom_fields = {}
        if hasattr(record, 'module'):
            custom_fields['module'] = record.module
        if hasattr(record, 'context'):
            custom_fields['context'] = record.context
        
        # Create the full message
        if custom_fields:
            record.message = f"{record.message} | {json.dumps(custom_fields)}"
        
        return super().format(record)

# Create base logger
logger = logging.getLogger("cert_automation")
logger.setLevel(logging.DEBUG)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = CustomFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def log_error_with_context(error: Exception, context: str, logger: Optional[logging.Logger] = None) -> None:
    """Log an error with additional context information"""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context,
        'timestamp': datetime.now().isoformat(),
        'traceback': traceback.format_exc()
    }
    
    log_message = json.dumps(error_data)
    (logger or base_logger).error(log_message)

def log_event(event_type: str, details: Optional[Dict[str, Any]] = None, level: str = 'INFO') -> None:
    """Log a structured event with consistent formatting"""
    event_data = {
        'timestamp': datetime.now().isoformat(),
        'event_type': event_type,
        'details': details or {}
    }
    
    log_message = json.dumps(event_data)
    getattr(logger, level.lower())(log_message) 