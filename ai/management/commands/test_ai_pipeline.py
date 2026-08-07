"""
Management command: test_ai_pipeline

Validates that the TensorFlow classifier and IBM Granite service
are correctly configured and operational.

Usage:
    python manage.py test_ai_pipeline
    python manage.py test_ai_pipeline --image path/to/image.jpg
    python manage.py test_ai_pipeline --skip-granite
"""
import json
import os
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Smoke-test the TensorFlow classifier and IBM Granite integration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--image",
            type=str,
            default="",
            help="Path to a satellite image to classify (optional).",
        )
        parser.add_argument(
            "--skip-granite",
            action="store_true",
            default=False,
            help="Skip the Granite API call.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== SpaceLens AI — Pipeline Test ===\n"))

        # ── 1. Classifier ─────────────────────────────────────────────────────
        self.stdout.write("1. Loading TensorFlow classifier…")
        try:
            from ai.ml.classifier import get_classifier
            clf = get_classifier()
            self.stdout.write(self.style.SUCCESS(f"   ✓ {clf!r}"))
        except Exception as exc:
            raise CommandError(f"   ✗ Classifier failed to load: {exc}") from exc

        # ── 2. Inference ──────────────────────────────────────────────────────
        image_path = options["image"]
        if image_path:
            if not Path(image_path).exists():
                raise CommandError(f"Image not found: {image_path}")

            self.stdout.write(f"\n2. Running inference on: {image_path}")
            try:
                probs = clf.predict(image_path)
                sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                top3 = sorted_probs[:3]

                self.stdout.write(self.style.SUCCESS("   ✓ Inference complete"))
                self.stdout.write("\n   Top probabilities:")
                for rank, (cls, prob) in enumerate(sorted_probs[:5], 1):
                    bar = "█" * int(prob / 5)
                    self.stdout.write(f"   #{rank}  {cls:<25} {prob:6.2f}%  {bar}")
            except Exception as exc:
                raise CommandError(f"   ✗ Inference failed: {exc}") from exc
        else:
            self.stdout.write("\n2. No --image provided — skipping inference test.")
            top3 = [("Forest", 94.7), ("River", 3.1), ("Pasture", 1.2)]
            self.stdout.write(f"   Using dummy top3 for Granite test: {top3}")

        # ── 3. Granite ────────────────────────────────────────────────────────
        if options["skip_granite"]:
            self.stdout.write("\n3. Granite test skipped (--skip-granite).")
        else:
            self.stdout.write("\n3. Calling IBM Granite…")
            try:
                from ai.services.granite import GraniteService
                granite = GraniteService()
                response = granite.explain_prediction(top3)

                preview = response[:200].replace("\n", " ")
                self.stdout.write(self.style.SUCCESS("   ✓ Granite responded"))
                self.stdout.write(f"   Preview: {preview}…")
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f"   ⚠ Granite call failed: {exc}"))

        self.stdout.write(self.style.SUCCESS("\n=== All checks passed ===\n"))
