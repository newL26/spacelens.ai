"""
Prediction history view — paginated, searchable list of past predictions.
"""
import logging

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.views import View
from django.db.models import Q

from prediction.models import Prediction

logger = logging.getLogger(__name__)


class PredictionHistoryView(LoginRequiredMixin, ListView):
    model = Prediction
    template_name = "prediction/history.html"
    context_object_name = "predictions"
    paginate_by = 12

    def get_queryset(self):
        qs = Prediction.objects.filter(user=self.request.user).order_by("-created_at")
        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(predicted_class__icontains=q)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["search_query"] = self.request.GET.get("q", "")
        ctx["active_page"] = "history"
        return ctx


class DeletePredictionView(LoginRequiredMixin, View):
    """POST-only — deletes a single prediction owned by the current user."""

    def post(self, request, pk, *args, **kwargs):
        prediction = get_object_or_404(Prediction, pk=pk)
        if prediction.user != request.user:
            return HttpResponseForbidden()

        prediction.image.delete(save=False)   # remove file from media/
        prediction.delete()
        logger.info("Prediction %s deleted by %s", pk, request.user.username)
        messages.success(request, "Prediction deleted.")
        return redirect("prediction:history")
