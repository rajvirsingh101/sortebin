"""
classifier.py — Waste classification using InceptionResNetV2 CNN.

Model: InceptionResNetV2 fine-tuned (last 50 layers unfrozen) on
       TrashNet + custom campus-collected images, resized to 256×256,
       with augmentation (rotation, shear, zoom, horizontal flip).
       Trained with Adam optimizer; callbacks: EarlyStopping,
       ReduceLROnPlateau, ModelCheckpoint.
       Overall validation accuracy: ~84% (paper, plastic, metal, others).

Confidence threshold: 0.7 — items below threshold classified as 'others'.
"""

import numpy as np
import tensorflow as tf
import cv2

CONFIDENCE_THRESHOLD = 0.70   # Per project report Section 4.1


class WasteClassifier:
    """
    Wraps a fine-tuned InceptionResNetV2 model.
    Input : BGR frame (OpenCV) from Pi Camera.
    Output: (category: str, confidence: float)
    """

    # Categories match the disc angle mapping in servo_controller.py
    CATEGORIES = ["others", "paper", "plastic", "wet_waste"]
    IMG_SIZE = (256, 256)   # Resize target used during training (report Section 1.8)

    def __init__(self, model_path: str = "models/sortebin_model.h5"):
        self.model = tf.keras.models.load_model(model_path)
        print(f"[CLASSIFIER] Model loaded from {model_path}")

    # ------------------------------------------------------------------
    # Pre-processing
    # ------------------------------------------------------------------
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """BGR → RGB, resize to 299×299, normalise to [0, 1], add batch dim."""
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, self.IMG_SIZE, interpolation=cv2.INTER_AREA)
        img = img.astype(np.float32) / 255.0
        return np.expand_dims(img, axis=0)

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict(self, frame: np.ndarray) -> tuple:
        """
        Returns
        -------
        (category, confidence) where category is one of CATEGORIES,
        or ('uncertain', raw_confidence) when below CONFIDENCE_THRESHOLD.
        """
        tensor = self._preprocess(frame)
        probs  = self.model.predict(tensor, verbose=0)[0]
        idx    = int(np.argmax(probs))
        conf   = float(probs[idx])

        if conf < CONFIDENCE_THRESHOLD:
            return "uncertain", conf

        return self.CATEGORIES[idx], conf
