# Recycling Robot

## About

The Recycling Robot is an autonomous sorting system built on the **mBot2** platform. Its goal is to identify recyclable items by material type and physically move each item to the correct designated zone — eliminating the need for manual sorting.

A **webcam** mounted at the sorting station inspects each item placed on the detection area. Using computer vision, the system analyses the colour and appearance of the item to classify its material (e.g. plastic, paper, metal). Once a material is identified, the classification is sent to the mBot2, which follows a **colour-coded line track** to navigate to the matching recycling bin zone and deposits the item there.

### How It Works

1. **Detection** — A coloured cube (representing a recyclable item) is placed inside a yellow A4 marker sheet in view of the webcam.
2. **Classification** — The host PC script detects the yellow boundary, isolates the item inside, and classifies its colour/material using HSV colour analysis. A YOLOv8 model provides an additional layer of object recognition.
3. **Decision** — The detected material type is mapped to a target drop-off zone on the track.
4. **Navigation** — The mBot2 follows the black line track, reading colour markers at junctions to determine when to turn or stop at the correct zone.
5. **Sorting** — The robot deposits the item in the appropriate recycling area and returns to the start for the next item.

### Material Categories

| Cube Colour | Recycling Category |
|-------------|-------------------|
| Blue | Plastic |
| Green | Glass |
| Red | Metal / Aluminium |
| Purple | Paper / Cardboard |
| Yellow | General Waste |

---

An mBot2-based robot system that follows a line track and detects coloured cubes using computer vision. The project combines on-robot firmware (MicroPython via CyberPi) with off-robot Python scripts running on a host PC.

---

## Project Structure

```
recycling-robot/
├── mBot Code/
│   ├── mbot2_line_follower_3.py   # Line follower v3 – grayscale only, U-turns on white
│   ├── mbot2_line_follower_4.py   # Line follower v4 – adds colour-marker support
│   └── cube_color_detector.py     # Webcam colour classifier for coloured cubes
├── mbot2_detection/
│   ├── detect.py                  # YOLOv8 real-time mBot2 detector (host PC)
│   └── mbot-detection.v2i.yolov8/ # Roboflow dataset (466 images, YOLOv8 format)
├── main.py                        # HSV-based multi-colour bounding-box demo
├── map.jpg / map3.jpg             # Track layout images
└── cheatsheet/
    └── mb10132_python_instruction_manual.pdf
```

---

## Components

### 1. Line Follower (mBot2 firmware)

Runs directly on the mBot2 via CyberPi. Uses the quad RGB sensor (L1 / R1 probes) to follow a black line. When both sensors see white (end of line), the robot performs a 180-degree U-turn and continues.

| File | Description |
|------|-------------|
| [mbot2_line_follower_3.py](mBot%20Code/mbot2_line_follower_3.py) | Grayscale threshold only. Struggles with yellow (reads as white). |
| [mbot2_line_follower_4.py](mBot%20Code/mbot2_line_follower_4.py) | Adds colour detection so yellow, purple, green, red, and blue markers are treated as "on-line". |

**Controls:** Press **A** to start, press **A** again to stop.

**Tunable constants:**

```python
SPEED      = 30   # Drive speed (0–100)
TURN_SPEED = 30   # U-turn speed
BLACK      = 50   # Grayscale threshold (below = on line)
```

---

### 2. Cube Colour Detector (host PC)

[mBot Code/cube_color_detector.py](mBot%20Code/cube_color_detector.py)

Detects the colour of a cube placed inside a **yellow A4 sheet** in front of a webcam.

**Pipeline:**
1. Capture webcam frames.
2. Detect the yellow A4 border via HSV thresholding.
3. Find the largest yellow quadrilateral and approximate its 4 corners.
4. Perspective-warp the quad to a flat top-down 420×594 px view (A4 ratio).
5. Mask out the yellow border and white paper background inside the warp.
6. Find the largest remaining blob — assumed to be the cube.
7. Classify the cube's mean HSV colour and display the result on both the webcam feed and the warped view.

**Detected colours:** Red, Orange, Yellow, Green, Cyan, Blue, Purple, Pink, Black, White, Gray

Press **q** to quit.

---

### 3. mBot2 Object Detector (host PC)

[mbot2_detection/detect.py](mbot2_detection/detect.py)

Real-time YOLOv8 detector that identifies the mBot2 robot in a webcam feed. Uses a custom-trained model.

**Model path (relative):** `../runs/detect/mbot2_detector3/weights/best.pt`

The training dataset was built with Roboflow:
- 466 images annotated in YOLOv8 format
- Augmentations: horizontal/vertical flip, ±20° rotation, ±25% brightness, Gaussian blur

Press **q** to quit.

---

### 4. Multi-Colour Bounding Box Demo (host PC)

[main.py](main.py)

Simple HSV-thresholding demo that draws labelled bounding boxes around red, blue, purple, and green objects in a live webcam feed. Useful for quick colour-tuning experiments.

Press **q** to quit.

---

## Requirements

### Host PC

```
opencv-python
numpy
Pillow
ultralytics
```

Install with:

```bash
pip install opencv-python numpy Pillow ultralytics
```

### mBot2 Firmware

The line follower scripts run on the mBot2's CyberPi using the `cyberpi` MicroPython library. Upload via the [mBlock IDE](https://ide.mblock.cc/).

---

## Hardware

- **mBot2** (Makeblock) with quad RGB sensor
- Webcam (for host-PC scripts)
- Yellow A4 sheet (used as a fiducial marker for the cube colour detector)
- Coloured cubes for classification
- Black-line track with colour markers
