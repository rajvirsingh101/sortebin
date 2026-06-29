"""
sensor.py — HC-SR04 ultrasonic fill-level sensor for SORT E-BIN.

One sensor is mounted at the top of each compartment.
It measures the distance to the waste surface; fill % is derived
from the known compartment depth (default 30 cm).
"""

import time
import logging

import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

SOUND_SPEED_CM_S = 34_300   # cm/s at ~20 °C


class UltrasonicSensor:
    """
    Reads distance via a single HC-SR04 trigger/echo pair and converts
    it to a fill-level percentage.
    """

    def __init__(
        self,
        trigger_pin: int,
        echo_pin: int,
        max_depth_cm: float = 30.0,
    ) -> None:
        self.trigger     = trigger_pin
        self.echo        = echo_pin
        self.max_depth   = max_depth_cm

        GPIO.setup(self.trigger, GPIO.OUT)
        GPIO.setup(self.echo,    GPIO.IN)
        GPIO.output(self.trigger, False)
        time.sleep(0.05)    # allow sensor to settle on init

    # ------------------------------------------------------------------
    # Internal measurement
    # ------------------------------------------------------------------
    def _measure_cm(self) -> float:
        """Single pulse-echo round-trip → distance in centimetres."""
        # 10 µs trigger pulse
        GPIO.output(self.trigger, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger, False)

        # Wait for echo HIGH then LOW
        t_start = time.time()
        while GPIO.input(self.echo) == 0:
            t_start = time.time()

        t_end = time.time()
        while GPIO.input(self.echo) == 1:
            t_end = time.time()

        return ((t_end - t_start) * SOUND_SPEED_CM_S) / 2.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_fill_percent(self, samples: int = 5) -> float:
        """
        Average `samples` distance readings and return fill level as a
        percentage (0 % = empty, 100 % = full).
        """
        readings = []
        for _ in range(samples):
            readings.append(self._measure_cm())
            time.sleep(0.06)

        avg_dist = sum(readings) / len(readings)
        fill = ((self.max_depth - avg_dist) / self.max_depth) * 100.0
        return max(0.0, min(100.0, fill))
