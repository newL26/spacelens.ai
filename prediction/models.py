"""
Prediction model — stores every inference run by a user.
"""
import os
from django.db import models
from django.contrib.auth.models import User


def prediction_image_path(instance, filename: str) -> str:
    """Upload satellite images to media/predictions/<user_id>/<filename>."""
    ext = os.path.splitext(filename)[1].lower()
    base = os.path.splitext(filename)[0]
    return f"predictions/{instance.user_id}/{base}{ext}"


class Prediction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prediction_set",
    )
    image = models.ImageField(upload_to=prediction_image_path)

    # ── ML outputs ────────────────────────────────────────────────────────────
    predicted_class = models.CharField(max_length=100)
    confidence = models.FloatField(
        help_text="Top-1 confidence score as a percentage (0–100)."
    )
    # Full probability dict serialised as JSON: {"Forest": 94.7, "River": 3.1, …}
    probabilities = models.JSONField(default=dict)

    # ── Granite LLM output ────────────────────────────────────────────────────
    granite_response = models.TextField(blank=True)

    # ── Metadata ──────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.predicted_class} ({self.confidence:.1f}%)"

    @property
    def confidence_level(self) -> str:
        """Returns 'high', 'medium', or 'low' for CSS pill colouring."""
        if self.confidence >= 75:
            return "high"
        if self.confidence >= 45:
            return "medium"
        return "low"

    @property
    def top3(self) -> list[tuple[str, float]]:
        """Return top-3 (class, probability) pairs sorted by probability desc."""
        sorted_probs = sorted(
            self.probabilities.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_probs[:3]

    @property
    def image_filename(self) -> str:
        return os.path.basename(self.image.name) if self.image else ""
