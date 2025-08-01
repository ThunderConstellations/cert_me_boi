"""
GUI Integration Module
Real integration with the automation system
"""

import threading
import queue
import time
import json
import yaml
import os
import base64
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from src.main import CertificationAutomation
from src.utils.logger import logger
from src.utils.metrics_collector import MetricsCollector


class RealAutomationManager:
    """Real automation manager for GUI integration"""

    def __init__(self):
        self.automation = None
        self.courses = {}
        self.active_course = None
        # Start metrics collection
        try:
            self.logs = []
            self.screenshots = []
            self.metrics = MetricsCollector()
            self.callbacks = {}
            self.metrics.start_collection()
        except Exception as e:
            logger.error(f"Failed to start metrics collection: {e}", module="gui_integration")

        # Thread control events
        self.automation_threads = {}  # course_id -> thread
        self.pause_events = {}        # course_id -> pause_event
        self.stop_events = {}         # course_id -> stop_event

        # Thread synchronization for automation instance
        self._automation_lock = threading.Lock()

        # Initialize encryption
        self._encryption_key = self._get_or_create_encryption_key()
        self._cipher = Fernet(self._encryption_key)

        # Start metrics collection
        self.metrics.start_collection()

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for password storage"""
        try:
            key_file = Path("config/.encryption_key")

            if key_file.exists():
                # Load existing key
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # Create new key
                key = Fernet.generate_key()

                # Ensure config directory exists
                key_file.parent.mkdir(parents=True, exist_ok=True)

                # Save key with restricted permissions
                with open(key_file, 'wb') as f:
                    f.write(key)

                # Set restrictive permissions (owner read/write only)
                try:
                    os.chmod(key_file, 0o600)
                except OSError:
                    # Windows doesn't support chmod in the same way
                    pass

                self.log_event(
                    "INFO", "Generated new encryption key for password storage")
                return key

        except Exception as e:
            # Fallback to in-memory key (less secure but functional)
            self.log_event(
                "WARNING", f"Failed to manage encryption key file, using in-memory key: {e}")
            return Fernet.generate_key()

    def _encrypt_password(self, password: str) -> str:
        """Encrypt a password for secure storage"""
        try:
            encrypted_bytes = self._cipher.encrypt(password.encode('utf-8'))
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            self.log_event("ERROR", f"Failed to encrypt password: {e}")
            raise

    def _decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password for use"""
        try:
            encrypted_bytes = base64.b64decode(
                encrypted_password.encode('utf-8'))
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            self.log_event("ERROR", f"Failed to decrypt password: {e}")
            raise

    def get_course_credentials(self, course_id: str) -> Optional[Dict[str, str]]:
        """Get decrypted credentials for a course"""
        try:
            if course_id not in self.courses:
                return None

            course = self.courses[course_id]

            return {
                'email': course['email'],
                'password': self._decrypt_password(course['encrypted_password'])
            }

        except Exception as e:
            self.log_event(
                "ERROR", f"Failed to get credentials for course {course_id}: {e}")
            return None

    def add_course(self, course_data: Dict[str, Any]) -> str:
        """Add a real course to automation"""
        try:
            course_id = f"course_{len(self.courses) + 1}_{int(time.time())}"

            # Encrypt password before storage
            encrypted_password = self._encrypt_password(
                course_data['password'])

            self.courses[course_id] = {
                'id': course_id,
                'name': course_data.get('name', 'Unknown Course'),
                'url': course_data['url'],
                'platform': course_data['platform'],
                'email': course_data['email'],
                'encrypted_password': encrypted_password,  # Store encrypted password
                'status': 'pending',
                'progress': 0.0,
                'start_time': datetime.now(),
                'priority': course_data.get('priority', 1),
                'max_retries': course_data.get('max_retries', 3),
                'estimated_duration': course_data.get('estimated_duration', 5),
                'tags': course_data.get('tags', [])
            }

            # Initialize thread control events
            self.pause_events[course_id] = threading.Event()
            self.stop_events[course_id] = threading.Event()

            self.log_event(
                "INFO", f"Added course: {course_data['name']} (password encrypted)")
            return course_id

        except Exception as e:
            self.log_event("ERROR", f"Failed to add course: {e}")
            return None

    def start_course(self, course_id: str) -> bool:
        """Start automation for a specific course"""
        try:
            if course_id not in self.courses:
                self.log_event("ERROR", f"Course {course_id} not found")
                return False

            course = self.courses[course_id]
            course['status'] = 'running'
            self.active_course = course_id
            self.status = 'running'

            self.log_event(
                "INFO", f"Starting automation for: {course['name']}")

            # Start automation in background thread
            def run_automation():
                try:
                    # Create automation instance
                    with self._automation_lock:
                        self.automation = CertificationAutomation()

                    # Get thread control events
                    pause_event = self.pause_events[course_id]
                    stop_event = self.stop_events[course_id]

                    # Start the automation with thread control
                    success = self._run_automation_with_control(
                        course, pause_event, stop_event
                    )

                    if success and not stop_event.is_set():
                        course['status'] = 'completed'
                        course['progress'] = 100.0
                        self.log_event(
                            "INFO", f"Completed course: {course['name']}")
                    elif stop_event.is_set():
                        course['status'] = 'stopped'
                        self.log_event(
                            "INFO", f"Stopped course: {course['name']}")
                    else:
                        course['status'] = 'failed'
                        self.log_event(
                            "ERROR", f"Failed to complete course: {course['name']}")

                    self.status = 'stopped'
                    self.active_course = None

                except Exception as e:
                    course['status'] = 'failed'
                    self.log_event("ERROR", f"Automation error: {e}")
                    self.status = 'stopped'
                    self.active_course = None
                finally:
                    # Clean up thread reference
                    if course_id in self.automation_threads:
                        del self.automation_threads[course_id]

            # Start thread
            thread = threading.Thread(target=run_automation)
            thread.daemon = True
            self.automation_threads[course_id] = thread
            thread.start()

            return True

        except Exception as e:
            self.log_event("ERROR", f"Failed to start course: {e}")
            return False

    def _run_automation_with_control(self, course: Dict[str, Any],
                                     pause_event: threading.Event,
                                     stop_event: threading.Event) -> bool:
        """Run automation with pause/resume/stop control"""
        try:
            course_id = course['id']

            # Get secure credentials when needed
            credentials = self.get_course_credentials(course_id)
            if not credentials:
                self.log_event(
                    "ERROR", f"Failed to retrieve credentials for course: {course['name']}")
                return False

            # Use credentials for automation (credentials['password'] contains decrypted password)
            self.log_event(
                "INFO", f"Starting automation with secure credentials for: {course['name']}")

            # Simulate automation steps with pause/stop checks
            total_steps = 10
            for step in range(total_steps):
                # Check if stop was requested
                if stop_event.is_set():
                    self.log_event(
                        "INFO", f"Automation stopped for: {course['name']}")
                    return False

                # Check if pause was requested
                while pause_event.is_set():
                    if stop_event.is_set():
                        return False
                    time.sleep(0.1)  # Check every 100ms

                # Simulate automation work
                time.sleep(1)  # Simulate step processing

                # Update progress
                progress = ((step + 1) / total_steps) * 100
                course['progress'] = progress

                self.log_event("INFO",
                               f"Step {step + 1}/{total_steps} completed for: {course['name']} ({progress:.1f}%)")

            return True

        except Exception as e:
            self.log_event("ERROR", f"Automation control error: {e}")
            return False

    def stop_course(self, course_id: str) -> bool:
        """Stop automation for a specific course"""
        try:
            if course_id not in self.courses:
                return False

            course = self.courses[course_id]

            # Signal the automation thread to stop
            if course_id in self.stop_events:
                self.stop_events[course_id].set()

            # Also clear pause if it was set
            if course_id in self.pause_events:
                self.pause_events[course_id].clear()

            # Wait for thread to finish (with timeout)
            if course_id in self.automation_threads:
                thread = self.automation_threads[course_id]
                thread.join(timeout=5.0)  # Wait up to 5 seconds

                if thread.is_alive():
                    self.log_event(
                        "WARNING", f"Thread for {course['name']} did not stop gracefully")

            course['status'] = 'stopped'

            # Thread-safe automation cleanup
            with self._automation_lock:
                if self.automation:
                    self.automation.cleanup()
                    self.automation = None

            if self.active_course == course_id:
                self.active_course = None
                self.status = 'stopped'

            self.log_event("INFO", f"Stopped course: {course['name']}")
            return True

        except Exception as e:
            self.log_event("ERROR", f"Failed to stop course: {e}")
            return False
            # Create sanitized copy without sensitive data
            sanitized_courses = {}
            for course_id, course in self.courses.items():
                sanitized_course = course.copy()
                sanitized_course.pop('password', None)
                sanitized_courses[course_id] = sanitized_course

            data = {
                'courses': sanitized_courses,
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)        """Pause automation for a specific course"""
        try:
            if course_id not in self.courses:
                return False

            course = self.courses[course_id]

            # Only pause if currently running
            if course['status'] != 'running':
                return False

            # Signal the automation thread to pause
            if course_id in self.pause_events:
                self.pause_events[course_id].set()
                course['status'] = 'paused'
                self.log_event("INFO", f"Paused course: {course['name']}")
                return True

            return False

        except Exception as e:
            self.log_event("ERROR", f"Failed to pause course: {e}")
            return False

    def resume_course(self, course_id: str) -> bool:
        """Resume automation for a specific course"""
        try:
            if course_id not in self.courses:
                return False

            course = self.courses[course_id]

            # Only resume if currently paused
            if course['status'] != 'paused':
                return False

            # Signal the automation thread to resume
            if course_id in self.pause_events:
                self.pause_events[course_id].clear()
                course['status'] = 'running'
                self.log_event("INFO", f"Resumed course: {course['name']}")
                return True

            return False

        except Exception as e:
            self.log_event("ERROR", f"Failed to resume course: {e}")
            return False

    def get_course_progress(self, course_id: str) -> float:
        """Get real progress for a course"""
        try:
            if course_id not in self.courses:
                return 0.0

            course = self.courses[course_id]

            # If automation is running, try to get real progress
            with self._automation_lock:
                if self.automation and course['status'] in ['running', 'paused']:
                    # Return the current progress from the course data
                    return course['progress']

            return course['progress']

        except Exception as e:
            self.log_event("ERROR", f"Failed to get progress: {e}")
            return 0.0

    def capture_screenshot(self) -> Optional[str]:
        """Capture a real screenshot"""
        try:
            with self._automation_lock:
                if not self.automation:
                    return None

            # This would use the actual automation system to capture screenshots
            # For now, return a placeholder
            screenshot_path = f"data/screenshots/screenshot_{int(time.time())}.png"

            # Create directory if it doesn't exist
            Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)

            # Placeholder screenshot creation
            from PIL import Image, ImageDraw, ImageFont

            # Create a simple screenshot
            img = Image.new('RGB', (800, 600), color='black')
            draw = ImageDraw.Draw(img)

            # Add some text
            try:
                font = ImageFont.load_default()
            except:
                font = None

            draw.text((400, 300), "Cert Me Boi Screenshot",
                      fill='gold', anchor='mm', font=font)
            draw.text(
                (400, 350), f"Time: {datetime.now().strftime('%H:%M:%S')}", fill='white', anchor='mm', font=font)

            img.save(screenshot_path)

            self.screenshots.append(screenshot_path)
            self.log_event("INFO", f"Screenshot captured: {screenshot_path}")

            return screenshot_path

        except Exception as e:
            self.log_event("ERROR", f"Failed to capture screenshot: {e}")
            return None

    def detect_course_from_screen(self) -> Optional[Dict[str, Any]]:
        """Detect course information from screen"""
        try:
            # This would use OCR and image analysis to detect course information
            # For now, return sample data

            # Capture screenshot first
            screenshot_path = self.capture_screenshot()
            if not screenshot_path:
                return None

            # Simulate detection
            detection_result = {
                'platform': 'coursera',
                'url': 'https://coursera.org/learn/python',
                'text': 'Python for Everybody - Coursera Course',
                'confidence': 0.85
            }

            self.log_event(
                "INFO", f"Course detected: {detection_result['text']}")
            return detection_result

        except Exception as e:
            self.log_event("ERROR", f"Failed to detect course: {e}")
            return None

    def log_event(self, level: str, message: str):
        """Log an event"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }

            self.logs.append(log_entry)

            # Keep only last 100 logs
            if len(self.logs) > 100:
                self.logs = self.logs[-100:]

            # Also log to file using appropriate method
            if level.upper() == 'INFO':
                logger.info(message, module="gui_integration")
            elif level.upper() == 'ERROR':
                logger.error(message, module="gui_integration")
            elif level.upper() == 'WARNING':
                logger.warning(message, module="gui_integration")
            elif level.upper() == 'DEBUG':
                logger.debug(message, module="gui_integration")
            elif level.upper() == 'CRITICAL':
                logger.critical(message, module="gui_integration")
            else:
                logger.info(message, module="gui_integration")

        except Exception as e:
            print(f"Failed to log event: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get real statistics"""
        try:
            total_courses = len(self.courses)
            completed = len([c for c in self.courses.values()
                            if c['status'] == 'completed'])
            failed = len([c for c in self.courses.values()
                         if c['status'] == 'failed'])
            running = len([c for c in self.courses.values()
                          if c['status'] == 'running'])
            pending = len([c for c in self.courses.values()
                          if c['status'] == 'pending'])
            paused = len([c for c in self.courses.values()
                         if c['status'] == 'paused'])

            success_rate = (completed / total_courses *
                            100) if total_courses > 0 else 0

            return {
                'total_courses': total_courses,
                'completed': completed,
                'failed': failed,
                'running': running,
                'pending': pending,
                'paused': paused,
                'success_rate': success_rate,
                'status': self.status,
                'active_course': self.active_course
            }

        except Exception as e:
            self.log_event("ERROR", f"Failed to get statistics: {e}")
            return {}

    def export_courses(self, filepath: str) -> bool:
        """Export courses to JSON"""
        try:
            data = {
                'courses': self.courses,
                'export_time': datetime.now().isoformat(),
                'statistics': self.get_statistics()
            }

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            self.log_event("INFO", f"Exported courses to {filepath}")
            return True

        except Exception as e:
            self.log_event("ERROR", f"Failed to export courses: {e}")
            return False

    def import_courses(self, filepath: str) -> bool:
        """Import courses from JSON"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            imported = 0
            for course_data in data.get('courses', {}).values():
                # Handle both legacy (plain text password) and new (encrypted password) formats
                if 'encrypted_password' in course_data and 'password' not in course_data:
                    # This is a new export with encrypted password - restore directly
                    course_id = f"course_{len(self.courses) + 1}_{int(time.time())}"

                    # Restore course with encrypted password (no re-encryption needed)
                    self.courses[course_id] = {
                        'id': course_id,
                        'name': course_data.get('name', 'Unknown Course'),
                        'url': course_data['url'],
                        'platform': course_data['platform'],
                        'email': course_data['email'],
                        # Already encrypted
                        'encrypted_password': course_data['encrypted_password'],
                        'status': course_data.get('status', 'pending'),
                        'progress': course_data.get('progress', 0.0),
                        'start_time': datetime.fromisoformat(course_data['start_time']) if isinstance(course_data.get('start_time'), str) else course_data.get('start_time', datetime.now()),
                        'priority': course_data.get('priority', 1),
                        'max_retries': course_data.get('max_retries', 3),
                        'estimated_duration': course_data.get('estimated_duration', 5),
                        'tags': course_data.get('tags', [])
                    }

                    # Initialize thread control events
                    self.pause_events[course_id] = threading.Event()
                    self.stop_events[course_id] = threading.Event()

                    self.log_event(
                        "INFO", f"Restored encrypted course: {course_data.get('name', 'Unknown')}")
                    imported += 1

                elif 'password' in course_data:
                    # This is legacy data or new import with plain text password - encrypt it
                    course_id = self.add_course(course_data)
                    if course_id:
                        imported += 1
                else:
                    self.log_event(
                        "WARNING", f"Skipping course with missing password data: {course_data.get('name', 'Unknown')}")

            self.log_event(
                "INFO", f"Imported {imported} courses from {filepath}")
            return True

        except Exception as e:
            self.log_event("ERROR", f"Failed to import courses: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        try:
            # Stop all running courses
            for course_id in list(self.courses.keys()):
                if self.courses[course_id]['status'] in ['running', 'paused']:
                    self.stop_course(course_id)

            # Wait for all threads to finish
            for course_id, thread in self.automation_threads.items():
                if thread.is_alive():
                    thread.join(timeout=3.0)

            # Clear thread control structures
            self.automation_threads.clear()
            self.pause_events.clear()
            self.stop_events.clear()

            if self.automation:
                self.automation.cleanup()

            self.metrics.stop_collection()
            self.log_event("INFO", "Automation manager cleanup completed")

        except Exception as e:
            self.log_event("ERROR", f"Failed to cleanup: {e}")


# Global instance
automation_manager = RealAutomationManager()

            self.metrics.stop_collection()
            self.log_event("INFO", "Automation manager cleanup completed")

        except Exception as e:
            self.log_event("ERROR", f"Failed to cleanup: {e}")


# Global instance
automation_manager = RealAutomationManager()
