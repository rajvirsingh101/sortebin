"""
main.py — SORT E-BIN main control loop.

Pipeline (from project report Section 4.1 flowchart):
  1. IR sensor checks disc is empty (ready state).
  2. User places waste on circular disc.
  3. IR sensor detects waste presence → triggers camera capture.
  4. InceptionResNetV2 classifies waste image on Raspberry Pi 4B.
  5. If confidence ≥ 0.7 → rotate disc to category angle + tilt to dispose.
     If confidence < 0.7 → classify as 'others' (0° / default bin).
  6. Disc resets to home position for next cycle.
"""

import logging
import time

import RPi.GPIO as GPIO
import cv2

from classifier       import WasteClassifier
from servo_controller import ServoController

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Hardware configuration ────────────────────────────────────────────────────
IR_SENSOR_PIN   = 4      # BCM pin — GPIO input from IR presence sensor
CAMERA_INDEX    = 0      # Pi Camera or USB camera
CAPTURE_WIDTH   = 640
CAPTURE_HEIGHT  = 480
LOOP_DELAY_S    = 0.1    # Polling interval (seconds) when waiting for IR trigger


def wait_for_waste(ir_pin: int) -> None:
    """
    Block until the IR sensor detects waste placed on the disc.
    IR sensor output: LOW when object detected, HIGH when clear.
    """
    logger.info("[IR] Disc ready — waiting for waste placement...")
    while GPIO.input(ir_pin) == GPIO.HIGH:
        time.sleep(LOOP_DELAY_S)
    logger.info("[IR] Waste detected on disc.")


def capture_frame(camera: cv2.VideoCapture):
    """Capture a single frame from the camera module."""
    ret, frame = camera.read()
    if not ret:
        logger.warning("[CAMERA] Frame capture failed.")
        return None
    return frame


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Initialising SORT E-BIN system...")

    # GPIO setup for IR sensor
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(IR_SENSOR_PIN, GPIO.IN)

    # Load model and initialise servo mechanism
    classifier = WasteClassifier("models/sortebin_model.h5")
    servo      = ServoController()

    # Open camera
    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH,  CAPTURE_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)

    logger.info("SORT E-BIN ready.")

    try:
        while True:
            # Step 1: Wait for IR sensor to detect waste on disc
            wait_for_waste(IR_SENSOR_PIN)

            # Step 2: Capture image of waste item
            frame = capture_frame(camera)
            if frame is None:
                time.sleep(0.2)
                continue

            # Step 3: Classify with InceptionResNetV2
            category, confidence = classifier.predict(frame)

            logger.info(
                "[CLASSIFIER] Prediction: %-10s  confidence: %.1f%%",
                category.upper(), confidence * 100,
            )

            # Step 4: Actuate disc mechanism
            # Note: classifier returns 'others' when confidence < 0.7 (threshold
            # defined in report Section 4.1). ServoController maps 'others' → 0°.
            servo.sort_waste(category)

    except KeyboardInterrupt:
        logger.info("Shutdown requested — exiting cleanly.")
    finally:
        camera.release()
        servo.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    main()
