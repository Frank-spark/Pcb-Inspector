import cv2
import numpy as np
from typing import Optional, Tuple
import logging

class CameraManager:
    """Manages webcam capture and image processing for PCB inspection."""
    
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap = None
        self.is_connected = False
        self.logger = logging.getLogger(__name__)
        
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
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 0.5)
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to camera {self.camera_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error connecting to camera: {e}")
            return False
    
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
            
        return frame
    
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
        
        # Convert back to BGR for saving
        enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced_bgr
    
    def get_camera_info(self) -> dict:
        """Get camera information and capabilities."""
        if not self.is_connected:
            return {"error": "Camera not connected"}
            
        info = {
            "width": int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": self.cap.get(cv2.CAP_PROP_FPS),
            "brightness": self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            "contrast": self.cap.get(cv2.CAP_PROP_CONTRAST),
            "camera_index": self.camera_index
        }
        
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
            
            # Capture a test image
            frame = camera.capture_snapshot("test_capture.jpg")
            if frame is not None:
                print("Test capture successful!")
            else:
                print("Test capture failed!") 