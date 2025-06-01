import os
import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import Mock, patch
import numpy as np
import pandas as pd

from src.utils.logger import CustomLogger
from src.utils.log_aggregator import LogAggregator
from src.utils.log_analyzer import LogAnalyzer

@pytest.fixture
def temp_log_dir():
    """Create a temporary directory for logs"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def test_logger(temp_log_dir):
    """Create a test logger instance"""
    logger = CustomLogger("test_logger")
    logger.log_dir = Path(temp_log_dir)
    return logger

@pytest.fixture
def test_aggregator(temp_log_dir):
    """Create a test log aggregator instance"""
    with patch('src.utils.log_aggregator.LogAggregator._load_config') as mock_config:
        mock_config.return_value = {
            'logging': {
                'log_dir': temp_log_dir,
                'max_size': 1024,  # 1KB for testing
                'backup_count': 3,
                'rotation': {
                    'max_days': 7,
                    'compress': True
                }
            },
            'metrics': {
                'intervals': {
                    'cleanup_interval': 1
                }
            }
        }
        aggregator = LogAggregator()
        yield aggregator

@pytest.fixture
def test_analyzer(temp_log_dir):
    """Create a test log analyzer instance"""
    analyzer = LogAnalyzer(temp_log_dir)
    return analyzer

def create_test_log_file(directory: Path, name: str, entries: list) -> Path:
    """Create a test log file with specified entries"""
    log_file = directory / name
    with open(log_file, 'w') as f:
        for entry in entries:
            timestamp = entry.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            level = entry.get('level', 'INFO')
            message = entry.get('message', 'Test message')
            context = entry.get('context', {})
            
            log_line = f"{timestamp} - test - {level} - {message} | Context: {json.dumps(context)}\n"
            f.write(log_line)
    return log_file

class TestCustomLogger:
    """Test cases for CustomLogger"""

    def test_basic_logging(self, test_logger):
        """Test basic logging functionality"""
        test_logger.info("Test info message", module="test")
        test_logger.error("Test error message", module="test", error_type="TestError")
        
        log_file = test_logger.log_dir / "test_logger.log"
        assert log_file.exists()
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert "INFO" in lines[0]
            assert "ERROR" in lines[1]

    def test_context_logging(self, test_logger):
        """Test logging with context"""
        context = {'user': 'test_user', 'action': 'test_action'}
        test_logger.info("Test message with context", module="test", **context)
        
        log_file = test_logger.log_dir / "test_logger.log"
        with open(log_file, 'r') as f:
            line = f.readline()
            assert 'test_user' in line
            assert 'test_action' in line

    def test_error_metrics(self, test_logger):
        """Test error metrics collection"""
        test_logger.error("Test error", module="test", error_type="TestError")
        metrics = test_logger.metrics.get_metrics()
        
        assert 'error_counts' in metrics
        assert 'test:TestError' in metrics['error_counts']
        assert metrics['error_counts']['test:TestError'] == 1

    @pytest.mark.asyncio
    async def test_async_logging(self, test_logger):
        """Test logging in async context"""
        async def async_operation():
            test_logger.info("Async operation", module="test")
            return True

        result = await async_operation()
        assert result
        
        log_file = test_logger.log_dir / "test_logger.log"
        with open(log_file, 'r') as f:
            line = f.readline()
            assert "Async operation" in line

class TestLogAggregator:
    """Test cases for LogAggregator"""

    def test_log_rotation(self, test_aggregator):
        """Test log file rotation"""
        # Create a large log file
        log_file = test_aggregator.log_dir / "test.log"
        with open(log_file, 'w') as f:
            f.write('x' * 2048)  # Write 2KB of data

        test_aggregator.rotate_logs()
        
        # Check that the original file was rotated
        assert log_file.exists()
        assert log_file.stat().st_size == 0
        
        # Check that archive was created
        archives = list(test_aggregator.archive_dir.glob("*.gz"))
        assert len(archives) == 1

    def test_log_cleanup(self, test_aggregator):
        """Test cleanup of old log files"""
        # Create old archive files
        old_date = datetime.now() - timedelta(days=10)
        archive_file = test_aggregator.archive_dir / "old_test.log.gz"
        archive_file.touch()
        os.utime(str(archive_file), (old_date.timestamp(), old_date.timestamp()))

        test_aggregator._cleanup_old_archives()
        
        # Check that old archive was removed
        assert not archive_file.exists()

    def test_component_log_aggregation(self, test_aggregator):
        """Test aggregation of component logs"""
        # Create test log files
        entries = [
            {'timestamp': '2024-03-14 10:00:00', 'level': 'INFO', 'message': 'Test 1'},
            {'timestamp': '2024-03-14 10:01:00', 'level': 'ERROR', 'message': 'Test 2'}
        ]
        create_test_log_file(test_aggregator.log_dir, "component_test.log", entries)

        logs = test_aggregator.aggregate_component_logs("component")
        assert len(logs) == 2
        assert logs[0]['level'] == 'INFO'
        assert logs[1]['level'] == 'ERROR'

class TestLogAnalyzer:
    """Test cases for LogAnalyzer"""

    def test_error_pattern_analysis(self, test_analyzer, temp_log_dir):
        """Test analysis of error patterns"""
        # Create test log file with errors
        entries = [
            {'level': 'ERROR', 'message': 'Test error 1', 'context': {'error_type': 'TypeError'}},
            {'level': 'ERROR', 'message': 'Test error 2', 'context': {'error_type': 'TypeError'}},
            {'level': 'ERROR', 'message': 'Test error 3', 'context': {'error_type': 'ValueError'}}
        ]
        create_test_log_file(Path(temp_log_dir), "test.log", entries)

        results = test_analyzer.process_logs()
        error_patterns = results['error_patterns']
        
        assert error_patterns['frequencies']['TypeError'] == 2
        assert error_patterns['frequencies']['ValueError'] == 1

    def test_performance_metrics_analysis(self, test_analyzer, temp_log_dir):
        """Test analysis of performance metrics"""
        # Create test log file with performance metrics
        entries = [
            {
                'level': 'INFO',
                'message': 'Operation completed',
                'context': {
                    'module': 'test',
                    'function': 'test_func',
                    'execution_time_ms': 100
                }
            },
            {
                'level': 'INFO',
                'message': 'Operation completed',
                'context': {
                    'module': 'test',
                    'function': 'test_func',
                    'execution_time_ms': 200
                }
            }
        ]
        create_test_log_file(Path(temp_log_dir), "test.log", entries)

        results = test_analyzer.process_logs()
        perf_metrics = results['performance_metrics']
        
        assert 'test:test_func' in perf_metrics
        assert perf_metrics['test:test_func']['mean'] == 150.0

    def test_anomaly_detection(self, test_analyzer, temp_log_dir):
        """Test anomaly detection in logs"""
        # Create test log file with normal and anomalous entries
        base_time = datetime.now()
        entries = []
        
        # Add normal entries
        for i in range(10):
            timestamp = base_time + timedelta(minutes=i)
            entries.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'level': 'INFO',
                'message': f'Normal entry {i}'
            })
        
        # Add anomalous entry
        anomaly_time = base_time + timedelta(hours=1)
        entries.append({
            'timestamp': anomaly_time.strftime('%Y-%m-%d %H:%M:%S'),
            'level': 'ERROR',
            'message': 'Anomalous entry'
        })
        
        create_test_log_file(Path(temp_log_dir), "test.log", entries)

        results = test_analyzer.process_logs()
        assert len(results['anomalies']) > 0

    def test_recommendations_generation(self, test_analyzer, temp_log_dir):
        """Test generation of recommendations"""
        # Create test log file with high error rate
        entries = [{'level': 'ERROR', 'message': f'Error {i}'} for i in range(5)]
        entries.extend([{'level': 'INFO', 'message': f'Info {i}'} for i in range(5)])
        create_test_log_file(Path(temp_log_dir), "test.log", entries)

        results = test_analyzer.process_logs()
        assert len(results['recommendations']) > 0
        
        # Check for high error rate recommendation
        error_recs = [r for r in results['recommendations'] if r['type'] == 'error_pattern']
        assert len(error_recs) > 0

    def test_component_health_metrics(self, test_analyzer, temp_log_dir):
        """Test component health metrics calculation"""
        # Create test log file with component events
        entries = [
            {'level': 'INFO', 'message': 'Normal operation', 'context': {'module': 'test_component'}},
            {'level': 'ERROR', 'message': 'Error occurred', 'context': {'module': 'test_component'}},
            {'level': 'WARNING', 'message': 'Warning event', 'context': {'module': 'test_component'}}
        ]
        create_test_log_file(Path(temp_log_dir), "test.log", entries)

        results = test_analyzer.process_logs()
        health_metrics = test_analyzer.get_component_health()
        
        assert 'test_component' in health_metrics
        component_health = health_metrics['test_component']
        assert component_health['total_events'] == 3
        assert component_health['error_rate'] == pytest.approx(1/3)
        assert component_health['warning_rate'] == pytest.approx(1/3) 