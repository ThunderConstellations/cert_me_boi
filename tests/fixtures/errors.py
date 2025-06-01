"""Error fixtures for testing"""

import pytest
from typing import Dict

class AutomationError(Exception):
    """Base class for automation errors"""
    pass

class BrowserError(AutomationError):
    """Browser automation errors"""
    pass

class MonitorError(AutomationError):
    """Screen monitoring errors"""
    pass

class AIError(AutomationError):
    """AI-related errors"""
    pass

@pytest.fixture
def error_factory() -> Dict[str, Exception]:
    """Factory for creating test errors"""
    return {
        "automation": AutomationError("Test automation error"),
        "browser": BrowserError("Test browser error"),
        "monitor": MonitorError("Test monitor error"),
        "ai": AIError("Test AI error")
    } 