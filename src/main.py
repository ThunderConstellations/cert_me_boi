"""Main script for course automation"""

import argparse
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
from src.automation.browser import BrowserAutomation
from src.automation.course_automation import CourseAutomation
from src.monitor.screen_monitor import ScreenMonitor
from src.utils.logger import logger
from src.utils.persistence import DatabaseManager
from src.utils.error_handler import AutomationError
from src.utils.recovery_manager import RecoveryManager
from src.utils.metrics_collector import MetricsCollector
from src.platform_discovery import PlatformDiscovery


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        path = Path(config_path)
        if not path.exists():
            return {}
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            return config if isinstance(config, dict) else {}
    except Exception as e:
        logger.error("Failed to load config", module="main", error=str(e))
        return {}


def setup_components(
    config: Dict[str, Any],
) -> Tuple[
    BrowserAutomation,
    CourseAutomation,
    ScreenMonitor,
    RecoveryManager,
    MetricsCollector,
    PlatformDiscovery,
]:
    """Set up automation components"""
    try:
        # Initialize components
        browser = BrowserAutomation()
        course = CourseAutomation()
        monitor = ScreenMonitor()
        recovery = RecoveryManager()
        metrics = MetricsCollector()
        discovery = PlatformDiscovery()

        # Start metrics collection
        metrics.start_collection()

        # Initialize recovery manager
        recovery.initialize(browser_instance=browser, monitor_instance=monitor)

        return browser, course, monitor, recovery, metrics, discovery
    except Exception as e:
        logger.error("Failed to set up components", module="main", error=str(e))
        raise


def cleanup_components(*components: Any) -> None:
    """Clean up automation components"""
    for component in components:
        try:
            if component and hasattr(component, "cleanup"):
                component.cleanup()
        except Exception as e:
            logger.error(
                "Failed to clean up component",
                module="main",
                component=component.__class__.__name__ if component else "None",
                error=str(e),
            )


def process_course(
    browser: BrowserAutomation,
    course: CourseAutomation,
    monitor: ScreenMonitor,
    recovery: RecoveryManager,
    url: str,
    platform: str,
    email: str,
    password: str,
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
        success = course.start_automation(browser.page, platform, url, credentials)

        # Post-automation: attempt to get certificate if successful
        if success:
            logger.info(
                "Automation successful, checking for certificate...", module="main"
            )
            cert_path = course.download_certificate("latest")
            if cert_path:
                logger.info(f"Certificate secured at: {cert_path}", module="main")

        return success

    except Exception as e:
        logger.error(f"Error during course processing: {e}", module="main", url=url)
        # Attempt recovery if possible
        try:
            logger.info("Attempting recovery...", module="main")
            # Determine component from exception if possible
            component = "browser"  # Default
            if "Monitor" in type(e).__name__:
                component = "monitor"
            elif "AI" in type(e).__name__:
                component = "ai"

            success_recovery = recovery.handle_error(e, component)
            if success_recovery:
                logger.info(
                    "Recovery successful, but course run needs restart.", module="main"
                )
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
        self.browser: Optional[BrowserAutomation] = None
        self.course: Optional[CourseAutomation] = None
        self.monitor: Optional[ScreenMonitor] = None
        self.recovery: Optional[RecoveryManager] = None
        self.metrics: Optional[MetricsCollector] = None
        self.discovery: Optional[PlatformDiscovery] = None
        self._setup_components()

    def _setup_components(self) -> None:
        """Set up and initialize automation components"""
        try:
            (
                self.browser,
                self.course,
                self.monitor,
                self.recovery,
                self.metrics,
                self.discovery,
            ) = setup_components(self.config)
        except Exception as e:
            logger.error(f"Failed to setup components: {e}", module="main")
            raise

    def discover_free_courses(self, limit: int = 10) -> None:
        """Find and display free certification opportunities"""
        try:
            if not self.discovery:
                logger.error("Discovery component not initialized", module="main")
                return

            print("\n🔍 Discovering Free Certification Opportunities...")
            print("=" * 60)
            opportunities = self.discovery.get_top_certifications(limit)

            if not opportunities:
                print("No opportunities found in catalog.")
                return

            for i, opt in enumerate(opportunities, 1):
                print(f"{i}. [{opt.platform.upper()}] {opt.title}")
                print(f"   Provider: {opt.provider}")
                print(
                    f"   Value Score: {opt.value_score}/100 | Difficulty: {opt.difficulty}"
                )
                print(f"   URL: {opt.url}")
                print("-" * 60)

            print(f"\nFound {len(opportunities)} high-value free certifications.")
        except Exception as e:
            logger.error(f"Discovery failed: {e}", module="main")
            print(f"Error during discovery: {e}")

    def run_multi_course(
        self, urls: List[str], platform: str, credentials: Dict[str, str]
    ) -> bool:
        """Run automation for multiple courses"""
        if not all(
            [self.browser, self.course, self.monitor, self.recovery, self.metrics]
        ):
            logger.error("Automation components not fully initialized", module="main")
            return False

        overall_success = True
        for url in urls:
            try:
                logger.info(f"Starting automation for: {url}", module="main")
                self.db.update_course_status(url, platform, "STARTED")

                # Type checking for mypy since they are Optional
                assert self.browser is not None
                assert self.course is not None
                assert self.monitor is not None
                assert self.recovery is not None
                assert self.metrics is not None

                success = process_course(
                    self.browser,
                    self.course,
                    self.monitor,
                    self.recovery,
                    url,
                    platform,
                    credentials.get("email", ""),
                    credentials.get("password", ""),
                )

                # Record metrics
                self.metrics.record_operation(
                    "course_automation",
                    "process_course",
                    success,
                    0.0,  # Duration placeholder
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

    def stop_automation(self) -> None:
        """Stop and cleanup all components"""
        try:
            logger.info("Stopping automation", module="main")
            cleanup_components(
                self.browser,
                self.course,
                self.monitor,
                self.recovery,
                self.metrics,
                self.discovery,
            )
        except Exception as e:
            logger.error(f"Failed to stop automation: {e}", module="main")

    def cleanup(self) -> None:
        """Clean up resources"""
        self.stop_automation()

    def __enter__(self) -> "CertificationAutomation":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.cleanup()


def main() -> None:
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(description="Course automation script")
    parser.add_argument(
        "--config", default="config/courses.yaml", help="Path to config file"
    )
    parser.add_argument("--urls", help="Course URLs (comma-separated)")
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--platform", default="generic", help="Platform name")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover free certification opportunities",
    )
    args = parser.parse_args()

    with CertificationAutomation(args.config) as automation:
        if args.discover:
            automation.discover_free_courses()
            if not args.urls:
                sys.exit(0)

        if not args.urls:
            parser.print_help()
            sys.exit(1)

        urls = [url.strip() for url in args.urls.split(",")]
        credentials = {"email": args.email or "", "password": args.password or ""}

        success = automation.run_multi_course(urls, args.platform, credentials)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
