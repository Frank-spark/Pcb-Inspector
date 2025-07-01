#!/usr/bin/env python3
"""
Board Detection Debug Script
============================

This script helps debug board detection issues by showing the detection process
step by step and allowing you to adjust detection parameters.

Usage:
    python debug_board_detection.py
"""

import cv2
import numpy as np
import time
from camera import CameraManager

def debug_board_detection():
    """Debug board detection with visual feedback."""
    print("PCB Board Detection Debug Tool")
    print("=" * 40)
    
    # Initialize camera
    print("Initializing camera...")
    camera = CameraManager()
    
    if not camera.connect():
        print("Failed to connect to camera!")
        return
    
    print("Camera connected successfully!")
    print(f"Camera info: {camera.get_camera_info()}")
    
    # Adjustable parameters
    min_area = 10000
    confidence_threshold = 0.7
    
    print(f"\nCurrent detection parameters:")
    print(f"  Min board area: {min_area}")
    print(f"  Confidence threshold: {confidence_threshold}")
    print(f"  Board detection enabled: {camera.board_detection_enabled}")
    
    print("\nControls:")
    print("  'a' - Increase min area by 1000")
    print("  's' - Decrease min area by 1000")
    print("  'd' - Increase confidence threshold by 0.1")
    print("  'f' - Decrease confidence threshold by 0.1")
    print("  'r' - Reset parameters to defaults")
    print("  'q' - Quit")
    
    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Create debug frame
            debug_frame = frame.copy()
            
            # Run board detection with current parameters
            camera.min_board_area = min_area
            camera.board_confidence_threshold = confidence_threshold
            
            board_info = camera.detect_board(frame)
            
            # Draw detection results
            if board_info:
                x, y, w, h = board_info["bbox"]
                confidence = board_info["confidence"]
                area = board_info["area"]
                
                # Draw bounding box
                cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Draw info text
                info_text = f"Board: {confidence:.1%} | Area: {area:.0f}"
                cv2.putText(debug_frame, info_text, (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                print(f"✓ Board detected! Confidence: {confidence:.1%}, Area: {area:.0f}")
            else:
                # Show detection process steps
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                
                # Find all contours
                edges = cv2.Canny(thresh, 30, 100)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # Draw all contours above min area
                large_contours = [c for c in contours if cv2.contourArea(c) >= min_area]
                cv2.drawContours(debug_frame, large_contours, -1, (0, 0, 255), 2)
                
                # Show largest contour info
                if large_contours:
                    largest_contour = max(large_contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    x, y, w, h = cv2.boundingRect(largest_contour)
                    aspect_ratio = w / h if h > 0 else 0
                    
                    info_text = f"Largest: Area={area:.0f}, AR={aspect_ratio:.2f}"
                    cv2.putText(debug_frame, info_text, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    print(f"✗ No board detected. Largest contour: Area={area:.0f}, Aspect Ratio={aspect_ratio:.2f}")
                else:
                    print(f"✗ No contours found above min area ({min_area})")
            
            # Draw parameter info
            param_text = f"Min Area: {min_area} | Confidence: {confidence_threshold:.1f}"
            cv2.putText(debug_frame, param_text, (10, debug_frame.shape[0] - 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow("Board Detection Debug - Press 'q' to quit", debug_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                min_area += 1000
                print(f"Min area increased to {min_area}")
            elif key == ord('s'):
                min_area = max(1000, min_area - 1000)
                print(f"Min area decreased to {min_area}")
            elif key == ord('d'):
                confidence_threshold = min(1.0, confidence_threshold + 0.1)
                print(f"Confidence threshold increased to {confidence_threshold:.1f}")
            elif key == ord('f'):
                confidence_threshold = max(0.1, confidence_threshold - 0.1)
                print(f"Confidence threshold decreased to {confidence_threshold:.1f}")
            elif key == ord('r'):
                min_area = 10000
                confidence_threshold = 0.7
                print("Parameters reset to defaults")
        
        cv2.destroyAllWindows()
        
    except KeyboardInterrupt:
        print("\nDebug interrupted by user")
    except Exception as e:
        print(f"Debug failed with error: {e}")
    finally:
        camera.disconnect()
        print("Camera disconnected")

if __name__ == "__main__":
    debug_board_detection() 