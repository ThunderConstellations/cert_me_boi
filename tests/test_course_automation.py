"""Test course automation module"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from playwright.sync_api import Page
from src.automation.course_automation import CourseAutomation
from src.utils.error_handler import AutomationError

@pytest.fixture
def mock_config():
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
        'ai': {
            'default_provider': 'openrouter',
            'default_model': 'test-model',
            'api_key': 'test-key',
            'max_tokens': 100,
            'temperature': 0.7,
            'model_categories': {
                'free_models': ['test-model'],
                'premium_models': []
            }
        },
        'monitor': {
            'templates': [],
            'capture_interval': 1.0,
            'regions': []
        },
        'platforms': [
            {
                'name': 'coursera',
                'selectors': {
                    'login_button': '#login-button',
                    'email_field': '#email',
                    'password_field': '#password'
                }
            }
        ],
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

@pytest.fixture
def mock_page():
    """Mock Playwright page"""
    page = Mock(spec=Page)
    page.goto.return_value = None
    page.fill.return_value = None
    page.click.return_value = None
    page.wait_for_load_state.return_value = None
    page.wait_for_selector.return_value = Mock()
    page.screenshot.return_value = None
    # Default is_visible to True for selectors used in tests
    page.is_visible.return_value = True
    page.url = "https://example.com/test-page"
    return page

@pytest.fixture
def course_automation(tmp_path, mock_config):
    """Course automation instance with temporary directories"""
    # Patch yaml.safe_load everywhere it might be used during init
    with patch('yaml.safe_load', return_value=mock_config):
        with patch('src.monitor.screen_monitor.mss.mss'), \
             patch('src.ai.model_handler.AutoTokenizer'), \
             patch('src.ai.model_handler.AutoModelForCausalLM'):
            automation = CourseAutomation()
            return automation

def test_initialization(course_automation):
    """Test course automation initialization"""
    assert course_automation.model_handler is not None
    assert course_automation.screen_monitor is not None

def test_set_page(course_automation, mock_page):
    """Test setting page instance"""
    course_automation.set_page(mock_page)
    assert course_automation.page == mock_page

def test_login_to_course(course_automation, mock_page):
    """Test login_to_course method"""
    course_automation.set_page(mock_page)
    course_automation.current_platform = 'coursera'
    
    result = course_automation.login_to_course("http://test.com", "test@email.com", "pass123")
    
    assert result is True
    mock_page.goto.assert_called_with("http://test.com")
    mock_page.fill.assert_any_call('#email', 'test@email.com')
    mock_page.fill.assert_any_call('#password', 'pass123')

def test_start_automation_basic(course_automation, mock_page):
    """Test start_automation method"""
    with patch.object(course_automation, 'login_to_course', return_value=True), \
         patch.object(course_automation, '_handle_generic_platform', return_value=True):
        result = course_automation.start_automation(
            mock_page, "coursera", "http://test.com", {"email": "t", "password": "p"}
        )
        assert result is True
        assert course_automation.current_platform == "coursera"

def test_handle_generic_platform_video(course_automation, mock_page):
    """Test generic platform handler with video"""
    course_automation.set_page(mock_page)
    mock_page.is_visible.side_effect = lambda s: '.video' in s
    
    with patch.object(course_automation, '_watch_video', return_value=True) as mock_watch:
        result = course_automation._handle_generic_platform(mock_page, "url")
        assert result is True
        mock_watch.assert_called_once()

def test_handle_generic_platform_quiz(course_automation, mock_page):
    """Test generic platform handler with quiz"""
    course_automation.set_page(mock_page)
    # Simulate quiz visible but not video
    def side_effect(selector):
        if '.quiz' in selector: return True
        return False
    mock_page.is_visible.side_effect = side_effect
    
    with patch.object(course_automation, '_handle_quiz', return_value=True) as mock_quiz:
        result = course_automation._handle_generic_platform(mock_page, "url")
        assert result is True
        mock_quiz.assert_called_once()
