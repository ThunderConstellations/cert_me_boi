import pytest
import time
from unittest.mock import Mock, patch
from src.automation.browser import BrowserAutomation

@pytest.fixture
def browser():
    mock_config = {
        'browser': {
            'screenshot_dir': 'data/screenshots',
            'timeout': 30,
            'headless': True,
            'user_agent': 'test-agent'
        }
    }
    with patch("src.automation.browser.sync_playwright"), \
         patch("yaml.safe_load", return_value=mock_config):
        ba = BrowserAutomation()
        ba.page = Mock()
        yield ba

def test_human_like_navigation(browser):
    """Test that navigation includes a delay"""
    with patch("time.sleep") as mock_sleep:
        browser.navigate("http://test.com")
        mock_sleep.assert_called()
        browser.page.goto.assert_called_with("http://test.com", timeout=30000)

def test_human_like_click(browser):
    """Test that clicking includes a hover and delay"""
    mock_element = Mock()
    browser.page.wait_for_selector.return_value = mock_element

    with patch("time.sleep") as mock_sleep:
        browser.click_element("#btn")
        mock_element.hover.assert_called_once()
        mock_element.click.assert_called_once()
        assert mock_sleep.call_count >= 2

def test_human_like_typing(browser):
    """Test that typing is done character by character"""
    mock_element = Mock()
    browser.page.wait_for_selector.return_value = mock_element

    with patch("time.sleep") as mock_sleep:
        browser.fill_input("#input", "abc")
        mock_element.click.assert_called_once()
        assert browser.page.keyboard.type.call_count == 3
        # Should sleep for each character + initial delay
        assert mock_sleep.call_count >= 4
