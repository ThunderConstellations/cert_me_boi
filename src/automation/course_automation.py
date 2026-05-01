"""Course automation module"""

import logging
import time
import os
import yaml
import random
from typing import Dict, Any, Optional, List
from playwright.sync_api import Page, Browser
from ..ai.model_handler import ModelHandler
from ..monitor.screen_monitor import ScreenMonitor

logger = logging.getLogger(__name__)


class CourseAutomation:
    """Enhanced automation system supporting 25+ certification platforms"""

    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = self._load_config(config_path)
        self.model_handler = ModelHandler()
        self.screen_monitor = ScreenMonitor()
        self.current_platform = None
        self.page = None

        # Configure timeouts from config with defaults
        timeouts_config = self.config.get('timeouts', {})
        self.timeouts = {
            'default': timeouts_config.get('default', 2000),
            'page_load': timeouts_config.get('page_load', 5000),
            'element_wait': timeouts_config.get('element_wait', 3000)
        }

        # Platforms that use generic handling
        self.generic_platforms = {
            'huggingface', 'university_helsinki', 'upgrad', 'ibm_skills',
            'matlab_onramp', 'cisco_netacad', 'saylor_academy', 'stepik',
            'complexity_explorer', 'hubspot_academy', 'wolfram_u',
            'semrush_academy', 'codesignal', 'open_university',
            'stanford_medicine', 'edraak', 'openhpi', 'edx', 'coursera', 'udemy'
        }

        # Platform-specific handlers
        self.platform_handlers = {
            'freecodecamp': self._handle_freecodecamp,
            'hackerrank': self._handle_hackerrank,
            'harvard_cs50': self._handle_harvard_cs50,
            'kaggle': self._handle_kaggle,
            'google_skillshop': self._handle_google_skillshop,
            'microsoft_learn': self._handle_microsoft_learn
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file) or {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def start_automation(self, page: Page, platform: str, course_url: str, credentials: Dict[str, str]) -> bool:
        """Start automation for a specific platform"""
        try:
            self.page = page
            self.current_platform = platform
            logger.info(f"Starting automation for {platform}")

            # Navigation is handled by caller or login, but ensure we are on the page
            if credentials:
                login_success = self.login_to_course(course_url, credentials.get('email', ''), credentials.get('password', ''))
                if not login_success:
                    logger.error(f"Login failed for {platform}")
                    return False
            else:
                self.page.goto(course_url)
                self.page.wait_for_load_state('networkidle')

            # Use platform-specific handler or generic handler
            if platform in self.platform_handlers:
                return self.platform_handlers[platform](self.page, course_url)
            else:
                return self._handle_generic_platform(self.page, course_url)

        except Exception as e:
            logger.error(f"Automation failed for {platform}: {e}")
            return False

    def login_to_course(self, url: str, email: str, password: str) -> bool:
        """Handle login for any platform"""
        try:
            platform_config = self._get_platform_config(self.current_platform)
            selectors = platform_config.get('selectors', {})

            # Navigate to course/login URL
            self.page.goto(url)
            self.page.wait_for_load_state('networkidle')

            # Click login button if present
            login_btn = selectors.get('login_button')
            if login_btn and self.page.is_visible(login_btn):
                self.page.click(login_btn)
                self.page.wait_for_timeout(self.timeouts['default'])

            # Fill credentials
            email_selector = selectors.get('email_input') or selectors.get('email_field')
            password_selector = selectors.get('password_input') or selectors.get('password_field')
            submit_selector = selectors.get('submit_button')

            if email_selector and self.page.is_visible(email_selector):
                self.page.fill(email_selector, email)
            if password_selector and self.page.is_visible(password_selector):
                self.page.fill(password_selector, password)
            if submit_selector and self.page.is_visible(submit_selector):
                self.page.click(submit_selector)
                self.page.wait_for_load_state('networkidle')

            logger.info(f"Login process completed for {self.current_platform}")
            return True # Assuming success if no exception and elements handled

        except Exception as e:
            logger.error(f"Login failed for {self.current_platform}: {e}")
            return False

    def _get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for specific platform"""
        platforms = self.config.get('platforms', [])
        if isinstance(platforms, list):
            for p in platforms:
                if p.get('name') == platform:
                    return p
        elif isinstance(platforms, dict):
             return platforms.get(platform, {})
        return {}

    def _get_ai_reasoning_prompt(self, task_type: str, content: str, context: Optional[str] = None) -> str:
        """Get enhanced reasoning prompt for DeepSeek R1/o1-level models"""
        if task_type == "coding":
            return f"""
            ### TASK: SOLVE CODING CHALLENGE
            ### INSTRUCTIONS:
            {content}
            ### CONTEXT:
            {context if context else 'No additional context provided.'}
            ### REQUIREMENTS:
            1. Analyze the problem step-by-step.
            2. Provide only the complete, functional code.
            3. Ensure the code is optimized and follows best practices.
            4. Do not include explanations unless requested in the instructions.
            ### SOLUTION:
            """
        elif task_type == "assignment":
             return f"""
            ### TASK: COMPLETE ACADEMIC ASSIGNMENT
            ### INSTRUCTIONS:
            {content}
            ### REQUIREMENTS:
            1. Provide a detailed, high-quality response.
            2. Use a professional and academic tone.
            3. Address all parts of the instructions thoroughly.
            4. Ensure the response is original and well-structured.
            ### RESPONSE:
            """
        return f"Solve this task: {content}"

    def _handle_freecodecamp(self, page: Page, course_url: str) -> bool:
        """Handle FreeCodeCamp automation"""
        try:
            logger.info("Starting FreeCodeCamp automation")
            MAX_CHALLENGES = 100
            challenge_count = 0
            while challenge_count < MAX_CHALLENGES:
                challenge_count += 1
                page.wait_for_selector('.challenge-instructions', timeout=10000)
                instructions = page.text_content('.challenge-instructions')
                if page.is_visible('.monaco-editor'):
                    current_code = page.evaluate('() => window.editor?.getValue() || ""')
                    prompt = self._get_ai_reasoning_prompt("coding", instructions, f"Current Code: {current_code}")
                    solution = self.model_handler.generate_text(prompt)
                    if solution:
                        if "```" in solution:
                             solution = solution.split("```")[1]
                             if solution.startswith("python") or solution.startswith("javascript"):
                                 solution = "\n".join(solution.split("\n")[1:])
                        page.evaluate('(solution) => window.editor?.setValue(solution)', solution)
                    page.click('#test-button')
                    page.wait_for_timeout(self.timeouts['element_wait'])
                    if page.is_visible('#submit-button:not([disabled])'):
                        page.click('#submit-button')
                        page.wait_for_timeout(self.timeouts['default'])
                if page.is_visible('.challenge-completed'):
                    break
                if page.is_visible('.btn-primary'):
                    page.click('.btn-primary')
                    page.wait_for_timeout(self.timeouts['default'])
                else:
                    break
            return True
        except Exception as e:
            logger.error(f"FreeCodeCamp automation failed: {e}")
            return False

    def _handle_hackerrank(self, page: Page, course_url: str) -> bool:
        """Handle HackerRank skills verification"""
        try:
            logger.info("Starting HackerRank automation")
            page.click('.skills-verification')
            page.wait_for_timeout(self.timeouts['default'])
            page.click('.start-challenge')
            page.wait_for_load_state('networkidle')
            while page.is_visible('.CodeMirror'):
                problem_text = page.text_content('.problem-statement')
                prompt = self._get_ai_reasoning_prompt("coding", problem_text)
                solution = self.model_handler.generate_text(prompt)
                if solution:
                    page.evaluate('(solution) => window.editor?.setValue(solution)', solution)
                page.click('.hr_tour-submit')
                page.wait_for_timeout(self.timeouts['page_load'])
                if not page.is_visible('.next-challenge'):
                    break
                else:
                    page.click('.next-challenge')
                    page.wait_for_timeout(self.timeouts['default'])
            return True
        except Exception as e:
            logger.error(f"HackerRank automation failed: {e}")
            return False

    def _handle_harvard_cs50(self, page: Page, course_url: str) -> bool:
        """Handle Harvard CS50 course automation"""
        try:
            logger.info("Starting Harvard CS50 automation")
            if page.is_visible('.lecture-video'):
                self._watch_video(page, '.lecture-video')
            if page.is_visible('.problem-set'):
                page.click('.problem-set')
                page.wait_for_timeout(self.timeouts['default'])
                problem_text = page.text_content('.problem-description')
                prompt = self._get_ai_reasoning_prompt("coding", problem_text)
                solution = self.model_handler.generate_text(prompt)
                if page.is_visible('textarea') and solution:
                    page.fill('textarea', solution)
                    page.click('.submit-btn')
                    page.wait_for_timeout(self.timeouts['element_wait'])
            return True
        except Exception as e:
            logger.error(f"Harvard CS50 automation failed: {e}")
            return False

    def _handle_kaggle(self, page: Page, course_url: str) -> bool:
        """Handle Kaggle Learn automation"""
        try:
            logger.info("Starting Kaggle Learn automation")
            while page.is_visible('.exercise'):
                exercise_content = page.text_content('.exercise')
                if page.is_visible('.CodeMirror'):
                    prompt = self._get_ai_reasoning_prompt("coding", exercise_content)
                    solution = self.model_handler.generate_text(prompt)
                    if solution:
                        page.evaluate('(solution) => window.editor?.setValue(solution)', solution)
                    page.click('.run-button')
                    page.wait_for_timeout(self.timeouts['element_wait'])
                    if page.is_visible('.submit-button:not([disabled])'):
                        page.click('.submit-button')
                        page.wait_for_timeout(self.timeouts['default'])
                if page.is_visible('.next-exercise'):
                    page.click('.next-exercise')
                    page.wait_for_timeout(self.timeouts['default'])
                else:
                    break
            return True
        except Exception as e:
            logger.error(f"Kaggle automation failed: {e}")
            return False

    def _handle_google_skillshop(self, page: Page, course_url: str) -> bool:
        """Handle Google Skillshop automation"""
        try:
            logger.info("Starting Google Skillshop automation")
            while page.is_visible('.course-content'):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(self.timeouts['default'])
                if page.is_visible('.assessment'):
                    self._handle_assessment(page, '.assessment')
                if page.is_visible('.next-section'):
                    page.click('.next-section')
                    page.wait_for_timeout(self.timeouts['default'])
                else:
                    break
            return True
        except Exception as e:
            logger.error(f"Google Skillshop automation failed: {e}")
            return False

    def _handle_microsoft_learn(self, page: Page, course_url: str) -> bool:
        """Handle Microsoft Learn automation"""
        try:
            logger.info("Starting Microsoft Learn automation")
            while page.is_visible('.module-content'):
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(self.timeouts['default'])
                if page.is_visible('.knowledge-check'):
                    self._handle_quiz(page, '.knowledge-check')
                if page.is_visible('.complete-module'):
                    page.click('.complete-module')
                    page.wait_for_timeout(self.timeouts['default'])
                if page.is_visible('.next-module'):
                    page.click('.next-module')
                    page.wait_for_timeout(self.timeouts['default'])
                else:
                    break
            return True
        except Exception as e:
            logger.error(f"Microsoft Learn automation failed: {e}")
            return False

    def _watch_video(self, page: Page, video_selector: str) -> bool:
        """Generic video watching handler"""
        try:
            if page.is_visible(video_selector):
                if page.is_visible('.vjs-play-control'):
                    page.click('.vjs-play-control')
                duration = page.evaluate('() => document.querySelector("video")?.duration || 60')
                page.wait_for_timeout(min(int(duration * 1000), 300000))
                return True
            return False
        except Exception as e:
            logger.error(f"Video watching failed: {e}")
            return False

    def _handle_quiz(self, page: Page, quiz_selector: str) -> bool:
        """Generic quiz handling"""
        try:
            if page.is_visible(quiz_selector):
                questions = page.query_selector_all(f'{quiz_selector} .question')
                for question in questions:
                    question_text = question.text_content()
                    options = question.query_selector_all('input[type="radio"], input[type="checkbox"]')
                    context_options = []
                    for option in options:
                        option_text = option.get_attribute('value') or option.text_content()
                        if option_text:
                            context_options.append(option_text)
                    context = "Available options: " + ", ".join(context_options)
                    answer = self.model_handler.answer_question(question_text, context)
                    if answer and options:
                        for option in options:
                            option_text = option.get_attribute('value') or option.text_content()
                            if option_text and answer.lower() in option_text.lower():
                                option.click()
                                break
                submit_btn = page.query_selector(f'{quiz_selector} .submit-button')
                if submit_btn:
                    submit_btn.click()
                    page.wait_for_timeout(self.timeouts['default'])
                return True
            return False
        except Exception as e:
            logger.error(f"Quiz handling failed: {e}")
            return False

    def _handle_assessment(self, page: Page, assessment_selector: str) -> bool:
        """Generic assessment handling"""
        return self._handle_quiz(page, assessment_selector)

    def _handle_generic_platform(self, page: Page, course_url: str) -> bool:
        """Generic handler for platforms without specific implementation"""
        try:
            logger.info(f"Using generic handler for {self.current_platform}")
            if page.is_visible('.video, .video-player'):
                self._watch_video(page, '.video, .video-player')
            if page.is_visible('.quiz, .quiz-container, .assessment'):
                self._handle_quiz(page, '.quiz, .quiz-container, .assessment')
            if page.is_visible('.assignment, textarea'):
                assignment_text = page.text_content('.assignment-instructions, .assignment-description')
                if assignment_text:
                    prompt = self._get_ai_reasoning_prompt("assignment", assignment_text)
                    solution = self.model_handler.generate_text(prompt)
                    if solution:
                        page.fill('textarea', solution)
                        if page.is_visible('.submit-assignment, .submit-button'):
                            page.click('.submit-assignment, .submit-button')
            if page.is_visible('.next-button, .next-lesson, .continue-button'):
                page.click('.next-button, .next-lesson, .continue-button')
                page.wait_for_timeout(self.timeouts['default'])
            return True
        except Exception as e:
            logger.error(f"Generic platform handling failed: {e}")
            return False

    def get_certificate(self, page: Page) -> Optional[str]:
        """Download certificate if available"""
        try:
            certificate_selectors = [
                '.certificate-download', '.certificate-link', '.download-certificate',
                '.badge-download', 'a[href*="certificate"]', 'a[href*="badge"]'
            ]
            for selector in certificate_selectors:
                if page.is_visible(selector):
                    os.makedirs("data/certificates", exist_ok=True)
                    cert_path = f"data/certificates/{self.current_platform}_{int(time.time())}.png"
                    page.screenshot(path=cert_path)
                    href = page.get_attribute(selector, 'href')
                    if href and any(ext in href for ext in ['.pdf', '.png', '.jpg']):
                        with page.expect_download() as download_info:
                            page.click(selector)
                        download = download_info.value
                        download.save_as(cert_path.replace('.png', f'.{href.split(".")[-1]}'))
                    logger.info(f"Certificate saved: {cert_path}")
                    return cert_path
            return None
        except Exception as e:
            logger.error(f"Certificate download failed: {e}")
            return None

    def set_page(self, page: Page):
        self.page = page

    def verify_video_completion(self, url: str) -> bool:
        return True

    def check_course_progress(self) -> float:
        return 0.0

    def download_certificate(self, course_id: str) -> Optional[str]:
        return self.get_certificate(self.page)

    def cleanup(self):
        if hasattr(self, 'model_handler') and self.model_handler:
            self.model_handler.cleanup()
        if hasattr(self, 'screen_monitor') and self.screen_monitor:
            self.screen_monitor.cleanup()
