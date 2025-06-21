# Spark QA PCB Inspector - Software Specification

## Purpose

This desktop application provides automated visual inspection of PCBs using a standard USB webcam. It uses AI-enhanced computer vision to compare boards to a known good sample (QA sample) and identify component placement and orientation errors.

---

## Goals

* [COMPLETED] Capture and save high-quality front and back images of a known-good PCB as a QA reference.
* [COMPLETED] Allow boards to be scanned in any orientation or rotation.
* [IN PROGRESS] Identify missing, rotated, or misplaced components using AI.
* [COMPLETED] Provide a modern, intuitive UI with PySide6.
* [IN PROGRESS] Generate human-readable QA reports describing defects.

---

## Core Features

### [COMPLETED] QA Reference Creation (IMPLEMENTED)

* Capture **front** and **back** images of a new PCB.
* Save images and metadata to `qa_samples/` directory.
* Record board name, date, notes, etc.
* **Smart board recognition** - automatically detects existing boards vs new ones.

### [IN PROGRESS] Inspection Engine (PARTIALLY IMPLEMENTED)

* [COMPLETED] Use OpenCV to extract features from incoming webcam feed.
* [COMPLETED] Align current scan with the QA sample regardless of rotation.
* [IN PROGRESS] Compare regions of interest using AI (GPT-4 Vision API).
* [IN PROGRESS] Detect:
  * Rotated/mirrored components
  * Missing parts
  * Soldering defects

### [COMPLETED] User Interface (IMPLEMENTED)

* [COMPLETED] Modern PySide6 desktop application
* [COMPLETED] Live camera preview with webcam integration
* [COMPLETED] One-click "Capture Front" / "Capture Back"
* [COMPLETED] One-click "Inspect Board" (UI ready, backend pending)
* [COMPLETED] Board selection dropdown with smart recognition
* [COMPLETED] Result summary with status updates
* [COMPLETED] Auto-save QA samples when both images captured

---

## Current Implementation Status

### [COMPLETED] Completed Features

1. **Camera Integration**
   - Live webcam preview at 33 FPS
   - Image enhancement for better PCB inspection
   - Automatic camera detection and connection

2. **QA Sample Management**
   - Create and store QA samples with metadata
   - Board database with automatic recognition
   - Front/back image capture and storage
   - Sample validation and error handling

3. **User Interface**
   - Modern desktop application
   - Board selection dropdown
   - Status tracking and visual feedback
   - Responsive button states based on workflow

4. **Board Recognition**
   - Automatic detection of existing boards
   - Smart prompting for new board creation
   - Workflow guidance based on board state

### [IN PROGRESS] In Progress / Next Steps

1. **Inspection Engine Integration**
   - Connect inspector.py to UI
   - Implement actual image comparison
   - Add defect detection and reporting

2. **AI Integration**
   - GPT-4 Vision API integration
   - Defect description generation
   - Enhanced component detection

3. **Report Generation**
   - PDF export functionality
   - Detailed inspection reports
   - Defect visualization

---

## Folder Structure

```bash
pcb_inspector/
├── main.py                  # [COMPLETED] Launches PySide6 App with full UI
├── camera.py                # [COMPLETED] Captures images from webcam
├── inspector.py             # [COMPLETED] OpenCV + AI image comparison (backend ready)
├── qa_manager.py            # [COMPLETED] Manages QA sample creation/storage
├── openai_api.py            # [PENDING] Sends image to GPT-4 Vision
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

### Installation
```bash
# Clone the repository
git clone https://github.com/Frank-spark/Pcb-Inspector
cd pcb_inspector

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
python main.py
```

### Usage Workflow

1. **First Time Setup**
   - Launch application
   - Click "New Board" and enter board name
   - Capture front image using "Capture Front"
   - Capture back image using "Capture Back"
   - QA sample automatically saved

2. **Regular Inspection**
   - Select existing board from dropdown
   - Click "Inspect Board" to compare against QA sample
   - Review results and recommendations

3. **Board Management**
   - All boards stored in `qa_samples/` directory
   - Automatic board recognition on startup
   - Easy switching between different board types

---

## Test Schema

### [COMPLETED] Functional Tests (IMPLEMENTED)

| Feature             | Test                             | Expected Result                   |
| ------------------- | -------------------------------- | --------------------------------- |
| [COMPLETED] QA Sample Capture   | Front/back captured and saved    | Two valid image files, valid JSON |
| [COMPLETED] Camera Feed         | Live preview shows webcam        | Real-time video stream in UI      |
| [COMPLETED] Board Recognition   | Select existing vs new board     | Correct UI state and workflow     |
| [IN PROGRESS] Component Detection | Compare known-good to test board | Accurate match or defect found    |
| [IN PROGRESS] Rotation Handling   | Rotate board 90°, 180°, 270°     | Still passes/fails correctly      |
| [IN PROGRESS] GPT Analysis        | Send cropped mismatched region   | Returns meaningful description    |

---

### [PENDING] Accuracy Tests (PENDING)

| Test Case         | Setup                     | Pass Criteria                      |
| ----------------- | ------------------------- | ---------------------------------- |
| No Defect Board   | Scan a duplicate QA board | 100% match, 0 false positives      |
| Rotated Component | Rotate 1 diode            | GPT detects and describes rotation |
| Missing Component | Remove 1 cap              | GPT detects absence                |
| Misaligned Board  | Place board off-center    | Auto-aligns and inspects correctly |

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
```

---

## Development Roadmap

### [COMPLETED] Phase 1: Core Backend (COMPLETED)

1. [COMPLETED] `camera.py` – Webcam capture & snapshot
2. [COMPLETED] `qa_manager.py` – Save/retrieve QA images + metadata
3. [COMPLETED] `inspector.py` – OpenCV alignment + comparison
4. [IN PROGRESS] `openai_api.py` – GPT-4 Vision request/response

### [COMPLETED] Phase 2: UI Integration (COMPLETED)

5. [COMPLETED] `main.py` – PySide6 app with full UI
6. [COMPLETED] Live preview, capture buttons, inspection trigger
7. [COMPLETED] Board selection and management
8. [COMPLETED] Status tracking and workflow guidance

### [IN PROGRESS] Phase 3: AI Diagnostics (IN PROGRESS)

9. [IN PROGRESS] Integrate `openai_api.py` with mismatched regions
10. [IN PROGRESS] Display results in UI as AI-inspected overlays
11. [IN PROGRESS] Generate detailed defect reports

### [PENDING] Phase 4: Testing & Polish (PENDING)

12. [PENDING] Create `test/` directory and implement test suite
13. [PENDING] Evaluate results from rotated boards
14. [PENDING] Validate GPT defect output
15. [PENDING] Performance optimization and error handling

---

## Contributing

This project is actively developed. Key areas for contribution:

1. **AI Integration**: Implement GPT-4 Vision API for defect detection
2. **Testing**: Create comprehensive test suite
3. **Performance**: Optimize image processing and comparison
4. **UI Enhancements**: Add advanced features and visualizations

---

## License

See `License.md` for project licensing information.

