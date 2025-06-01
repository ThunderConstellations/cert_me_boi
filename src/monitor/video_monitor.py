"""Video monitoring module for analyzing video progress"""

import cv2
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from ..utils.logger import logger, log_execution_time, log_monitor_event
from ..utils.error_handler import MonitorError, retry_on_error, safe_monitor_operation

class VideoMonitor:
    """Handles video progress monitoring and analysis"""
    
    def __init__(self, config_path: str = "config/monitor.yaml"):
        """Initialize video monitor"""
        self.config = self._load_config(config_path)
        
        # Initialize directories
        self.screenshot_dir = Path("data/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir = Path("data/templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize frame buffer
        self.frame_buffer: List[np.ndarray] = []
        self.buffer_size = self.config['frame_analysis']['buffer_size']
        
        # Initialize thresholds
        self.motion_threshold = self.config['frame_analysis']['motion_threshold']
        self.progress_threshold = self.config['frame_analysis']['progress_threshold']
        self.blur_threshold = self.config['frame_analysis']['blur_threshold']
        
        # Initialize screenshot counter
        self.screenshot_count = 0
        self.max_screenshots = self.config['screenshots']['max_per_session']
        
        logger.info(
            "Video monitor initialized",
            module="video_monitor",
            context={"config": self.config}
        )

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(
                "Failed to load config",
                module="video_monitor",
                error=str(e)
            )
            # Return default configuration
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

    @safe_monitor_operation
    def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze a video frame
        
        Args:
            frame: BGR frame to analyze
            
        Returns:
            Dict containing analysis metrics
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise MonitorError("Invalid frame")
            
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Update frame buffer
        if len(self.frame_buffer) >= self.buffer_size:
            self.frame_buffer.pop(0)
        self.frame_buffer.append(gray)
        
        # Calculate metrics
        motion_detected = self._detect_motion(gray)
        brightness = np.mean(gray)
        contrast = np.std(gray)
        blur_score = self._calculate_blur(frame)
        
        metrics = {
            'motion_detected': motion_detected,
            'brightness': brightness,
            'contrast': contrast,
            'blur_score': blur_score
        }
        
        logger.info(
            "Monitor event: frame_analysis",
            module="monitor",
            context={
                "event_type": "frame_analysis",
                "metrics": metrics
            }
        )
        
        return metrics

    def _detect_motion(self, current_frame: np.ndarray) -> bool:
        """Detect motion between frames
        
        Args:
            current_frame: Current grayscale frame
            
        Returns:
            True if motion detected, False otherwise
        """
        if len(self.frame_buffer) < 1:
            return False
            
        # Compare with previous frame
        prev_frame = self.frame_buffer[-1]
        frame_diff = cv2.absdiff(current_frame, prev_frame)
        motion_score = np.sum(frame_diff)
        
        return motion_score > self.motion_threshold

    def _calculate_blur(self, frame: np.ndarray) -> float:
        """Calculate blur score using Laplacian variance
        
        Args:
            frame: BGR frame
            
        Returns:
            Blur score (higher means less blur)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    @safe_monitor_operation
    def detect_progress_bar(self, frame: np.ndarray) -> Optional[float]:
        """Detect video progress bar and calculate progress
        
        Args:
            frame: BGR frame
            
        Returns:
            Progress value between 0 and 1, or None if no bar detected
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise MonitorError("Invalid frame")
            
        # Get progress bar region of interest
        height, width = frame.shape[:2]
        roi_top = int(height * self.config['progress_bar']['roi']['top_percent'])
        roi_height = int(height * self.config['progress_bar']['roi']['height_percent'])
        roi = frame[roi_top:roi_top + roi_height, :]
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Detect white bar background
        white_lower = np.array(self.config['progress_bar']['color_ranges']['white']['lower'])
        white_upper = np.array(self.config['progress_bar']['color_ranges']['white']['upper'])
        white_mask = cv2.inRange(hsv, white_lower, white_upper)
        
        # Detect gray filled portion
        gray_lower = np.array(self.config['progress_bar']['color_ranges']['gray']['lower'])
        gray_upper = np.array(self.config['progress_bar']['color_ranges']['gray']['upper'])
        gray_mask = cv2.inRange(hsv, gray_lower, gray_upper)
        
        # Find contours
        white_contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        gray_contours, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find largest white contour (full bar)
        if not white_contours:
            return None
            
        white_contour = max(white_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(white_contour)
        
        # Validate bar dimensions
        min_width = width * self.config['progress_bar']['min_width_percent']
        min_height = self.config['progress_bar']['min_height_pixels']
        
        if w < min_width or h < min_height:
            return None
            
        # Find largest gray contour (filled portion)
        if not gray_contours:
            progress = 0.0
        else:
            gray_contour = max(gray_contours, key=cv2.contourArea)
            _, _, gray_w, _ = cv2.boundingRect(gray_contour)
            progress = gray_w / w
            
        logger.info(
            "Monitor event: progress_detection",
            module="monitor",
            context={
                "event_type": "progress_detection",
                "progress": progress,
                "bar_width": w,
                "bar_height": h
            }
        )
        
        return progress

    @safe_monitor_operation
    def verify_video_playing(self, frame: np.ndarray) -> bool:
        """Verify video is playing by checking motion and blur
        
        Args:
            frame: BGR frame
            
        Returns:
            True if video appears to be playing, False otherwise
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise MonitorError("Invalid frame")
            
        metrics = self.analyze_frame(frame)
        motion_detected = metrics['motion_detected']
        blur_score = metrics['blur_score']
        
        is_playing = motion_detected and blur_score > self.blur_threshold
        
        logger.info(
            "Monitor event: playback_status",
            module="monitor",
            context={
                "event_type": "playback_status",
                "is_playing": is_playing,
                "motion_detected": motion_detected,
                "blur_score": blur_score
            }
        )
        
        return is_playing

    @safe_monitor_operation
    def save_frame(self, frame: np.ndarray, name: str) -> Optional[str]:
        """Save frame as screenshot
        
        Args:
            frame: BGR frame
            name: Screenshot name
            
        Returns:
            Path to saved screenshot, or None if max screenshots reached
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise MonitorError("Invalid frame")
            
        if self.screenshot_count >= self.max_screenshots:
            logger.warning(
                "Maximum screenshots reached",
                module="video_monitor",
                context={"max_screenshots": self.max_screenshots}
            )
            return None
            
        # Save screenshot
        filename = f"{name}.png"
        path = self.screenshot_dir / filename
        cv2.imwrite(
            str(path),
            frame,
            [cv2.IMWRITE_PNG_COMPRESSION, self.config['screenshots']['png_compression']]
        )
        
        self.screenshot_count += 1
        
        logger.info(
            "Monitor event: screenshot_saved",
            module="monitor",
            context={
                "event_type": "screenshot_saved",
                "path": str(path),
                "name": name,
                "count": self.screenshot_count
            }
        )
        
        return str(path)

    @safe_monitor_operation
    def match_template(self, frame: np.ndarray, template_name: str) -> Optional[Tuple[int, int, float]]:
        """Match template in frame
        
        Args:
            frame: BGR frame
            template_name: Template name
            
        Returns:
            Tuple of (x, y, confidence) or None if no match
        """
        if frame is None or not isinstance(frame, np.ndarray):
            raise MonitorError("Invalid frame")
            
        # Load template
        template_path = self.template_dir / f"{template_name}.png"
        if not template_path.exists():
            raise MonitorError(f"Template {template_name} not found")
            
        template = cv2.imread(str(template_path))
        if template is None:
            raise MonitorError(f"Failed to load template {template_name}")
            
        # Get template matching parameters
        threshold = self.config['template_matching']['threshold']
        scale_range = self.config['template_matching']['scale_range']
        scale_steps = self.config['template_matching']['scale_steps']
        
        # Try different scales
        best_result = None
        best_confidence = -1
        
        scales = np.linspace(scale_range[0], scale_range[1], scale_steps)
        for scale in scales:
            # Resize template
            if scale != 1.0:
                width = int(template.shape[1] * scale)
                height = int(template.shape[0] * scale)
                scaled_template = cv2.resize(template, (width, height))
            else:
                scaled_template = template
                
            # Match template
            result = cv2.matchTemplate(frame, scaled_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val > best_confidence:
                best_confidence = max_val
                best_result = (max_loc[0], max_loc[1], max_val)
                
        # Check if match found
        if best_confidence < threshold:
            return None
            
        logger.info(
            "Monitor event: template_matched",
            module="monitor",
            context={
                "event_type": "template_matched",
                "template": template_name,
                "confidence": best_result[2],
                "location": [best_result[0], best_result[1]]
            }
        )
        
        return best_result 