import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from camera import CameraManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spark QA PCB Inspector")
        
        # Set window size and position
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Initialize camera
        self.camera = CameraManager()
        self.camera_connected = self.camera.connect()
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("Spark QA PCB Inspector - AI-Powered Visual QA")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Camera preview
        self.camera_label = QLabel("Initializing camera...")
        self.camera_label.setStyleSheet("""
            background-color: #27272a; 
            border: 2px solid #52525b; 
            border-radius: 10px; 
            padding: 10px; 
            color: #a1a1aa;
            font-size: 18px;
        """)
        self.camera_label.setAlignment(Qt.AlignCenter)
        self.camera_label.setMinimumHeight(400)
        layout.addWidget(self.camera_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.capture_front_btn = QPushButton("Capture Front")
        self.capture_front_btn.setStyleSheet("""
            QPushButton {
                background-color: #38bdf8; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
            }
            QPushButton:disabled {
                background-color: #52525b;
                color: #a1a1aa;
            }
        """)
        self.capture_front_btn.clicked.connect(self.capture_front)
        
        self.capture_back_btn = QPushButton("Capture Back")
        self.capture_back_btn.setStyleSheet("""
            QPushButton {
                background-color: #38bdf8; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0ea5e9;
            }
            QPushButton:disabled {
                background-color: #52525b;
                color: #a1a1aa;
            }
        """)
        self.capture_back_btn.clicked.connect(self.capture_back)
        
        self.inspect_btn = QPushButton("Inspect Board")
        self.inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f472b6; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ec4899;
            }
            QPushButton:disabled {
                background-color: #52525b;
                color: #a1a1aa;
            }
        """)
        self.inspect_btn.clicked.connect(self.inspect_board)
        
        button_layout.addWidget(self.capture_front_btn)
        button_layout.addWidget(self.capture_back_btn)
        button_layout.addWidget(self.inspect_btn)
        button_layout.addStretch()  # Add space to push buttons to the left
        layout.addLayout(button_layout)
        
        # Result area
        self.result_label = QLabel("Inspection results will appear here.")
        self.result_label.setStyleSheet("""
            background-color: #18181b; 
            border: 1px solid #52525b; 
            border-radius: 5px; 
            padding: 50px; 
            color: #a1a1aa;
            font-size: 16px;
        """)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setMinimumHeight(150)
        layout.addWidget(self.result_label)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #18181b;
                color: #fafafa;
            }
        """)
        
        # Setup camera timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        if self.camera_connected:
            self.timer.start(30)  # Update every 30ms (~33 FPS)
            self.capture_front_btn.setEnabled(True)
            self.capture_back_btn.setEnabled(True)
            self.inspect_btn.setEnabled(True)
        else:
            self.camera_label.setText("Camera not connected. Please check your webcam.")
            self.capture_front_btn.setEnabled(False)
            self.capture_back_btn.setEnabled(False)
            self.inspect_btn.setEnabled(False)
    
    def update_camera(self):
        """Update camera preview"""
        if self.camera_connected:
            frame = self.camera.get_frame()
            if frame is not None:
                # Convert frame to QPixmap
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(q_image)
                
                # Scale pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
    
    def capture_front(self):
        """Capture front image"""
        if self.camera_connected:
            frame = self.camera.capture_snapshot("front_capture.jpg")
            if frame is not None:
                self.result_label.setText("Front image captured successfully!")
                self.result_label.setStyleSheet("""
                    background-color: #18181b; 
                    border: 1px solid #10b981; 
                    border-radius: 5px; 
                    padding: 50px; 
                    color: #10b981;
                    font-size: 16px;
                """)
    
    def capture_back(self):
        """Capture back image"""
        if self.camera_connected:
            frame = self.camera.capture_snapshot("back_capture.jpg")
            if frame is not None:
                self.result_label.setText("Back image captured successfully!")
                self.result_label.setStyleSheet("""
                    background-color: #18181b; 
                    border: 1px solid #10b981; 
                    border-radius: 5px; 
                    padding: 50px; 
                    color: #10b981;
                    font-size: 16px;
                """)
    
    def inspect_board(self):
        """Inspect board"""
        self.result_label.setText("Inspection in progress...")
        self.result_label.setStyleSheet("""
            background-color: #18181b; 
            border: 1px solid #f59e0b; 
            border-radius: 5px; 
            padding: 50px; 
            color: #f59e0b;
            font-size: 16px;
        """)
        # TODO: Implement actual inspection logic
    
    def closeEvent(self, event):
        """Clean up camera on close"""
        if self.camera_connected:
            self.camera.disconnect()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 