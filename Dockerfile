# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  SpaceLens AI — Multi-stage Dockerfile                                  ║
# ║                                                                          ║
# ║  Stage 1 (builder): install Python deps into a venv                     ║
# ║  Stage 2 (runtime): copy only the venv + app, run as non-root           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

# System build deps (psycopg2 needs libpq-dev, Pillow needs libjpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment so Stage 2 can copy it cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip first for reproducibility
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy only requirements to leverage Docker layer cache
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt


# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL maintainer="SpaceLens AI <noreply@spacelens.ai>"
LABEL description="SpaceLens AI — Satellite Image Intelligence Platform"

# Runtime system libs only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        libpng16-16 \
        libtiff6 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN groupadd --gid 1001 spacelens \
 && useradd  --uid 1001 --gid spacelens --shell /bin/bash --create-home spacelens

# App directory
WORKDIR /app

# Copy application source
COPY --chown=spacelens:spacelens . .

# Create runtime directories that must exist
RUN mkdir -p /app/staticfiles /app/media/predictions /app/logs \
 && chown -R spacelens:spacelens /app/staticfiles /app/media /app/logs

# Copy and set the entrypoint
COPY --chown=spacelens:spacelens docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER spacelens

# Collect static files at build time
RUN DJANGO_SETTINGS_MODULE=spacelens.settings.production \
    SECRET_KEY=build-time-placeholder \
    DATABASE_URL=postgres://u:p@localhost/db \
    python manage.py collectstatic --noinput --clear 2>/dev/null || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn"]
