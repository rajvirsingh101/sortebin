"""
servo_controller.py — Two-servo circular disc mechanism for SORT E-BIN.

Hardware design (from project report):
  Servo 1 — Rotation: rotates the circular disc to the angle corresponding
             to the predicted waste category.
  Servo 2 — Tilt: tilts the disc downward so waste slides into the correct
             bin below, then resets flat.

Category → disc rotation angle (from report Section 4.1 flowchart):
  others    →   0°   (default / low-confidence fallback)
  plastic   →  90°
  wet_waste → 180°
  paper     → 270°
"""

import time
import logging

import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

# ── GPIO pin assignments (BCM numbering) ─────────────────────────────────────
ROTATION_SERVO_PIN = 17   # Servo 1 — disc rotation
TILT_SERVO_PIN     = 27   # Servo 2 — disc tilt for disposal

# ── Category → disc rotation angle (degrees) ─────────────────────────────────
CATEGORY_ANGLES: dict[str, float] = {
    "others":    0.0,
    "plastic":  90.0,
    "wet_waste": 180.0,
    "paper":    270.0,
}

HOME_ANGLE     = 0.0    # Resting / home angle after each cycle
TILT_OPEN      = 45.0   # Degrees to tilt disc downward for waste disposal
TILT_CLOSED    = 0.0    # Flat (horizontal) resting position
PWM_FREQ       = 50     # Hz — standard for SG90 / MG996R servos
TILT_HOLD_TIME = 1.2    # Seconds disc stays tilted before resetting


def _angle_to_duty(angle: float) -> float:
    """
    Convert angle (0–270°) to PWM duty cycle.
    SG90: 0° → 2%, 270° → 12%; linear interpolation.
    """
    return 2.0 + (angle / 27.0)


class ServoController:
    """
    Controls the two-servo circular disc sorting mechanism.

    Operation sequence per sort cycle:
      1. Rotate disc to the category angle (Servo 1).
      2. Tilt disc downward to drop waste (Servo 2).
      3. Reset — tilt back flat, rotate back to home (0°).
    """

    def __init__(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Rotation servo (Servo 1)
        GPIO.setup(ROTATION_SERVO_PIN, GPIO.OUT)
        self._rotation = GPIO.PWM(ROTATION_SERVO_PIN, PWM_FREQ)
        self._rotation.start(_angle_to_duty(HOME_ANGLE))

        # Tilt servo (Servo 2)
        GPIO.setup(TILT_SERVO_PIN, GPIO.OUT)
        self._tilt = GPIO.PWM(TILT_SERVO_PIN, PWM_FREQ)
        self._tilt.start(_angle_to_duty(TILT_CLOSED))

        logger.info(
            "[SERVO] Disc mechanism initialised — rotation pin BCM%d, tilt pin BCM%d.",
            ROTATION_SERVO_PIN, TILT_SERVO_PIN,
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _move(self, pwm: GPIO.PWM, angle: float, settle: float = 0.5) -> None:
        """Command a servo to `angle` degrees, wait, then cut signal."""
        pwm.ChangeDutyCycle(_angle_to_duty(angle))
        time.sleep(settle)
        pwm.ChangeDutyCycle(0)   # Kill signal to prevent jitter when idle

    # ── Public API ────────────────────────────────────────────────────────────

    def sort_waste(self, category: str) -> None:
        """
        Full disposal cycle for the given waste category.
        Falls back to 'others' (0°) for unrecognised categories.
        """
        angle = CATEGORY_ANGLES.get(category.lower(), CATEGORY_ANGLES["others"])

        logger.info("[SERVO] Category '%s' — rotating disc to %.0f°.", category, angle)

        # Step 1: Rotate disc to align with correct bin opening
        self._move(self._rotation, angle, settle=0.6)

        # Step 2: Tilt disc to drop waste
        self._move(self._tilt, TILT_OPEN, settle=0.4)
        time.sleep(TILT_HOLD_TIME)

        # Step 3: Reset — tilt back flat, then rotate back to home
        self._move(self._tilt, TILT_CLOSED, settle=0.4)
        self._move(self._rotation, HOME_ANGLE, settle=0.6)

        logger.info("[SERVO] Cycle complete — disc reset to home.")

    def cleanup(self) -> None:
        """Stop PWM signals and release all GPIO resources."""
        self._rotation.stop()
        self._tilt.stop()
        GPIO.cleanup()
        logger.info("[SERVO] GPIO resources released.")
