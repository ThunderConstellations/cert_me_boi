"""Test video monitor module"""

import pytest
import numpy as np
import cv2
from pathlib import Path
from unittest.mock import Mock, patch
from src.monitor.video_monitor import VideoMonitor
from src.utils.error_handler import MonitorError

@pytest.fixture
def mock_config():
    """Mock monitor configuration"""
    return {
        'frame_analysis': {
            'buffer_size': 10,
            'motion_threshold': 1000,
            'progress_threshold': 0.9,
            'blur_threshold': 100
        },
        'progress_bar': {
            'color_ranges': {
                'white': {
                    'lower': [0, 0, 200],
                    'upper': [180, 30, 255]
                },
                'gray': {
                    'lower': [0, 0, 100],
                    'upper': [180, 30, 200]
                }
            },
            'roi': {
                'top_percent': 0.8,
                'height_percent': 0.1
            },
            'min_width_percent': 0.3,
            'min_height_pixels': 5
        },
        'template_matching': {
            'threshold': 0.8,
            'scale_range': [0.8, 1.2],
            'scale_steps': 5
        },
        'screenshots': {
            'max_per_session': 100,
            'jpeg_quality': 95,
            'png_compression': 9
        },
        'logging': {
            'frame_metrics': True
        }
    }

@pytest.fixture
def video_monitor(tmp_path, mock_config):
    """Create video monitor instance with temporary directories"""
    with patch('src.monitor.video_monitor.yaml.safe_load') as mock_load:
        mock_load.return_value = mock_config
        monitor = VideoMonitor()
        monitor.screenshot_dir = tmp_path / "screenshots"
        monitor.template_dir = tmp_path / "templates"
        monitor.screenshot_dir.mkdir(parents=True, exist_ok=True)
        monitor.template_dir.mkdir(parents=True, exist_ok=True)
        return monitor

@pytest.fixture
def sample_frame():
    """Create a sample frame for testing"""
    # Create a 100x100 grayscale frame with a gradient
    frame = np.zeros((100, 100), dtype=np.uint8)
    for i in range(100):
        frame[:, i] = i * 2.55  # Create gradient from 0 to 255
    # Convert to BGR
    return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

@pytest.fixture
def sample_progress_frame():
    """Create a sample frame with a progress bar"""
    # Create a black frame
    frame = np.zeros((200, 400, 3), dtype=np.uint8)
    # Add white progress bar in bottom portion
    frame[160:180, 50:350] = [255, 255, 255]  # White bar
    frame[160:180, 50:200] = [200, 200, 200]  # Gray filled portion
    return frame

def test_initialization(video_monitor, tmp_path, mock_config):
    """Test video monitor initialization"""
    assert video_monitor.screenshot_dir == tmp_path / "screenshots"
    assert video_monitor.template_dir == tmp_path / "templates"
    assert video_monitor.screenshot_dir.exists()
    assert video_monitor.template_dir.exists()
    assert len(video_monitor.frame_buffer) == 0
    assert video_monitor.buffer_size == mock_config['frame_analysis']['buffer_size']
    assert video_monitor.motion_threshold == mock_config['frame_analysis']['motion_threshold']
    assert video_monitor.progress_threshold == mock_config['frame_analysis']['progress_threshold']
    assert video_monitor.blur_threshold == mock_config['frame_analysis']['blur_threshold']
    assert video_monitor.screenshot_count == 0
    assert video_monitor.max_screenshots == mock_config['screenshots']['max_per_session']

def test_analyze_frame(video_monitor, sample_frame):
    """Test frame analysis"""
    metrics = video_monitor.analyze_frame(sample_frame)
    
    assert isinstance(metrics, dict)
    assert 'motion_detected' in metrics
    assert 'brightness' in metrics
    assert 'contrast' in metrics
    assert 'blur_score' in metrics
    assert len(video_monitor.frame_buffer) == 1

def test_analyze_frame_invalid(video_monitor):
    """Test frame analysis with invalid frame"""
    with pytest.raises(MonitorError, match="Invalid frame"):
        video_monitor.analyze_frame(None)

