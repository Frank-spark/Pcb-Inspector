# Spark QA PCB Inspector - Software Specification

## Purpose

This desktop application provides automated visual inspection of PCBs using a standard USB webcam. It uses AI-enhanced computer vision to compare boards to a known good sample (QA sample) and identify component placement and orientation errors.

---

## Goals

* [COMPLETED] Capture and save high-quality front and back images of a known-good PCB as a QA reference.
* [COMPLETED] Allow boards to be scanned in any orientation or rotation.
* [COMPLETED] Identify missing, rotated, or misplaced components using AI.
* [COMPLETED] Provide a modern, intuitive UI with PySide6.
* [COMPLETED] Generate human-readable QA reports describing defects.
* [COMPLETED] User-friendly API key management with persistent storage.
* [COMPLETED] **NEW: Advanced camera controls with zoom and focus capabilities.**
* [COMPLETED] **NEW: Automatic board detection and recognition.**
* [COMPLETED] **NEW: Auto-zoom functionality to focus on detected boards.**
* [COMPLETED] **NEW: Intelligent Inspection Workflow (IMPLEMENTED)**

---

## Core Features

### [COMPLETED] QA Reference Creation (IMPLEMENTED)

* Capture **front** and **back** images of a new PCB.
* Save images and metadata to `qa_samples/` directory.
* Record board name, date, notes, etc.
* **Smart board recognition** - automatically detects existing boards vs new ones.

### [COMPLETED] Inspection Engine (FULLY IMPLEMENTED)

* [COMPLETED] Use OpenCV to extract features from incoming webcam feed.
* [COMPLETED] Align current scan with the QA sample regardless of rotation.
* [COMPLETED] Compare regions of interest using AI (GPT-4o Vision).
* [COMPLETED] Detect:
  * Rotated/mirrored components
  * Missing parts
  * Soldering defects
  * Completely different boards

### [COMPLETED] User Interface (IMPLEMENTED)

* [COMPLETED] Modern PySide6 desktop application
* [COMPLETED] Live camera preview with webcam integration
* [COMPLETED] One-click "Capture Front" / "Capture Back"
* [COMPLETED] One-click "Inspect Board" with full AI analysis
* [COMPLETED] Board selection dropdown with smart recognition
* [COMPLETED] Result summary with comprehensive analysis
* [COMPLETED] Auto-save QA samples when both images captured
* [COMPLETED] Real-time progress indicators and visual feedback
* [COMPLETED] Settings menu for API key management
* [COMPLETED] **NEW: Advanced camera controls with zoom, focus, and board detection**

### [COMPLETED] **NEW: Advanced Camera Controls (IMPLEMENTED)**

* [COMPLETED] **Zoom Controls**: Digital zoom from 0.5x to 4.0x with smooth scaling
* [COMPLETED] **Focus Controls**: Toggle between auto-focus and manual focus modes
* [COMPLETED] **Manual Focus**: Adjustable focus distance with slider control
* [COMPLETED] **Board Detection**: Real-time PCB board detection using contour analysis
* [COMPLETED] **Auto-Zoom**: Automatically zoom to fit detected boards in frame
* [COMPLETED] **Visual Feedback**: Real-time board detection overlay with confidence scores
* [COMPLETED] **Enhanced Image Processing**: Improved contrast and edge enhancement for better inspection

### [COMPLETED] **NEW: Intelligent Inspection Workflow (IMPLEMENTED)**

* [COMPLETED] **Auto-Detection**: Automatically detects PCB boards in camera view
* [COMPLETED] **Auto-Zoom & Focus**: Automatically optimizes camera settings for capture
* [COMPLETED] **Board Recognition**: Identifies known board types from existing QC samples
* [COMPLETED] **QC Sample Creation**: Prompts to create QC samples for unknown boards
* [COMPLETED] **Seamless Workflow**: One-click inspection with intelligent automation
* [COMPLETED] **Smart Capture**: Auto-zoom and focus when capturing front/back images

---

## Current Implementation Status

### [COMPLETED] Completed Features

1. **Camera Integration**
   - Live webcam preview at 33 FPS
   - Image enhancement for better PCB inspection
   - Automatic camera detection and connection
   - **NEW: Advanced zoom controls (0.5x - 4.0x)**
   - **NEW: Focus controls (auto/manual with slider)**
   - **NEW: Real-time board detection with visual overlay**
   - **NEW: Intelligent auto-zoom and focus for optimal capture**

