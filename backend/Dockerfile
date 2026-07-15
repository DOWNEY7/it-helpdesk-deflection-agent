# ─────────────────────────────────────────────────────────────────
# Stage 1: Builder — install dependencies
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools for any compiled dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────────────────────────
# Stage 2: Runtime — minimal image
# ─────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# Security: run as non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --no-create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Create log and data directories with correct ownership
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

USER appuser

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Production startup command
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-config", "/dev/null"]
