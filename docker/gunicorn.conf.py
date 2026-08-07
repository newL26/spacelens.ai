# ╔══════════════════════════════════════════════════════════════╗
# ║  SpaceLens AI — Gunicorn Configuration                      ║
# ╚══════════════════════════════════════════════════════════════╝
import multiprocessing
import os

# ── Binding ───────────────────────────────────────────────────────────────────
bind = "0.0.0.0:8000"

# ── Workers ───────────────────────────────────────────────────────────────────
# Formula: (2 × CPU cores) + 1
# Cap at 9 to avoid OOM on machines with many cores + large TF model in memory
workers = min((multiprocessing.cpu_count() * 2) + 1, 9)

# sync workers are fine for CPU-bound TF inference
# Use 'gthread' if you want threaded workers instead
worker_class = "sync"
threads = 1

# ── Timeouts ──────────────────────────────────────────────────────────────────
# TF inference + Granite LLM call can take up to 60 s
timeout         = 120
graceful_timeout = 30
keepalive        = 5

# ── Performance ───────────────────────────────────────────────────────────────
max_requests        = 500   # recycle workers to prevent memory leaks
max_requests_jitter = 50    # randomise to avoid thundering herd

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog  = "-"    # stdout
errorlog   = "-"    # stderr
loglevel   = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'
)

# ── Process name ─────────────────────────────────────────────────────────────
proc_name = "spacelens_ai"

# ── Preload app (loads TF model ONCE in master, workers fork) ─────────────────
# WARNING: if your TF version is not fork-safe, set preload_app = False
# and let each worker warm up independently via AiConfig.ready()
preload_app = False

# ── Server mechanics ─────────────────────────────────────────────────────────
forwarded_allow_ips = "*"   # trust X-Forwarded-For from Nginx
secure_scheme_headers = {
    "X-FORWARDED-PROTOCOL": "ssl",
    "X-FORWARDED-PROTO":    "https",
    "X-FORWARDED-SSL":      "on",
}
