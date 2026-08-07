"""
Reports views — PDF download endpoint.
"""
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404
from django.views import View

from prediction.models import Prediction
from reports.generator import generate_prediction_report

logger = logging.getLogger(__name__)


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