2. **QA Sample Management**
   - Create and store QA samples with metadata
   - Board database with automatic recognition
   - Front/back image capture and storage
   - Sample validation and error handling
   - **NEW: Automatic QC sample creation for unknown boards**

3. **User Interface**
   - Modern desktop application with dark theme
   - Board selection dropdown
   - Status tracking and visual feedback
   - Responsive button states based on workflow
   - Progress indicators during inspection
   - Settings menu for API key management
   - **NEW: Camera control panel with zoom, focus, and detection buttons**
   - **NEW: Real-time zoom level display**
   - **NEW: Board detection status indicators**
   - **NEW: Intelligent workflow prompts and guidance**

4. **Board Recognition**
   - Automatic detection of existing boards
   - Smart prompting for new board creation
   - Workflow guidance based on board state
   - **NEW: Real-time board detection using computer vision**
   - **NEW: Confidence scoring for board detection**
   - **NEW: Auto-zoom functionality to frame detected boards**
   - **NEW: Automatic board type identification from existing samples**

5. **AI Integration**
   - OpenAI GPT-4o Vision API integration
   - Image analysis and defect detection
   - Component identification
   - Structured JSON response parsing
   - Background processing for non-blocking UI
   - **Enhanced comparison logic** for detecting different boards
   - **Detailed comparison notes** in results

6. **Inspection Engine**
   - Combined OpenCV + AI analysis
   - Real-time image alignment and comparison
   - Defect detection and severity assessment
   - Comprehensive result reporting
   - Color-coded quality indicators
   - **Improved defect detection** for missing components and layout differences
   - **NEW: Intelligent inspection workflow with auto-detection**

7. **API Key Management**
   - User-friendly dialog for API key entry
   - Persistent storage in config file
   - Settings menu for key updates
   - Secure handling without environment variables

8. **NEW: Advanced Camera Features**
   - **Digital Zoom**: Software-based zoom with high-quality interpolation
   - **Focus Control**: Hardware and software focus management
   - **Board Detection**: Contour-based PCB detection with confidence scoring
   - **Auto-Zoom**: Intelligent zoom adjustment to frame detected boards
   - **Enhanced Processing**: Improved image quality for better inspection results

9. **NEW: Intelligent Workflow**
   - **One-Click Inspection**: Automatically detects, zooms, and inspects boards
   - **Smart Board Recognition**: Identifies known boards from existing samples
   - **QC Sample Creation**: Seamless workflow for unknown board types
   - **Auto-Optimization**: Automatic camera settings for best results
   - **User Guidance**: Clear prompts and instructions throughout the process

### [PENDING] Future Enhancements

1. **Report Generation**
   - PDF export functionality
   - Detailed inspection reports with images
   - Defect visualization overlays

2. **Advanced Features**
   - Batch processing for multiple boards
   - Component counting and verification
   - Solder joint analysis
   - Custom defect classification
   - **Hardware zoom support for compatible cameras**
   - **Advanced board tracking and stabilization**

---

## Folder Structure

```bash
pcb_inspector/
├── main.py                  # [COMPLETED] Launches PySide6 App with full UI + AI integration
├── camera.py                # [COMPLETED] Captures images from webcam + NEW zoom/focus controls
├── inspector.py             # [COMPLETED] OpenCV + AI image comparison
├── qa_manager.py            # [COMPLETED] Manages QA sample creation/storage
├── openai_api.py            # [COMPLETED] Sends image to GPT-4o Vision
├── test_camera_controls.py  # [NEW] Test script for camera features
├── ui/
│   ├── index.html           # [COMPLETED] Tailwind UI (alternative web version)
│   └── app.js               # [COMPLETED] WebView frontend logic (alternative)
├── qa_samples/              # [COMPLETED] Auto-created directory
│   └── sample_001/
│       ├── front.jpg
│       ├── back.jpg
│       └── metadata.json
├── test/                    # [PENDING] Test suite
│   ├── test_alignment.py
│   ├── test_ai_response.py
│   └── test_camera.py
└── requirements.txt         # [COMPLETED] Python dependencies
```

---

## Installation & Usage

### Prerequisites
- Python 3.7-3.11 (PySide6 compatibility)
- USB webcam
- Windows/Linux/macOS
- OpenAI API key (for AI-powered inspection)

### Installation
```bash
# Clone the repository
git clone https://github.com/Frank-spark/Pcb-Inspector
cd pcb_inspector

# Install dependencies
pip install -r requirements.txt
```

### OpenAI API Setup

To enable AI-powered PCB inspection, you need to set up your OpenAI API key:

