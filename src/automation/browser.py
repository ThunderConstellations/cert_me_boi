"""Browser automation module"""

from typing import Optional, Dict, Any
from pathlib import Path
import yaml
from playwright.sync_api import sync_playwright, Browser, Page
from src.utils.logger import logger, log_event, log_error_with_context

# Create component-specific logger
automation_logger = logger

def log_automation_event(event_type: str, **kwargs) -> None:
    """Log automation-specific events"""
    log_event(event_type, kwargs, level='INFO')

class BrowserAutomation:
    """Browser automation using Playwright"""

    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = self._load_config(config_path)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshot_dir = Path(self.config['browser']['screenshot_dir'])
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load browser configuration"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            log_error_with_context(e, "Failed to load browser config")
            return {
                'browser': {
                    'headless': True,
                    'timeout': 30,
                    'retry_attempts': 3,
                    'screenshot_dir': 'data/screenshots',
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }

    def start(self) -> bool:
        """Start browser session"""
        try:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(
                headless=self.config['browser']['headless']
            )
            self.page = self.browser.new_page(
                user_agent=self.config['browser']['user_agent']
            )
            log_automation_event("browser_started")
            return True
        except Exception as e:
            log_error_with_context(e, "Failed to start browser")
            return False

    def cleanup(self) -> None:
        """Clean up browser resources"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            log_automation_event("browser_closed")
        except Exception as e:
            log_error_with_context(e, "Failed to clean up browser")

    def navigate(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            self.page.goto(url, timeout=self.config['browser']['timeout'] * 1000)
            log_automation_event("page_loaded", url=url)
            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to navigate to {url}")
            return False

    def click_element(self, selector: str) -> bool:
        """Click element by selector"""
        try:
            self.page.click(selector, timeout=self.config['browser']['timeout'] * 1000)
            log_automation_event("element_clicked", selector=selector)
            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to click element {selector}")
            return False

    def fill_input(self, selector: str, value: str) -> bool:
        """Fill input field"""
        try:
            self.page.fill(selector, value, timeout=self.config['browser']['timeout'] * 1000)
            log_automation_event("input_filled", selector=selector)
            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to fill input {selector}")
            return False

    def save_screenshot(self, name: str) -> Optional[str]:
        """Save page screenshot"""
        try:
            path = self.screenshot_dir / f"{name}.png"
            self.page.screenshot(path=str(path))
            log_automation_event("screenshot_saved", path=str(path))
            return str(path)
        except Exception as e:
            log_error_with_context(e, f"Failed to save screenshot {name}")
            return None

    def login(self, url: str, email: str, password: str) -> bool:
        """Log in to course provider"""
        try:
            # Navigate to login page
            if not self.navigate(url):
                return False

            # Fill login form
            if not self.fill_input("#email", email):
                return False
            if not self.fill_input("#password", password):
                return False

            # Click login button
            if not self.click_element("#login-button"):
                return False

            log_automation_event("login_successful", url=url)
            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to login at {url}")
            return False

    def download_certificate(self, url: str, save_path: Path) -> bool:
        """Download course certificate"""
        try:
            # Navigate to certificate page
            if not self.navigate(url):
                return False

            # Wait for certificate to load
            self.page.wait_for_selector("#certificate-container")

            # Save certificate screenshot
            if not self.save_screenshot(save_path.stem):
                return False

            log_automation_event("certificate_downloaded", url=url, path=str(save_path))
            return True
        except Exception as e:
            log_error_with_context(e, f"Failed to download certificate from {url}")
            return False 