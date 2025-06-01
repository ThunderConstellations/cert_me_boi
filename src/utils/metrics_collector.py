"""Metrics collection module"""

import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
import threading
from pathlib import Path
import yaml
import psutil
from .logger import logger, log_error_with_context

class MetricsCollector:
    """Collects and manages system and application metrics"""

    def __init__(self, config_path: str = "config/error_handling.yaml"):
        self.config = self._load_config(config_path)
        self.metrics = {
            'system': {},
            'components': {},
            'errors': {},
            'performance': {}
        }
        self.collection_thread = None
        self.is_collecting = False
        self.lock = threading.Lock()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load metrics configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            log_error_with_context(e, "Failed to load metrics config")
            return {
                'metrics': {
                    'thresholds': {
                        'error_rate': {
                            'warning': 0.1,
                            'critical': 0.25
                        },
                        'response_time': {
                            'warning': 5000,
                            'critical': 15000
                        },
                        'memory_usage': {
                            'warning': 0.8,
                            'critical': 0.9
                        }
                    },
                    'intervals': {
                        'error_metrics': 60,
                        'performance_metrics': 30,
                        'cleanup_interval': 3600
                    },
                    'aggregation': {
                        'window_size': 3600,
                        'bucket_size': 300
                    }
                }
            }

    def start_collection(self) -> None:
        """Start metrics collection"""
        if not self.collection_thread or not self.collection_thread.is_alive():
            self.is_collecting = True
            self.collection_thread = threading.Thread(
                target=self._collection_task,
                daemon=True
            )
            self.collection_thread.start()
            logger.info("Started metrics collection", module="metrics")

    def stop_collection(self) -> None:
        """Stop metrics collection"""
        if self.collection_thread and self.collection_thread.is_alive():
            self.is_collecting = False
            self.collection_thread.join(timeout=5)
            logger.info("Stopped metrics collection", module="metrics")

    def _collection_task(self) -> None:
        """Main collection task"""
        while self.is_collecting:
            try:
                # Collect system metrics
                self._collect_system_metrics()

                # Collect performance metrics
                self._collect_performance_metrics()

                # Check thresholds
                self._check_thresholds()

                # Clean up old metrics
                self._cleanup_old_metrics()

                # Sleep until next collection
                time.sleep(self.config['metrics']['intervals']['performance_metrics'])
            except Exception as e:
                log_error_with_context(e, "Error in metrics collection")
                time.sleep(60)  # Sleep on error

    def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        try:
            with self.lock:
                self.metrics['system'].update({
                    'timestamp': datetime.now().isoformat(),
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('/').percent
                })
        except Exception as e:
            log_error_with_context(e, "Failed to collect system metrics")

    def _collect_performance_metrics(self) -> None:
        """Collect performance metrics"""
        try:
            process = psutil.Process()
            with self.lock:
                self.metrics['performance'].update({
                    'timestamp': datetime.now().isoformat(),
                    'cpu_usage': process.cpu_percent(),
                    'memory_usage': process.memory_percent(),
                    'thread_count': process.num_threads(),
                    'handle_count': process.num_handles()
                })
        except Exception as e:
            log_error_with_context(e, "Failed to collect performance metrics")

    def _check_thresholds(self) -> None:
        """Check metric thresholds"""
        try:
            thresholds = self.config['metrics']['thresholds']
            
            # Check memory usage
            memory_percent = self.metrics['system'].get('memory_percent', 0)
            if memory_percent > thresholds['memory_usage']['critical']:
                logger.critical(
                    "Memory usage critical",
                    module="metrics",
                    usage=memory_percent
                )
            elif memory_percent > thresholds['memory_usage']['warning']:
                logger.warning(
                    "Memory usage high",
                    module="metrics",
                    usage=memory_percent
                )

            # Check error rate
            error_rate = self._calculate_error_rate()
            if error_rate > thresholds['error_rate']['critical']:
                logger.critical(
                    "Error rate critical",
                    module="metrics",
                    rate=error_rate
                )
            elif error_rate > thresholds['error_rate']['warning']:
                logger.warning(
                    "Error rate high",
                    module="metrics",
                    rate=error_rate
                )
        except Exception as e:
            log_error_with_context(e, "Failed to check thresholds")

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        try:
            with self.lock:
                total_ops = sum(
                    comp.get('total_operations', 0)
                    for comp in self.metrics['components'].values()
                )
                total_errors = sum(
                    comp.get('error_count', 0)
                    for comp in self.metrics['components'].values()
                )
                return total_errors / total_ops if total_ops > 0 else 0
        except Exception:
            return 0

    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics"""
        try:
            cutoff = time.time() - self.config['metrics']['aggregation']['window_size']
            with self.lock:
                # Clean up component metrics
                for component in self.metrics['components'].values():
                    if 'history' in component:
                        component['history'] = [
                            entry for entry in component['history']
                            if entry['timestamp'] > cutoff
                        ]

                # Clean up error metrics
                self.metrics['errors'] = {
                    key: value for key, value in self.metrics['errors'].items()
                    if value['timestamp'] > cutoff
                }
        except Exception as e:
            log_error_with_context(e, "Failed to clean up old metrics")

    def record_operation(
        self,
        component: str,
        operation: str,
        success: bool,
        duration: float
    ) -> None:
        """Record component operation"""
        try:
            with self.lock:
                if component not in self.metrics['components']:
                    self.metrics['components'][component] = {
                        'total_operations': 0,
                        'error_count': 0,
                        'history': []
                    }

                comp_metrics = self.metrics['components'][component]
                comp_metrics['total_operations'] += 1
                if not success:
                    comp_metrics['error_count'] += 1

                comp_metrics['history'].append({
                    'timestamp': time.time(),
                    'operation': operation,
                    'success': success,
                    'duration': duration
                })

                logger.debug(
                    f"Recorded {component} operation",
                    module="metrics",
                    operation=operation,
                    success=success,
                    duration=duration
                )
        except Exception as e:
            log_error_with_context(e, "Failed to record operation")

    def record_error(
        self,
        component: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record error occurrence"""
        try:
            with self.lock:
                error_key = f"{component}:{type(error).__name__}"
                self.metrics['errors'][error_key] = {
                    'timestamp': time.time(),
                    'count': self.metrics['errors'].get(error_key, {}).get('count', 0) + 1,
                    'last_message': str(error),
                    'context': context
                }

                logger.error(
                    f"Recorded error in {component}",
                    module="metrics",
                    error_type=type(error).__name__,
                    context=context
                )
        except Exception as e:
            log_error_with_context(e, "Failed to record error")

    def get_metrics(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get current metrics"""
        try:
            with self.lock:
                if component:
                    return {
                        'component': self.metrics['components'].get(component, {}),
                        'errors': {
                            k: v for k, v in self.metrics['errors'].items()
                            if k.startswith(f"{component}:")
                        }
                    }
                return dict(self.metrics)
        except Exception as e:
            log_error_with_context(e, "Failed to get metrics")
            return {}

    def save_metrics(self, path: Path) -> bool:
        """Save metrics to file"""
        try:
            with self.lock:
                metrics_json = json.dumps(self.metrics, indent=2)
                path.write_text(metrics_json)
                logger.info(
                    "Saved metrics to file",
                    module="metrics",
                    path=str(path)
                )
                return True
        except Exception as e:
            log_error_with_context(e, "Failed to save metrics")
            return False

    def load_metrics(self, path: Path) -> bool:
        """Load metrics from file"""
        try:
            metrics_json = path.read_text()
            with self.lock:
                self.metrics = json.loads(metrics_json)
                logger.info(
                    "Loaded metrics from file",
                    module="metrics",
                    path=str(path)
                )
                return True
        except Exception as e:
            log_error_with_context(e, "Failed to load metrics")
            return False

# Example usage:
if __name__ == "__main__":
    # Initialize metrics collector
    collector = MetricsCollector()
    
    # Start collection
    collector.start_collection()
    
    # Simulate some operations
    collector.record_operation("browser", "navigate", True, 500.0)
    collector.record_operation("browser", "click", False, 1000.0)
    collector.record_error("browser", Exception("ElementNotFoundError"))
    
    # Get metrics summary
    summary = collector.get_metrics()
    print(json.dumps(summary, indent=2))
    
    # Stop collection
    collector.stop_collection() 