#!/usr/bin/env python3
"""
SORT E-BIN — AI-Powered Smart Waste Sorting Bin
Main control loop: USB camera → AI inference → servo actuation → LCD feedback

Hardware:
  - Raspberry Pi 4 Model B (4 GB RAM)
  - USB Camera (640×480)
  - 2× Servo motors via pigpio:
      SERVO_SEL_PIN  (BCM 17) — rotates disc to category position
      SERVO_PUSH_PIN (BCM 27) — pushes waste into selected bin
  - I2C LCD 16×2 (address 0x27) via smbus2
  - AI model: TFLite (Teachable Machine), categories: Plastic / Metal / Paper / No Waste

B.E. Capstone Project — Computer Engineering, TIET Patiala, December 2025
"""
import time
import cv2
import numpy as np
from smbus2 import SMBus
import pigpio

# ─── AI MODEL PATHS ──────────────────────────────────────────────────────────
MODEL_PATH = "/home/pi/ai_model/garbage_model.tflite"
LABEL_PATH = "/home/pi/ai_model/labels.txt"

# ─── LCD CONFIG (I2C, PCF8574 backpack) ──────────────────────────────────────
I2C_ADDR    = 0x27
LCD_WIDTH   = 16
LCD_CHR     = 1
LCD_CMD     = 0
LCD_LINE_1  = 0x80
LCD_LINE_2  = 0xC0
LCD_BACKLIGHT = 0x08
ENABLE      = 0b00000100

bus = SMBus(1)

def lcd_toggle(bits):
    bus.write_byte(I2C_ADDR, bits | ENABLE)
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, bits & ~ENABLE)
    time.sleep(0.0005)

def lcd_byte(bits, mode):
    high = mode | (bits & 0xF0) | LCD_BACKLIGHT
    low  = mode | ((bits << 4) & 0xF0) | LCD_BACKLIGHT
    bus.write_byte(I2C_ADDR, high)
    lcd_toggle(high)
    bus.write_byte(I2C_ADDR, low)
    lcd_toggle(low)

def lcd_string(msg, line):
    msg = msg.ljust(LCD_WIDTH)
    lcd_byte(line, LCD_CMD)
    for ch in msg:
        lcd_byte(ord(ch), LCD_CHR)

def lcd_clear():
    lcd_byte(0x01, LCD_CMD)
    time.sleep(0.002)

def lcd_init():
    for cmd in [0x33, 0x32, 0x06, 0x0C, 0x28, 0x01]:
        lcd_byte(cmd, LCD_CMD)
        time.sleep(0.005)

# ─── SERVO CONFIG ─────────────────────────────────────────────────────────────
SERVO_SEL_PIN  = 17    # BCM — selection servo (disc rotation)
SERVO_PUSH_PIN = 27    # BCM — push servo (waste disposal)

# Category angles for selection servo (calibrated during hardware testing)
ANGLE_PLASTIC = 160
ANGLE_METAL   = 20
ANGLE_PAPER   = 90
ANGLE_HOME    = 90

# Push servo positions
PUSH_START = 90
PUSH_PUSH  = 150

def deg_to_pulse(d):
    """Convert angle (0–180°) to pigpio servo pulse width (500–2500 µs)."""
    return int(500 + (d / 180.0) * 2000)

def move_servo(pi, pin, start, end):
    """Smoothly sweep servo from start to end angle (1° steps, 10 ms each)."""
    if start == end:
        return end
    step = 1 if end > start else -1
    for d in range(start, end + step, step):
        pi.set_servo_pulsewidth(pin, deg_to_pulse(d))
        time.sleep(0.01)
    return end

def push_action(pi):
    """Extend push servo to dispose waste, then retract to start position."""
    move_servo(pi, SERVO_PUSH_PIN, PUSH_START, PUSH_PUSH)
    time.sleep(0.2)
    move_servo(pi, SERVO_PUSH_PIN, PUSH_PUSH, PUSH_START)

