import cv2
import numpy as np
import mss
import time
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from ..utils.logger import logger, log_execution_time

class ScreenMonitor:
    def __init__(self, config_path: str = "config/courses.yaml"):
        """Initialize the screen monitor with configuration"""
        self.config = self._load_config(config_path)
        self.sct = mss.mss()
        self.templates = self._load_templates()
        self.regions = self.config['monitor']['regions']
        self.capture_interval = self.config['monitor']['capture_interval']
        logger.info("Screen monitor initialized", module="screen_monitor")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}", module="screen_monitor")
            raise

    def _load_templates(self) -> Dict[str, np.ndarray]:
        """Load and cache template images for matching"""
        templates = {}
        for template in self.config['monitor']['templates']:
            try:
                path = Path(template['path'])
                if path.exists():
                    img = cv2.imread(str(path))
                    if img is not None:
                        templates[template['name']] = {
                            'image': img,
                            'confidence': template['confidence']
                        }
                    else:
                        logger.error(f"Failed to load template: {path}", module="screen_monitor")
            except Exception as e:
                logger.error(f"Error loading template {template['name']}: {str(e)}", module="screen_monitor")
        return templates

    @log_execution_time
    def capture_region(self, region: Dict[str, int]) -> np.ndarray:
        """Capture a specific region of the screen"""
        try:
            screenshot = self.sct.grab({
                'left': region['coordinates'][0],
                'top': region['coordinates'][1],
                'width': region['coordinates'][2] - region['coordinates'][0],
                'height': region['coordinates'][3] - region['coordinates'][1]
            })
            return np.array(screenshot)
        except Exception as e:
            logger.error(f"Failed to capture region: {str(e)}", module="screen_monitor")
            return None

    def find_template(self, screen: np.ndarray, template_name: str) -> Optional[Tuple[int, int, float]]:
        """Find a template in the screen image using template matching"""
        if template_name not in self.templates:
            logger.warning(f"Template {template_name} not found", module="screen_monitor")
            return None

        template_data = self.templates[template_name]
        template = template_data['image']
        confidence_threshold = template_data['confidence']

        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence_threshold:
                return (max_loc[0], max_loc[1], max_val)
            return None
        except Exception as e:
            logger.error(f"Template matching failed: {str(e)}", module="screen_monitor")
            return None

    def save_screenshot(self, image: np.ndarray, name: str) -> str:
        """Save a screenshot to the configured directory"""
        try:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{name}_{timestamp}.png"
            path = Path(self.config['settings']['screenshot_dir']) / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(path), image)
            logger.info(f"Screenshot saved: {filename}", module="screen_monitor")
            return str(path)
        except Exception as e:
            logger.error(f"Failed to save screenshot: {str(e)}", module="screen_monitor")
            return ""

    def monitor_regions(self, callback=None) -> None:
        """Continuously monitor specified regions and detect changes"""
        logger.info("Starting region monitoring", module="screen_monitor")
        previous_frames = {}

        try:
            while True:
                for region in self.regions:
                    current_frame = self.capture_region(region)
                    if current_frame is None:
                        continue

                    region_name = region['name']
                    if region_name in previous_frames:
                        # Calculate frame difference
                        diff = cv2.absdiff(current_frame, previous_frames[region_name])
                        change_detected = np.mean(diff) > 5.0  # Adjust threshold as needed

                        if change_detected:
                            logger.info(
                                f"Change detected in region: {region_name}",
                                module="screen_monitor",
                                change_value=float(np.mean(diff))
                            )
                            if callback:
                                callback(region_name, current_frame)

                    previous_frames[region_name] = current_frame

                time.sleep(self.capture_interval)
        except KeyboardInterrupt:
            logger.info("Screen monitoring stopped", module="screen_monitor")
        except Exception as e:
            logger.error(f"Screen monitoring error: {str(e)}", module="screen_monitor")
        finally:
            self.sct.close()

    def check_video_progress(self, region_name: str = "video_player") -> float:
        """Check video progress by analyzing the progress bar region"""
        try:
            region = next((r for r in self.regions if r['name'] == region_name), None)
            if not region:
                logger.warning(f"Region {region_name} not found", module="screen_monitor")
                return 0.0

            frame = self.capture_region(region)
            if frame is None:
                return 0.0

            # Convert to grayscale and threshold to detect progress bar
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            # Calculate progress based on white pixels (progress bar)
            progress = np.sum(thresh == 255) / thresh.size
            logger.debug(
                f"Video progress: {progress:.2%}",
                module="screen_monitor",
                region=region_name
            )
            return progress
        except Exception as e:
            logger.error(f"Failed to check video progress: {str(e)}", module="screen_monitor")
            return 0.0

    def detect_video_state(self) -> str:
        """Detect if video is playing, paused, or ended"""
        try:
            # Check for play/pause button
            region = next((r for r in self.regions if r['name'] == "video_player"), None)
            if not region:
                return "unknown"

            frame = self.capture_region(region)
            if frame is None:
                return "unknown"

            # Check for play button template
            play_button = self.find_template(frame, "play_button")
            if play_button:
                return "paused"

            # Check progress
            progress = self.check_video_progress()
            if progress > 0.98:  # Assuming video is complete at 98%
                return "ended"
            
            return "playing"
        except Exception as e:
            logger.error(f"Failed to detect video state: {str(e)}", module="screen_monitor")
            return "unknown"

if __name__ == "__main__":
    # Test the screen monitor
    def on_change(region_name: str, frame: np.ndarray):
        print(f"Change detected in {region_name}")

    monitor = ScreenMonitor()
    monitor.monitor_regions(callback=on_change) 