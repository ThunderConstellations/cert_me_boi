"""Main script for course automation"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import yaml
from src.automation.browser import BrowserAutomation
from src.automation.course_automation import CourseAutomation
from src.monitor.screen_monitor import ScreenMonitor
from src.utils.logger import logger
from src.utils.persistence import DatabaseManager
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
        raise

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
    recovery: RecoveryManager,
    url: str,
    platform: str,
    email: str,
    password: str
) -> bool:
    """Process a single course with recovery support"""
    start_time = time.time()
    try:
        # Start browser session if not already running
        if not browser.page:
            if not browser.start():
                raise AutomationError("Failed to start browser")

        # Set up course page
        course.set_page(browser.page)

        # Run core automation logic
        credentials = {"email": email, "password": password}
        success = course.start_automation(
            browser.page,
            platform,
            url,
            credentials
        )

        # Post-automation: attempt to get certificate if successful
        if success:
            logger.info("Automation successful, checking for certificate...", module="main")
            cert_path = course.download_certificate("latest")
            if cert_path:
                logger.info(f"Certificate secured at: {cert_path}", module="main")

        return success

    except Exception as e:
        logger.error(f"Error during course processing: {e}", module="main", url=url)
        # Attempt recovery if possible
        try:
             logger.info("Attempting recovery...", module="main")
             recovery.attempt_recovery()
             # Optionally retry processing here, but for now just report failure
        except Exception as rec_err:
             logger.error(f"Recovery failed: {rec_err}", module="main")
        return False
    finally:
        duration = time.time() - start_time
        logger.info(f"Finished processing {url} in {duration:.2f}s", module="main")

class CertificationAutomation:
    """Main certification automation class for GUI and CLI integration"""
    
    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = load_config(config_path)
        self.db = DatabaseManager()
        self.browser = None
        self.course = None
        self.monitor = None
        self.recovery = None
        self.metrics = None
        self._setup_components()
    
    def _setup_components(self):
        """Set up and initialize automation components"""
        try:
            self.browser, self.course, self.monitor, self.recovery, self.metrics = setup_components(self.config)
        except Exception as e:
            logger.error(f"Failed to setup components: {e}", module="main")
            raise
    
    def run_multi_course(self, urls: List[str], platform: str, credentials: Dict[str, str]) -> bool:
        """Run automation for multiple courses"""
        overall_success = True
        for url in urls:
            try:
                logger.info(f"Starting automation for: {url}", module="main")
                self.db.update_course_status(url, platform, "STARTED")

                success = process_course(
                    self.browser,
                    self.course,
                    self.monitor,
                    self.recovery,
                    url,
                    platform,
                    credentials.get('email', ''),
                    credentials.get('password', '')
                )

                # Record metrics
                self.metrics.record_operation(
                    "course_automation",
                    "process_course",
                    success,
                    0.0  # Duration placeholder
                )

                status = "COMPLETED" if success else "FAILED"
                self.db.update_course_status(url, platform, status)

                if success:
                    logger.info(f"Course processing completed successfully for: {url}")
                else:
                    logger.error(f"Course processing failed for: {url}")
                    overall_success = False

            except Exception as e:
                logger.error(f"Unhandled error processing {url}: {e}", module="main")
                self.db.update_course_status(url, platform, "FAILED")
                overall_success = False

        return overall_success

    def stop_automation(self):
        """Stop and cleanup all components"""
        try:
            logger.info("Stopping automation", module="main")
            cleanup_components(self.browser, self.course, self.monitor, self.recovery, self.metrics)
        except Exception as e:
            logger.error(f"Failed to stop automation: {e}", module="main")
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_automation()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(description="Course automation script")
    parser.add_argument("--config", default="config/courses.yaml", help="Path to config file")
    parser.add_argument("--urls", required=True, help="Course URLs (comma-separated)")
    parser.add_argument("--email", required=True, help="Login email")
    parser.add_argument("--password", required=True, help="Login password")
    parser.add_argument("--platform", default="generic", help="Platform name")
    args = parser.parse_args()

    urls = [url.strip() for url in args.urls.split(",")]
    credentials = {"email": args.email, "password": args.password}

    with CertificationAutomation(args.config) as automation:
        success = automation.run_multi_course(urls, args.platform, credentials)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
