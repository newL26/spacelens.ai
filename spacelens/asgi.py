"""
SpaceLens AI — ASGI Entry Point
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelens.settings.production")

application = get_asgi_application()
