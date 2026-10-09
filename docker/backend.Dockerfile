# ─── MemoryLeak Backend Dockerfile ───────────────────────────────────────────
# Multi-stage build:
#   builder — installs Python dependencies
#   runtime — minimal production image
#
# For development (docker-compose.yml) the source is mounted as a volume
# so the container is rebuilt only when requirements.txt changes.

# ─── Stage 1: builder ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system libraries only
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

# Create a non-root user for security
RUN groupadd --gid 1001 memoryleak \
    && useradd --uid 1001 --gid memoryleak --shell /bin/bash --create-home memoryleak \
    && chown -R memoryleak:memoryleak /app

USER memoryleak

# Health check — polls the FastAPI /health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Default command — uvicorn in production mode
# Development overrides this via docker-compose command: with --reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
