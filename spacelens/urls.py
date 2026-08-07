"""
SpaceLens AI — Root URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.health import HealthCheckView

urlpatterns = [
    path("admin/", admin.site.urls),

    # Health check (no auth — used by Docker / load balancer)
    path("health/", HealthCheckView.as_view(), name="health"),

    # Public landing page
    path("", include("core.urls", namespace="core")),

    # Authentication
    path("accounts/", include("accounts.urls", namespace="accounts")),

    # Authenticated dashboard
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),

    # Prediction engine
    path("predict/", include("prediction.urls", namespace="prediction")),

    # PDF Reports
    path("reports/", include("reports.urls", namespace="reports")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
