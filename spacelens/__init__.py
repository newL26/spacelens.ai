"""
SpaceLens AI — Django project init.
Ensure the correct settings module is active at import time.
"""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "spacelens.settings.development")