def test_detect_motion(video_monitor, sample_frame):
    """Test motion detection"""
    # First frame - no motion detected
    gray1 = cv2.cvtColor(sample_frame, cv2.COLOR_BGR2GRAY)
    video_monitor.frame_buffer = [gray1]
    assert not video_monitor._detect_motion(gray1)
    
    # Second frame with significant change
    frame2 = sample_frame.copy()
    frame2[:, :] = [255, 255, 255]  # White frame
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    video_monitor.frame_buffer.append(gray1)
    assert video_monitor._detect_motion(gray2)

def test_calculate_blur(video_monitor, sample_frame):
    """Test blur calculation"""
    # Clear frame should have higher variance
    blur_score = video_monitor._calculate_blur(sample_frame)
    assert blur_score > 0
    
    # Blurred frame should have lower variance
    blurred_frame = cv2.GaussianBlur(sample_frame, (15, 15), 0)
    blurred_score = video_monitor._calculate_blur(blurred_frame)
    assert blurred_score < blur_score

def test_detect_progress_bar(video_monitor, sample_progress_frame):
    """Test progress bar detection"""
    progress = video_monitor.detect_progress_bar(sample_progress_frame)
    
    assert progress is not None
    assert 0 <= progress <= 1

def test_detect_progress_bar_no_bar(video_monitor, sample_frame):
    """Test progress bar detection with no bar"""
    progress = video_monitor.detect_progress_bar(sample_frame)
    assert progress is None

def test_verify_video_playing(video_monitor, sample_frame):
    """Test video playback verification"""
    # First frame
    video_monitor.analyze_frame(sample_frame)
    
    # Second frame with motion
    frame2 = sample_frame.copy()
    frame2[:, :] = [255, 255, 255]  # Significant change
    is_playing = video_monitor.verify_video_playing(frame2)
    
    assert isinstance(is_playing, bool)

def test_save_frame(video_monitor, sample_frame):
    """Test frame saving"""
    path = video_monitor.save_frame(sample_frame, "test_frame")
    
    assert path is not None
    assert Path(path).exists()
    assert Path(path).name == "test_frame.png"
    assert video_monitor.screenshot_count == 1

def test_save_frame_max_screenshots(video_monitor, sample_frame):
    """Test frame saving when max screenshots reached"""
    video_monitor.screenshot_count = video_monitor.max_screenshots
    path = video_monitor.save_frame(sample_frame, "test_frame")
    assert path is None

def test_save_frame_invalid(video_monitor):
    """Test frame saving with invalid frame"""
    with pytest.raises(MonitorError, match="Invalid frame"):
        video_monitor.save_frame(None, "test_frame")

def test_match_template(video_monitor, sample_frame):
    """Test template matching"""
    # Save template
    template_path = video_monitor.template_dir / "test_template.png"
    cv2.imwrite(str(template_path), sample_frame[10:30, 10:30])
    
    # Match template
    result = video_monitor.match_template(sample_frame, "test_template")
    
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 3  # x, y, confidence
    assert 0 <= result[0] <= sample_frame.shape[1]  # x
    assert 0 <= result[1] <= sample_frame.shape[0]  # y
    assert 0 <= result[2] <= 1.0  # confidence

def test_match_template_not_found(video_monitor, sample_frame):
    """Test template matching when template doesn't exist"""
    with pytest.raises(MonitorError, match="Template nonexistent not found"):
        video_monitor.match_template(sample_frame, "nonexistent")

def test_match_template_no_match(video_monitor, sample_frame):
    """Test template matching when no match found"""
    # Save template that won't match
    template = np.zeros((20, 20, 3), dtype=np.uint8)
    template_path = video_monitor.template_dir / "test_template.png"
    cv2.imwrite(str(template_path), template)
    
    result = video_monitor.match_template(sample_frame, "test_template")
    assert result is None

def test_match_template_with_scale(video_monitor, sample_frame):
    """Test template matching with different scales"""
    # Save template
    template = sample_frame[10:30, 10:30].copy()
    template_path = video_monitor.template_dir / "test_template.png"
    cv2.imwrite(str(template_path), template)
    
    # Scale up the frame
    scaled_frame = cv2.resize(sample_frame, None, fx=1.2, fy=1.2)
    
    # Match template
    result = video_monitor.match_template(scaled_frame, "test_template")
    
    assert result is not None
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert result[2] >= video_monitor.template_config['threshold'] 