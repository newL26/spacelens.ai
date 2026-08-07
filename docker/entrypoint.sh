#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  SpaceLens AI — Container Entrypoint                        ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-spacelens.settings.production}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SpaceLens AI — Starting up"
echo "  Settings: ${DJANGO_SETTINGS_MODULE}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Wait for PostgreSQL to be ready ───────────────────────────────────────────
echo "⏳  Waiting for database…"
MAX_TRIES=30
TRIES=0
until python -c "
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE}')
django.setup()
from django.db import connections
connections['default'].ensure_connection()
print('DB ready')
" 2>/dev/null; do
    TRIES=$((TRIES + 1))
    if [ "$TRIES" -ge "$MAX_TRIES" ]; then
        echo "✗  Database not reachable after ${MAX_TRIES} attempts. Aborting."
        exit 1
    fi
    echo "   Attempt ${TRIES}/${MAX_TRIES} — retrying in 2 s…"
    sleep 2
done

echo "✓  Database is ready"

# ── Run migrations ────────────────────────────────────────────────────────────
echo "⏳  Applying migrations…"
python manage.py migrate --noinput
echo "✓  Migrations applied"

# ── Collect static files (in case volume mount overwrote them) ────────────────
echo "⏳  Collecting static files…"
python manage.py collectstatic --noinput --clear 2>/dev/null || true
echo "✓  Static files collected"

# ── Create superuser from env (non-interactive, idempotent) ───────────────────
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && \
   [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ] && \
   [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
    echo "⏳  Ensuring superuser exists…"
    python manage.py createsuperuser \
        --noinput \
        --username  "${DJANGO_SUPERUSER_USERNAME}" \
        --email     "${DJANGO_SUPERUSER_EMAIL}" 2>/dev/null || true
    echo "✓  Superuser ready"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Dispatch command ──────────────────────────────────────────────────────────
case "${1:-gunicorn}" in
    gunicorn)
        echo "🚀  Starting Gunicorn on 0.0.0.0:8000"
        exec gunicorn spacelens.wsgi:application \
            --config /app/docker/gunicorn.conf.py
        ;;
    dev)
        echo "🛠   Starting Django dev server on 0.0.0.0:8000"
        export DJANGO_SETTINGS_MODULE=spacelens.settings.development
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    worker)
        echo "⚙️   Starting background worker (placeholder for Celery)"
        exec python manage.py shell -c "print('Worker placeholder')"
        ;;
    *)
        exec "$@"
        ;;
esac