1. **Get an API Key**
   - Sign up or log in at https://platform.openai.com/
   - Navigate to "API Keys" section
   - Create a new API key

2. **Enter API Key in the Application**
   - On first launch, the app will prompt you to enter your OpenAI API key.
   - You can update the key anytime from the "Settings" menu in the app.
   - The key is securely saved in a config file in your home directory (e.g., `~/.pcb_inspector_config.json`).

3. **Test the Setup**
   - Launch the app and ensure AI-powered inspection features are available.

**Note:** Keep your API key secure and never commit it to version control.

### Running the Application
```bash
python main.py
```

### Testing Camera Controls
```bash
# Test the new camera features
python test_camera_controls.py

# Test the intelligent inspection workflow
python test_intelligent_inspection.py
```

### Usage Workflow

#### **NEW: Intelligent One-Click Inspection (Recommended)**
1. **Place PCB in camera view**
2. **Click "Inspect Board"** - The system will:
   - Automatically detect the board
   - Auto-zoom and focus for optimal capture
   - Identify if it's a known board type
   - If known: Perform full inspection immediately
   - If unknown: Prompt to create QC sample

#### **Traditional Manual Workflow**
1. **First Time Setup**
   - Launch application
   - Enter your OpenAI API key when prompted
   - Click "New Board" and enter board name
   - **Use zoom and focus controls to get optimal view**
   - **Use "Detect Board" to verify board is properly framed**
   - **Use "Auto Zoom to Board" for automatic framing**
   - Capture front image using "Capture Front" (now with auto-zoom/focus)
   - Capture back image using "Capture Back" (now with auto-zoom/focus)
   - QA sample automatically saved

2. **Regular Inspection**
   - Select existing board from dropdown
   - **Adjust camera settings for optimal inspection**
   - **Use board detection to ensure proper alignment**
   - Click "Inspect Board" to compare against QA sample

#### **NEW: QC Sample Creation Workflow**
When an unknown board is detected during inspection:
1. **System prompts**: "Unknown board detected. Create QC sample?"
2. **User confirms**: Enter board name when prompted
3. **Auto-capture**: Front image automatically captured with optimal settings
4. **Flip board**: User flips board to back side
5. **Auto-capture**: Back image automatically captured with optimal settings
6. **QC sample saved**: Ready for future inspections

### NEW: Camera Control Features

#### Zoom Controls
- **Zoom In (+)**: Increase zoom level by 20%
- **Zoom Out (−)**: Decrease zoom level by 20%
- **Reset Zoom**: Return to 1.0x zoom level
- **Zoom Range**: 0.5x to 4.0x with smooth scaling

#### Focus Controls
- **Auto Focus**: Enable automatic focus (recommended for most cases)
- **Manual Focus**: Enable manual focus control
- **Focus Slider**: Adjust focus distance when in manual mode (0-100%)

#### Board Detection
- **Detect Board**: Manually trigger board detection in current frame
- **Auto Zoom to Board**: Automatically zoom to frame detected board
- **Real-time Detection**: Continuous board detection with visual overlay
- **Confidence Scoring**: Shows detection confidence percentage

#### Intelligent Workflow
- **One-Click Inspection**: Automatically handles detection, zoom, focus, and inspection
- **Smart Recognition**: Identifies known boards from existing QC samples
- **QC Sample Creation**: Seamless workflow for unknown board types
- **Auto-Optimization**: Automatic camera settings for best results

#### Tips for Best Results
1. **Good Lighting**: Ensure adequate lighting for clear board visibility
2. **Stable Camera**: Keep camera steady during capture
3. **Proper Distance**: Position camera 10-20cm from board surface
4. **Use Auto-Zoom**: Let the system automatically frame your board
5. **Check Detection**: Verify board is detected before capturing images
6. **Trust the System**: Use "Inspect Board" for the most intelligent workflow

---

## Test Schema

### [COMPLETED] Functional Tests (IMPLEMENTED)

| Feature             | Test                             | Expected Result                   |
| ------------------- | -------------------------------- | --------------------------------- |
| [COMPLETED] QA Sample Capture   | Front/back captured and saved    | Two valid image files, valid JSON |
| [COMPLETED] Camera Feed         | Live preview shows webcam        | Real-time video stream in UI      |
| [COMPLETED] Board Recognition   | Select existing vs new board     | Correct UI state and workflow     |
| [COMPLETED] OpenAI API Integration | Send image to GPT-4o Vision     | Returns structured analysis       |
| [COMPLETED] Inspection Workflow | Complete inspection process      | Full analysis with results display |
| [COMPLETED] Background Processing | Non-blocking UI during analysis | Responsive interface during AI calls |
| [COMPLETED] API Key Management  | Enter and update API key via UI  | Persistent storage and loading    |
| [COMPLETED] Different Board Detection | Show completely different board | AI correctly marks as "FAIL"      |

