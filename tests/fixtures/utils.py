"""Utility fixtures for testing"""

import os
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, Generator

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
def temp_log_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Temporary log directory"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    old_log_dir = os.environ.get("LOG_DIR")
    os.environ["LOG_DIR"] = str(log_dir)
    yield log_dir
    if old_log_dir:
        os.environ["LOG_DIR"] = old_log_dir
    else:
        del os.environ["LOG_DIR"]

@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Temporary configuration directory"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    old_config_dir = os.environ.get("CONFIG_DIR")
    os.environ["CONFIG_DIR"] = str(config_dir)
    yield config_dir
    if old_config_dir:
        os.environ["CONFIG_DIR"] = old_config_dir
    else:
        del os.environ["CONFIG_DIR"]

@pytest.fixture
def assert_logs_contain():
    """Assert that logs contain expected text"""
    def _assert_logs_contain(log_file: Path, expected_text: str):
        assert log_file.exists(), f"Log file {log_file} does not exist"
        content = log_file.read_text()
        assert expected_text in content, f"Expected text '{expected_text}' not found in logs"
    return _assert_logs_contain

@pytest.fixture
def assert_metrics_recorded():
    """Assert that metrics were recorded correctly"""
    def _assert_metrics_recorded(metrics: Dict[str, Any], component: str, operation: str, success: bool):
        key = f"{component}:{operation}"
        assert key in metrics, f"No metrics found for {key}"
        assert metrics[key]["success"] == success, f"Expected success={success} for {key}"
    return _assert_metrics_recorded 