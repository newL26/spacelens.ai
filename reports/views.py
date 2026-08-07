"""
Reports views — PDF download endpoint.
"""
import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404
from django.views import View

from ai.services.granite import GraniteService
from prediction.models import Prediction
from reports.generator import generate_prediction_report

logger = logging.getLogger(__name__)


_GRANITE_PLACEHOLDER_MARKERS = (
    "risk assessment requires ibm watsonx.ai configuration",
    "this is a placeholder response",
    "granite integration",
)


def _has_watsonx_config() -> bool:
    api_key = getattr(settings, "WATSONX_API_KEY", "")
    project_id = getattr(settings, "WATSONX_PROJECT_ID", "")
    return bool(api_key and project_id)


def _is_placeholder_response(text: str) -> bool:
    normalised = (text or "").strip().lower()
    if not normalised:
        return True
    return any(marker in normalised for marker in _GRANITE_PLACEHOLDER_MARKERS)


def _refresh_granite_if_needed(prediction: Prediction) -> None:
    """
    Backfill stale placeholder Granite output on legacy predictions.

    Older predictions may have been stored before watsonx credentials were set.
    """
    current_response = (prediction.granite_response or "").strip()
    if not _is_placeholder_response(current_response):
        return

    try:
        granite_text = GraniteService().explain_prediction(prediction.top3).strip()
        if not granite_text:
            return

        # Always persist a newer response for stale placeholder records, even if
        # Granite still falls back, so users see the current runtime reason.
        if granite_text != current_response:
            prediction.granite_response = granite_text
            prediction.save(update_fields=["granite_response"])
            logger.info("Granite response refreshed for prediction %s", prediction.pk)
    except Exception as exc:
        logger.warning(
            "Could not refresh Granite response for prediction %s: %s",
            prediction.pk,
            exc,
        )


class DownloadReportView(LoginRequiredMixin, View):
    """
    GET /reports/download/<pk>/
    Generates and streams a PDF report for the given Prediction.
    Only the owning user may download their own reports.
    """

    def get(self, request, pk, *args, **kwargs):
        prediction = get_object_or_404(Prediction, pk=pk)

        if prediction.user != request.user:
            return HttpResponseForbidden()

        _refresh_granite_if_needed(prediction)

        try:
            pdf_bytes = generate_prediction_report(prediction)
        except Exception as exc:
            logger.exception("PDF generation failed for prediction %s: %s", pk, exc)
            raise Http404("Could not generate report. Please try again.") from exc

        filename = f"spacelens_report_{prediction.pk:05d}_{prediction.predicted_class.replace(' ', '_')}.pdf"

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = len(pdf_bytes)
        return response
