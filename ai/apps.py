from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ai"
    verbose_name = "AI Engine"

    def ready(self):
        """
        Pre-load the TensorFlow model when Django starts so every request
        shares the same in-memory model instance (no cold-start per request).
        """
        from ai.ml.classifier import get_classifier  # noqa: F401
        get_classifier()
