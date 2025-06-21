"""
Spark QA PCB Inspector - Main Application
=========================================

This is the main desktop application for automated PCB inspection using computer vision.
The app provides a GUI interface for capturing QA samples and inspecting PCBs against
known good references.

Key Features:
- Live camera preview with webcam integration
- QA sample creation and management
- Board recognition and database management
- Automated inspection workflow
- Modern dark-mode UI

Author: Spark QA Team
"""

import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                               QLabel, QPushButton, QHBoxLayout, QComboBox, 
                               QMessageBox, QInputDialog, QTextEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from camera import CameraManager
from qa_manager import QAManager
from inspector import PCBInspector

class MainWindow(QMainWindow):
    """
    Main application window for the PCB Inspector.
    
    This class manages the entire user interface and coordinates between
    the camera, QA manager, and inspector components.
    """
    
    def __init__(self):
        """Initialize the main application window and all components."""
        super().__init__()
        self.setWindowTitle("Spark QA PCB Inspector")
        
        # Set window size and position (centered, resizable)
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Initialize core system components
        self.camera = CameraManager()          # Handles webcam capture
        self.qa_manager = QAManager()          # Manages QA sample database
        self.inspector = PCBInspector()        # Performs image analysis
        self.camera_connected = self.camera.connect()  # Connect to webcam
        
        # Track current board state
        self.current_board_name = ""           # Name of currently selected board
        self.front_captured = False            # Whether front image is captured
        self.back_captured = False             # Whether back image is captured
        
        # Setup the user interface
        self.setup_ui()
        
        # Initialize camera preview timer
        self.setup_camera_timer()
        
        # Load existing boards into the dropdown
        self.load_existing_boards()
    
    def setup_ui(self):
        """Create and configure all UI elements."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create header section
        self.create_header(layout)
        
        # Create board selection section
        self.create_board_selection(layout)
        
        # Create status display
        self.create_status_display(layout)
        
        # Create camera preview area
        self.create_camera_preview(layout)
        
        # Create action buttons
        self.create_action_buttons(layout)
        
        # Create result display area
        self.create_result_display(layout)
        
        # Apply dark theme styling
        self.apply_dark_theme()
    
    def create_header(self, layout):
        """Create the application header with title."""
        header = QLabel("Spark QA PCB Inspector - AI-Powered Visual QA")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8; padding: 20px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
    
    def create_board_selection(self, layout):
        """Create the board selection dropdown and new board button."""
        board_layout = QHBoxLayout()
        
        # Board selection label
        board_layout.addWidget(QLabel("Select Board:"))
        
        # Board dropdown - shows all previously created boards
        self.board_combo = QComboBox()
        self.board_combo.setStyleSheet("""
            QComboBox {
                background-color: #27272a;
                border: 1px solid #52525b;
                border-radius: 5px;
                padding: 5px;
                color: white;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
        """)
        self.board_combo.currentTextChanged.connect(self.on_board_selected)
        board_layout.addWidget(self.board_combo)
        
        # New board button - creates a new board entry
        self.new_board_btn = QPushButton("New Board")
        self.new_board_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.new_board_btn.clicked.connect(self.create_new_board)
        board_layout.addWidget(self.new_board_btn)
        
        # Add stretch to push elements to the left
        board_layout.addStretch()
        layout.addLayout(board_layout)
    
    def create_status_display(self, layout):
        """Create the status display bar showing current application state."""
        self.status_label = QLabel("Ready to capture or inspect")
        self.status_label.setStyleSheet("""
            background-color: #27272a;
            border: 1px solid #52525b;
            border-radius: 5px;
            padding: 10px;
            color: #a1a1aa;
            font-size: 14px;
        """)
        layout.addWidget(self.status_label)
    
    def create_camera_preview(self, layout):
        """Create the camera preview area for live webcam feed."""
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
        self.camera_label.setMinimumHeight(400)  # Ensure minimum size for preview
        layout.addWidget(self.camera_label)
    
    def create_action_buttons(self, layout):
        """Create the main action buttons for capture and inspection."""
        button_layout = QHBoxLayout()
        
        # Capture Front button - captures front image of current board
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
        
        # Capture Back button - captures back image of current board
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
        
        # Inspect Board button - compares current board against QA sample
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
        
        # Add buttons to layout
        button_layout.addWidget(self.capture_front_btn)
        button_layout.addWidget(self.capture_back_btn)
        button_layout.addWidget(self.inspect_btn)
        button_layout.addStretch()  # Push buttons to the left
        layout.addLayout(button_layout)
    
    def create_result_display(self, layout):
        """Create the result display area for showing inspection results."""
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
    
    def apply_dark_theme(self):
        """Apply dark theme styling to the main window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #18181b;
                color: #fafafa;
            }
        """)
    
    def setup_camera_timer(self):
        """Setup timer for updating camera preview at regular intervals."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
        
        if self.camera_connected:
            # Start camera preview at ~33 FPS (30ms intervals)
            self.timer.start(30)
            self.capture_front_btn.setEnabled(True)
            self.capture_back_btn.setEnabled(True)
            self.inspect_btn.setEnabled(True)
        else:
            # Show error if camera not connected
            self.camera_label.setText("Camera not connected. Please check your webcam.")
            self.capture_front_btn.setEnabled(False)
            self.capture_back_btn.setEnabled(False)
            self.inspect_btn.setEnabled(False)
    
    def load_existing_boards(self):
        """Load all existing boards from the QA database into the dropdown."""
        samples = self.qa_manager.list_qa_samples()
        self.board_combo.clear()
        self.board_combo.addItem("-- Select a board --")
        
        # Add each board to the dropdown with its sample ID as data
        for sample in samples:
            self.board_combo.addItem(sample["board_name"], sample["sample_id"])
    
    def create_new_board(self):
        """Create a new board entry by prompting for board name."""
        board_name, ok = QInputDialog.getText(self, "New Board", "Enter board name:")
        if ok and board_name.strip():
            self.current_board_name = board_name.strip()
            self.board_combo.addItem(board_name)
            self.board_combo.setCurrentText(board_name)
            
            # Reset capture state for new board
            self.front_captured = False
            self.back_captured = False
            self.update_status()
            self.status_label.setText(f"New board '{board_name}' created. Please capture front and back images.")
    
    def on_board_selected(self, board_name):
        """
        Handle board selection from dropdown.
        
        This function determines if the selected board is new or existing,
        and updates the UI state accordingly.
        """
        if board_name == "-- Select a board --":
            # No board selected - reset state
            self.current_board_name = ""
            self.front_captured = False
            self.back_captured = False
            self.update_status()
            return
        
        # Get the sample ID for the selected board
        sample_id = self.board_combo.currentData()
        if sample_id:
            # Board exists in database - check if it has valid images
            sample = self.qa_manager.get_qa_sample(sample_id)
            if sample:
                # Board has valid QA sample - ready for inspection
                self.current_board_name = board_name
                self.front_captured = True
                self.back_captured = True
                self.update_status()
                self.status_label.setText(f"Board '{board_name}' loaded. Ready for inspection.")
            else:
                # Board exists but missing images - need to recapture
                self.current_board_name = board_name
                self.front_captured = False
                self.back_captured = False
                self.update_status()
                self.status_label.setText(f"Board '{board_name}' found but missing images. Please recapture.")
        else:
            # New board (not in database yet)
            self.current_board_name = board_name
            self.front_captured = False
            self.back_captured = False
            self.update_status()
            self.status_label.setText(f"New board '{board_name}'. Please capture front and back images.")
    
    def update_status(self):
        """Update button states based on current application state."""
        has_board = bool(self.current_board_name)
        can_capture = has_board and self.camera_connected
        can_inspect = has_board and self.front_captured and self.back_captured
        
        # Enable/disable buttons based on current state
        self.capture_front_btn.setEnabled(can_capture)
        self.capture_back_btn.setEnabled(can_capture)
        self.inspect_btn.setEnabled(can_inspect)
    
    def update_camera(self):
        """Update the camera preview with the latest frame from webcam."""
        if self.camera_connected:
            frame = self.camera.get_frame()
            if frame is not None:
                # Convert OpenCV frame to Qt format for display
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(q_image)
                
                # Scale image to fit preview area while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
    
    def capture_front(self):
        """Capture front image of the current board."""
        if self.camera_connected and self.current_board_name:
            # Capture enhanced image using camera manager
            frame = self.camera.capture_snapshot("temp_front.jpg")
            if frame is not None:
                self.front_captured = True
                self.update_status()
                
                # Update UI with success message
                self.result_label.setText("Front image captured successfully!")
                self.result_label.setStyleSheet("""
                    background-color: #18181b; 
                    border: 1px solid #10b981; 
                    border-radius: 5px; 
                    padding: 50px; 
                    color: #10b981;
                    font-size: 16px;
                """)
                self.status_label.setText(f"Front captured for '{self.current_board_name}'. Capture back image or save QA sample.")
    
    def capture_back(self):
        """Capture back image of the current board."""
        if self.camera_connected and self.current_board_name:
            # Capture enhanced image using camera manager
            frame = self.camera.capture_snapshot("temp_back.jpg")
            if frame is not None:
                self.back_captured = True
                self.update_status()
                
                # Update UI with success message
                self.result_label.setText("Back image captured successfully!")
                self.result_label.setStyleSheet("""
                    background-color: #18181b; 
                    border: 1px solid #10b981; 
                    border-radius: 5px; 
                    padding: 50px; 
                    color: #10b981;
                    font-size: 16px;
                """)
                self.status_label.setText(f"Back captured for '{self.current_board_name}'. Ready to save QA sample or inspect.")
                
                # If both images are captured, automatically save as QA sample
                if self.front_captured:
                    self.save_qa_sample()
    
    def save_qa_sample(self):
        """Save the captured front and back images as a QA sample."""
        if self.front_captured and self.back_captured:
            try:
                # Create QA sample using the QA manager
                sample_id = self.qa_manager.create_qa_sample(
                    board_name=self.current_board_name,
                    front_image_path="temp_front.jpg",
                    back_image_path="temp_back.jpg",
                    notes=f"QA sample created for {self.current_board_name}"
                )
                
                # Update the board dropdown to include the new sample
                self.load_existing_boards()
                self.board_combo.setCurrentText(self.current_board_name)
                
                # Show success message
                self.result_label.setText(f"QA sample saved successfully! Sample ID: {sample_id}")
                self.status_label.setText(f"QA sample created for '{self.current_board_name}'. Ready for inspection.")
                
            except Exception as e:
                # Show error message if saving fails
                self.result_label.setText(f"Error saving QA sample: {str(e)}")
    
    def inspect_board(self):
        """Inspect the current board against its QA sample."""
        # Validate that a board is selected
        if not self.current_board_name:
            QMessageBox.warning(self, "No Board Selected", "Please select a board to inspect.")
            return
        
        # Validate that a QA sample exists
        sample_id = self.board_combo.currentData()
        if not sample_id:
            QMessageBox.warning(self, "No QA Sample", "Please create a QA sample for this board first.")
            return
        
        # Show inspection in progress
        self.result_label.setText("Inspection in progress...")
        self.result_label.setStyleSheet("""
            background-color: #18181b; 
            border: 1px solid #f59e0b; 
            border-radius: 5px; 
            padding: 50px; 
            color: #f59e0b;
            font-size: 16px;
        """)
        
        # TODO: Implement actual inspection logic using inspector.py
        # This would:
        # 1. Capture current board image
        # 2. Load QA sample images
        # 3. Align and compare images
        # 4. Detect defects and generate report
        # 5. Display results in the UI
    
    def closeEvent(self, event):
        """Handle application shutdown - clean up camera connection."""
        if self.camera_connected:
            self.camera.disconnect()
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 