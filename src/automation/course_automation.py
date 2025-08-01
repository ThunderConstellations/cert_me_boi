"""Course automation module"""

import asyncio
import logging
import time
import os
from typing import Dict, Any, Optional, List
from playwright.async_api import Page, Browser
from ..ai.model_handler import ModelHandler
from ..monitor.screen_monitor import ScreenMonitor
import yaml

logger = logging.getLogger(__name__)


class CourseAutomation:
    """Enhanced automation system supporting 25+ certification platforms"""

    def __init__(self, config_path: str = "config/courses.yaml"):
        self.config = self._load_config(config_path)
        self.model_handler = ModelHandler()
        self.screen_monitor = ScreenMonitor()
        self.current_platform = None

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

        # Platform-specific handlers (only for platforms with custom implementations)
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
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    async def start_automation(self, page: Page, platform: str, course_url: str, credentials: Dict[str, str]) -> bool:
        """Start automation for a specific platform"""
        try:
            self.current_platform = platform
            logger.info(f"Starting automation for {platform}")

            # Navigate to course URL
            await page.goto(course_url)
            await page.wait_for_load_state('networkidle')

            # Perform login if credentials provided
            if credentials:
                login_success = await self._login(page, platform, credentials)
                if not login_success:
                    error_msg = f"Login failed for {platform}, aborting automation"
                    logger.error(error_msg)
                    raise RuntimeError(
                        f"Authentication failed for platform '{platform}'. Cannot proceed with automation on authenticated pages without valid login.")

            # Use platform-specific handler or generic handler
            if platform in self.platform_handlers:
                return await self.platform_handlers[platform](page, course_url)
            elif platform in self.generic_platforms or platform not in self.platform_handlers:
                return await self._handle_generic_platform(page, course_url)
            else:
                return await self._handle_generic_platform(page, course_url)

        except Exception as e:
            logger.error(f"Automation failed for {platform}: {e}")
            return False

    async def _login(self, page: Page, platform: str, credentials: Dict[str, str]) -> bool:
        """Handle login for any platform"""
        try:
            platform_config = self._get_platform_config(platform)
            selectors = platform_config.get('selectors', {})

            # Click login button
            login_btn = selectors.get('login_button')
            if login_btn:
                await page.click(login_btn)
                await page.wait_for_timeout(self.timeouts['default'])

            # Fill credentials
            email_selector = selectors.get('email_input')
            password_selector = selectors.get('password_input')
            submit_selector = selectors.get('submit_button')

            if email_selector:
                await page.fill(email_selector, credentials.get('email', ''))
            if password_selector:
                await page.fill(password_selector, credentials.get('password', ''))
            if submit_selector:
                await page.click(submit_selector)
                await page.wait_for_load_state('networkidle')

            logger.info(f"Login completed for {platform}")
            return True

        except Exception as e:
            logger.error(f"Login failed for {platform}: {e}")
            return False

    def _get_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for specific platform"""
        platforms = self.config.get('platforms', [])
        for p in platforms:
            if p.get('name') == platform:
                return p
        return {}

    # Platform-specific automation handlers

    async def _handle_freecodecamp(self, page: Page, course_url: str) -> bool:
        """Handle FreeCodeCamp automation"""
        try:
            logger.info("Starting FreeCodeCamp automation")

            MAX_CHALLENGES = 100
            challenge_count = 0
            while True:
                if challenge_count >= MAX_CHALLENGES:
                    logger.warning(
                        f"Reached maximum challenge limit ({MAX_CHALLENGES})")
                    break
                challenge_count += 1

                # Wait for challenge to load
                await page.wait_for_selector('.challenge-instructions', timeout=10000)

                # Get challenge instructions
                instructions = await page.text_content('.challenge-instructions')

                # Use AI to solve coding challenge
                if await page.is_visible('.monaco-editor'):
                    # Get current code
                    current_code = await page.evaluate('() => window.editor?.getValue() || ""')

                    # Generate solution using AI
                    prompt = f"Solve this coding challenge:\n{instructions}\n\nCurrent code:\n{current_code}\n\nProvide only the complete solution code:"
                    solution = await self.model_handler.generate_text(prompt)

                    # Input solution safely using parameter passing
                    if solution:
                        await page.evaluate('(solution) => window.editor?.setValue(solution)', solution)

                    # Run tests
                    await page.click('#test-button')
                    await page.wait_for_timeout(self.timeouts['element_wait'])

                    # Submit if tests pass
                    if await page.is_visible('#submit-button:not([disabled])'):
                        await page.click('#submit-button')
                        await page.wait_for_timeout(self.timeouts['default'])

                # Check if completed
                if await page.is_visible('.challenge-completed'):
                    break

                # Move to next challenge
                if await page.is_visible('.btn-primary'):
                    await page.click('.btn-primary')
                    await page.wait_for_timeout(self.timeouts['default'])
                else:
                    break

            return True

        except Exception as e:
            logger.error(f"FreeCodeCamp automation failed: {e}")
            return False

    async def _handle_hackerrank(self, page: Page, course_url: str) -> bool:
        """Handle HackerRank skills verification"""
        try:
            logger.info("Starting HackerRank automation")

            # Navigate to skills verification
            await page.click('.skills-verification')
            await page.wait_for_timeout(self.timeouts['default'])

            # Start test
            await page.click('.start-challenge')
            await page.wait_for_load_state('networkidle')

            # Solve coding problems
            while await page.is_visible('.CodeMirror'):
                # Get problem statement
                problem_text = await page.text_content('.problem-statement')

                # Generate solution
                prompt = f"Solve this coding problem:\n{problem_text}\n\nProvide only the complete solution code:"
                solution = await self.model_handler.generate_text(prompt)

                # Input solution safely using parameter passing
                if solution:
                    await page.evaluate('(solution) => window.editor?.setValue(solution)', solution)

                # Submit
                await page.click('.hr_tour-submit')
                await page.wait_for_timeout(self.timeouts['page_load'])

                # Check if there's a next problem
                if not await page.is_visible('.next-challenge'):
                    break
                else:
                    await page.click('.next-challenge')
                    await page.wait_for_timeout(self.timeouts['default'])

            return True

        except Exception as e:
            logger.error(f"HackerRank automation failed: {e}")
            return False

    async def _handle_harvard_cs50(self, page: Page, course_url: str) -> bool:
        """Handle Harvard CS50 course automation"""
        try:
            logger.info("Starting Harvard CS50 automation")

            # Watch lectures
            if await page.is_visible('.lecture-video'):
                await self._watch_video(page, '.lecture-video')

            # Complete problem sets
            if await page.is_visible('.problem-set'):
                await page.click('.problem-set')
                await page.wait_for_timeout(self.timeouts['default'])

                # Get problem requirements
                problem_text = await page.text_content('.problem-description')

                # Generate solution using AI
                prompt = f"Solve this CS50 problem:\n{problem_text}\n\nProvide only the complete solution code:"
                solution = await self.model_handler.generate_text(prompt)

                # Submit solution
                if await page.is_visible('textarea') and solution:
                    await page.fill('textarea', solution)
                    await page.click('.submit-btn')
                    await page.wait_for_timeout(self.timeouts['element_wait'])

            return True

        except Exception as e:
            logger.error(f"Harvard CS50 automation failed: {e}")
            return False

    async def _handle_kaggle(self, page: Page, course_url: str) -> bool:
        """Handle Kaggle Learn automation"""
        try:
            logger.info("Starting Kaggle Learn automation")

            # Navigate through exercises
            while await page.is_visible('.exercise'):
                # Read exercise content
                exercise_content = await page.text_content('.exercise')

                # Complete coding exercise
                if await page.is_visible('.CodeMirror'):
                    prompt = f"Solve this Kaggle exercise:\n{exercise_content}\n\nProvide only the complete solution code:"
                    solution = await self.model_handler.generate_text(prompt)
                    if solution:
                        await page.evaluate('(solution) => window.editor?.setValue(solution)', solution)

                    # Run code
                    await page.click('.run-button')
                    await page.wait_for_timeout(self.timeouts['element_wait'])

                    # Submit if successful
                    if await page.is_visible('.submit-button:not([disabled])'):
                        await page.click('.submit-button')
                        await page.wait_for_timeout(self.timeouts['default'])

                # Move to next exercise
                if await page.is_visible('.next-exercise'):
                    await page.click('.next-exercise')
                    await page.wait_for_timeout(self.timeouts['default'])
                else:
                    break

            return True

        except Exception as e:
            logger.error(f"Kaggle automation failed: {e}")
            return False

    async def _handle_google_skillshop(self, page: Page, course_url: str) -> bool:
        """Handle Google Skillshop automation"""
        try:
            logger.info("Starting Google Skillshop automation")

            # Complete course content
            while await page.is_visible('.course-content'):
                # Read lesson content
                # Scroll to bottom of the page
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(self.timeouts['default'])
                # Take assessments
                if await page.is_visible('.assessment'):
                    await self._handle_assessment(page, '.assessment')

                # Move to next section
                if await page.is_visible('.next-section'):
                    await page.click('.next-section')
                    await page.wait_for_timeout(self.timeouts['default'])
                else:
                    break

            return True

        except Exception as e:
            logger.error(f"Google Skillshop automation failed: {e}")
            return False

    async def _handle_microsoft_learn(self, page: Page, course_url: str) -> bool:
        """Handle Microsoft Learn automation"""
        try:
            logger.info("Starting Microsoft Learn automation")

            # Complete learning modules
            while await page.is_visible('.module-content'):
                # Read content
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await page.wait_for_timeout(self.timeouts['default'])

                # Complete knowledge checks
                if await page.is_visible('.knowledge-check'):
                    await self._handle_quiz(page, '.knowledge-check')

                # Mark module complete
                if await page.is_visible('.complete-module'):
                    await page.click('.complete-module')
                    await page.wait_for_timeout(self.timeouts['default'])

                # Next module
                if await page.is_visible('.next-module'):
                    await page.click('.next-module')
                    await page.wait_for_timeout(self.timeouts['default'])
                else:
                    break

            return True

        except Exception as e:
            logger.error(f"Microsoft Learn automation failed: {e}")
            return False

    # Generic handlers for common course elements

    async def _watch_video(self, page: Page, video_selector: str) -> bool:
        """Generic video watching handler"""
        try:
            if await page.is_visible(video_selector):
                # Click play
                if await page.is_visible('.vjs-play-control'):
                    await page.click('.vjs-play-control')

                # Wait for video to complete (simulate watching)
                duration = await page.evaluate('() => document.querySelector("video")?.duration || 60')
                # Max 5 minutes
                await page.wait_for_timeout(min(int(duration * 1000), 300000))

                return True
            return False
        except Exception as e:
            logger.error(f"Video watching failed: {e}")
            return False

    async def _handle_quiz(self, page: Page, quiz_selector: str) -> bool:
        """Generic quiz handling"""
        try:
            if await page.is_visible(quiz_selector):
                # Get quiz questions
                questions = await page.query_selector_all(f'{quiz_selector} .question')

                for question in questions:
                    question_text = await question.text_content()

                    # Get all option texts to provide context
                    options = await question.query_selector_all('input[type="radio"], input[type="checkbox"]')
                    context_options = []
                    for option in options:
                        option_text = await option.get_attribute('value') or await option.text_content()
                        if option_text:
                            context_options.append(option_text)

                    context = "Available options: " + \
                        ", ".join(context_options)

                    # Get answer using AI
                    answer = await self.model_handler.answer_question(question_text, context)

                    # Select answer (adapt based on question type)
                    if answer and options:
                        # Find best matching option
                        for option in options:
                            option_text = await option.get_attribute('value') or await option.text_content()
                            if option_text and answer.lower() in option_text.lower():
                                await option.click()
                                break

                # Submit quiz
                submit_btn = await page.query_selector(f'{quiz_selector} .submit-button')
                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_timeout(self.timeouts['default'])

                return True
            return False
        except Exception as e:
            logger.error(f"Quiz handling failed: {e}")
            return False

    async def _handle_assessment(self, page: Page, assessment_selector: str) -> bool:
        """Generic assessment handling"""
        try:
            return await self._handle_quiz(page, assessment_selector)
        except Exception as e:
            logger.error(f"Assessment handling failed: {e}")
            return False

    # Generic handler for platforms without specific implementation
    async def _handle_generic_platform(self, page: Page, course_url: str) -> bool:
        """Generic handler for platforms without specific implementation"""
        try:
            logger.info(f"Using generic handler for {self.current_platform}")

            # Basic course completion flow
            # 1. Watch videos if present
            if await page.is_visible('.video, .video-player'):
                await self._watch_video(page, '.video, .video-player')

            # 2. Complete quizzes if present
            if await page.is_visible('.quiz, .quiz-container, .assessment'):
                await self._handle_quiz(page, '.quiz, .quiz-container, .assessment')

            # 3. Submit assignments if present
            if await page.is_visible('.assignment, textarea'):
                assignment_text = await page.text_content('.assignment-instructions, .assignment-description')
                if assignment_text:
                    prompt = f"Complete this assignment:\n{assignment_text}\n\nProvide a detailed response:"
                    solution = await self.model_handler.generate_text(prompt)
                    if solution:
                        await page.fill('textarea', solution)
                        if await page.is_visible('.submit-assignment, .submit-button'):
                            await page.click('.submit-assignment, .submit-button')

            # 4. Navigate to next content
            if await page.is_visible('.next-button, .next-lesson, .continue-button'):
                await page.click('.next-button, .next-lesson, .continue-button')
                await page.wait_for_timeout(self.timeouts['default'])

            return True
        except Exception as e:
            logger.error(f"Generic platform handling failed: {e}")
            return False

    async def get_certificate(self, page: Page) -> Optional[str]:
        """Download certificate if available"""
        try:
            certificate_selectors = [
                '.certificate-download',
                '.certificate-link',
                '.download-certificate',
                '.badge-download',
                'a[href*="certificate"]',
                'a[href*="badge"]'
            ]

            for selector in certificate_selectors:
                if await page.is_visible(selector):
                    # Take screenshot of certificate
                    os.makedirs("data/certificates", exist_ok=True)
                    cert_path = f"data/certificates/{self.current_platform}_{int(time.time())}.png"
                    await page.screenshot(path=cert_path)

                    # Try to download if it's a download link
                    href = await page.get_attribute(selector, 'href')
                    if href and any(ext in href for ext in ['.pdf', '.png', '.jpg']):
                        async with page.expect_download() as download_info:
                            await page.click(selector)
                        download = await download_info.value
                        await download.save_as(cert_path.replace('.png', f'.{href.split(".")[-1]}'))

                    logger.info(f"Certificate saved: {cert_path}")
                    return cert_path

            return None

        except Exception as e:
            logger.error(f"Certificate download failed: {e}")
            return None
