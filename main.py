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
import os
import cv2
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                               QLabel, QPushButton, QHBoxLayout, QComboBox, 
                               QMessageBox, QInputDialog, QTextEdit, QProgressBar,
                               QSlider)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QAction
from camera import CameraManager
from qa_manager import QAManager
from inspector import PCBInspector
from openai_api import OpenAIAnalyzer
import json
from pathlib import Path
import time
import logging

CONFIG_PATH = Path.home() / ".pcb_inspector_config.json"

def load_api_key():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
                return data.get('openai_api_key', None)
        except Exception:
            return None
    return None

def save_api_key(api_key):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({'openai_api_key': api_key}, f)

class InspectionWorker(QThread):
    """Background worker for performing AI inspection."""
    
    progress_updated = Signal(str)
    inspection_complete = Signal(dict)
    inspection_error = Signal(str)
    
    def __init__(self, current_image_path, qa_sample_id, qa_manager, inspector, ai_analyzer):
        super().__init__()
        self.current_image_path = current_image_path
        self.qa_sample_id = qa_sample_id
        self.qa_manager = qa_manager
        self.inspector = inspector
        self.ai_analyzer = ai_analyzer
    
    def run(self):
        """Perform the inspection in background thread."""
        try:
            self.progress_updated.emit("Loading QA sample...")
            
            # Get QA sample images
            sample = self.qa_manager.get_qa_sample(self.qa_sample_id)
            if not sample:
                self.inspection_error.emit("QA sample not found")
                return
            
            front_path = sample["image_paths"]["front"]
            back_path = sample["image_paths"]["back"]
            
            self.progress_updated.emit("Performing computer vision analysis...")
            
            # Load images for OpenCV analysis
            current_img = cv2.imread(self.current_image_path)
            reference_img = cv2.imread(front_path)  # Assume front for now
            
            if current_img is None or reference_img is None:
                self.inspection_error.emit("Failed to load images for analysis")
                return
            
            # Perform OpenCV alignment and comparison
            aligned_img, alignment_info = self.inspector.align_images(reference_img, current_img)
            comparison_result = self.inspector.compare_images(reference_img, aligned_img)
            defect_analysis = self.inspector.analyze_defects(reference_img, aligned_img, comparison_result)
            
            self.progress_updated.emit("Performing AI analysis...")
            
            # Perform AI analysis
            ai_result = self.ai_analyzer.compare_pcb_images(self.current_image_path, front_path)
            
            self.progress_updated.emit("Generating comprehensive report...")
            
            # Combine results
            combined_result = {
                "opencv_analysis": {
                    "alignment": alignment_info,
                    "comparison": comparison_result,
                    "defects": defect_analysis
                },
                "ai_analysis": ai_result,
                "timestamp": datetime.now().isoformat(),
                "qa_sample_id": self.qa_sample_id,
                "current_image_path": self.current_image_path
            }
            
            self.inspection_complete.emit(combined_result)
            
        except Exception as e:
            self.inspection_error.emit(f"Inspection failed: {str(e)}")

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
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Set window size and position (centered, resizable)
        self.setGeometry(100, 100, 1400, 900)
        self.setMinimumSize(1200, 700)
        
        # Initialize core system components
        self.camera = CameraManager()          # Handles webcam capture
        self.qa_manager = QAManager()          # Manages QA sample database
        self.inspector = PCBInspector()        # Performs image analysis
        
        # Get API key from environment and initialize AI analyzer
        api_key = load_api_key()
        if not api_key:
            api_key, ok = QInputDialog.getText(self, "OpenAI API Key Required", "Enter your OpenAI API key:")
            if ok and api_key:
                save_api_key(api_key)
            else:
                QMessageBox.critical(self, "API Key Required", "An OpenAI API key is required to use this application.")
                sys.exit(1)
        self.ai_analyzer = OpenAIAnalyzer(api_key=api_key)    # AI-powered analysis
        
        self.camera_connected = self.camera.connect()  # Connect to webcam
        
        # Track current board state
        self.current_board_name = ""           # Name of currently selected board
        self.front_captured = False            # Whether front image is captured
        self.back_captured = False             # Whether back image is captured
        self.inspection_worker = None          # Background inspection worker
        
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
        
        # Add a menu option to update the API key
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        api_key_action = QAction("Set OpenAI API Key", self)
        api_key_action.triggered.connect(self.prompt_api_key)
        settings_menu.addAction(api_key_action)
    
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
        
        # Add progress bar for inspection
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #52525b;
                border-radius: 5px;
                text-align: center;
                background-color: #18181b;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_bar)
    
    def create_camera_preview(self, layout):
        """Create the camera preview area for live webcam feed with zoom and focus controls."""
        # Camera preview container
        camera_container = QWidget()
        camera_layout = QVBoxLayout(camera_container)
        
        # Camera preview label
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
        camera_layout.addWidget(self.camera_label)
        
        # Camera controls section
        controls_layout = QHBoxLayout()
        
        # Zoom controls
        zoom_group = QWidget()
        zoom_layout = QVBoxLayout(zoom_group)
        zoom_layout.setContentsMargins(10, 5, 10, 5)
        
        zoom_label = QLabel("Zoom Controls")
        zoom_label.setStyleSheet("color: #fafafa; font-weight: bold; font-size: 12px;")
        zoom_layout.addWidget(zoom_label)
        
        zoom_buttons_layout = QHBoxLayout()
        
        self.zoom_out_btn = QPushButton("−")
        self.zoom_out_btn.setStyleSheet("""
            QPushButton {
                background-color: #52525b; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 16px;
                font-weight: bold;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #71717a;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        
        self.zoom_reset_btn = QPushButton("Reset")
        self.zoom_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #52525b; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #71717a;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setStyleSheet("""
            QPushButton {
                background-color: #52525b; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 16px;
                font-weight: bold;
                min-width: 30px;
            }
            QPushButton:hover {
                background-color: #71717a;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        zoom_buttons_layout.addWidget(self.zoom_out_btn)
        zoom_buttons_layout.addWidget(self.zoom_reset_btn)
        zoom_buttons_layout.addWidget(self.zoom_in_btn)
        zoom_layout.addLayout(zoom_buttons_layout)
        
        # Zoom level display
        self.zoom_level_label = QLabel("Zoom: 1.0x")
        self.zoom_level_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        zoom_layout.addWidget(self.zoom_level_label)
        
        controls_layout.addWidget(zoom_group)
        
        # Focus controls
        focus_group = QWidget()
        focus_layout = QVBoxLayout(focus_group)
        focus_layout.setContentsMargins(10, 5, 10, 5)
        
        focus_label = QLabel("Focus Controls")
        focus_label.setStyleSheet("color: #fafafa; font-weight: bold; font-size: 12px;")
        focus_layout.addWidget(focus_label)
        
        self.auto_focus_btn = QPushButton("Auto Focus")
        self.auto_focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #059669; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.auto_focus_btn.clicked.connect(self.toggle_auto_focus)
        
        self.manual_focus_btn = QPushButton("Manual Focus")
        self.manual_focus_btn.setStyleSheet("""
            QPushButton {
                background-color: #52525b; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #71717a;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.manual_focus_btn.clicked.connect(self.enable_manual_focus)
        
        focus_buttons_layout = QHBoxLayout()
        focus_buttons_layout.addWidget(self.auto_focus_btn)
        focus_buttons_layout.addWidget(self.manual_focus_btn)
        focus_layout.addLayout(focus_buttons_layout)
        
        # Focus distance slider
        self.focus_slider = QSlider(Qt.Horizontal)
        self.focus_slider.setRange(0, 100)
        self.focus_slider.setValue(50)
        self.focus_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #52525b;
                height: 8px;
                background: #27272a;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #38bdf8;
                border: 1px solid #0ea5e9;
                width: 18px;
                margin: -2px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #0ea5e9;
            }
        """)
        self.focus_slider.valueChanged.connect(self.set_focus_distance)
        self.focus_slider.setEnabled(False)
        focus_layout.addWidget(self.focus_slider)
        
        # Focus capability status
        self.focus_status_label = QLabel("Checking focus capabilities...")
        self.focus_status_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        focus_layout.addWidget(self.focus_status_label)
        
        controls_layout.addWidget(focus_group)
        
        # Board detection controls
        detection_group = QWidget()
        detection_layout = QVBoxLayout(detection_group)
        detection_layout.setContentsMargins(10, 5, 10, 5)
        
        detection_label = QLabel("Board Detection")
        detection_label.setStyleSheet("color: #fafafa; font-weight: bold; font-size: 12px;")
        detection_layout.addWidget(detection_label)
        
        self.detect_board_btn = QPushButton("Detect Board")
        self.detect_board_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6d28d9;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.detect_board_btn.clicked.connect(self.detect_board)
        
        self.auto_zoom_btn = QPushButton("Auto Zoom to Board")
        self.auto_zoom_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626; 
                color: white; 
                border: none; 
                padding: 5px 10px; 
                border-radius: 3px; 
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #b91c1c;
            }
            QPushButton:disabled {
                background-color: #3f3f46;
                color: #71717a;
            }
        """)
        self.auto_zoom_btn.clicked.connect(self.auto_zoom_to_board)
        
        detection_layout.addWidget(self.detect_board_btn)
        detection_layout.addWidget(self.auto_zoom_btn)
        
        # Board detection status
        self.board_status_label = QLabel("No board detected")
        self.board_status_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        detection_layout.addWidget(self.board_status_label)
        
        controls_layout.addWidget(detection_group)
        
        # Add stretch to push controls to the left
        controls_layout.addStretch()
        
        camera_layout.addLayout(controls_layout)
        layout.addWidget(camera_container)
    
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
            
            # Check focus capabilities
            self.check_focus_capabilities()
        else:
            # Show error if camera not connected
            self.camera_label.setText("Camera not connected. Please check your webcam.")
            self.capture_front_btn.setEnabled(False)
            self.capture_back_btn.setEnabled(False)
            self.inspect_btn.setEnabled(False)
    
    def check_focus_capabilities(self):
        """Check and update focus control capabilities."""
        if not self.camera_connected:
            return
        
        focus_info = self.camera.get_focus_info()
        autofocus_supported = focus_info.get("autofocus_supported", False)
        focus_supported = focus_info.get("focus_supported", False)
        
        if autofocus_supported or focus_supported:
            if autofocus_supported and focus_supported:
                self.focus_status_label.setText("Focus: Auto/Manual supported")
                self.focus_status_label.setStyleSheet("color: #10b981; font-size: 11px;")
            elif autofocus_supported:
                self.focus_status_label.setText("Focus: Auto only")
                self.focus_status_label.setStyleSheet("color: #f59e0b; font-size: 11px;")
                self.manual_focus_btn.setEnabled(False)
                self.focus_slider.setEnabled(False)
            else:
                self.focus_status_label.setText("Focus: Manual only")
                self.focus_status_label.setStyleSheet("color: #f59e0b; font-size: 11px;")
                self.auto_focus_btn.setEnabled(False)
        else:
            self.focus_status_label.setText("Focus: Not supported by webcam")
            self.focus_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.auto_focus_btn.setEnabled(False)
            self.manual_focus_btn.setEnabled(False)
            self.focus_slider.setEnabled(False)
    
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
                # Update zoom display
                self.update_zoom_display()
                
                # Detect board in frame (optional visualization)
                board_info = self.camera.detect_board(frame)
                display_frame = frame.copy()
                
                # Draw board detection overlay if board is detected
                if board_info:
                    x, y, w, h = board_info["bbox"]
                    confidence = board_info["confidence"]
                    
                    # Draw bounding box
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    
                    # Draw confidence text
                    cv2.putText(display_frame, f"Board: {confidence:.1%}", 
                               (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Update board status label
                    if hasattr(self, 'board_status_label'):
                        self.board_status_label.setText(f"Board detected: {confidence:.1%}")
                        self.board_status_label.setStyleSheet("color: #10b981; font-size: 11px;")
                
                # Convert OpenCV frame to Qt format for display
                height, width, channel = display_frame.shape
                bytes_per_line = 3 * width
                q_image = QImage(display_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
                pixmap = QPixmap.fromImage(q_image)
                
                # Scale image to fit preview area while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.camera_label.setPixmap(scaled_pixmap)
    
    def capture_front(self):
        """Capture front image of the current board with auto-zoom and focus."""
        if self.camera_connected and self.current_board_name:
            # First, try to detect and auto-zoom to the board
            frame = self.camera.get_frame()
            if frame is not None:
                # Detect board and auto-zoom
                board_info = self.camera.detect_board(frame)
                if board_info:
                    # Auto-zoom to the detected board
                    zoomed_frame = self.camera.auto_zoom_to_board(frame)
                    if zoomed_frame is not None:
                        self.update_zoom_display()
                        self.status_label.setText(f"Auto-zoomed to board at {self.camera.get_zoom():.1f}x for front capture")
                        time.sleep(0.5)  # Brief pause to let user see the zoom
                
                # Ensure good focus for capture
                if not self.camera.auto_focus:
                    # Check if camera supports focus control
                    focus_info = self.camera.get_focus_info()
                    if focus_info.get("autofocus_supported", False):
                        # If manual focus, try to optimize it
                        self.camera.set_auto_focus(True)
                        time.sleep(0.3)  # Let autofocus settle
                    else:
                        # Camera doesn't support focus control, skip focus adjustment
                        pass
                
                # Capture enhanced image using camera manager
                frame = self.camera.capture_snapshot("temp_front.jpg")
                if frame is not None:
                    self.front_captured = True
                    self.update_status()
                    
                    # Update UI with success message
                    self.result_label.setText("Front image captured successfully with auto-zoom and focus!")
                    self.result_label.setStyleSheet("""
                        background-color: #18181b; 
                        border: 1px solid #10b981; 
                        border-radius: 5px; 
                        padding: 50px; 
                        color: #10b981;
                        font-size: 16px;
                    """)
                    self.status_label.setText(f"Front captured for '{self.current_board_name}'. Capture back image or save QA sample.")
                else:
                    self.status_label.setText("Failed to capture front image")
            else:
                self.status_label.setText("Failed to get camera frame")
        else:
            if not self.camera_connected:
                self.status_label.setText("Camera not connected")
            else:
                self.status_label.setText("No board selected")
    
    def capture_back(self):
        """Capture back image of the current board with auto-zoom and focus."""
        if self.camera_connected and self.current_board_name:
            # First, try to detect and auto-zoom to the board
            frame = self.camera.get_frame()
            if frame is not None:
                # Detect board and auto-zoom
                board_info = self.camera.detect_board(frame)
                if board_info:
                    # Auto-zoom to the detected board
                    zoomed_frame = self.camera.auto_zoom_to_board(frame)
                    if zoomed_frame is not None:
                        self.update_zoom_display()
                        self.status_label.setText(f"Auto-zoomed to board at {self.camera.get_zoom():.1f}x for back capture")
                        time.sleep(0.5)  # Brief pause to let user see the zoom
                
                # Ensure good focus for capture
                if not self.camera.auto_focus:
                    # Check if camera supports focus control
                    focus_info = self.camera.get_focus_info()
                    if focus_info.get("autofocus_supported", False):
                        # If manual focus, try to optimize it
                        self.camera.set_auto_focus(True)
                        time.sleep(0.3)  # Let autofocus settle
                    else:
                        # Camera doesn't support focus control, skip focus adjustment
                        pass
                
                # Capture enhanced image using camera manager
                frame = self.camera.capture_snapshot("temp_back.jpg")
                if frame is not None:
                    self.back_captured = True
                    self.update_status()
                    
                    # Update UI with success message
                    self.result_label.setText("Back image captured successfully with auto-zoom and focus!")
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
                else:
                    self.status_label.setText("Failed to capture back image")
            else:
                self.status_label.setText("Failed to get camera frame")
        else:
            if not self.camera_connected:
                self.status_label.setText("Camera not connected")
            else:
                self.status_label.setText("No board selected")
    
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
        """Intelligent board inspection with auto-detection and QC sample creation."""
        if not self.camera_connected:
            QMessageBox.warning(self, "Camera Not Connected", "Please connect your webcam to perform inspection.")
            return
        
        # Step 1: Capture current frame and detect board
        current_frame = self.camera.get_frame()
        if current_frame is None:
            QMessageBox.warning(self, "Capture Failed", "Failed to capture current board image.")
            return
        
        # Step 2: Detect board in the frame
        board_info = self.camera.detect_board(current_frame)
        if not board_info:
            QMessageBox.warning(self, "No Board Detected", 
                              "No PCB board detected in the camera view. Please ensure a board is visible and try again.")
            return
        
        # Step 3: Auto-zoom and focus to the detected board
        zoomed_frame = self.camera.auto_zoom_to_board(current_frame)
        if zoomed_frame is not None:
            self.update_zoom_display()
            self.status_label.setText(f"Auto-zoomed to board at {self.camera.get_zoom():.1f}x for inspection")
            time.sleep(0.5)  # Brief pause to let user see the zoom
        
        # Step 4: Ensure good focus for inspection
        if not self.camera.auto_focus:
            # Check if camera supports focus control
            focus_info = self.camera.get_focus_info()
            if focus_info.get("autofocus_supported", False):
                self.camera.set_auto_focus(True)
                time.sleep(0.3)  # Let autofocus settle
            else:
                # Camera doesn't support focus control, skip focus adjustment
                pass
        
        # Step 5: Capture the optimized image for inspection
        inspection_frame = self.camera.capture_snapshot("current_inspection.jpg")
        if inspection_frame is None:
            QMessageBox.warning(self, "Capture Failed", "Failed to capture optimized board image for inspection.")
            return
        
        # Step 6: Try to identify the board type
        board_name = self._identify_board_type(inspection_frame)
        
        if board_name:
            # Board is recognized - proceed with inspection
            self._perform_inspection(board_name, "current_inspection.jpg")
        else:
            # Board is unknown - prompt for QC sample creation
            self._prompt_for_qc_sample_creation(inspection_frame)
    
    def _identify_board_type(self, inspection_frame):
        """Try to identify the board type using computer vision and existing samples."""
        try:
            # Get all existing QA samples
            samples = self.qa_manager.list_qa_samples()
            
            best_match = None
            best_score = 0.0
            
            for sample in samples:
                # Load the reference image
                ref_path = sample["image_paths"]["front"]
                ref_img = cv2.imread(ref_path)
                
                if ref_img is not None:
                    # Align and compare images
                    aligned_img, alignment_info = self.inspector.align_images(ref_img, inspection_frame)
                    if alignment_info.get("success", False):
                        comparison_result = self.inspector.compare_images(ref_img, aligned_img)
                        similarity = comparison_result.get("similarity_score", 0.0)
                        
                        if similarity > best_score and similarity > 0.85:  # 85% similarity threshold
                            best_score = similarity
                            best_match = sample["board_name"]
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Error identifying board type: {e}")
            return None
    
    def _perform_inspection(self, board_name, image_path):
        """Perform inspection for a known board."""
        # Find the QA sample for this board
        samples = self.qa_manager.list_qa_samples()
        sample_id = None
        
        for sample in samples:
            if sample["board_name"] == board_name:
                sample_id = sample["sample_id"]
                break
        
        if not sample_id:
            QMessageBox.warning(self, "QA Sample Not Found", 
                              f"QA sample for '{board_name}' not found. Please create a QA sample first.")
            return
        
        # Update UI to show we're inspecting the detected board
        self.current_board_name = board_name
        self.board_combo.setCurrentText(board_name)
        
        # Show inspection in progress
        self.result_label.setText(f"Inspecting detected board: {board_name}\n\nAnalyzing with AI and computer vision...")
        self.result_label.setStyleSheet("""
            background-color: #18181b; 
            border: 1px solid #f59e0b; 
            border-radius: 5px; 
            padding: 50px; 
            color: #f59e0b;
            font-size: 16px;
        """)
        
        # Disable inspection button during analysis
        self.inspect_btn.setEnabled(False)
        self.inspect_btn.setText("Inspecting...")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Start background inspection
        self.inspection_worker = InspectionWorker(
            image_path,
            sample_id,
            self.qa_manager,
            self.inspector,
            self.ai_analyzer
        )
        
        # Connect signals
        self.inspection_worker.progress_updated.connect(self.update_inspection_progress)
        self.inspection_worker.inspection_complete.connect(self.handle_inspection_complete)
        self.inspection_worker.inspection_error.connect(self.handle_inspection_error)
        
        # Start the inspection
        self.inspection_worker.start()
    
    def _prompt_for_qc_sample_creation(self, inspection_frame):
        """Prompt user to create a QC sample for the unknown board."""
        # Save the current frame for QC sample creation
        cv2.imwrite("temp_front.jpg", inspection_frame)
        
        # Ask user if they want to create a QC sample
        reply = QMessageBox.question(
            self, 
            "Unknown Board Detected", 
            "This board type has not been seen before.\n\n"
            "Would you like to create a QC sample for this board?\n\n"
            "This will capture front and back images to use as a reference for future inspections.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # Prompt for board name
            board_name, ok = QInputDialog.getText(
                self, 
                "New Board QC Sample", 
                "Enter a name for this board type:"
            )
            
            if ok and board_name.strip():
                self.current_board_name = board_name.strip()
                self.front_captured = True
                self.back_captured = False
                
                # Update UI
                self.board_combo.addItem(board_name)
                self.board_combo.setCurrentText(board_name)
                self.update_status()
                
                # Show instructions for back capture
                self.result_label.setText(
                    f"QC Sample Creation Started\n\n"
                    f"Board: {board_name}\n"
                    f"Front image captured ✓\n\n"
                    f"Please flip the board and click 'Capture Back' to complete the QC sample."
                )
                self.result_label.setStyleSheet("""
                    background-color: #18181b; 
                    border: 1px solid #38bdf8; 
                    border-radius: 5px; 
                    padding: 50px; 
                    color: #38bdf8;
                    font-size: 16px;
                """)
                
                self.status_label.setText(f"QC sample creation started for '{board_name}'. Please capture back image.")
                
                # Enable capture back button
                self.capture_back_btn.setEnabled(True)
                
            else:
                # User cancelled - clean up
                self.status_label.setText("QC sample creation cancelled")
                self.result_label.setText("QC sample creation was cancelled.")
        else:
            # User declined - show message
            self.status_label.setText("Inspection cancelled - unknown board type")
            self.result_label.setText(
                "Inspection cancelled.\n\n"
                "To inspect this board type, you need to create a QC sample first.\n"
                "Click 'Inspect Board' again and choose 'Yes' when prompted."
            )
            self.result_label.setStyleSheet("""
                background-color: #18181b; 
                border: 1px solid #ef4444; 
                border-radius: 5px; 
                padding: 50px; 
                color: #ef4444;
                font-size: 16px;
            """)
    
    def update_inspection_progress(self, message):
        """Update the progress display during inspection."""
        self.status_label.setText(f"Inspection: {message}")
    
    def handle_inspection_complete(self, results):
        """Handle completed inspection results."""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Re-enable inspection button
        self.inspect_btn.setEnabled(True)
        self.inspect_btn.setText("Inspect Board")
        
        # Display results
        self.display_inspection_results(results)
        
        # Update status
        self.status_label.setText("Inspection completed successfully!")
    
    def handle_inspection_error(self, error_message):
        """Handle inspection errors."""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Re-enable inspection button
        self.inspect_btn.setEnabled(True)
        self.inspect_btn.setText("Inspect Board")
        
        # Show error message
        self.result_label.setText(f"Inspection failed: {error_message}")
        self.result_label.setStyleSheet("""
            background-color: #18181b; 
            border: 1px solid #ef4444; 
            border-radius: 5px; 
            padding: 50px; 
            color: #ef4444;
            font-size: 16px;
        """)
        
        # Update status
        self.status_label.setText("Inspection failed. Please try again.")
    
    def display_inspection_results(self, results):
        """Display comprehensive inspection results in the UI."""
        try:
            # Extract results
            opencv_results = results.get("opencv_analysis", {})
            ai_results = results.get("ai_analysis", {})
            
            # Build result text
            result_text = f"""
INSPECTION RESULTS
==================
Board: {self.current_board_name}
Timestamp: {results.get('timestamp', 'N/A')}

COMPUTER VISION ANALYSIS:
"""
            
            # OpenCV results
            comparison = opencv_results.get("comparison", {})
            if "similarity_score" in comparison:
                similarity = comparison["similarity_score"]
                result_text += f"Similarity Score: {similarity:.2%}\n"
                
                if similarity >= 0.95:
                    result_text += "Status: PASS (High similarity)\n"
                elif similarity >= 0.85:
                    result_text += "Status: NEEDS REVIEW (Moderate similarity)\n"
                else:
                    result_text += "Status: FAIL (Low similarity)\n"
            
            defects = opencv_results.get("defects", {})
            if defects and "total_defects" in defects:
                result_text += f"Defects Detected: {defects['total_defects']}\n"
                result_text += f"Severity: {defects.get('severity', 'Unknown')}\n"
            
            # AI results
            if ai_results.get("success"):
                ai_analysis = ai_results.get("analysis", {})
                result_text += f"""

AI ANALYSIS:
Overall Quality: {ai_analysis.get('overall_quality', 'Unknown')}
Confidence: {ai_analysis.get('confidence_score', 0):.1%}

Defects Found: {len(ai_analysis.get('defects_found', []))}
Components Identified: {len(ai_analysis.get('components_identified', []))}

COMPARISON NOTES:
{ai_analysis.get('comparison_notes', 'No comparison notes available.')}

DETAILED DEFECTS:
"""
                defects = ai_analysis.get('defects_found', [])
                if defects:
                    for i, defect in enumerate(defects, 1):
                        result_text += f"{i}. {defect.get('type', 'Unknown')} - {defect.get('description', 'No description')}\n"
                else:
                    result_text += "No defects detected by AI.\n"
                
                result_text += "\nRECOMMENDATIONS:\n"
                recommendations = ai_analysis.get('recommendations', [])
                if recommendations:
                    for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
                        result_text += f"{i}. {rec}\n"
                else:
                    result_text += "No specific recommendations from AI.\n"
            else:
                result_text += "\nAI Analysis: Failed or not available\n"
            
            # Update UI
            self.result_label.setText(result_text)
            
            # Set color based on overall result
            if ai_results.get("success"):
                ai_analysis = ai_results.get("analysis", {})
                quality = ai_analysis.get('overall_quality', 'needs_review')
                
                if quality == 'pass':
                    color = "#10b981"  # Green
                elif quality == 'fail':
                    color = "#ef4444"  # Red
                else:
                    color = "#f59e0b"  # Yellow
            else:
                color = "#f59e0b"  # Yellow for needs review
            
            self.result_label.setStyleSheet(f"""
                background-color: #18181b; 
                border: 1px solid {color}; 
                border-radius: 5px; 
                padding: 20px; 
                color: {color};
                font-size: 14px;
                text-align: left;
            """)
            
        except Exception as e:
            self.result_label.setText(f"Error displaying results: {str(e)}")
            self.result_label.setStyleSheet("""
                background-color: #18181b; 
                border: 1px solid #ef4444; 
                border-radius: 5px; 
                padding: 50px; 
                color: #ef4444;
                font-size: 16px;
            """)
    
    def closeEvent(self, event):
        """Handle application shutdown - clean up camera connection."""
        if self.camera_connected:
            self.camera.disconnect()
        
        # Stop any running inspection
        if self.inspection_worker and self.inspection_worker.isRunning():
            self.inspection_worker.terminate()
            self.inspection_worker.wait()
        
        event.accept()

    def prompt_api_key(self):
        api_key, ok = QInputDialog.getText(self, "Set OpenAI API Key", "Enter your OpenAI API key:")
        if ok and api_key:
            save_api_key(api_key)
            self.ai_analyzer.api_key = api_key
            QMessageBox.information(self, "API Key Updated", "OpenAI API key updated successfully.")

    # Camera control methods
    def zoom_in(self):
        """Zoom in the camera view."""
        if self.camera_connected:
            success = self.camera.zoom_in(1.2)
            if success:
                self.update_zoom_display()
                self.status_label.setText(f"Zoomed in to {self.camera.get_zoom():.1f}x")
    
    def zoom_out(self):
        """Zoom out the camera view."""
        if self.camera_connected:
            success = self.camera.zoom_out(1.2)
            if success:
                self.update_zoom_display()
                self.status_label.setText(f"Zoomed out to {self.camera.get_zoom():.1f}x")
    
    def reset_zoom(self):
        """Reset zoom to 1.0x."""
        if self.camera_connected:
            success = self.camera.reset_zoom()
            if success:
                self.update_zoom_display()
                self.status_label.setText("Zoom reset to 1.0x")
    
    def update_zoom_display(self):
        """Update the zoom level display."""
        if hasattr(self, 'zoom_level_label'):
            zoom_level = self.camera.get_zoom()
            self.zoom_level_label.setText(f"Zoom: {zoom_level:.1f}x")
    
    def toggle_auto_focus(self):
        """Toggle between auto focus and manual focus."""
        if self.camera_connected:
            # Check if camera supports focus control
            focus_info = self.camera.get_focus_info()
            
            if not focus_info.get("autofocus_supported", False):
                self.status_label.setText("Your webcam doesn't support focus control")
                return
            
            current_auto = self.camera.auto_focus
            success = self.camera.set_auto_focus(not current_auto)
            if success:
                if self.camera.auto_focus:
                    self.auto_focus_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #059669; 
                            color: white; 
                            border: none; 
                            padding: 5px 10px; 
                            border-radius: 3px; 
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #047857;
                        }
                    """)
                    self.focus_slider.setEnabled(False)
                    self.status_label.setText("Auto focus enabled")
                else:
                    self.auto_focus_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #52525b; 
                            color: white; 
                            border: none; 
                            padding: 5px 10px; 
                            border-radius: 3px; 
                            font-size: 12px;
                        }
                        QPushButton:hover {
                            background-color: #71717a;
                        }
                    """)
                    self.focus_slider.setEnabled(True)
                    self.status_label.setText("Manual focus enabled")
            else:
                self.status_label.setText("Failed to change focus mode")
    
    def enable_manual_focus(self):
        """Enable manual focus mode."""
        if self.camera_connected:
            # Check if camera supports focus control
            focus_info = self.camera.get_focus_info()
            
            if not focus_info.get("focus_supported", False):
                self.status_label.setText("Your webcam doesn't support manual focus")
                return
            
            success = self.camera.set_auto_focus(False)
            if success:
                self.auto_focus_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #52525b; 
                        color: white; 
                        border: none; 
                        padding: 5px 10px; 
                        border-radius: 3px; 
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #71717a;
                    }
                """)
                self.focus_slider.setEnabled(True)
                self.status_label.setText("Manual focus enabled")
            else:
                self.status_label.setText("Failed to enable manual focus")
    
    def set_focus_distance(self, value):
        """Set focus distance from slider value (0-100)."""
        if self.camera_connected and not self.camera.auto_focus:
            # Check if camera supports focus control
            focus_info = self.camera.get_focus_info()
            
            if not focus_info.get("focus_supported", False):
                self.focus_slider.setEnabled(False)
                return
            
            # Convert slider value (0-100) to focus distance (0.0-1.0)
            focus_distance = value / 100.0
            success = self.camera.set_focus(focus_distance)
            if success:
                self.status_label.setText(f"Focus distance set to {focus_distance:.2f}")
            else:
                self.status_label.setText("Failed to set focus distance")
    
    def detect_board(self):
        """Detect PCB board in the current camera frame."""
        if not self.camera_connected:
            self.status_label.setText("Camera not connected")
            return
        
        # Get current frame
        frame = self.camera.get_frame()
        if frame is None:
            self.status_label.setText("Failed to capture frame")
            return
        
        # Detect board
        board_info = self.camera.detect_board(frame)
        if board_info:
            confidence = board_info.get("confidence", 0)
            area = board_info.get("area", 0)
            bbox = board_info.get("bbox", [0, 0, 0, 0])
            
            self.board_status_label.setText(
                f"Board detected! Confidence: {confidence:.1%}, "
                f"Area: {area:.0f}px, Size: {bbox[2]}x{bbox[3]}px"
            )
            self.board_status_label.setStyleSheet("color: #10b981; font-size: 11px;")
            self.status_label.setText(f"Board detected with {confidence:.1%} confidence")
        else:
            self.board_status_label.setText("No board detected")
            self.board_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.status_label.setText("No board detected in current view")
    
    def auto_zoom_to_board(self):
        """Automatically zoom to fit the detected board in the frame."""
        if not self.camera_connected:
            self.status_label.setText("Camera not connected")
            return
        
        # Get current frame
        frame = self.camera.get_frame()
        if frame is None:
            self.status_label.setText("Failed to capture frame")
            return
        
        # Detect and zoom to board
        zoomed_frame = self.camera.auto_zoom_to_board(frame)
        if zoomed_frame is not None:
            self.update_zoom_display()
            self.board_status_label.setText("Auto-zoomed to board")
            self.board_status_label.setStyleSheet("color: #10b981; font-size: 11px;")
            self.status_label.setText(f"Auto-zoomed to board at {self.camera.get_zoom():.1f}x")
        else:
            self.board_status_label.setText("No board found for auto-zoom")
            self.board_status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
            self.status_label.setText("No board detected for auto-zoom")

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 