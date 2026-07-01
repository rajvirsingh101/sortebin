#!/usr/bin/env python3
"""
SORT E-BIN -- AI-Powered Smart Waste Sorting Bin
Main control loop -- matches system design from the capstone project report.

Pipeline (report Section 4.1 flowchart):
  1. IR sensor confirms disc is empty and ready.
  2. User places waste on circular disc.
  3. IR sensor detects waste presence -> triggers camera capture.
  4. InceptionResNetV2 (TensorFlow/Keras) classifies waste on Raspberry Pi 4B.
  5. Confidence >= 0.7 -> rotate disc to category angle, tilt to dispose.
     Confidence < 0.7 -> default to 'others' bin (0 degrees).
  6. Disc resets to home position for next cycle.

Model : InceptionResNetV2 fine-tuned on TrashNet + custom campus images.
        Exported in .keras format for on-device edge inference.
        Validation accuracy: ~84%.  Confidence threshold: 0.7.

Categories and disc angles (report Section 4.1):
  Others    ->   0 degrees
  Plastic   ->  90 degrees
  Wet Waste -> 180 degrees
  Paper     -> 270 degrees

B.E. Capstone Project - Computer Engineering - TIET Patiala - December 2025
"""

import time
import cv2
import numpy as np
import RPi.GPIO as GPIO
import tensorflow as tf

# -- Model --------------------------------------------------------------------
MODEL_PATH           = "/home/pi/sortebin/model.keras"
IMG_SIZE             = (256, 256)
CONFIDENCE_THRESHOLD = 0.7
CATEGORIES           = ["others", "plastic", "wet_waste", "paper"]

# -- GPIO (BCM numbering) -----------------------------------------------------
IR_SENSOR_PIN = 4    # IR presence sensor: LOW when waste detected on disc
ROTATION_PIN  = 17   # Servo 1: disc rotation to category angle
TILT_PIN      = 27   # Servo 2: disc tilt to drop waste into bin

# -- Servo settings -----------------------------------------------------------
PWM_FREQ = 50

CATEGORY_ANGLES = {
    "others":    0.0,
    "plastic":  90.0,
    "wet_waste": 180.0,
    "paper":    270.0,
}

HOME_ANGLE  = 0.0
TILT_OPEN   = 45.0
TILT_CLOSED = 0.0
TILT_HOLD   = 1.5

# -- Classifier ---------------------------------------------------------------

class WasteClassifier:
    """
    InceptionResNetV2-based waste classifier for edge inference on Raspberry Pi.

    Architecture: InceptionResNetV2 (ImageNet, frozen base)
      -> Global Average Pooling -> Dropout (0.5) -> Dense (128, ReLU) -> Softmax (4 classes)

    Training: TrashNet + custom campus images, 256x256, augmented.
    Fine-tuning: last 50 layers. Optimizer: Adam.
    Validation accuracy: ~84%.
    """

    def __init__(self, model_path):
        self.model = tf.keras.models.load_model(model_path)
        print("[CLASSIFIER] Model loaded from", model_path)

    def _preprocess(self, frame):
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, IMG_SIZE, interpolation=cv2.INTER_AREA)
        img = img.astype("float32") / 255.0
        return img[None, ...]

    def predict(self, frame):
        probs = self.model.predict(self._preprocess(frame), verbose=0)[0]
        idx   = int(probs.argmax())
        conf  = float(probs[idx])
        if conf < CONFIDENCE_THRESHOLD:
            return "others", conf
        return CATEGORIES[idx], conf


# -- Servo helpers -------------------------------------------------------------

def _angle_to_duty(angle):
    return 2.0 + (angle / 27.0)

def _move(pwm, angle, settle=0.6):
    pwm.ChangeDutyCycle(_angle_to_duty(angle))
    time.sleep(settle)
    pwm.ChangeDutyCycle(0)

def sort_waste(rotation_pwm, tilt_pwm, category):
    angle = CATEGORY_ANGLES.get(category, HOME_ANGLE)
    print("[SERVO] '{}' -> {} degrees".format(category, int(angle)))
    _move(rotation_pwm, angle)
    _move(tilt_pwm, TILT_OPEN, settle=0.4)
    time.sleep(TILT_HOLD)
    _move(tilt_pwm, TILT_CLOSED, settle=0.4)
    _move(rotation_pwm, HOME_ANGLE)
    print("[SERVO] Disc reset to home.")


# -- Main ---------------------------------------------------------------------

def main():
    print("Initialising SORT E-BIN system...")

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(IR_SENSOR_PIN, GPIO.IN)
    GPIO.setup(ROTATION_PIN,  GPIO.OUT)
    GPIO.setup(TILT_PIN,      GPIO.OUT)

    rotation_pwm = GPIO.PWM(ROTATION_PIN, PWM_FREQ)
    tilt_pwm     = GPIO.PWM(TILT_PIN,     PWM_FREQ)
    rotation_pwm.start(_angle_to_duty(HOME_ANGLE))
    tilt_pwm.start(_angle_to_duty(TILT_CLOSED))

    classifier = WasteClassifier(MODEL_PATH)

    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("SORT E-BIN ready. Waiting for waste...")

    try:
        while True:
            print("[IR] Waiting for waste placement...")
            while GPIO.input(IR_SENSOR_PIN) == GPIO.HIGH:
                time.sleep(0.05)
            print("[IR] Waste detected.")

            ret, frame = camera.read()
            if not ret:
                print("[CAMERA] Capture failed - retrying.")
                time.sleep(0.2)
                continue

            category, confidence = classifier.predict(frame)
            print("[CLASSIFIER] {}  {:.1%}".format(category.upper(), confidence))

            sort_waste(rotation_pwm, tilt_pwm, category)

    except KeyboardInterrupt:
        print("Shutdown requested.")
    finally:
        camera.release()
        rotation_pwm.stop()
        tilt_pwm.stop()
        GPIO.cleanup()
        print("Exit clean.")


if __name__ == "__main__":
    main()
