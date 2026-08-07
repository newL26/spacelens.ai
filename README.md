# SpaceLens AI — Deployment Guide

> AI-powered satellite image intelligence platform  
> Django 4.2 · TensorFlow 2.16 · IBM watsonx.ai Granite · PostgreSQL 15

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start — Local Development](#quick-start--local-development)
3. [Docker Production Deployment](#docker-production-deployment)
4. [Environment Variables Reference](#environment-variables-reference)
5. [ML Model Setup](#ml-model-setup)
6. [IBM watsonx.ai Configuration](#ibm-watsonxai-configuration)
7. [Database Migrations](#database-migrations)
8. [Static & Media Files](#static--media-files)
9. [Health Check](#health-check)
10. [Useful Commands](#useful-commands)

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Docker | 24+ |
| Docker Compose | v2 (plugin) |
| PostgreSQL | 15+ (or use the Compose service) |

---

## Quick Start — Local Development

### 1. Clone and set up environment

```bash
cd spacelens/
cp .env.example .env
# Edit .env — set DATABASE_URL, WATSONX_API_KEY, WATSONX_PROJECT_ID
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Place your trained model

```bash
# Copy your .keras or .h5 model to:
cp /path/to/your/model.keras ai/ml/model.keras
```

### 4. Run database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 6. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 7. Start the development server

```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000**

### 8. Test the AI pipeline

```bash
python manage.py test_ai_pipeline --image path/to/sample.jpg
```

---

## Docker Production Deployment

### 1. Prepare environment

```bash
cp .env.example .env
# Fill in all required values — especially:
#   SECRET_KEY, DATABASE_URL, WATSONX_API_KEY, WATSONX_PROJECT_ID
#   ALLOWED_HOSTS=yourdomain.com
#   DEBUG=False
```

### 2. Place the ML model

```bash
mkdir -p ai/ml/
cp /path/to/model.keras ai/ml/model.keras
```

### 3. Build and start all services

```bash
docker compose up -d --build
```

Services started:
- `spacelens_db`    — PostgreSQL 15 on internal network
- `spacelens_web`   — Django + Gunicorn on port 8000 (internal)
- `spacelens_nginx` — Nginx reverse proxy on ports **80** / **443**

### 4. Check logs

```bash
docker compose logs -f web
docker compose logs -f nginx
```

### 5. Verify health

```bash
curl http://localhost/health/
# Expected: {"status": "ok", "database": "ok"}
```

---

## Development with Docker

Use the dev override to mount source code live (no rebuild on code change):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

- Django dev server runs on **http://localhost:8000** (directly, no Nginx)
- PostgreSQL exposed on **localhost:5432**
- Source code mounted as a volume — edits reload immediately

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | Django secret key — generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | — | `False` | Set `True` for development only |
| `ALLOWED_HOSTS` | ✅ | — | Comma-separated list: `yourdomain.com,www.yourdomain.com` |
| `DATABASE_URL` | ✅ | — | PostgreSQL DSN: `postgres://user:pass@host:5432/dbname` |
| `WATSONX_API_KEY` | ✅ | — | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | ✅ | — | watsonx.ai project UUID |
| `WATSONX_URL` | — | `https://us-south.ml.cloud.ibm.com` | Regional endpoint |
| `WATSONX_MODEL_ID` | — | `ibm/granite-13b-instruct-v2` | Granite model identifier |
| `ML_MODEL_PATH` | — | `ai/ml/model.keras` | Path to trained `.keras` / `.h5` model |
| `ML_CLASS_NAMES` | — | EuroSAT 10 classes | Comma-separated class labels matching model output order |
| `DEFAULT_FROM_EMAIL` | — | `noreply@spacelens.ai` | Sender address for password-reset emails |
| `DJANGO_SUPERUSER_USERNAME` | — | — | Auto-create superuser on container start |
| `DJANGO_SUPERUSER_PASSWORD` | — | — | Superuser password |
| `DJANGO_SUPERUSER_EMAIL` | — | — | Superuser email |
| `SECURE_SSL_REDIRECT` | — | `True` (prod) | Set `False` if SSL is terminated upstream |
| `POSTGRES_DB` | — | `spacelens_db` | Compose DB name |
| `POSTGRES_USER` | — | `spacelens_user` | Compose DB user |
| `POSTGRES_PASSWORD` | — | `spacelens_pass` | Compose DB password — **change in production** |

---

## ML Model Setup

1. Train or obtain a Keras model on the **EuroSAT** dataset (or your own).
2. Save it:
   ```python
   model.save("model.keras")   # recommended format
   # or
   model.save("model.h5")      # legacy HDF5 format
   ```
3. Place it at `ai/ml/model.keras` (or set `ML_MODEL_PATH` in `.env`).
4. Set `ML_CLASS_NAMES` to match the neuron order of your model's output layer.
5. Set `ML_IMAGE_SIZE` in `settings/base.py` if your model uses a size other than 64×64.

> **Without a model file:** SpaceLens AI starts normally and returns uniform  
> dummy probabilities (equal weight for all classes). Granite still runs.

---

## IBM watsonx.ai Configuration

1. Sign in to [IBM Cloud](https://cloud.ibm.com) and create a watsonx.ai project.
2. Generate an API key under **Manage → Access → API Keys**.
3. Copy your **Project ID** from the watsonx.ai project settings.
4. Set in `.env`:
   ```env
   WATSONX_API_KEY=your-ibm-cloud-api-key
   WATSONX_PROJECT_ID=your-watsonx-project-id
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
   ```

> **Without credentials:** Granite responses are replaced with a structured  
> placeholder that preserves the 5-section report format.

---

## Database Migrations

```bash
# Development
python manage.py migrate

# Inside Docker
docker compose exec web python manage.py migrate

# Generate new migrations after model changes
python manage.py makemigrations
```

---

## Static & Media Files

| Location | Served by | Notes |
|----------|-----------|-------|
| `staticfiles/` | Nginx (`/static/`) + WhiteNoise (fallback) | Populated by `collectstatic` |
| `media/` | Nginx (`/media/`) | User-uploaded satellite images |

```bash
# Collect static files
python manage.py collectstatic --noinput
```

In production (Docker), both directories are Docker named volumes shared between the `web` and `nginx` containers.

---

## Health Check

```
GET /health/
```

Response:
```json
{"status": "ok", "database": "ok"}
```

Used by Docker `HEALTHCHECK` and Nginx upstream monitoring. Returns **503** if the database is unreachable.

---

## Useful Commands

```bash
# Run development server
python manage.py runserver

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Test AI pipeline end-to-end
python manage.py test_ai_pipeline --image sample.jpg

# Test AI pipeline (skip Granite API call)
python manage.py test_ai_pipeline --image sample.jpg --skip-granite

# Collect static files
python manage.py collectstatic --noinput

# Open Django shell
python manage.py shell

# Docker: view running containers
docker compose ps

# Docker: tail application logs
docker compose logs -f web

# Docker: run management command inside container
docker compose exec web python manage.py migrate

# Docker: rebuild after code changes
docker compose up -d --build web

# Docker: stop all services
docker compose down

# Docker: full teardown including volumes (destroys database!)
docker compose down -v
```

---

## Project Structure

```
spacelens/
├── ai/                     AI engine (TF classifier + Granite client)
│   ├── ml/                 Model file goes here
│   └── services/           IBM watsonx.ai client
├── accounts/               Auth (login, register, profile)
├── core/                   Landing page, health check
├── dashboard/              Authenticated overview
├── prediction/             ML inference views + history
├── reports/                PDF report generation
├── templates/              All Django templates
├── static/                 CSS, JS, images
├── media/                  User uploads (runtime)
├── docker/                 Gunicorn, Nginx, entrypoint
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

*Built with IBM watsonx.ai Granite · TensorFlow · Django · PostgreSQL*
