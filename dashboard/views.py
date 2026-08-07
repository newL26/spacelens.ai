"""
Dashboard views — authenticated overview with stats and recent activity.
"""
import json
import logging
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Avg, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from prediction.models import Prediction

logger = logging.getLogger(__name__)


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        qs = Prediction.objects.filter(user=user)

        # ── Core stats ────────────────────────────────────────────────────────
        total = qs.count()
        avg_conf = qs.aggregate(avg=Avg("confidence"))["avg"] or 0.0
        last_30 = qs.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).count()

        # Top predicted class
        top_class_row = (
            qs.values("predicted_class")
            .annotate(cnt=Count("id"))
            .order_by("-cnt")
            .first()
        )
        top_class = top_class_row["predicted_class"] if top_class_row else "—"

        # ── Activity chart: predictions per day (last 14 days) ────────────────
        since = timezone.now() - timedelta(days=14)
        daily_qs = (
            qs.filter(created_at__gte=since)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )

        # Build a full 14-day series (fill missing days with 0)
        date_map = {row["day"]: row["count"] for row in daily_qs}
        activity_labels = []
        activity_values = []
        for i in range(14):
            day = (timezone.now() - timedelta(days=13 - i)).date()
            activity_labels.append(day.strftime("%b %d"))
            activity_values.append(date_map.get(day, 0))

        # ── Class distribution ────────────────────────────────────────────────
        class_dist = list(
            qs.values("predicted_class")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        # ── Recent predictions ────────────────────────────────────────────────
        recent = qs.select_related("user").order_by("-created_at")[:6]

        ctx.update({
            "active_page": "dashboard",
            "stats": {
                "total": total,
                "avg_confidence": round(avg_conf, 1),
                "last_30": last_30,
                "top_class": top_class,
            },
            "recent_predictions": recent,
            "activity_labels": json.dumps(activity_labels),
            "activity_values": json.dumps(activity_values),
            "class_dist": class_dist,
        })
        return ctx
