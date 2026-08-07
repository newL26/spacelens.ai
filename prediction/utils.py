"""
Image upload validation helpers for the prediction app.
"""
import os
import logging
from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS: list[str] = getattr(
    settings, "ALLOWED_IMAGE_EXTENSIONS", [".jpg", ".jpeg", ".png", ".tif", ".tiff"]
)
_MAX_SIZE_MB: int = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10)
_MAX_SIZE_BYTES: int = _MAX_SIZE_MB * 1024 * 1024


def validate_satellite_image(image) -> None:
    """
    Django field validator — raises ValidationError on bad input.

    Checks:
      1. File extension is in the allowed list.
      2. File size does not exceed MAX_UPLOAD_SIZE_MB.
      3. Pillow can open the file (basic integrity check).
    """
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. "
            f"Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
        )

    if image.size > _MAX_SIZE_BYTES:
        raise ValidationError(
            f"Image is too large ({image.size / 1024 / 1024:.1f} MB). "
            f"Maximum allowed size is {_MAX_SIZE_MB} MB."
        )

    # Light integrity check via Pillow
    try:
        from PIL import Image as PilImage
        image.seek(0)
        with PilImage.open(image) as img:
            img.verify()
        image.seek(0)
    except Exception as exc:
        logger.warning("Image validation failed: %s", exc)
        raise ValidationError(
            "The file could not be read as a valid image. "
            "Please upload a proper satellite image."
        ) from exc
