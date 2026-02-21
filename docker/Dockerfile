# ── Stage 1: dependency builder ──────────────────────────────────────────────
FROM python:3.11-slim AS builder
ARG BUILD_VERSION=dev
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.11-slim
ARG BUILD_VERSION=dev
LABEL org.opencontainers.image.title="LLM Code Assist" \
      org.opencontainers.image.version="${BUILD_VERSION}" \
      org.opencontainers.image.description="AI-powered code generation and project management" \
      maintainer="LLM Code Assist"

# Install curl (needed for healthcheck + entrypoint Ollama calls) and redis-tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user and application directories
RUN groupadd -r appgroup \
    && useradd -r -g appgroup -d /app -s /sbin/nologin appuser \
    && mkdir -p /app/projects /app/data \
    && chown -R appuser:appgroup /app

# Copy application source
WORKDIR /app
COPY --chown=appuser:appgroup app/ ./app/
COPY --chown=appuser:appgroup agents/ ./agents/
COPY --chown=appuser:appgroup utils/ ./utils/
COPY --chown=appuser:appgroup celery_app/ ./celery_app/
COPY --chown=appuser:appgroup templates/ ./templates/
COPY --chown=appuser:appgroup static/ ./static/
COPY --chown=appuser:appgroup scripts/ ./scripts/
COPY --chown=appuser:appgroup wsgi.py run.py requirements.txt ./

# Copy and secure entrypoint (owned by root so it can't be overwritten by app user)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER appuser

EXPOSE 8001

# Health check — hits the /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "gunicorn", \
     "--worker-class", "eventlet", \
     "--workers", "1", \
     "--bind", "0.0.0.0:8001", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "wsgi:app"]
