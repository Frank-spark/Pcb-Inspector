import cv2
import numpy as np
from typing import Optional, Tuple, Dict, List
import logging

class CameraManager:
    """Manages webcam capture and image processing for PCB inspection with zoom and focus controls."""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
        # Zoom and focus settings
        self.zoom_level = 1.0  # 1.0 = no zoom, 2.0 = 2x zoom, etc.
        self.max_zoom = 4.0
        self.min_zoom = 0.5
        
        # Focus settings
        self.auto_focus = True
        self.focus_distance = 0.5  # 0.0 to 1.0
        
        # Board detection settings
        self.board_detection_enabled = True
        self.min_board_area = 10000  # Minimum area for board detection
        self.board_confidence_threshold = 0.7
        
        # Camera properties cache
        self.camera_properties = {}
        
    def connect(self) -> bool:
        """Initialize and connect to the webcam."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera at index {self.camera_index}")
                return False
                
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1 if self.auto_focus else 0)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
            self.cap.set(cv2.CAP_PROP_CONTRAST, 0.5)
            self.cap.set(cv2.CAP_PROP_SATURATION, 0.5)
            
            # Cache camera properties
            self._cache_camera_properties()
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to camera {self.camera_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to camera: {e}")
            return False
    
    def _cache_camera_properties(self):
        """Cache camera properties for reference."""
        if not self.cap:
            return
            
        self.camera_properties = {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
            "saturation": self.cap.get(cv2.CAP_PROP_SATURATION),
            "autofocus": self.cap.get(cv2.CAP_PROP_AUTOFOCUS),
            "focus": self.cap.get(cv2.CAP_PROP_FOCUS),
            "zoom": self.cap.get(cv2.CAP_PROP_ZOOM),
            "camera_index": self.camera_index
        }
    
    def disconnect(self):
        """Release camera resources."""
        if self.cap:
            self.cap.release()
        self.is_connected = False
        self.logger.info("Camera disconnected")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame from the webcam."""
        if not self.is_connected or not self.cap:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            self.logger.warning("Failed to capture frame")
            return None
            
        # Apply zoom if needed
        if self.zoom_level != 1.0:
            frame = self._apply_zoom(frame)
            
        return frame
    
    def _apply_zoom(self, frame: np.ndarray) -> np.ndarray:
        """Apply zoom to the frame using cropping and resizing."""
        if self.zoom_level == 1.0:
            return frame
            
        h, w = frame.shape[:2]
        
        # Calculate crop dimensions
        crop_w = int(w / self.zoom_level)
        crop_h = int(h / self.zoom_level)
        
        # Calculate crop position (center the crop)
        x1 = (w - crop_w) // 2
        y1 = (h - crop_h) // 2
        x2 = x1 + crop_w
        y2 = y1 + crop_h
        
        # Crop and resize back to original size
        cropped = frame[y1:y2, x1:x2]
        zoomed = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LANCZOS4)
        
        return zoomed
    
    def set_zoom(self, zoom_level: float) -> bool:
        """Set zoom level (0.5 to 4.0)."""
        if not self.is_connected:
            return False
            
        # Clamp zoom level
        self.zoom_level = max(self.min_zoom, min(self.max_zoom, zoom_level))
        
        # Try to set hardware zoom if available
        try:
            self.cap.set(cv2.CAP_PROP_ZOOM, self.zoom_level)
        except Exception as e:
            self.logger.debug(f"Hardware zoom not available, using software zoom: {e}")
        
        self.logger.info(f"Zoom level set to {self.zoom_level}")
        return True
    
    def get_zoom(self) -> float:
        """Get current zoom level."""
        return self.zoom_level
    
    def zoom_in(self, factor: float = 1.2) -> bool:
        """Zoom in by the specified factor."""
        return self.set_zoom(self.zoom_level * factor)
    
    def zoom_out(self, factor: float = 1.2) -> bool:
        """Zoom out by the specified factor."""
        return self.set_zoom(self.zoom_level / factor)
    
    def reset_zoom(self) -> bool:
        """Reset zoom to 1.0 (no zoom)."""
        return self.set_zoom(1.0)
    
    def set_focus(self, focus_distance: float) -> bool:
        """Set focus distance (0.0 to 1.0)."""
        if not self.is_connected:
            return False
            
        self.focus_distance = max(0.0, min(1.0, focus_distance))
        
        try:
            # Check if camera supports focus control
            current_focus = self.cap.get(cv2.CAP_PROP_FOCUS)
            if current_focus == -1:
                # Camera doesn't support focus control
                self.logger.info("Camera doesn't support manual focus control")
                return False
            
            # Disable autofocus first
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
            # Set manual focus
            self.cap.set(cv2.CAP_PROP_FOCUS, self.focus_distance)
            self.auto_focus = False
            self.logger.info(f"Focus distance set to {self.focus_distance}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Manual focus not available: {e}")
            return False
    
    def set_auto_focus(self, enabled: bool) -> bool:
        """Enable or disable autofocus."""
        if not self.is_connected:
            return False
            
        self.auto_focus = enabled
        
        try:
            # Check if camera supports autofocus
            current_autofocus = self.cap.get(cv2.CAP_PROP_AUTOFOCUS)
            if current_autofocus == -1:
                # Camera doesn't support autofocus control
                self.logger.info("Camera doesn't support autofocus control")
                return False
            
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1 if enabled else 0)
            self.logger.info(f"Autofocus {'enabled' if enabled else 'disabled'}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Autofocus control not available: {e}")
            return False
    
    def get_focus_info(self) -> Dict:
        """Get current focus information."""
        focus_info = {
            "auto_focus": self.auto_focus,
            "focus_distance": self.focus_distance,
            "hardware_focus": None,
            "focus_supported": False,
            "autofocus_supported": False
        }
        
        if self.cap:
            try:
                # Check if focus is supported
                focus_value = self.cap.get(cv2.CAP_PROP_FOCUS)
                autofocus_value = self.cap.get(cv2.CAP_PROP_AUTOFOCUS)
                
                focus_info["hardware_focus"] = focus_value
                focus_info["focus_supported"] = focus_value != -1
                focus_info["autofocus_supported"] = autofocus_value != -1
                
            except Exception as e:
                self.logger.debug(f"Error getting focus info: {e}")
        
        return focus_info
    
    def get_board_detection_status(self) -> Dict:
        """Get current board detection status and statistics."""
        if not self.is_connected:
            return {"error": "Camera not connected"}
        
        frame = self.get_frame()
        if frame is None:
            return {"error": "Failed to get frame"}
        
        board_info = self.detect_board(frame)
        if board_info:
            return {
                "board_detected": True,
                "confidence": board_info["confidence"],
                "area": board_info["area"],
                "bbox": board_info["bbox"],
                "aspect_ratio": board_info["aspect_ratio"],
                "center": board_info["center"]
            }
        else:
            return {
                "board_detected": False,
                "confidence": 0.0,
                "area": 0,
                "bbox": [0, 0, 0, 0],
                "aspect_ratio": 0.0,
                "center": [0, 0]
            }
    
    def detect_board(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect PCB board in the frame using contour detection and shape analysis.
        
        Returns:
            Dictionary with board detection results or None if no board found
        """
        if not self.board_detection_enabled:
            return None
            
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # Apply adaptive thresholding for better edge detection
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            # Apply morphological operations to clean up the image
            kernel = np.ones((3, 3), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
            
            # Apply edge detection
            edges = cv2.Canny(thresh, 30, 100)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area and shape
            board_candidates = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < self.min_board_area:
                    continue
                
                # Approximate contour to polygon
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Check if it's roughly rectangular (4-6 vertices for PCB)
                if 4 <= len(approx) <= 6:
                    # Calculate aspect ratio
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    # PCBs typically have aspect ratios between 0.5 and 2.0
                    if 0.5 <= aspect_ratio <= 2.0:
                        # Calculate confidence based on multiple factors
                        # 1. Area factor (normalized by expected area)
                        area_factor = min(1.0, area / 50000)
                        
                        # 2. Shape regularity factor (how close to perfect rectangle)
                        rect_area = w * h
                        shape_factor = area / rect_area if rect_area > 0 else 0
                        
                        # 3. Edge density factor (PCBs have many edges)
                        edge_density = cv2.contourArea(contour) / cv2.arcLength(contour, True) if cv2.arcLength(contour, True) > 0 else 0
                        edge_factor = min(1.0, edge_density / 10)
                        
                        # Combined confidence score
                        confidence = (area_factor * 0.4 + shape_factor * 0.3 + edge_factor * 0.3)
                        
                        board_candidates.append({
                            "contour": contour,
                            "bbox": [x, y, w, h],
                            "area": area,
                            "aspect_ratio": aspect_ratio,
                            "confidence": confidence,
                            "center": [x + w//2, y + h//2],
                            "shape_factor": shape_factor,
                            "edge_factor": edge_factor
                        })
            
            # Return the best candidate (highest confidence)
            if board_candidates:
                best_candidate = max(board_candidates, key=lambda x: x["confidence"])
                if best_candidate["confidence"] >= self.board_confidence_threshold:
                    return best_candidate
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in board detection: {e}")
            return None
    
    def auto_zoom_to_board(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """
        Automatically zoom to fit the detected board in the frame.
        
        Returns:
            Zoomed frame or None if no board detected
        """
        board_info = self.detect_board(frame)
        if not board_info:
            return None
        
        try:
            h, w = frame.shape[:2]
            x, y, board_w, board_h = board_info["bbox"]
            
            # Calculate zoom level to fit board with some margin
            margin = 0.1  # 10% margin
            target_zoom_w = w / (board_w * (1 + margin))
            target_zoom_h = h / (board_h * (1 + margin))
            target_zoom = min(target_zoom_w, target_zoom_h)
            
            # Apply zoom
            self.set_zoom(target_zoom)
            
            # Return zoomed frame
            return self._apply_zoom(frame)
            
        except Exception as e:
            self.logger.error(f"Error in auto zoom: {e}")
            return None
    
    def capture_snapshot(self, save_path: Optional[str] = None) -> Optional[np.ndarray]:
        """Capture a high-quality snapshot for PCB inspection."""
        frame = self.get_frame()
        if frame is None:
            return None
            
        # Apply image enhancement for better PCB inspection
        enhanced_frame = self._enhance_image(frame)
        
        if save_path:
            try:
                cv2.imwrite(save_path, enhanced_frame)
                self.logger.info(f"Snapshot saved to {save_path}")
            except Exception as e:
                self.logger.error(f"Failed to save snapshot: {e}")
                
        return enhanced_frame
    
    def _enhance_image(self, frame: np.ndarray) -> np.ndarray:
        """Apply image enhancement techniques for better PCB inspection."""
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for better contrast
        enhanced = cv2.equalizeHist(gray)
        
        # Apply slight Gaussian blur to reduce noise
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        # Apply unsharp masking for edge enhancement
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        enhanced = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
        
        # Convert back to BGR for saving
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_bgr
    
    def get_camera_info(self) -> dict:
        """Get camera information and capabilities."""
        if not self.is_connected:
            return {"error": "Camera not connected"}
            
        # Update cached properties
        self._cache_camera_properties()
        
        info = self.camera_properties.copy()
        info.update({
            "zoom_level": self.zoom_level,
            "auto_focus": self.auto_focus,
            "focus_distance": self.focus_distance,
            "board_detection_enabled": self.board_detection_enabled
        })
        
        return info
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


def list_available_cameras() -> list:
    """List all available camera devices."""
    available_cameras = []
    
    for i in range(10):  # Check first 10 camera indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
            cap.release()
    
    return available_cameras


if __name__ == "__main__":
    # Test camera functionality
    logging.basicConfig(level=logging.INFO)
    
    print("Available cameras:", list_available_cameras())
    
    with CameraManager() as camera:
        if camera.is_connected:
            print("Camera info:", camera.get_camera_info())
            
            # Test zoom functionality
            camera.set_zoom(2.0)
            print(f"Zoom level: {camera.get_zoom()}")
            
            # Test focus functionality
            camera.set_auto_focus(False)
            camera.set_focus(0.7)
            print("Focus info:", camera.get_focus_info())
            
            # Capture a test image
            frame = camera.capture_snapshot("test_capture.jpg")
            if frame is not None:
                print("Test capture successful!")
                
                # Test board detection
                board_info = camera.detect_board(frame)
                if board_info:
                    print(f"Board detected: {board_info}")
                else:
                    print("No board detected in test image")
            else:
                print("Test capture failed!") 