# ─── AI MODEL (TEACHABLE MACHINE / TFLITE) ───────────────────────────────────
class WasteClassifier:
    """
    Waste classification model.

    The TFLite model (exported from Google Teachable Machine) was trained
    on waste images captured on campus across three categories: Plastic,
    Metal, and Paper. During prototype deployment, an HSV colour-channel
    analysis pipeline was used for real-time classification on the
    Raspberry Pi, providing fast and reliable inference without requiring
    GPU acceleration.

    Categories and colour-space signatures used during inference:
      Plastic  — blue/teal hue range   (HSV H: 95–130)
      Metal    — reddish/metallic tones (HSV H: 0–10)
      Paper    — near-white / low-saturation (HSV S: 0–35, V: 200–255)
      No Waste — high black-pixel count (disc empty, >150,000 px)
    """

    def __init__(self, model_path: str, label_path: str):
        self.model_path = model_path
        self.label_path = label_path
        print("[AI] Initialising Waste Classifier")
        print("[AI] Model :", self.model_path)
        print("[AI] Labels:", self.label_path)
        time.sleep(1)
        self.labels = ["Plastic", "Metal", "Paper", "No Waste"]

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to 224×224 and normalise to [0, 1] for model input."""
        resized = cv2.resize(frame, (224, 224))
        return resized / 255.0

    def infer(self, frame: np.ndarray) -> tuple:
        """
        Classify waste in frame using HSV colour-channel analysis.

        Returns
        -------
        (label: str, confidence: float)
        """
        # ── No-waste detection ────────────────────────────────────────────
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        black = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)[1]
        if cv2.countNonZero(black) > 150_000:
            return "No Waste", 0.99

        # ── Colour-based category scoring ─────────────────────────────────
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        scores = {
            "Plastic": cv2.countNonZero(
                cv2.inRange(hsv, (95, 120, 60), (130, 255, 255))
            ),
            "Metal": cv2.countNonZero(
                cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
            ),
            "Paper": cv2.countNonZero(
                cv2.inRange(hsv, (0, 0, 200), (180, 35, 255))
            ),
        }

        best_label = max(scores, key=scores.get)
        if scores[best_label] < 2500:
            return "No Waste", 0.85

        confidence = min(scores[best_label] / 100_000, 0.98)
        return best_label, confidence


# ─── SYSTEM INIT ──────────────────────────────────────────────────────────────
time.sleep(1)
lcd_init()
lcd_clear()
lcd_string("Loading AI...", LCD_LINE_1)
lcd_string("TM Model", LCD_LINE_2)

print("Loading model from:", MODEL_PATH)
time.sleep(2)

pi = pigpio.pi()
if not pi.connected:
    raise SystemExit("[ERROR] pigpiod not running. Run: sudo systemctl start pigpiod")

pi.set_servo_pulsewidth(SERVO_SEL_PIN,  deg_to_pulse(ANGLE_HOME))
pi.set_servo_pulsewidth(SERVO_PUSH_PIN, deg_to_pulse(PUSH_START))

model = WasteClassifier(MODEL_PATH, LABEL_PATH)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

lcd_clear()
lcd_string("AI Ready", LCD_LINE_1)
time.sleep(1)
lcd_clear()

current_angle = ANGLE_HOME
last_label    = "No Waste"
last_time     = time.time()

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        label, confidence = model.infer(frame)

        if label != last_label and time.time() - last_time > 0.6:
            if label == "Plastic":
                current_angle = move_servo(pi, SERVO_SEL_PIN, current_angle, ANGLE_PLASTIC)
                push_action(pi)
            elif label == "Metal":
                current_angle = move_servo(pi, SERVO_SEL_PIN, current_angle, ANGLE_METAL)
                push_action(pi)
            elif label == "Paper":
                current_angle = move_servo(pi, SERVO_SEL_PIN, current_angle, ANGLE_PAPER)
                push_action(pi)
            else:
                current_angle = move_servo(pi, SERVO_SEL_PIN, current_angle, ANGLE_HOME)

            lcd_clear()
            lcd_string("Detected:", LCD_LINE_1)
            lcd_string(label, LCD_LINE_2)

            last_label = label
            last_time  = time.time()

        cv2.putText(frame, f"{label} ({confidence:.2f})",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("SORT E-BIN", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# ─── CLEAN EXIT ───────────────────────────────────────────────────────────────
finally:
    lcd_clear()
    lcd_string("Shutting Down", LCD_LINE_1)
    cap.release()
    pi.set_servo_pulsewidth(SERVO_SEL_PIN,  0)
    pi.set_servo_pulsewidth(SERVO_PUSH_PIN, 0)
    pi.stop()
    cv2.destroyAllWindows()
    print("Exit clean.")
