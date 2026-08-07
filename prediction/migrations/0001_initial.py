"""
Initial migration for the prediction app.
"""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import prediction.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Prediction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to=prediction.models.prediction_image_path)),
                ("predicted_class", models.CharField(max_length=100)),
                ("confidence", models.FloatField(help_text="Top-1 confidence score as a percentage (0–100).")),
                ("probabilities", models.JSONField(default=dict)),
                ("granite_response", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prediction_set",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Prediction",
                "verbose_name_plural": "Predictions",
                "ordering": ["-created_at"],
            },
        ),
    ]
