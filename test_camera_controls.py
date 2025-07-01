#!/usr/bin/env python3
"""
Test script for PCB Inspector Camera Controls
==============================================

This script demonstrates the new zoom, focus, and board detection capabilities
of the enhanced camera system.

Usage:
    python test_camera_controls.py

Features tested:
- Zoom in/out controls
- Focus controls (auto/manual)
- Board detection
- Auto-zoom to board
"""

import cv2
import numpy as np
import time
from camera import CameraManager

def test_camera_controls():
    """Test the enhanced camera controls."""
    print("PCB Inspector Camera Controls Test")
    print("=" * 40)
    
    # Initialize camera
    print("Initializing camera...")
    camera = CameraManager()
    
    if not camera.connect():
        print("Failed to connect to camera!")
        return
    
    print("Camera connected successfully!")
    print(f"Camera info: {camera.get_camera_info()}")
    
    try:
        # Test 1: Basic zoom controls
        print("\n1. Testing zoom controls...")
        print(f"Initial zoom: {camera.get_zoom():.1f}x")
        
        # Zoom in
        camera.zoom_in(1.5)
        print(f"After zoom in: {camera.get_zoom():.1f}x")
        time.sleep(1)
        
        # Zoom out
        camera.zoom_out(1.2)
        print(f"After zoom out: {camera.get_zoom():.1f}x")
        time.sleep(1)
        
        # Reset zoom
        camera.reset_zoom()
        print(f"After reset: {camera.get_zoom():.1f}x")
        
        # Test 2: Focus controls
        print("\n2. Testing focus controls...")
        print(f"Initial focus info: {camera.get_focus_info()}")
        
        # Enable manual focus
        camera.set_auto_focus(False)
        print("Manual focus enabled")
        
        # Set different focus distances
        for focus_val in [0.2, 0.5, 0.8]:
            camera.set_focus(focus_val)
            print(f"Focus set to {focus_val:.1f}")
            time.sleep(0.5)
        
        # Re-enable auto focus
        camera.set_auto_focus(True)
        print("Auto focus re-enabled")
        
        # Test 3: Board detection
        print("\n3. Testing board detection...")
        print("Please place a PCB board in front of the camera...")
        print("Press 'd' to detect board, 'q' to quit")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Display frame
            cv2.imshow("Camera Test - Press 'd' to detect board, 'q' to quit", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('d'):
                # Detect board
                board_info = camera.detect_board(frame)
                if board_info:
                    print(f"Board detected! Confidence: {board_info['confidence']:.1%}")
                    print(f"Board area: {board_info['area']:.0f} pixels")
                    print(f"Board size: {board_info['bbox'][2]}x{board_info['bbox'][3]} pixels")
                    
                    # Draw detection on frame
                    x, y, w, h = board_info["bbox"]
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"Board: {board_info['confidence']:.1%}", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.imshow("Board Detection", frame)
                    cv2.waitKey(2000)  # Show for 2 seconds
                else:
                    print("No board detected")
            elif key == ord('z'):
                # Auto-zoom to board
                print("Auto-zooming to board...")
                zoomed_frame = camera.auto_zoom_to_board(frame)
                if zoomed_frame is not None:
                    print(f"Auto-zoomed to {camera.get_zoom():.1f}x")
                    cv2.imshow("Auto-zoomed", zoomed_frame)
                    cv2.waitKey(2000)  # Show for 2 seconds
                else:
                    print("No board found for auto-zoom")
        
        cv2.destroyAllWindows()
        
        # Test 4: Capture enhanced snapshot
        print("\n4. Testing enhanced snapshot capture...")
        snapshot = camera.capture_snapshot("test_enhanced_snapshot.jpg")
        if snapshot is not None:
            print("Enhanced snapshot captured successfully!")
            print("Saved as 'test_enhanced_snapshot.jpg'")
        else:
            print("Failed to capture enhanced snapshot")
        
        print("\nCamera controls test completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Cleanup
        camera.disconnect()
        cv2.destroyAllWindows()
        print("Camera disconnected")

if __name__ == "__main__":
    test_camera_controls() 