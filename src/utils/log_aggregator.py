import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import gzip
from .logger import logger

class LogAggregator:
    """Aggregates and manages logs from different components"""
    
    def __init__(self, config_path: str = "config/error_handling.yaml"):
        self.config = self._load_config(config_path)
        self.log_dir = Path(self.config['logging']['log_dir'])
        self.archive_dir = self.log_dir / "archive"
        self.lock = Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Create necessary directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(
                "Failed to load config",
                module="log_aggregator",
                error=str(e)
            )
            return {
                'logging': {
                    'log_dir': 'logs',
                    'max_size': 10485760,  # 10MB
                    'backup_count': 5,
                    'rotation': {
                        'max_days': 30,
                        'compress': True
                    }
                }
            }

    def rotate_logs(self) -> None:
        """Rotate log files based on size and age"""
        try:
            with self.lock:
                for log_file in self.log_dir.glob("*.log"):
                    try:
                        # Check file size
                        if log_file.stat().st_size > self.config['logging']['max_size']:
                            self._rotate_file(log_file)
                    except Exception as e:
                        logger.error(
                            "Failed to rotate log file",
                            module="log_aggregator",
                            file=str(log_file),
                            error=str(e)
                        )
        except Exception as e:
            logger.error(
                "Failed to rotate logs",
                module="log_aggregator",
                error=str(e)
            )

    def _rotate_file(self, log_file: Path) -> None:
        """Rotate a single log file"""
        try:
            # Generate rotation timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create backup filename
            backup_name = f"{log_file.stem}_{timestamp}{log_file.suffix}"
            backup_path = self.archive_dir / backup_name
            
            # Move current log to archive
            shutil.move(str(log_file), str(backup_path))
            
            # Compress if configured
            if self.config['logging']['rotation']['compress']:
                self._compress_file(backup_path)
                backup_path.unlink()  # Remove original after compression
            
            # Create new empty log file
            log_file.touch()
            
            logger.info(
                "Rotated log file",
                module="log_aggregator",
                source=str(log_file),
                destination=str(backup_path)
            )
            
            # Clean up old archives
            self._cleanup_old_archives()

        except Exception as e:
            logger.error(
                "Failed to rotate file",
                module="log_aggregator",
                file=str(log_file),
                error=str(e)
            )

    def _compress_file(self, file_path: Path) -> None:
        """Compress a file using gzip"""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            logger.debug(
                "Compressed log file",
                module="log_aggregator",
                source=str(file_path),
                destination=str(compressed_path)
            )

        except Exception as e:
            logger.error(
                "Failed to compress file",
                module="log_aggregator",
                file=str(file_path),
                error=str(e)
            )

    def _cleanup_old_archives(self) -> None:
        """Clean up old archived logs"""
        try:
            max_age = timedelta(days=self.config['logging']['rotation']['max_days'])
            cutoff_date = datetime.now() - max_age

            for archive_file in self.archive_dir.glob("*"):
                try:
                    # Check file age
                    file_date = datetime.fromtimestamp(archive_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        archive_file.unlink()
                        logger.debug(
                            "Removed old archive",
                            module="log_aggregator",
                            file=str(archive_file)
                        )
                except Exception as e:
                    logger.warning(
                        "Failed to check/remove archive file",
                        module="log_aggregator",
                        file=str(archive_file),
                        error=str(e)
                    )

        except Exception as e:
            logger.error(
                "Failed to clean up archives",
                module="log_aggregator",
                error=str(e)
            )

    def start_background_rotation(self) -> None:
        """Start background log rotation"""
        def rotation_task():
            while True:
                try:
                    # Sleep for the configured interval
                    interval = self.config['metrics']['intervals'].get('cleanup_interval', 3600)
                    time.sleep(interval)
                    
                    # Rotate logs
                    self.rotate_logs()
                    
                except Exception as e:
                    logger.error(
                        "Error in background rotation",
                        module="log_aggregator",
                        error=str(e)
                    )
                    time.sleep(60)  # Sleep on error to prevent tight loop

        self.executor.submit(rotation_task)
        logger.info(
            "Started background log rotation",
            module="log_aggregator"
        )

    def aggregate_component_logs(self, component: str, days: int = 1) -> List[Dict[str, Any]]:
        """Aggregate logs for a specific component"""
        try:
            aggregated_logs = []
            cutoff_date = datetime.now() - timedelta(days=days)

            # Search in current logs
            component_logs = self.log_dir.glob(f"{component}*.log")
            for log_file in component_logs:
                self._aggregate_file_logs(log_file, cutoff_date, aggregated_logs)

            # Search in archives
            archive_logs = self.archive_dir.glob(f"{component}*.log*")
            for archive_file in archive_logs:
                self._aggregate_file_logs(archive_file, cutoff_date, aggregated_logs)

            return sorted(aggregated_logs, key=lambda x: x['timestamp'])

        except Exception as e:
            logger.error(
                "Failed to aggregate component logs",
                module="log_aggregator",
                component=component,
                error=str(e)
            )
            return []

    def _aggregate_file_logs(self, file_path: Path, cutoff_date: datetime, aggregated_logs: List[Dict[str, Any]]) -> None:
        """Aggregate logs from a single file"""
        try:
            # Handle compressed files
            if file_path.suffix == '.gz':
                opener = gzip.open
            else:
                opener = open

            with opener(file_path, 'rt') as f:
                for line in f:
                    try:
                        # Parse log entry
                        entry = self._parse_log_entry(line)
                        if not entry:
                            continue

                        # Check if entry is within time range
                        if entry['timestamp'] >= cutoff_date:
                            aggregated_logs.append(entry)

                    except Exception as e:
                        logger.warning(
                            "Failed to parse log entry",
                            module="log_aggregator",
                            file=str(file_path),
                            line=line,
                            error=str(e)
                        )

        except Exception as e:
            logger.error(
                "Failed to aggregate file logs",
                module="log_aggregator",
                file=str(file_path),
                error=str(e)
            )

    def _parse_log_entry(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a log entry into structured data"""
        try:
            # Example format: 2024-03-14 10:15:30 - name - LEVEL - Message | Context: {...}
            import re
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

    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about log files"""
        try:
            stats = {
                'total_size': 0,
                'file_count': 0,
                'archive_size': 0,
                'archive_count': 0,
                'components': set(),
                'oldest_log': None,
                'newest_log': None
            }

            # Current logs
            for log_file in self.log_dir.glob("*.log"):
                stats['total_size'] += log_file.stat().st_size
                stats['file_count'] += 1
                stats['components'].add(log_file.stem.split('_')[0])
                
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if not stats['newest_log'] or mtime > stats['newest_log']:
                    stats['newest_log'] = mtime
                if not stats['oldest_log'] or mtime < stats['oldest_log']:
                    stats['oldest_log'] = mtime

            # Archives
            for archive_file in self.archive_dir.glob("*"):
                stats['archive_size'] += archive_file.stat().st_size
                stats['archive_count'] += 1

            # Convert components set to list for JSON serialization
            stats['components'] = list(stats['components'])
            
            return stats

        except Exception as e:
            logger.error(
                "Failed to get log stats",
                module="log_aggregator",
                error=str(e)
            )
            return {} 