"""
Core health-check endpoint — used by Docker / load-balancer probes.
Returns 200 OK with basic system status.
"""
from django.http import JsonResponse
from django.views import View
from django.db import connections
from django.db.utils import OperationalError


class HealthCheckView(View):
    """
    GET /health/
    Returns:
        200 {"status": "ok", "database": "ok"}
        503 {"status": "error", "database": "unavailable"}
    """

    def get(self, request, *args, **kwargs):
        db_ok = self._check_db()
        status = "ok" if db_ok else "error"
        payload = {
            "status": status,
            "database": "ok" if db_ok else "unavailable",
        }
        http_status = 200 if db_ok else 503
        return JsonResponse(payload, status=http_status)

    @staticmethod
    def _check_db() -> bool:
        try:
            connections["default"].ensure_connection()
            return True
        except OperationalError:
            return False
