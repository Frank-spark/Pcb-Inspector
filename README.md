

#  Spark QA PCB Inspector - Software Specification

##  Purpose

This desktop application provides automated visual inspection of PCBs using a standard USB webcam. It uses AI-enhanced computer vision to compare boards to a known good sample (QA sample) and identify component placement and orientation errors.

---

##  Goals

* Capture and save high-quality front and back images of a known-good PCB as a QA reference.
* Allow boards to be scanned in any orientation or rotation.
* Identify missing, rotated, or misplaced components using AI.
* Provide a modern, intuitive UI with QT + Tailwind.
* Generate human-readable QA reports describing defects.

---

##  Core Features

###  QA Reference Creation

* Capture **front** and **back** images of a new PCB.
* Save images and metadata to `qa_samples/` directory.
* Record board name, date, notes, etc.

###  Inspection Engine

* Use OpenCV to extract features from incoming webcam feed.
* Align current scan with the QA sample regardless of rotation.
* Compare regions of interest using AI (GPT-4 Vision API).
* Detect:

  * Rotated/mirrored components
  * Missing parts
  * Soldering defects

###  User Interface

* Tailwind-based frontend inside QT WebView
* Live camera preview
* One-click “Capture Front” / “Capture Back”
* One-click “Inspect Board”
* Result summary with AI-generated defect descriptions
* Save/Export PDF report

---

##  Folder Structure

```bash
pcb_inspector/
├── main.py                  # Launches QT App + WebView
├── camera.py                # Captures images from webcam
├── inspector.py             # OpenCV + AI image comparison
├── qa_manager.py            # Manages QA sample creation/storage
├── openai_api.py            # Sends image to GPT-4 Vision
├── ui/
│   ├── index.html           # Tailwind UI
│   └── app.js               # WebView frontend logic
├── qa_samples/
│   └── sample_001/
│       ├── front.jpg
│       ├── back.jpg
│       └── metadata.json
├── test/
│   ├── test_alignment.py    # Test alignment & rotation correction
│   ├── test_ai_response.py  # Validate GPT-based error detection
│   └── test_camera.py       # Validate webcam functionality
└── requirements.txt         # Python dependencies
```

---

##  Test Schema

###  Functional Tests

| Feature             | Test                             | Expected Result                   |
| ------------------- | -------------------------------- | --------------------------------- |
| QA Sample Capture   | Front/back captured and saved    | Two valid image files, valid JSON |
| Camera Feed         | Live preview shows webcam        | Real-time video stream in UI      |
| Component Detection | Compare known-good to test board | Accurate match or defect found    |
| Rotation Handling   | Rotate board 90°, 180°, 270°     | Still passes/fails correctly      |
| GPT Analysis        | Send cropped mismatched region   | Returns meaningful description    |

---

###  Accuracy Tests

| Test Case         | Setup                     | Pass Criteria                      |
| ----------------- | ------------------------- | ---------------------------------- |
| No Defect Board   | Scan a duplicate QA board | 100% match, 0 false positives      |
| Rotated Component | Rotate 1 diode            | GPT detects and describes rotation |
| Missing Component | Remove 1 cap              | GPT detects absence                |
| Misaligned Board  | Place board off-center    | Auto-aligns and inspects correctly |

---

###  Regression Scripts

* `test/test_alignment.py`: Simulates rotated board positions and checks matching
* `test/test_ai_response.py`: Sends known images of errors and asserts descriptive output
* `test/test_camera.py`: Confirms webcam detection and frame readout

---

###  Dependencies (`requirements.txt`)

```txt
opencv-python
pyside6
flask
python-socketio
requests
numpy
Pillow
```

---

##  Roadmap Step-by-Step

###  Phase 1: Core Backend

1. `camera.py` – Webcam capture & snapshot
2. `qa_manager.py` – Save/retrieve QA images + metadata
3. `inspector.py` – OpenCV alignment + comparison
4. `openai_api.py` – GPT-4 Vision request/response

###  Phase 2: UI Integration

5. `ui/index.html` – Tailwind page
6. `ui/app.js` – Live preview, capture buttons, inspection trigger
7. `main.py` – PySide app loading QT WebView with `/ui/`

###  Phase 3: AI Diagnostics

8. Integrate `openai_api.py` with mismatched regions
9. Display results in UI as AI-inspected overlays

###  Phase 4: Testing

10. Create `test/` directory and implement test suite
11. Evaluate results from rotated boards
12. Validate GPT defect output

