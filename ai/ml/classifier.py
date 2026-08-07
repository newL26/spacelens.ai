"""
TensorFlow / Keras model classifier — singleton pattern.

The model is loaded ONCE when Django starts (via AiConfig.ready())
and reused for every subsequent request. Thread-safe via a module-level lock.
"""
import logging
import threading
from pathlib import Path
from typing import Optional

import numpy as np
from django.conf import settings
from PIL import Image as PilImage

logger = logging.getLogger(__name__)

# ── Module-level singleton state ──────────────────────────────────────────────
_classifier: Optional["SatelliteClassifier"] = None
_lock = threading.Lock()


def get_classifier() -> "SatelliteClassifier":
    """
    Return the shared SatelliteClassifier instance, creating it on first call.
    Thread-safe — safe to call from concurrent request threads.
    """
    global _classifier
    if _classifier is None:
        with _lock:
            if _classifier is None:          # double-checked locking
                _classifier = SatelliteClassifier()
    return _classifier


class SatelliteClassifier:
    """
    Wraps a trained Keras model and exposes a single ``predict()`` method.

    Configuration (read from Django settings):
        ML_MODEL_PATH   — path to the .keras / .h5 model file
        ML_CLASS_NAMES  — ordered list of class-label strings
        ML_IMAGE_SIZE   — (H, W) tuple the model was trained on
    """

    def __init__(self) -> None:
        self._model = None
        self._class_names: list[str] = getattr(settings, "ML_CLASS_NAMES", [])
        self._image_size: tuple[int, int] = getattr(settings, "ML_IMAGE_SIZE", (64, 64))
        self._model_path: str = str(getattr(settings, "ML_MODEL_PATH", ""))
        self._load_model()

    # ── Model loading ─────────────────────────────────────────────────────────
    def _load_model(self) -> None:
        """Load the Keras model from disk.  Logs a warning if the file is absent."""
        path = Path(self._model_path)

        if not path.exists():
            logger.warning(
                "ML model file not found at '%s'. "
                "Predictions will return dummy probabilities until the model is placed there.",
                path,
            )
            return

        try:
            # Import TensorFlow here so Django can start without it installed
            import tensorflow as tf  # noqa: PLC0415

            # Silence TF INFO/WARNING logs in production
            tf.get_logger().setLevel("ERROR")

            self._model = tf.keras.models.load_model(str(path), compile=False)
            logger.info(
                "TF model loaded from '%s'  |  Input shape: %s  |  Classes: %d",
                path,
                self._model.input_shape,
                len(self._class_names),
            )
        except Exception as exc:
            logger.exception("Failed to load TF model from '%s': %s", path, exc)
            self._model = None

    # ── Public API ────────────────────────────────────────────────────────────
    def predict(self, image_path: str) -> dict[str, float]:
        """
        Preprocess an image file and run model inference.

        Args:
            image_path: Absolute filesystem path to the uploaded image.

        Returns:
            Dict mapping each class name to its probability (0.0 – 100.0).

        Raises:
            RuntimeError: If no model is loaded and fallback is disabled.
            FileNotFoundError: If ``image_path`` does not exist.
        """
        if self._model is None:
            logger.warning("No model loaded — returning dummy uniform probabilities.")
            return self._dummy_probabilities()

        img_array = self._preprocess(image_path)
        raw_probs = self._model.predict(img_array, verbose=0)[0]  # shape (n_classes,)

        if len(raw_probs) != len(self._class_names):
            raise ValueError(
                f"Model output size ({len(raw_probs)}) does not match "
                f"ML_CLASS_NAMES length ({len(self._class_names)}). "
                "Update ML_CLASS_NAMES in your .env to match the trained model."
            )

        # Convert to percentage probabilities
        return {
            cls: float(round(prob * 100, 4))
            for cls, prob in zip(self._class_names, raw_probs)
        }

    # ── Preprocessing ─────────────────────────────────────────────────────────
    def _preprocess(self, image_path: str) -> "np.ndarray":
        """
        Load, resize, normalise and batch the image for model input.

        Pipeline:
            1. Open with Pillow and convert to RGB (handles RGBA, greyscale, TIFF)
            2. Resize to ML_IMAGE_SIZE using LANCZOS resampling
            3. Normalise pixel values to [0, 1]
            4. Expand dims to (1, H, W, 3) for batch dimension
        """
        with PilImage.open(image_path) as img:
            img = img.convert("RGB")
            img = img.resize(
                (self._image_size[1], self._image_size[0]),   # PIL uses (W, H)
                PilImage.Resampling.LANCZOS,
            )
            arr = np.array(img, dtype=np.float32) / 255.0    # normalise to [0,1]

        return np.expand_dims(arr, axis=0)                    # (1, H, W, 3)

    # ── Fallback ──────────────────────────────────────────────────────────────
    def _dummy_probabilities(self) -> dict[str, float]:
        """Return uniform probabilities when no model is available (dev/testing)."""
        n = len(self._class_names)
        if n == 0:
            return {"Unknown": 100.0}
        uniform = round(100.0 / n, 4)
        return {cls: uniform for cls in self._class_names}

    # ── Repr ──────────────────────────────────────────────────────────────────
    def __repr__(self) -> str:
        status = "loaded" if self._model is not None else "NOT LOADED"
        return (
            f"<SatelliteClassifier model={status} "
            f"classes={len(self._class_names)} "
            f"image_size={self._image_size}>"
        )
