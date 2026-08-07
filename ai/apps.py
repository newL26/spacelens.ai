from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai"
    verbose_name = "AI Engine"

    def ready(self) -> None:
        """
        Pre-warm the TensorFlow classifier when Django starts so the first
        HTTP request is never delayed by model loading.

        Called once per process — NOT once per thread/worker.
        Gunicorn with multiple workers calls this once per worker.
        """
        # Guard against double-invocation during test collection
        import os
        if os.environ.get("RUN_MAIN") == "true" or not _is_django_runserver():
            _warm_classifier()


def _is_django_runserver() -> bool:
    """True only when running `manage.py runserver` (auto-reloader child)."""
    import sys
    return "runserver" in sys.argv


def _warm_classifier() -> None:
    """Load the model singleton. Errors are caught so Django still starts."""
    try:
        from ai.ml.classifier import get_classifier
        clf = get_classifier()
        logger.info("AI warm-up complete: %r", clf)
    except Exception as exc:
        logger.warning(
            "AI warm-up skipped — model unavailable at startup: %s", exc
        )