---

### [PENDING] Accuracy Tests (PENDING)

| Test Case         | Setup                     | Pass Criteria                      |
| ----------------- | ------------------------- | ---------------------------------- |
| No Defect Board   | Scan a duplicate QA board | 100% match, 0 false positives      |
| Rotated Component | Rotate 1 diode            | GPT detects and describes rotation |
| Missing Component | Remove 1 cap              | GPT detects absence                |
| Misaligned Board  | Place board off-center    | Auto-aligns and inspects correctly |
| Different Board   | Show completely different board | AI marks as "FAIL" with explanation |

---

### [PENDING] Regression Scripts (PENDING)

* `test/test_alignment.py`: Simulates rotated board positions and checks matching
* `test/test_ai_response.py`: Sends known images of errors and asserts descriptive output
* `test/test_camera.py`: Confirms webcam detection and frame readout

---

## Dependencies (`requirements.txt`)

```txt
opencv-python==4.8.1.78
pyside6==6.6.0
flask==3.0.0
python-socketio==5.10.0
requests==2.31.0
numpy==1.24.3
Pillow==10.0.1
openai==1.3.0
scikit-image==0.21.0
```

---

## Development Roadmap

### [COMPLETED] Phase 1: Core Backend (COMPLETED)

1. [COMPLETED] `camera.py` – Webcam capture & snapshot
2. [COMPLETED] `qa_manager.py` – Save/retrieve QA images + metadata
3. [COMPLETED] `inspector.py` – OpenCV alignment + comparison
4. [COMPLETED] `openai_api.py` – GPT-4o Vision request/response

### [COMPLETED] Phase 2: UI Integration (COMPLETED)

5. [COMPLETED] `main.py` – PySide6 app with full UI
6. [COMPLETED] Live preview, capture buttons, inspection trigger
7. [COMPLETED] Board selection and management
8. [COMPLETED] Status tracking and workflow guidance

### [COMPLETED] Phase 3: AI Diagnostics (COMPLETED)

9. [COMPLETED] Integrate `openai_api.py` with mismatched regions
10. [COMPLETED] Display results in UI as AI-inspected overlays
11. [COMPLETED] Generate detailed defect reports
12. [COMPLETED] Enhanced comparison logic for different boards

### [COMPLETED] Phase 4: User Experience (COMPLETED)

13. [COMPLETED] API key management via UI
14. [COMPLETED] Persistent configuration storage
15. [COMPLETED] Settings menu for key updates
16. [COMPLETED] Improved error handling and user feedback

### [PENDING] Phase 5: Testing & Polish (PENDING)

17. [PENDING] Create `test/` directory and implement test suite
18. [PENDING] Evaluate results from rotated boards
19. [PENDING] Validate GPT defect output
20. [PENDING] Performance optimization and error handling

---

## Technical Notes

### AI Model Information
- **Current Model**: GPT-4o (updated from deprecated gpt-4-vision-preview)
- **Vision Capabilities**: Full image analysis and defect detection
- **Response Format**: Structured JSON with defect details and recommendations
- **Processing**: Background threads for non-blocking UI
- **Comparison Logic**: Enhanced prompts for detecting different boards

### Performance Features
- **Real-time camera preview** at 33 FPS
- **Background AI analysis** to maintain UI responsiveness
- **Combined OpenCV + AI** for comprehensive inspection
- **Progress indicators** during analysis
- **Error handling** for network and API issues
- **Persistent API key storage** for seamless user experience

### Recent Improvements
- **User-friendly API key entry** via dialog instead of environment variables
- **Enhanced AI comparison logic** for better detection of different boards
- **Detailed comparison notes** in inspection results
- **Settings menu** for API key management
- **Improved error handling** and user feedback
- **Added scikit-image dependency** for better image processing

---

## Contributing

This project is actively developed. Key areas for contribution:

1. **Testing**: Create comprehensive test suite
2. **Performance**: Optimize image processing and comparison
3. **UI Enhancements**: Add advanced features and visualizations
4. **Documentation**: Improve user guides and examples

---

## License

See `License.md` for project licensing information.

