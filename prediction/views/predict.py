"""
Prediction view — handles image upload → ML inference → Granite LLM → DB save.
"""
import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import FormView, DetailView

from prediction.forms import PredictionForm
from prediction.models import Prediction
from ai.ml.classifier import get_classifier
from ai.services.granite import GraniteService

logger = logging.getLogger(__name__)


class PredictView(LoginRequiredMixin, FormView):
    """
    Step 1 — GET:  render the upload form.
    Step 2 — POST: run the full AI pipeline and redirect to the result.
    """
    template_name = "prediction/predict.html"
    form_class = PredictionForm

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_page"] = "predict"
        ctx["class_names"] = getattr(settings, "ML_CLASS_NAMES", [])
        ctx["max_upload_mb"] = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10)
        ctx["pipeline_steps"] = [
            {"title": "Image Upload",     "desc": "Satellite image is securely received and validated."},
            {"title": "Preprocessing",    "desc": "Resized & normalised to match the training distribution."},
            {"title": "TF Inference",     "desc": "Keras model outputs probability scores for all 10 classes."},
            {"title": "IBM Granite LLM",  "desc": "Top-3 classes are sent to Granite for an intelligence report."},
            {"title": "Save & Display",   "desc": "Results are stored in PostgreSQL and displayed with a chart."},
        ]
        return ctx

    def form_valid(self, form):
        image_file = self.request.FILES["image"]

        # ── 1. Save image to DB (unsaved instance first for path resolution) ──
        instance = form.save(commit=False)
        instance.user = self.request.user
        instance.predicted_class = ""   # populated below
        instance.confidence = 0.0
        instance.save()                 # writes image to media/

        try:
            # ── 2. Run TF classifier ──────────────────────────────────────────
            classifier = get_classifier()
            probabilities: dict[str, float] = classifier.predict(instance.image.path)

            sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
            top_class, top_confidence = sorted_probs[0]
            top3 = sorted_probs[:3]

            # ── 3. Call IBM Granite ───────────────────────────────────────────
            granite = GraniteService()
            granite_text = granite.explain_prediction(top3)

        except Exception as exc:
            logger.exception("AI pipeline failed for prediction %s", instance.pk)
            instance.delete()           # clean up orphaned image record
            messages.error(
                self.request,
                "An error occurred during analysis. Please try again. "
                f"({type(exc).__name__})",
            )
            return redirect("prediction:predict")

        # ── 4. Persist results ────────────────────────────────────────────────
        instance.predicted_class = top_class
        instance.confidence = round(top_confidence, 4)
        instance.probabilities = {k: round(v, 4) for k, v in probabilities.items()}
        instance.granite_response = granite_text
        instance.save()

        logger.info(
            "Prediction %s complete: %s (%.1f%%) by %s",
            instance.pk,
            top_class,
            top_confidence,
            self.request.user.username,
        )

        messages.success(
            self.request,
            f"Analysis complete — {top_class} detected with {top_confidence:.1f}% confidence.",
        )
        return redirect("prediction:result", pk=instance.pk)

    def form_invalid(self, form):
        messages.error(self.request, "Please upload a valid satellite image.")
        return super().form_invalid(form)


class PredictionResultView(LoginRequiredMixin, DetailView):
    """Display the full result for a single prediction."""
    model = Prediction
    template_name = "prediction/result.html"
    context_object_name = "prediction"

    def get_queryset(self):
        # Users can only view their own predictions
        return Prediction.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pred = self.object

        # Prepare chart data (all classes, sorted by probability desc)
        sorted_probs = sorted(pred.probabilities.items(), key=lambda x: x[1], reverse=True)
        ctx["chart_labels"] = json.dumps([p[0] for p in sorted_probs])
        ctx["chart_values"] = json.dumps([round(p[1], 2) for p in sorted_probs])
        ctx["top3"] = pred.top3
        ctx["active_page"] = "predict"
        return ctx
