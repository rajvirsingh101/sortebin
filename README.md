# SORT E-BIN — AI-Powered Smart Waste Sorting Bin

> B.E. Capstone Project · Computer Engineering · Thapar Institute of Engineering and Technology · December 2025

---

## Overview

SORT E-BIN is a fully integrated, intelligent waste segregation system that combines AI-based image classification, IoT-enabled monitoring, and servo-actuated physical sorting. Built and deployed as a working hardware prototype on campus.

**The problem:** Improper waste segregation at source is one of the largest barriers to effective recycling. Manual sorting is inconsistent and costly at scale.

**The solution:** A smart bin that classifies waste in real time using a camera and AI model, then automatically directs it to the correct compartment — with no human intervention.

---

## System Architecture

```
┌──────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────────┐
│  USB Camera      │────▶│  Waste Classifier            │────▶│  Selection Servo (BCM 17)│
│  (640 × 480)     │     │  TFLite (Teachable Machine)  │     │  Plastic: 160°           │
└──────────────────┘     │  + HSV colour analysis       │     │  Metal:    20°           │
                         │  Categories:                 │     │  Paper:    90°           │
                         │  Plastic / Metal / Paper /   │     └──────────────────────────┘
                         │  No Waste                    │                  │
                         └──────────────────────────────┘                  ▼
                                                                ┌──────────────────────────┐
                                                                │  Push Servo (BCM 27)     │
                                                                │  90° → 150° → 90°       │
                                                                └──────────────────────────┘
                                                                           │
                                                                           ▼
                                                                ┌──────────────────────────┐
                                                                │  I2C LCD 16×2            │
                                                                │  Displays category name  │
                                                                └──────────────────────────┘
```

---

## Hardware

| Component              | Specification           | Role                                      |
|------------------------|-------------------------|-------------------------------------------|
| Raspberry Pi 4 Model B | 4 GB RAM                | Central compute and GPIO controller       |
| USB Camera             | 640 × 480               | Waste image capture                       |
| Servo Motor — Selection| SG90 / MG996R, BCM 17   | Rotates disc to correct bin position      |
| Servo Motor — Push     | SG90 / MG996R, BCM 27   | Pushes waste off disc into bin            |
| LCD Display            | I2C 16×2, address 0x27  | Real-time category feedback               |
| Power Supply           | 5 V / 3 A               | System power                              |

---

## Software Stack

| Layer              | Technology                                                  |
|--------------------|-------------------------------------------------------------|
| AI Classification  | Python, TFLite (Google Teachable Machine), OpenCV (HSV)     |
| Hardware Control   | Python, pigpio                                              |
| LCD Interface      | Python, smbus2 (I2C)                                        |
| Dataset            | Custom waste images captured on campus (Plastic/Metal/Paper)|

---

## Servo Angle Calibration

Angles determined empirically during hardware integration and testing:

| Category  | Selection Servo Angle |
|-----------|-----------------------|
| Plastic   | 160°                  |
| Metal     | 20°                   |
| Paper     | 90° (home)            |
| No Waste  | 90° (home)            |

Push servo: extends from 90° → 150°, then retracts to 90° to dispose waste.

---

## Classification Logic

The system uses HSV colour-channel analysis for real-time inference on the Raspberry Pi:

- **No Waste** — detected when >150,000 dark pixels (disc empty)
- **Plastic** — blue/teal hue range (HSV H: 95–130)
- **Metal** — reddish/metallic tones (HSV H: 0–10)
- **Paper** — near-white, low saturation (HSV S: 0–35, V: 200–255)

If no category scores above threshold, defaults to No Waste.

> **Model weights:** The TFLite model (`garbage_model.tflite`) was trained using Google Teachable Machine on custom campus waste images and runs on the Raspberry Pi at `/home/pi/ai_model/`. The weights file is not committed to this repo due to size. Contact the team for the model file.

---

## Repository Structure

```
sortebin/
├── main.py                  # Full system control loop
├── requirements.txt         # Python dependencies
├── CAPSTONE_CPG287.pdf      # Full project report (TIET, December 2025)
└── README.md
```

---

## Quick Start

```bash
# On Raspberry Pi:
sudo systemctl start pigpiod
pip install -r requirements.txt

# Place garbage_model.tflite and labels.txt at /home/pi/ai_model/
python main.py
```

---

## Team

| Roll No.   | Name          | Role                                                              |
|------------|---------------|-------------------------------------------------------------------|
| 102203548  | Tanya         | ML model training, dataset collection and augmentation            |
| 102203604  | Smriti Singh  | Model evaluation and performance analysis                         |
| 102203631  | Rajvir Singh  | Hardware integration, servo calibration, system deployment, demo  |
| 102203652  | Shreya Singh  | System architecture and documentation                             |

**Mentors:** Dr. Ravneet Kaur (Assistant Professor-I) · Dr. Harcharan Jit Singh (System Manager IT), CSED, TIET Patiala

---

## License

Academic project — Thapar Institute of Engineering and Technology, Patiala, 2025.
