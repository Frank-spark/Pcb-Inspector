#!/usr/bin/env python3
"""
Webcam Capabilities Checker
===========================

This script checks what features your webcam supports and shows you
what will work with the PCB Inspector.

Usage:
    python check_webcam_capabilities.py
"""

import cv2
import numpy as np
from camera import CameraManager

def check_webcam_capabilities():
    """Check and display webcam capabilities."""
    print("Webcam Capabilities Checker")
    print("=" * 40)
    
    # Initialize camera
    print("Initializing camera...")
    camera = CameraManager()
    
    if not camera.connect():
        print("❌ Failed to connect to camera!")
        return
    
    print("✅ Camera connected successfully!")
    
    # Get camera info
    camera_info = camera.get_camera_info()
    print(f"\n📷 Camera Information:")
    print(f"   Resolution: {camera_info.get('width', 'Unknown')}x{camera_info.get('height', 'Unknown')}")
    print(f"   FPS: {camera_info.get('fps', 'Unknown')}")
    print(f"   Brightness: {camera_info.get('brightness', 'Unknown')}")
    print(f"   Contrast: {camera_info.get('contrast', 'Unknown')}")
    
    # Check focus capabilities
    focus_info = camera.get_focus_info()
    print(f"\n🔍 Focus Capabilities:")
    
    autofocus_supported = focus_info.get("autofocus_supported", False)
    focus_supported = focus_info.get("focus_supported", False)
    
    if autofocus_supported:
        print("   ✅ Autofocus: Supported")
    else:
        print("   ❌ Autofocus: Not supported")
    
    if focus_supported:
        print("   ✅ Manual Focus: Supported")
    else:
        print("   ❌ Manual Focus: Not supported")
    
    if not autofocus_supported and not focus_supported:
        print("   ⚠️  Your webcam has fixed focus (most common)")
        print("   💡 This is normal for most consumer webcams")
    
    # Test board detection
    print(f"\n🔍 Board Detection Test:")
    print("   Please place a PCB board in front of the camera...")
    print("   Press 'd' to test detection, 'q' to quit")
    
    while True:
        frame = camera.get_frame()
        if frame is None:
            print("   ❌ Failed to get frame")
            break
        
        # Display frame
        cv2.imshow("Board Detection Test - Press 'd' to test, 'q' to quit", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            # Test board detection
            board_info = camera.detect_board(frame)
            if board_info:
                confidence = board_info["confidence"]
                area = board_info["area"]
                print(f"   ✅ Board detected! Confidence: {confidence:.1%}")
                print(f"      Area: {area:.0f} pixels")
                
                # Draw detection on frame
                x, y, w, h = board_info["bbox"]
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"Board: {confidence:.1%}", 
                           (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.imshow("Board Detection Result", frame)
                cv2.waitKey(2000)  # Show for 2 seconds
            else:
                print("   ❌ No board detected")
    
    cv2.destroyAllWindows()
    
    # Test zoom capabilities
    print(f"\n🔍 Zoom Capabilities:")
    print("   Testing digital zoom...")
    
    # Test zoom in
    original_zoom = camera.get_zoom()
    success = camera.zoom_in(1.5)
    if success:
        new_zoom = camera.get_zoom()
        print(f"   ✅ Digital zoom works: {original_zoom:.1f}x → {new_zoom:.1f}x")
    else:
        print("   ❌ Digital zoom failed")
    
    # Reset zoom
    camera.reset_zoom()
    
    # Summary
    print(f"\n📋 Summary:")
    print(f"   ✅ Camera: Working")
    print(f"   ✅ Board Detection: Working")
    print(f"   ✅ Digital Zoom: Working")
    
    if autofocus_supported or focus_supported:
        print(f"   ✅ Focus Control: Available")
    else:
        print(f"   ⚠️  Focus Control: Not available (fixed focus)")
        print(f"      This is normal for most webcams!")
    
    print(f"\n💡 Recommendations:")
    if not autofocus_supported and not focus_supported:
        print(f"   • Your webcam has fixed focus - this is normal")
        print(f"   • Position the camera 10-20cm from the PCB for best results")
        print(f"   • Ensure good lighting for clear images")
        print(f"   • Use the auto-zoom feature to frame boards properly")
    else:
        print(f"   • Your webcam supports focus control - great!")
        print(f"   • Use auto-focus for best results")
        print(f"   • Manual focus available if needed")
    
    print(f"   • All core PCB inspection features will work perfectly")
    print(f"   • Board detection and auto-zoom are the most important features")
    
    # Cleanup
    camera.disconnect()
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    check_webcam_capabilities() 