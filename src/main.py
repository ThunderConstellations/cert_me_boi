"""Main script for course automation"""

import argparse
import sys
from pathlib import Path
from typing import Dict, Any
import yaml
from playwright.sync_api import sync_playwright
from src.automation.browser import BrowserAutomation
from src.automation.course_automation import CourseAutomation
from src.monitor.screen_monitor import ScreenMonitor
from src.utils.logger import logger
from src.utils.error_handler import AutomationError
from src.utils.recovery_manager import RecoveryManager
from src.utils.metrics_collector import MetricsCollector

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(
            "Failed to load config",
            module="main",
            error=str(e)
        )
        sys.exit(1)

def setup_components(config: Dict[str, Any]) -> tuple:
    """Set up automation components"""
    try:
        # Initialize components
        browser = BrowserAutomation()
        course = CourseAutomation()
        monitor = ScreenMonitor()
        recovery = RecoveryManager()
        metrics = MetricsCollector()

        # Start metrics collection
        metrics.start_collection()

        # Initialize recovery manager
        recovery.initialize(
            browser_instance=browser,
            monitor_instance=monitor
        )

        return browser, course, monitor, recovery, metrics
    except Exception as e:
        logger.error(
            "Failed to set up components",
            module="main",
            error=str(e)
        )
        sys.exit(1)

def cleanup_components(*components) -> None:
    """Clean up automation components"""
    for component in components:
        try:
            if hasattr(component, 'cleanup'):
                component.cleanup()
        except Exception as e:
            logger.error(
                "Failed to clean up component",
                module="main",
                component=component.__class__.__name__,
                error=str(e)
            )

def process_course(
    browser: BrowserAutomation,
    course: CourseAutomation,
    monitor: ScreenMonitor,
    url: str,
    email: str,
    password: str
) -> bool:
    """Process a single course"""
    try:
        # Start browser session
        if not browser.start():
            raise AutomationError("Failed to start browser")

        # Set up course page
        course.set_page(browser.page)

        # Log in to course
        if not course.login_to_course(url, email, password):
            raise AutomationError("Failed to log in")

        # Monitor course progress
        progress = course.check_course_progress()
        logger.info(
            "Course progress",
            module="main",
            progress=progress
        )

        # Verify video completion
        if not course.verify_video_completion(url):
            logger.warning(
                "Video not completed",
                module="main",
                url=url
            )
            return False

        # Download certificate if available
        cert_path = course.download_certificate("course123")
        if cert_path:
            logger.info(
                "Certificate downloaded",
                module="main",
                path=cert_path
            )
            return True
        return False

    except Exception as e:
        logger.error(
            "Failed to process course",
            module="main",
            url=url,
            error=str(e)
        )
        return False

class CertificationAutomation:
    """Main certification automation class for GUI integration"""
    
    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = load_config(config_path)
        self.browser = None
        self.course = None
        self.monitor = None
        self.recovery = None
        self.metrics = None
        self._setup_components()
    
    def _setup_components(self):
        """Set up automation components"""
        try:
            self.browser, self.course, self.monitor, self.recovery, self.metrics = setup_components(self.config)
        except Exception as e:
            logger.error(f"Failed to setup components: {e}", module="main")
            raise
    
    def start_automation(self, platform: str, credentials: Dict[str, str]) -> bool:
        """Start automation for a course"""
        try:
            url = credentials.get('course_url', '')
            email = credentials.get('email', '')
            password = credentials.get('password', '')
            
            logger.info(f"Starting automation for platform: {platform}", module="main")
            
            # Process the course
            success = process_course(
                self.browser,
                self.course,
                self.monitor,
                url,
                email,
                password
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Automation failed: {e}", module="main")
            return False
    
    def stop_automation(self):
        """Stop automation"""
        try:
            logger.info("Stopping automation", module="main")
            cleanup_components(self.browser, self.course, self.monitor, self.recovery, self.metrics)
        except Exception as e:
            logger.error(f"Failed to stop automation: {e}", module="main")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop_automation()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}", module="main")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Course automation script")
    parser.add_argument("--config", default="config/courses.yaml", help="Path to config file")
    parser.add_argument("--url", required=True, help="Course URL")
    parser.add_argument("--email", required=True, help="Login email")
    parser.add_argument("--password", required=True, help="Login password")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Set up components
    browser, course, monitor, recovery, metrics = setup_components(config)

    try:
        # Process course
        success = process_course(
            browser,
            course,
            monitor,
            args.url,
            args.email,
            args.password
        )

        # Record metrics
        metrics.record_operation(
            "course_automation",
            "process_course",
            success,
            0.0  # Duration placeholder
        )

        if success:
            logger.info("Course processing completed successfully")
            sys.exit(0)
        else:
            logger.error("Course processing failed")
            sys.exit(1)

    except Exception as e:
        logger.error(
            "Unhandled error",
            module="main",
            error=str(e)
        )
        sys.exit(1)

    finally:
        # Clean up components
        cleanup_components(browser, course, monitor, recovery, metrics)

if __name__ == "__main__":
    main() 