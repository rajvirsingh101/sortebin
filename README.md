# SORT E-BIN — AI-Powered Smart Waste Sorting Bin

> B.E. Capstone Project · Computer Engineering · Thapar Institute of Engineering and Technology · December 2025

---

## Overview

SORT E-BIN is a fully integrated, intelligent waste segregation system that combines a Convolutional Neural Network for image-based classification, IoT-enabled fill-level monitoring, and servo-actuated physical sorting. Built and deployed as a working prototype on campus.

**The problem:** Improper waste segregation at source is one of the largest barriers to effective recycling. Manual sorting is inconsistent and costly at scale.

**The solution:** A smart bin that classifies waste in real time and automatically directs it to the correct compartment — with no human intervention.

---

## System Architecture

```
┌─────────────────┐      ┌──────────────────────────┐      ┌──────────────────────┐
│  Pi Camera v2   │ ───▶ │  InceptionResNetV2 CNN   │ ───▶ │  ServoController     │
│  (640 × 480)    │      │  5-class classifier       │      │  5 SG90 servo motors │
└─────────────────┘      │  ~91% val accuracy        │      └──────────────────────┘
                         └──────────────────────────┘                │
                                                                     ▼
                         ┌──────────────────────────────────────────────────────────┐
                         │  Compartments:  Plastic │ Paper │ Metal │ Glass │ Organic │
                         └──────────────────────────────────────────────────────────┘
                                    ▲
                         HC-SR04 ultrasonic sensors (one per compartment)
                         → fill-level %, alert when > 85%
```

---

## Hardware

| Component            | Specification        | Role                               |
|----------------------|----------------------|------------------------------------|
| Raspberry Pi 4B      | 4 GB RAM             | Central compute / GPIO controller  |
| Pi Camera Module v2  | 8 MP                 | Waste image capture                |
| SG90 Servo (× 5)     | 0–180°               | Compartment door actuation         |
| HC-SR04 Sensor (× 5) | 2–400 cm             | Fill-level measurement             |
| 5 V / 3 A PSU        | —                    | System power                       |

---

## Software Stack

| Layer              | Technology                                         |
|--------------------|----------------------------------------------------|
| ML Classification  | Python, TensorFlow / Keras, InceptionResNetV2      |
| Hardware Control   | Python, RPi.GPIO                                   |
| Image Processing   | OpenCV                                             |
| Dataset            | TrashNet + custom augmentation (~25,000 images)    |

---

## Key Results

| Metric                   | Value          |
|--------------------------|----------------|
| Classification accuracy  | ~91% (test set)|
| Waste categories         | 5              |
| Sorting cycle time       | ~2.2 s         |
| Fill-level accuracy      | ±3 %           |
| Confidence threshold     | 75 %           |

---

## Repository Structure

```
sortebin/
├── main.py               # Control loop — capture → classify → actuate → monitor
├── classifier.py         # InceptionResNetV2 inference wrapper
├── servo_controller.py   # GPIO servo actuation (RPi.GPIO)
├── sensor.py             # HC-SR04 fill-level sensing
├── models/               # Trained model weights (sortebin_model.h5)
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

> Requires Raspberry Pi with RPi.GPIO. On non-Pi hardware, mock the GPIO calls for testing.

---

## Team

| Roll No.  | Name         | Role                                                                 |
|-----------|--------------|----------------------------------------------------------------------|
| 102203548 | Tanya        | ML model training, dataset collection & augmentation                |
| 102203604 | Smriti Singh | Model evaluation, performance analysis                               |
| 102203631 | Rajvir Singh | Hardware integration, GPIO / servo control, sensor wiring, demo     |
| 102203652 | Shreya Singh | System architecture, documentation                                   |

**Mentors:** Dr. Ravneet Kaur (Assistant Professor-I) · Dr. Harcharan Jit Singh (System Manager IT), CSED, TIET Patiala

---

## License

Academic project — Thapar Institute of Engineering and Technology, Patiala, 2025.
