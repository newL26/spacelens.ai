"""
Management command: debug_watsonx_config

Prints effective watsonx-related Django settings and environment status
for fast runtime diagnostics.

Usage:
    python manage.py debug_watsonx_config
"""
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Print effective watsonx configuration values seen by Django."

    def handle(self, *args, **options):
        api_key = getattr(settings, "WATSONX_API_KEY", "") or ""
        project_id = getattr(settings, "WATSONX_PROJECT_ID", "") or ""
        url = getattr(settings, "WATSONX_URL", "") or ""
        model_id = getattr(settings, "WATSONX_MODEL_ID", "") or ""

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Watsonx Runtime Configuration ==="))
        self.stdout.write(f"DJANGO_SETTINGS_MODULE: {settings.SETTINGS_MODULE}")
        self.stdout.write(f"WATSONX_API_KEY set: {bool(api_key)}")
        self.stdout.write(f"WATSONX_PROJECT_ID set: {bool(project_id)}")
        self.stdout.write(f"WATSONX_URL: {url}")
        self.stdout.write(f"WATSONX_MODEL_ID: {model_id}")

        if api_key:
            self.stdout.write(f"WATSONX_API_KEY prefix: {api_key[:6]}***")
        if project_id:
            self.stdout.write(f"WATSONX_PROJECT_ID prefix: {project_id[:8]}***")

        if api_key and project_id:
            self.stdout.write(self.style.SUCCESS("Status: credentials present in Django settings."))
        else:
            self.stdout.write(self.style.WARNING("Status: missing credentials in Django settings."))
