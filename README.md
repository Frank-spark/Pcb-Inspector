# Spark QA PCB Inspector - Software Specification

## Purpose

This desktop application provides automated visual inspection of PCBs using a standard USB webcam. It uses AI-enhanced computer vision to compare boards to a known good sample (QA sample) and identify component placement and orientation errors.

---

## Goals

* ✅ Capture and save high-quality front and back images of a known-good PCB as a QA reference.
* ✅ Allow boards to be scanned in any orientation or rotation.
* 🔄 Identify missing, rotated, or misplaced components using AI.
* ✅ Provide a modern, intuitive UI with PySide6 + dark theme.
* 🔄 Generate human-readable QA reports describing defects.

---

## Core Features

### ✅ QA Reference Creation (IMPLEMENTED)

* Capture **front** and **back** images of a new PCB.
* Save images and metadata to `qa_samples/` directory.
* Record board name, date, notes, etc.
* **Smart board recognition** - automatically detects existing boards vs new ones.

### 🔄 Inspection Engine (PARTIALLY IMPLEMENTED)

* ✅ Use OpenCV to extract features from incoming webcam feed.
* ✅ Align current scan with the QA sample regardless of rotation.
* 🔄 Compare regions of interest using AI (GPT-4 Vision API).
* 🔄 Detect:
  * Rotated/mirrored components
  * Missing parts
  * Soldering defects

### ✅ User Interface (IMPLEMENTED)

* ✅ Modern dark-mode PySide6 desktop application
* ✅ Live camera preview with webcam integration
* ✅ One-click "Capture Front" / "Capture Back"
* ✅ One-click "Inspect Board" (UI ready, backend pending)
* ✅ Board selection dropdown with smart recognition
* ✅ Result summary with status updates
* ✅ Auto-save QA samples when both images captured

---

## Current Implementation Status

### ✅ Completed Features

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
   - Modern dark-mode desktop application
   - Board selection dropdown
   - Status tracking and visual feedback
   - Responsive button states based on workflow

4. **Board Recognition**
   - Automatic detection of existing boards
   - Smart prompting for new board creation
   - Workflow guidance based on board state

### 🔄 In Progress / Next Steps

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
├── main.py                  # ✅ Launches PySide6 App with full UI
├── camera.py                # ✅ Captures images from webcam
├── inspector.py             # ✅ OpenCV + AI image comparison (backend ready)
├── qa_manager.py            # ✅ Manages QA sample creation/storage
├── openai_api.py            # 🔄 Sends image to GPT-4 Vision (pending)
├── ui/
│   ├── index.html           # ✅ Tailwind UI (alternative web version)
│   └── app.js               # ✅ WebView frontend logic (alternative)
├── qa_samples/              # ✅ Auto-created directory
│   └── sample_001/
│       ├── front.jpg
│       ├── back.jpg
│       └── metadata.json
├── test/                    # 🔄 Test suite (pending)
│   ├── test_alignment.py
│   ├── test_ai_response.py
│   └── test_camera.py
└── requirements.txt         # ✅ Python dependencies
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
git clone <repository-url>
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

### ✅ Functional Tests (IMPLEMENTED)

| Feature             | Test                             | Expected Result                   |
| ------------------- | -------------------------------- | --------------------------------- |
| ✅ QA Sample Capture   | Front/back captured and saved    | Two valid image files, valid JSON |
| ✅ Camera Feed         | Live preview shows webcam        | Real-time video stream in UI      |
| ✅ Board Recognition   | Select existing vs new board     | Correct UI state and workflow     |
| 🔄 Component Detection | Compare known-good to test board | Accurate match or defect found    |
| 🔄 Rotation Handling   | Rotate board 90°, 180°, 270°     | Still passes/fails correctly      |
| 🔄 GPT Analysis        | Send cropped mismatched region   | Returns meaningful description    |

---

### 🔄 Accuracy Tests (PENDING)

| Test Case         | Setup                     | Pass Criteria                      |
| ----------------- | ------------------------- | ---------------------------------- |
| No Defect Board   | Scan a duplicate QA board | 100% match, 0 false positives      |
| Rotated Component | Rotate 1 diode            | GPT detects and describes rotation |
| Missing Component | Remove 1 cap              | GPT detects absence                |
| Misaligned Board  | Place board off-center    | Auto-aligns and inspects correctly |

---

### 🔄 Regression Scripts (PENDING)

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

### ✅ Phase 1: Core Backend (COMPLETED)

1. ✅ `camera.py` – Webcam capture & snapshot
2. ✅ `qa_manager.py` – Save/retrieve QA images + metadata
3. ✅ `inspector.py` – OpenCV alignment + comparison
4. 🔄 `openai_api.py` – GPT-4 Vision request/response

### ✅ Phase 2: UI Integration (COMPLETED)

5. ✅ `main.py` – PySide6 app with full UI
6. ✅ Live preview, capture buttons, inspection trigger
7. ✅ Board selection and management
8. ✅ Status tracking and workflow guidance

### 🔄 Phase 3: AI Diagnostics (IN PROGRESS)

9. 🔄 Integrate `openai_api.py` with mismatched regions
10. 🔄 Display results in UI as AI-inspected overlays
11. 🔄 Generate detailed defect reports

### 🔄 Phase 4: Testing & Polish (PENDING)

12. 🔄 Create `test/` directory and implement test suite
13. 🔄 Evaluate results from rotated boards
14. 🔄 Validate GPT defect output
15. 🔄 Performance optimization and error handling

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

