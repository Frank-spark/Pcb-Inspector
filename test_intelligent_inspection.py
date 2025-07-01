#!/usr/bin/env python3
"""
Test script for Intelligent PCB Inspection Workflow
===================================================

This script demonstrates the new intelligent inspection features:
- Automatic board detection and recognition
- Auto-zoom and focus for optimal capture
- QC sample creation for unknown boards
- Seamless workflow from detection to inspection

Usage:
    python test_intelligent_inspection.py

Features tested:
- Board detection accuracy
- Auto-zoom functionality
- Board type identification
- QC sample creation workflow
"""

import cv2
import numpy as np
import time
import json
from camera import CameraManager
from qa_manager import QAManager
from inspector import PCBInspector

def test_intelligent_inspection():
    """Test the intelligent inspection workflow."""
    print("Intelligent PCB Inspection Test")
    print("=" * 40)
    
    # Initialize components
    print("Initializing components...")
    camera = CameraManager()
    qa_manager = QAManager()
    inspector = PCBInspector()
    
    if not camera.connect():
        print("Failed to connect to camera!")
        return
    
    print("Camera connected successfully!")
    
    try:
        # Test 1: Board Detection and Status
        print("\n1. Testing board detection...")
        print("Please place a PCB board in front of the camera...")
        print("Press 's' to check detection status, 'q' to quit")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Display frame
            cv2.imshow("Board Detection Test - Press 's' for status, 'q' to quit", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Check board detection status
                status = camera.get_board_detection_status()
                if status.get("board_detected", False):
                    print(f"✓ Board detected! Confidence: {status['confidence']:.1%}")
                    print(f"  Area: {status['area']:.0f}px, Size: {status['bbox'][2]}x{status['bbox'][3]}px")
                else:
                    print("✗ No board detected")
        
        cv2.destroyAllWindows()
        
        # Test 2: Auto-zoom and Focus
        print("\n2. Testing auto-zoom and focus...")
        print("Please place a PCB board in front of the camera...")
        print("Press 'z' to auto-zoom, 'f' to test focus, 'q' to quit")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Display frame
            cv2.imshow("Auto-zoom Test - Press 'z' to zoom, 'f' for focus, 'q' to quit", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('z'):
                # Auto-zoom to board
                print("Auto-zooming to board...")
                zoomed_frame = camera.auto_zoom_to_board(frame)
                if zoomed_frame is not None:
                    print(f"✓ Auto-zoomed to {camera.get_zoom():.1f}x")
                    cv2.imshow("Auto-zoomed", zoomed_frame)
                    cv2.waitKey(2000)  # Show for 2 seconds
                else:
                    print("✗ No board found for auto-zoom")
            elif key == ord('f'):
                # Test focus
                print("Testing focus...")
                camera.set_auto_focus(True)
                time.sleep(0.5)
                print("✓ Auto-focus enabled")
        
        cv2.destroyAllWindows()
        
        # Test 3: Board Type Identification
        print("\n3. Testing board type identification...")
        print("Please place a PCB board in front of the camera...")
        print("Press 'i' to identify board type, 'q' to quit")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Display frame
            cv2.imshow("Board Identification Test - Press 'i' to identify, 'q' to quit", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('i'):
                # Test board identification
                print("Identifying board type...")
                
                # Auto-zoom first for better identification
                zoomed_frame = camera.auto_zoom_to_board(frame)
                if zoomed_frame is not None:
                    # Capture optimized image
                    inspection_frame = camera.capture_snapshot("test_identification.jpg")
                    if inspection_frame is not None:
                        # Try to identify board type
                        board_name = identify_board_type(inspection_frame, qa_manager, inspector)
                        if board_name:
                            print(f"✓ Board identified as: {board_name}")
                        else:
                            print("✗ Unknown board type - would prompt for QC sample creation")
                    else:
                        print("✗ Failed to capture image for identification")
                else:
                    print("✗ No board detected for identification")
        
        cv2.destroyAllWindows()
        
        # Test 4: QC Sample Creation Workflow
        print("\n4. Testing QC sample creation workflow...")
        print("This simulates the workflow when an unknown board is detected")
        print("Please place a PCB board in front of the camera...")
        print("Press 'c' to simulate QC sample creation, 'q' to quit")
        
        while True:
            frame = camera.get_frame()
            if frame is None:
                print("Failed to get frame")
                break
            
            # Display frame
            cv2.imshow("QC Sample Creation Test - Press 'c' to simulate, 'q' to quit", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                # Simulate QC sample creation
                print("Simulating QC sample creation workflow...")
                
                # Auto-zoom and capture front
                zoomed_frame = camera.auto_zoom_to_board(frame)
                if zoomed_frame is not None:
                    front_frame = camera.capture_snapshot("test_front.jpg")
                    if front_frame is not None:
                        print("✓ Front image captured with auto-zoom")
                        print("  (In real app, would prompt for board name)")
                        print("  (Then prompt to flip board and capture back)")
                        
                        # Simulate back capture
                        time.sleep(1)
                        back_frame = camera.capture_snapshot("test_back.jpg")
                        if back_frame is not None:
                            print("✓ Back image captured")
                            print("  (In real app, would save QC sample)")
                        else:
                            print("✗ Failed to capture back image")
                    else:
                        print("✗ Failed to capture front image")
                else:
                    print("✗ No board detected for QC sample creation")
        
        cv2.destroyAllWindows()
        
        print("\nIntelligent inspection test completed successfully!")
        print("\nKey Features Demonstrated:")
        print("- Real-time board detection with confidence scoring")
        print("- Automatic zoom and focus optimization")
        print("- Board type identification from existing samples")
        print("- QC sample creation workflow for unknown boards")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        # Cleanup
        camera.disconnect()
        cv2.destroyAllWindows()
        print("Camera disconnected")

def identify_board_type(inspection_frame, qa_manager, inspector):
    """Try to identify the board type using computer vision and existing samples."""
    try:
        # Get all existing QA samples
        samples = qa_manager.list_qa_samples()
        
        best_match = None
        best_score = 0.0
        
        for sample in samples:
            # Load the reference image
            ref_path = sample["image_paths"]["front"]
            ref_img = cv2.imread(ref_path)
            
            if ref_img is not None:
                # Align and compare images
                aligned_img, alignment_info = inspector.align_images(ref_img, inspection_frame)
                if alignment_info.get("success", False):
                    comparison_result = inspector.compare_images(ref_img, aligned_img)
                    similarity = comparison_result.get("similarity_score", 0.0)
                    
                    if similarity > best_score and similarity > 0.85:  # 85% similarity threshold
                        best_score = similarity
                        best_match = sample["board_name"]
        
        return best_match
        
    except Exception as e:
        print(f"Error identifying board type: {e}")
        return None

if __name__ == "__main__":
    test_intelligent_inspection() 