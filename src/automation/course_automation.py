"""Course automation module"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import yaml
from playwright.sync_api import Page, expect
from ..utils.logger import logger, log_execution_time
from ..utils.error_handler import AutomationError, retry_on_error

class CourseAutomation:
    """Handles course-specific automation tasks"""
    
    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = self._load_config(config_path)
        self.page: Optional[Page] = None
        self.certificate_dir = Path(self.config['certificates']['save_dir'])
        self.certificate_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_dir = Path(self.config['settings']['screenshot_dir'])
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Course automation initialized", module="course_automation")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load course configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(
                "Failed to load course config",
                module="course_automation",
                error=str(e)
            )
            return {
                'settings': {
                    'screenshot_dir': 'data/screenshots',
                    'delay_between_actions': 2
                },
                'certificates': {
                    'save_dir': 'data/certificates',
                    'verify_text': True,
                    'min_confidence': 0.8
                },
                'courses': {
                    'default': {
                        'selectors': {
                            'login_button': '#login-button',
                            'email_field': '#email',
                            'password_field': '#password',
                            'certificate_container': '#certificate-container',
                            'progress_bar': '.progress-bar',
                            'video_player': '.video-player'
                        },
                        'timeouts': {
                            'navigation': 30000,
                            'element': 5000,
                            'certificate': 10000
                        }
                    }
                }
            }

    def set_page(self, page: Page) -> None:
        """Set the Playwright page instance"""
        self.page = page

    @retry_on_error(max_attempts=3)
    @log_execution_time
    def login_to_course(self, url: str, email: str, password: str) -> bool:
        """Log in to course provider"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")

            # Navigate to login page
            self.page.goto(url)
            
            # Get selectors from config
            selectors = self.config['courses']['default']['selectors']
            
            # Fill login form
            self.page.fill(selectors['email_field'], email)
            self.page.fill(selectors['password_field'], password)
            
            # Take screenshot before login
            self.take_screenshot("login_form")
            
            # Click login button
            self.page.click(selectors['login_button'])
            
            # Wait for navigation
            self.page.wait_for_load_state('networkidle')
            
            # Verify successful login
            expect(self.page.locator(selectors['login_button'])).not_to_be_visible()
            
            logger.info(
                "Successfully logged in to course",
                module="course_automation",
                url=url
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to log in to course",
                module="course_automation",
                url=url,
                error=str(e)
            )
            return False

    @retry_on_error(max_attempts=3)
    @log_execution_time
    def check_course_progress(self) -> float:
        """Check course progress percentage"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")

            # Get progress bar selector
            progress_selector = self.config['courses']['default']['selectors']['progress_bar']
            
            # Wait for progress bar
            progress_bar = self.page.wait_for_selector(progress_selector)
            if not progress_bar:
                return 0.0
            
            # Take screenshot of progress bar
            self.take_element_screenshot(progress_selector, "progress_bar")
            
            # Get progress value
            progress_text = progress_bar.get_attribute('aria-valuenow')
            progress = float(progress_text) if progress_text else 0.0
            
            logger.info(
                "Course progress checked",
                module="course_automation",
                progress=progress
            )
            return progress
        except Exception as e:
            logger.error(
                "Failed to check course progress",
                module="course_automation",
                error=str(e)
            )
            return 0.0

    @retry_on_error(max_attempts=3)
    @log_execution_time
    def download_certificate(self, course_id: str) -> Optional[str]:
        """Download course completion certificate"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")

            # Get certificate selector
            cert_selector = self.config['courses']['default']['selectors']['certificate_container']
            
            # Wait for certificate
            self.page.wait_for_selector(cert_selector)
            
            # Take screenshot before download
            self.take_element_screenshot(cert_selector, "certificate_preview")
            
            # Save certificate screenshot
            cert_path = self.certificate_dir / f"{course_id}_certificate.png"
            self.page.screenshot(path=str(cert_path))
            
            logger.info(
                "Certificate downloaded",
                module="course_automation",
                course_id=course_id,
                path=str(cert_path)
            )
            return str(cert_path)
        except Exception as e:
            logger.error(
                "Failed to download certificate",
                module="course_automation",
                course_id=course_id,
                error=str(e)
            )
            return None

    @retry_on_error(max_attempts=3)
    @log_execution_time
    def verify_video_completion(self, video_url: str) -> bool:
        """Verify video completion status"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")

            # Navigate to video page
            self.page.goto(video_url)
            
            # Get video player selector
            video_selector = self.config['courses']['default']['selectors']['video_player']
            
            # Wait for video player
            video = self.page.wait_for_selector(video_selector)
            if not video:
                return False
            
            # Take screenshot of video player
            self.take_element_screenshot(video_selector, "video_player")
            
            # Check if video is completed
            completed = video.evaluate('video => video.ended')
            
            logger.info(
                "Video completion verified",
                module="course_automation",
                url=video_url,
                completed=completed
            )
            return completed
        except Exception as e:
            logger.error(
                "Failed to verify video completion",
                module="course_automation",
                url=video_url,
                error=str(e)
            )
            return False

    def take_screenshot(self, name: str, full_page: bool = False) -> Optional[str]:
        """Take a screenshot of the current page"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")
            
            screenshot_path = self.screenshot_dir / f"{name}_{self.page.url.split('/')[-1]}.png"
            self.page.screenshot(path=str(screenshot_path), full_page=full_page)
            
            logger.info(
                "Screenshot taken",
                module="course_automation",
                name=name,
                path=str(screenshot_path)
            )
            return str(screenshot_path)
        except Exception as e:
            logger.error(
                "Failed to take screenshot",
                module="course_automation",
                name=name,
                error=str(e)
            )
            return None

    def take_element_screenshot(self, selector: str, name: str) -> Optional[str]:
        """Take a screenshot of a specific element"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")
            
            element = self.page.locator(selector)
            if not element:
                return None
            
            screenshot_path = self.screenshot_dir / f"{name}.png"
            element.screenshot(path=str(screenshot_path))
            
            logger.info(
                "Element screenshot taken",
                module="course_automation",
                name=name,
                selector=selector,
                path=str(screenshot_path)
            )
            return str(screenshot_path)
        except Exception as e:
            logger.error(
                "Failed to take element screenshot",
                module="course_automation",
                name=name,
                selector=selector,
                error=str(e)
            )
            return None

    def verify_ui_element(self, selector: str, state: str = "visible") -> bool:
        """Verify UI element state"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")
            
            element = self.page.locator(selector)
            
            if state == "visible":
                expect(element).to_be_visible()
            elif state == "hidden":
                expect(element).not_to_be_visible()
            elif state == "enabled":
                expect(element).to_be_enabled()
            elif state == "disabled":
                expect(element).to_be_disabled()
            
            logger.info(
                "UI element verified",
                module="course_automation",
                selector=selector,
                state=state
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to verify UI element",
                module="course_automation",
                selector=selector,
                state=state,
                error=str(e)
            )
            return False

    def wait_for_navigation(self, timeout: Optional[int] = None) -> bool:
        """Wait for page navigation to complete"""
        try:
            if not self.page:
                raise AutomationError("Page not initialized")
            
            if timeout is None:
                timeout = self.config['courses']['default']['timeouts']['navigation']
            
            self.page.wait_for_load_state('networkidle', timeout=timeout)
            return True
        except Exception as e:
            logger.error(
                "Failed to wait for navigation",
                module="course_automation",
                timeout=timeout,
                error=str(e)
            )
            return False 