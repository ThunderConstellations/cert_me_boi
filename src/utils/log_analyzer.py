import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import pandas as pd
from sklearn.cluster import DBSCAN
import numpy as np
from .logger import logger

class LogAnalyzer:
    """Analyzes log files to extract insights and patterns"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.error_patterns = defaultdict(int)
        self.performance_metrics = defaultdict(list)
        self.component_stats = defaultdict(lambda: defaultdict(int))
        self.time_series_data = []

    def process_logs(self, days: int = 7) -> Dict[str, Any]:
        """Process logs from the last N days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            results = {
                'error_patterns': {},
                'performance_metrics': {},
                'component_stats': {},
                'anomalies': [],
                'recommendations': []
            }

            # Process each log file
            for log_file in self.log_dir.glob("*.log"):
                if not self._is_log_recent(log_file, cutoff_date):
                    continue

                self._process_log_file(log_file, results)

            # Analyze the collected data
            self._analyze_error_patterns(results)
            self._analyze_performance_metrics(results)
            self._detect_anomalies(results)
            self._generate_recommendations(results)

            return results

        except Exception as e:
            logger.error(
                "Failed to process logs",
                module="log_analyzer",
                error=str(e)
            )
            return {}

    def _is_log_recent(self, log_file: Path, cutoff_date: datetime) -> bool:
        """Check if log file is more recent than cutoff date"""
        try:
            file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
            return file_date >= cutoff_date
        except Exception:
            return False

    def _process_log_file(self, log_file: Path, results: Dict[str, Any]) -> None:
        """Process a single log file"""
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse log entry
                        entry = self._parse_log_entry(line)
                        if not entry:
                            continue

                        # Update statistics based on entry type
                        if entry['level'] == 'ERROR':
                            self._process_error_entry(entry)
                        elif 'execution_time_ms' in entry.get('context', {}):
                            self._process_performance_entry(entry)

                        # Update component statistics
                        component = entry.get('context', {}).get('module', 'unknown')
                        self.component_stats[component]['total'] += 1
                        self.component_stats[component][entry['level'].lower()] += 1

                        # Add to time series data
                        self.time_series_data.append({
                            'timestamp': entry['timestamp'],
                            'level': entry['level'],
                            'component': component,
                            'message': entry['message']
                        })

                    except Exception as e:
                        logger.warning(
                            "Failed to process log entry",
                            module="log_analyzer",
                            error=str(e),
                            line=line
                        )

        except Exception as e:
            logger.error(
                "Failed to process log file",
                module="log_analyzer",
                file=str(log_file),
                error=str(e)
            )

    def _parse_log_entry(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a log entry into structured data"""
        try:
            # Example format: 2024-03-14 10:15:30 - name - LEVEL - Message | Context: {...}
            match = re.match(
                r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+(\w+)\s+-\s+(.*?)(?:\s+\|\s+Context:\s+(.*))?$',
                line
            )
            
            if not match:
                return None

            timestamp_str, name, level, message, context_str = match.groups()
            
            entry = {
                'timestamp': datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S'),
                'name': name,
                'level': level,
                'message': message,
                'context': json.loads(context_str) if context_str else {}
            }

            return entry

        except Exception:
            return None

    def _process_error_entry(self, entry: Dict[str, Any]) -> None:
        """Process an error log entry"""
        error_type = entry.get('context', {}).get('error_type', 'unknown')
        self.error_patterns[error_type] += 1

    def _process_performance_entry(self, entry: Dict[str, Any]) -> None:
        """Process a performance log entry"""
        context = entry.get('context', {})
        if 'execution_time_ms' in context:
            component = context.get('module', 'unknown')
            operation = context.get('function', 'unknown')
            metric_key = f"{component}:{operation}"
            self.performance_metrics[metric_key].append(context['execution_time_ms'])

    def _analyze_error_patterns(self, results: Dict[str, Any]) -> None:
        """Analyze error patterns and frequencies"""
        total_errors = sum(self.error_patterns.values())
        if total_errors == 0:
            return

        results['error_patterns'] = {
            'frequencies': dict(self.error_patterns),
            'percentages': {
                error_type: (count / total_errors) * 100
                for error_type, count in self.error_patterns.items()
            }
        }

    def _analyze_performance_metrics(self, results: Dict[str, Any]) -> None:
        """Analyze performance metrics"""
        performance_stats = {}
        
        for metric_key, durations in self.performance_metrics.items():
            if not durations:
                continue

            stats = {
                'mean': np.mean(durations),
                'median': np.median(durations),
                'p95': np.percentile(durations, 95),
                'min': min(durations),
                'max': max(durations),
                'std': np.std(durations)
            }
            
            performance_stats[metric_key] = stats

        results['performance_metrics'] = performance_stats

    def _detect_anomalies(self, results: Dict[str, Any]) -> None:
        """Detect anomalies in the log data"""
        try:
            # Convert time series data to DataFrame
            df = pd.DataFrame(self.time_series_data)
            if df.empty:
                return

            # Prepare features for clustering
            df['timestamp_num'] = pd.to_numeric(df['timestamp'])
            features = df[['timestamp_num']].values

            # Use DBSCAN for anomaly detection
            dbscan = DBSCAN(eps=300000, min_samples=2)  # 5 minutes in milliseconds
            clusters = dbscan.fit_predict(features)

            # Find anomalies (points labeled as noise by DBSCAN)
            anomaly_indices = np.where(clusters == -1)[0]
            
            # Extract anomalous events
            anomalies = []
            for idx in anomaly_indices:
                event = df.iloc[idx]
                anomalies.append({
                    'timestamp': event['timestamp'].isoformat(),
                    'level': event['level'],
                    'component': event['component'],
                    'message': event['message']
                })

            results['anomalies'] = anomalies

        except Exception as e:
            logger.error(
                "Failed to detect anomalies",
                module="log_analyzer",
                error=str(e)
            )

    def _generate_recommendations(self, results: Dict[str, Any]) -> None:
        """Generate recommendations based on analysis"""
        recommendations = []

        # Check error patterns
        error_patterns = results.get('error_patterns', {}).get('percentages', {})
        for error_type, percentage in error_patterns.items():
            if percentage > 10:  # More than 10% of errors
                recommendations.append({
                    'type': 'error_pattern',
                    'severity': 'high' if percentage > 25 else 'medium',
                    'message': f"High frequency of {error_type} errors ({percentage:.1f}%)",
                    'suggestion': "Consider implementing specific error handling for this case"
                })

        # Check performance metrics
        perf_metrics = results.get('performance_metrics', {})
        for metric_key, stats in perf_metrics.items():
            if stats['p95'] > 5000:  # P95 > 5 seconds
                recommendations.append({
                    'type': 'performance',
                    'severity': 'high' if stats['p95'] > 15000 else 'medium',
                    'message': f"Slow performance detected in {metric_key}",
                    'suggestion': "Consider optimization or caching strategies"
                })

        # Check component health
        for component, stats in self.component_stats.items():
            error_rate = stats.get('error', 0) / stats['total'] if stats['total'] > 0 else 0
            if error_rate > 0.1:  # More than 10% error rate
                recommendations.append({
                    'type': 'component_health',
                    'severity': 'high' if error_rate > 0.25 else 'medium',
                    'message': f"High error rate in component {component} ({error_rate:.1%})",
                    'suggestion': "Review component reliability and error handling"
                })

        results['recommendations'] = recommendations

    def get_component_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health metrics for each component"""
        health_metrics = {}
        
        for component, stats in self.component_stats.items():
            total = stats['total']
            if total == 0:
                continue

            error_rate = stats.get('error', 0) / total
            warning_rate = stats.get('warning', 0) / total
            
            health_metrics[component] = {
                'total_events': total,
                'error_rate': error_rate,
                'warning_rate': warning_rate,
                'health_score': 1 - (error_rate + warning_rate * 0.5),  # Simple health score
                'status': self._get_health_status(error_rate, warning_rate)
            }

        return health_metrics

    def _get_health_status(self, error_rate: float, warning_rate: float) -> str:
        """Determine component health status"""
        if error_rate > 0.25 or warning_rate > 0.5:
            return 'critical'
        elif error_rate > 0.1 or warning_rate > 0.25:
            return 'warning'
        else:
            return 'healthy'

    def export_analysis(self, output_dir: str = "logs/analysis") -> None:
        """Export analysis results to files"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Process recent logs
            results = self.process_logs()
            
            # Export results to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            with open(output_path / f"analysis_{timestamp}.json", 'w') as f:
                json.dump(results, f, indent=2, default=str)

            # Export time series data to CSV
            df = pd.DataFrame(self.time_series_data)
            if not df.empty:
                df.to_csv(output_path / f"timeseries_{timestamp}.csv", index=False)

            logger.info(
                "Exported log analysis",
                module="log_analyzer",
                output_dir=str(output_path)
            )

        except Exception as e:
            logger.error(
                "Failed to export analysis",
                module="log_analyzer",
                error=str(e)
            ) 