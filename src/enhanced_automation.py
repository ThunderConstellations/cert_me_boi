"""
Enhanced Automation System for Cert Me Boi
Advanced features including multi-course queuing, smart scheduling, and improved AI
"""

import asyncio
import threading
import queue
import time
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from src.main import CertificationAutomation
from src.utils.logger import logger
from src.utils.metrics_collector import MetricsCollector
from src.utils.recovery_manager import RecoveryManager

class CourseStatus(Enum):
    """Course status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Course:
    """Course data structure"""
    id: str
    name: str
    url: str
    platform: str
    email: str
    password: str
    status: CourseStatus
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_count: int = 0
    max_retries: int = 3
    priority: int = 1  # Higher number = higher priority
    estimated_duration: Optional[float] = None  # in hours
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.start_time is None:
            self.start_time = datetime.now()

class EnhancedAutomation:
    """Enhanced automation system with multi-course support"""
    
    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = self._load_config(config_path)
        self.courses: Dict[str, Course] = {}
        self.course_queue = queue.PriorityQueue()
        self.running = False
        self.paused = False
        self.workers: List[threading.Thread] = []
        self.max_workers = self.config.get('max_workers', 2)
        self.metrics = MetricsCollector()
        self.recovery_manager = RecoveryManager()
        self.callbacks: Dict[str, List[Callable]] = {
            'course_started': [],
            'course_completed': [],
            'course_failed': [],
            'progress_updated': [],
            'error_occurred': []
        }
        
        # Initialize logging
        self.logger = logger
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}
    
    def add_course(self, course: Course) -> bool:
        """Add a course to the queue"""
        try:
            self.courses[course.id] = course
            # Add to priority queue (negative priority for max-heap behavior)
            self.course_queue.put((-course.priority, course.id))
            self.logger.info(f"Added course: {course.name}")
            self._trigger_callback('course_started', course)
            return True
        except Exception as e:
            self.logger.error(f"Failed to add course: {e}")
            return False
    
    def remove_course(self, course_id: str) -> bool:
        """Remove a course from the queue"""
        try:
            if course_id in self.courses:
                course = self.courses[course_id]
                course.status = CourseStatus.CANCELLED
                self.logger.info(f"Removed course: {course.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to remove course: {e}")
            return False
    
    def pause_course(self, course_id: str) -> bool:
        """Pause a specific course"""
        try:
            if course_id in self.courses:
                course = self.courses[course_id]
                course.status = CourseStatus.PAUSED
                self.logger.info(f"Paused course: {course.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause course: {e}")
            return False
    
    def resume_course(self, course_id: str) -> bool:
        """Resume a specific course"""
        try:
            if course_id in self.courses:
                course = self.courses[course_id]
                course.status = CourseStatus.PENDING
                # Re-add to queue
                self.course_queue.put((-course.priority, course_id))
                self.logger.info(f"Resumed course: {course.name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume course: {e}")
            return False
    
    def start_automation(self) -> bool:
        """Start the automation system"""
        try:
            if self.running:
                self.logger.warning("Automation already running")
                return False
            
            self.running = True
            self.paused = False
            
            # Start worker threads
            for i in range(self.max_workers):
                worker = threading.Thread(
                    target=self._worker_loop,
                    args=(f"worker-{i}",),
                    daemon=True
                )
                worker.start()
                self.workers.append(worker)
            
            self.logger.info(f"Started automation with {self.max_workers} workers")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start automation: {e}")
            return False
    
    def stop_automation(self) -> bool:
        """Stop the automation system"""
        try:
            self.running = False
            self.paused = True
            
            # Wait for workers to finish
            for worker in self.workers:
                worker.join(timeout=5)
            
            self.workers.clear()
            self.logger.info("Stopped automation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop automation: {e}")
            return False
    
    def pause_automation(self) -> bool:
        """Pause the automation system"""
        try:
            self.paused = True
            self.logger.info("Paused automation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to pause automation: {e}")
            return False
    
    def resume_automation(self) -> bool:
        """Resume the automation system"""
        try:
            self.paused = False
            self.logger.info("Resumed automation")
            return True
        except Exception as e:
            self.logger.error(f"Failed to resume automation: {e}")
            return False
    
    def _worker_loop(self, worker_name: str):
        """Worker thread loop"""
        self.logger.info(f"Started worker: {worker_name}")
        
        while self.running:
            try:
                if self.paused:
                    time.sleep(1)
                    continue
                
                # Get next course from queue
                try:
                    priority, course_id = self.course_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if course_id not in self.courses:
                    continue
                
                course = self.courses[course_id]
                
                # Check if course should be processed
                if course.status != CourseStatus.PENDING:
                    continue
                
                # Process the course
                self._process_course(course, worker_name)
                
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}")
                time.sleep(1)
        
        self.logger.info(f"Stopped worker: {worker_name}")
    
    def _process_course(self, course: Course, worker_name: str):
        """Process a single course"""
        try:
            self.logger.info(f"Processing course: {course.name} (Worker: {worker_name})")
            
            # Update status
            course.status = CourseStatus.RUNNING
            course.start_time = datetime.now()
            
            # Create automation instance
            automation = CertificationAutomation()
            
            # Start automation
            success = automation.start_automation(
                course.platform,
                {
                    "email": course.email,
                    "password": course.password,
                    "course_url": course.url
                }
            )
            
            if success:
                course.status = CourseStatus.COMPLETED
                course.end_time = datetime.now()
                course.progress = 100.0
                self._trigger_callback('course_completed', course)
                self.logger.info(f"Completed course: {course.name}")
            else:
                course.status = CourseStatus.FAILED
                course.error_count += 1
                self._trigger_callback('course_failed', course)
                self.logger.error(f"Failed course: {course.name}")
            
        except Exception as e:
            course.status = CourseStatus.FAILED
            course.error_count += 1
            self._trigger_callback('error_occurred', course, str(e))
            self.logger.error(f"Error processing course {course.name}: {e}")
    
    def get_course_status(self, course_id: str) -> Optional[Course]:
        """Get course status"""
        return self.courses.get(course_id)
    
    def get_all_courses(self) -> List[Course]:
        """Get all courses"""
        return list(self.courses.values())
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.course_queue.qsize()
    
    def get_running_courses(self) -> List[Course]:
        """Get currently running courses"""
        return [course for course in self.courses.values() 
                if course.status == CourseStatus.RUNNING]
    
    def get_completed_courses(self) -> List[Course]:
        """Get completed courses"""
        return [course for course in self.courses.values() 
                if course.status == CourseStatus.COMPLETED]
    
    def get_failed_courses(self) -> List[Course]:
        """Get failed courses"""
        return [course for course in self.courses.values() 
                if course.status == CourseStatus.FAILED]
    
    def retry_failed_courses(self) -> int:
        """Retry all failed courses"""
        retried = 0
        for course in self.get_failed_courses():
            if course.error_count < course.max_retries:
                course.status = CourseStatus.PENDING
                course.error_count += 1
                self.course_queue.put((-course.priority, course.id))
                retried += 1
        
        self.logger.info(f"Retried {retried} failed courses")
        return retried
    
    def add_callback(self, event: str, callback: Callable):
        """Add event callback"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callback(self, event: str, course: Course, *args):
        """Trigger event callbacks"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(course, *args)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
    
    def export_courses(self, filepath: str) -> bool:
        """Export courses to JSON file"""
        try:
            data = {
                'courses': [asdict(course) for course in self.courses.values()],
                'export_time': datetime.now().isoformat(),
                'total_courses': len(self.courses),
                'completed': len(self.get_completed_courses()),
                'failed': len(self.get_failed_courses())
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.logger.info(f"Exported courses to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to export courses: {e}")
            return False
    
    def import_courses(self, filepath: str) -> bool:
        """Import courses from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            imported = 0
            for course_data in data.get('courses', []):
                # Convert status string back to enum
                course_data['status'] = CourseStatus(course_data['status'])
                course = Course(**course_data)
                if self.add_course(course):
                    imported += 1
            
            self.logger.info(f"Imported {imported} courses from {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to import courses: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get automation statistics"""
        total = len(self.courses)
        completed = len(self.get_completed_courses())
        failed = len(self.get_failed_courses())
        running = len(self.get_running_courses())
        pending = len([c for c in self.courses.values() 
                      if c.status == CourseStatus.PENDING])
        
        success_rate = (completed / total * 100) if total > 0 else 0
        
        return {
            'total_courses': total,
            'completed': completed,
            'failed': failed,
            'running': running,
            'pending': pending,
            'success_rate': success_rate,
            'queue_size': self.get_queue_size(),
            'is_running': self.running,
            'is_paused': self.paused,
            'active_workers': len(self.workers)
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_automation()
        self.metrics.stop_collection()
        self.logger.info("Enhanced automation cleanup completed")

# Example usage
if __name__ == "__main__":
    # Create enhanced automation
    automation = EnhancedAutomation()
    
    # Add some courses
    courses = [
        Course(
            id="python-basics",
            name="Python Basics",
            url="https://coursera.org/learn/python",
            platform="coursera",
            email="user@example.com",
            password="password",
            status=CourseStatus.PENDING,
            priority=1
        ),
        Course(
            id="data-science",
            name="Data Science",
            url="https://udemy.com/course/data-science",
            platform="udemy",
            email="user@example.com",
            password="password",
            status=CourseStatus.PENDING,
            priority=2
        )
    ]
    
    for course in courses:
        automation.add_course(course)
    
    # Start automation
    automation.start_automation()
    
    try:
        # Run for a while
        time.sleep(60)
    except KeyboardInterrupt:
        print("Stopping automation...")
    finally:
        automation.cleanup() 