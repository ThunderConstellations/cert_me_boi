"""Test course automation module"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from playwright.sync_api import Page, expect
from src.automation.course_automation import CourseAutomation
from src.utils.error_handler import AutomationError

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
    page.url = "https://example.com/test-page"
    return page

@pytest.fixture
def course_automation(tmp_path):
    """Course automation instance with temporary directories"""
    with patch('src.automation.course_automation.yaml.safe_load') as mock_load:
        mock_load.return_value = {
            'settings': {
                'screenshot_dir': str(tmp_path / 'screenshots'),
                'delay_between_actions': 2
            },
            'certificates': {
                'save_dir': str(tmp_path / 'certificates'),
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
        automation = CourseAutomation()
        return automation

def test_initialization(course_automation, tmp_path):
    """Test course automation initialization"""
    assert course_automation.page is None
    assert course_automation.certificate_dir == Path(tmp_path / 'certificates')
    assert course_automation.certificate_dir.exists()
    assert course_automation.screenshot_dir == Path(tmp_path / 'screenshots')
    assert course_automation.screenshot_dir.exists()

def test_set_page(course_automation, mock_page):
    """Test setting page instance"""
    course_automation.set_page(mock_page)
    assert course_automation.page == mock_page

def test_login_success(course_automation, mock_page):
    """Test successful login"""
    # Mock locator for login button visibility check
    login_button = Mock()
    mock_page.locator.return_value = login_button
    
    course_automation.set_page(mock_page)
    result = course_automation.login_to_course(
        'https://example.com',
        'test@example.com',
        'password123'
    )
    assert result is True
    mock_page.goto.assert_called_once()
    assert mock_page.fill.call_count == 2
    mock_page.click.assert_called_once()
    mock_page.wait_for_load_state.assert_called_once_with('networkidle')
    mock_page.screenshot.assert_called_once()

def test_login_failure_no_page(course_automation):
    """Test login failure when page not initialized"""
    with pytest.raises(AutomationError, match="Page not initialized"):
        course_automation.login_to_course(
            'https://example.com',
            'test@example.com',
            'password123'
        )

def test_check_progress(course_automation, mock_page):
    """Test checking course progress"""
    # Mock progress bar element
    progress_bar = Mock()
    progress_bar.get_attribute.return_value = "75"
    mock_page.wait_for_selector.return_value = progress_bar
    
    # Mock locator for screenshot
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    progress = course_automation.check_course_progress()
    
    assert progress == 75.0
    mock_page.wait_for_selector.assert_called_once()
    progress_bar.get_attribute.assert_called_once_with('aria-valuenow')
    element_locator.screenshot.assert_called_once()

def test_check_progress_no_value(course_automation, mock_page):
    """Test checking progress with no value"""
    # Mock progress bar element with no value
    progress_bar = Mock()
    progress_bar.get_attribute.return_value = None
    mock_page.wait_for_selector.return_value = progress_bar
    
    # Mock locator for screenshot
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    progress = course_automation.check_course_progress()
    
    assert progress == 0.0
    element_locator.screenshot.assert_called_once()

def test_download_certificate(course_automation, mock_page, tmp_path):
    """Test certificate download"""
    # Mock locator for screenshot
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    cert_path = course_automation.download_certificate('course123')
    
    expected_path = str(tmp_path / 'certificates' / 'course123_certificate.png')
    assert cert_path == expected_path
    mock_page.wait_for_selector.assert_called_once()
    mock_page.screenshot.assert_called_once_with(path=expected_path)
    element_locator.screenshot.assert_called_once()

def test_verify_video_completion(course_automation, mock_page):
    """Test video completion verification"""
    # Mock video element
    video = Mock()
    video.evaluate.return_value = True
    mock_page.wait_for_selector.return_value = video
    
    # Mock locator for screenshot
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    completed = course_automation.verify_video_completion('https://example.com/video')
    
    assert completed is True
    mock_page.goto.assert_called_once_with('https://example.com/video')
    mock_page.wait_for_selector.assert_called_once()
    video.evaluate.assert_called_once_with('video => video.ended')
    element_locator.screenshot.assert_called_once()

def test_verify_video_not_completed(course_automation, mock_page):
    """Test video not completed verification"""
    # Mock video element
    video = Mock()
    video.evaluate.return_value = False
    mock_page.wait_for_selector.return_value = video
    
    # Mock locator for screenshot
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    completed = course_automation.verify_video_completion('https://example.com/video')
    
    assert completed is False
    element_locator.screenshot.assert_called_once()

def test_verify_video_element_not_found(course_automation, mock_page):
    """Test video verification when element not found"""
    mock_page.wait_for_selector.return_value = None
    
    course_automation.set_page(mock_page)
    completed = course_automation.verify_video_completion('https://example.com/video')
    
    assert completed is False

def test_take_screenshot(course_automation, mock_page, tmp_path):
    """Test taking page screenshot"""
    course_automation.set_page(mock_page)
    screenshot_path = course_automation.take_screenshot("test")
    
    expected_path = str(tmp_path / 'screenshots' / 'test_test-page.png')
    assert screenshot_path == expected_path
    mock_page.screenshot.assert_called_once_with(
        path=expected_path,
        full_page=False
    )

def test_take_element_screenshot(course_automation, mock_page, tmp_path):
    """Test taking element screenshot"""
    # Mock element locator
    element_locator = Mock()
    element_locator.screenshot.return_value = None
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    screenshot_path = course_automation.take_element_screenshot(
        "#test-element",
        "test_element"
    )
    
    expected_path = str(tmp_path / 'screenshots' / 'test_element.png')
    assert screenshot_path == expected_path
    mock_page.locator.assert_called_once_with("#test-element")
    element_locator.screenshot.assert_called_once_with(path=expected_path)

def test_verify_ui_element_visible(course_automation, mock_page):
    """Test verifying visible UI element"""
    # Mock element locator
    element_locator = Mock()
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    result = course_automation.verify_ui_element("#test-element", "visible")
    
    assert result is True
    mock_page.locator.assert_called_once_with("#test-element")

def test_verify_ui_element_hidden(course_automation, mock_page):
    """Test verifying hidden UI element"""
    # Mock element locator
    element_locator = Mock()
    mock_page.locator.return_value = element_locator
    
    course_automation.set_page(mock_page)
    result = course_automation.verify_ui_element("#test-element", "hidden")
    
    assert result is True
    mock_page.locator.assert_called_once_with("#test-element")

def test_wait_for_navigation(course_automation, mock_page):
    """Test waiting for navigation"""
    course_automation.set_page(mock_page)
    result = course_automation.wait_for_navigation()
    
    assert result is True
    mock_page.wait_for_load_state.assert_called_once_with(
        'networkidle',
        timeout=30000
    )

def test_wait_for_navigation_custom_timeout(course_automation, mock_page):
    """Test waiting for navigation with custom timeout"""
    course_automation.set_page(mock_page)
    result = course_automation.wait_for_navigation(timeout=5000)
    
    assert result is True
    mock_page.wait_for_load_state.assert_called_once_with(
        'networkidle',
        timeout=5000
    ) 