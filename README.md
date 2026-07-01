# SORT E-BIN -- AI-Powered Smart Waste Sorting Bin

> B.E. Capstone Project - Computer Engineering - Thapar Institute of Engineering and Technology - December 2025

---

## Overview

SORT E-BIN is an intelligent waste segregation system that combines deep learning-based image classification with IoT-enabled hardware to automate waste sorting at source. Built and demonstrated as a working hardware prototype at TIET Patiala.

**Problem:** Improper waste segregation at source is one of the largest barriers to effective recycling. Manual sorting is inconsistent and unscalable.

**Solution:** A smart bin that uses a Pi Camera and an InceptionResNetV2 CNN to classify waste in real time, then physically routes it to the correct compartment via a servo-actuated disc mechanism -- fully automated, no human intervention required.

---

## System Architecture

```
+------------------+     +--------------------------------------------+
|  IR Sensor       |---->|  Raspberry Pi 4B (BCM4)                    |
|  (waste detect)  |     |                                            |
+------------------+     |  +--------------------------------------+  |
                         |  |  InceptionResNetV2 (TensorFlow/Keras)|  |
+------------------+     |  |  model.keras -- 256x256 input        |  |
|  Pi Camera       |---->|  |  4 classes | threshold 0.7          |  |
|  (image capture) |     |  +--------------------------------------+  |
+------------------+     |           |                                |
                         |      Category + confidence                 |
                         +-----------+---------------------------------+
                                     |
                          +----------v----------+
                          |  Disc Rotation      |
                          |  Servo (BCM 17)     |
                          |  Others:    0 deg   |
                          |  Plastic:  90 deg   |
                          |  Wet Waste: 180 deg |
                          |  Paper:    270 deg  |
                          +----------+----------+
                                     |
                          +----------v----------+
                          |  Disc Tilt Servo    |
                          |  (BCM 27)           |
                          |  Tilts -> waste     |
                          |  drops into bin     |
                          +---------------------+
```

---

## Hardware

| Component                | Specification            | Role                                          |
|--------------------------|--------------------------|-----------------------------------------------|
| Raspberry Pi 4 Model B   | 4 GB RAM                 | Central compute and GPIO controller           |
| Pi Camera Module         | 640 x 480                | Waste image capture                           |
| IR Sensor                | Digital out (BCM 4)      | Detects waste placement on disc               |
| Servo Motor -- Rotation  | MG996R / SG90, BCM 17   | Rotates disc to correct bin angle             |
| Servo Motor -- Tilt      | SG90, BCM 27             | Tilts disc to drop waste into bin             |
| Power Supply             | 5 V / 3 A                | System power                                  |

---

## Software Stack

| Layer              | Technology                                                          |
|--------------------|---------------------------------------------------------------------|
| AI Classification  | Python 3.9, TensorFlow 2.x / Keras, InceptionResNetV2 (.keras)     |
| Image Preprocessing| OpenCV -- BGR to RGB, resize 256x256, normalise [0, 1]             |
| Hardware Control   | RPi.GPIO -- servo PWM, IR sensor input                              |
| Dataset            | TrashNet + custom campus waste images (augmented)                   |

---

## AI Model

**Architecture:** InceptionResNetV2 with ImageNet pre-trained weights
**Transfer learning:** Base frozen, last 50 layers fine-tuned
**Custom head:** Global Average Pooling -> Dropout (0.5) -> Dense (128, ReLU) -> Softmax (4 classes)
**Training:** Adam optimiser | EarlyStopping, ReduceLROnPlateau, ModelCheckpoint callbacks
**Validation accuracy:** ~84%
**Confidence threshold:** 0.7 (items below threshold are routed to *Others*)
**Export format:** `.keras` (TensorFlow SavedModel format)

---

## Waste Categories & Disc Angles

| Category   | Disc Angle | Notes                                        |
|------------|-----------|----------------------------------------------|
| Others     | 0 deg     | Default / low-confidence fallback            |
| Plastic    | 90 deg    |                                              |
| Wet Waste  | 180 deg   |                                              |
| Paper      | 270 deg   |                                              |

---

## Repository Structure

```
sortebin/
+-- main.py                  # Full system control loop (Pi Camera + InceptionResNetV2 + servos)
+-- requirements.txt         # Python dependencies
+-- CAPSTONE_CPG287.pdf      # Full project report (TIET, December 2025)
+-- README.md
```

> **Model weights:** `model.keras` is not committed to this repo due to file size.
> Contact the team for the trained model file.

---

## Quick Start

```bash
# On Raspberry Pi 4B -- Python 3.9+
pip install -r requirements.txt

# Place model.keras at /home/pi/sortebin/model.keras
# Connect Pi Camera, IR sensor (BCM4), rotation servo (BCM17), tilt servo (BCM27)

python main.py
```

---

## Team

| Roll No.   | Name          | Role                                                                               |
|------------|---------------|------------------------------------------------------------------------------------|
| 102203548  | Tanya         | ML model training, dataset collection and augmentation                             |
| 102203604  | Smriti Singh  | Model evaluation, performance benchmarking (MobileNet / VGG-19 / AlexNet comparison) |
| 102203631  | Rajvir Singh  | Hardware integration, GPIO wiring, servo calibration, system deployment, live demo |
| 102203652  | Shreya Singh  | System architecture, report documentation                                          |

**Mentors:** Dr. Ravneet Kaur (Assistant Professor-I) - Dr. Harcharan Jit Singh (System Manager IT), CSED, TIET Patiala

---

## License

Academic project -- Thapar Institute of Engineering and Technology, Patiala, 2025.
