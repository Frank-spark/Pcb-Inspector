#!/usr/bin/env python3
"""
Simple Board Detection Test
===========================

This script tests board detection with different parameter settings
to help identify the optimal values for your setup.

Usage:
    python test_board_detection.py
"""

import cv2
import numpy as np
from camera import CameraManager

def test_board_detection():
    """Test board detection with different parameters."""
    print("PCB Board Detection Test")
    print("=" * 30)
    
    # Initialize camera
    camera = CameraManager()
    
    if not camera.connect():
        print("Failed to connect to camera!")
        return
    
    print("Camera connected successfully!")
    
    # Test different parameter combinations
    test_params = [
        {"min_area": 5000, "confidence": 0.5},
        {"min_area": 10000, "confidence": 0.7},
        {"min_area": 15000, "confidence": 0.6},
        {"min_area": 20000, "confidence": 0.5},
        {"min_area": 5000, "confidence": 0.3},
        {"min_area": 10000, "confidence": 0.4},
    ]
    
    print("\nTesting board detection with different parameters...")
    print("Place a PCB board in front of the camera and press any key to continue...")
    
    for i, params in enumerate(test_params, 1):
        print(f"\n--- Test {i}/{len(test_params)} ---")
        print(f"Min area: {params['min_area']}, Confidence threshold: {params['confidence']}")
        
        # Set parameters
        camera.min_board_area = params["min_area"]
        camera.board_confidence_threshold = params["confidence"]
        
        # Capture frame
        frame = camera.get_frame()
        if frame is None:
            print("Failed to get frame")
            continue
        
        # Test detection
        board_info = camera.detect_board(frame)
        
        if board_info:
            print(f"✓ BOARD DETECTED!")
            print(f"  Confidence: {board_info['confidence']:.1%}")
            print(f"  Area: {board_info['area']:.0f} pixels")
            print(f"  Aspect ratio: {board_info['aspect_ratio']:.2f}")
            
            # Draw detection on frame
            x, y, w, h = board_info["bbox"]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"Board: {board_info['confidence']:.1%}", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Show frame
            cv2.imshow(f"Test {i} - Board Detected", frame)
            cv2.waitKey(2000)  # Show for 2 seconds
            cv2.destroyAllWindows()
            
            print(f"✓ SUCCESS: Board detected with parameters: min_area={params['min_area']}, confidence={params['confidence']}")
            break
        else:
            print("✗ No board detected")
            
            # Show frame with contours for debugging
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            edges = cv2.Canny(thresh, 30, 100)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Draw all contours above min area
            large_contours = [c for c in contours if cv2.contourArea(c) >= params["min_area"]]
            cv2.drawContours(frame, large_contours, -1, (0, 0, 255), 2)
            
            if large_contours:
                largest = max(large_contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                x, y, w, h = cv2.boundingRect(largest)
                aspect_ratio = w / h if h > 0 else 0
                print(f"  Largest contour: Area={area:.0f}, Aspect ratio={aspect_ratio:.2f}")
            
            cv2.imshow(f"Test {i} - No Board Detected", frame)
            cv2.waitKey(1000)  # Show for 1 second
            cv2.destroyAllWindows()
    
    print("\n" + "=" * 30)
    print("Test completed!")
    print("\nRecommendations:")
    print("1. If no board was detected, try:")
    print("   - Better lighting")
    print("   - Cleaner background")
    print("   - Board closer to camera")
    print("   - Board more centered in frame")
    print("2. If board was detected, note the working parameters")
    print("3. Run debug_board_detection.py for interactive tuning")
    
    camera.disconnect()

if __name__ == "__main__":
    test_board_detection() 