# Multi-stage Dockerfile for Planning & Discovery Service

# ============================================================================
# Stage 1: Base image with uv and Python
# ============================================================================
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base AS dependencies

# sentence-transformers / torch need build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Workspace config and lock file
COPY pyproject.toml uv.lock ./

# Common packages used by this service
COPY common/database  ./common/database
COPY common/kafka     ./common/kafka
COPY common/llm       ./common/llm
COPY common/pricing   ./common/pricing
COPY common/utils     ./common/utils

# Service manifest only (no source yet — layer cache)
COPY services/planning-discovery/pyproject.toml ./services/planning-discovery/

# Install all workspace deps (no dev extras)
RUN uv sync --frozen --no-dev --package planning-discovery-service

# ============================================================================
# Stage 3: Builder (Prisma client generation)
# ============================================================================
FROM dependencies AS builder

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/common/database
ENV HOME=/app \
    PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /app/.cache/prisma-python && \
    prisma generate && prisma py fetch

WORKDIR /app

# ============================================================================
# Stage 4: Runtime
# ============================================================================
FROM base AS runtime

# Runtime system deps (torch CPU-only is large but already baked in the venv)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/.cache && chown -R appuser:appuser /app

# Installed venv + generated Prisma client
COPY --from=builder --chown=appuser:appuser /app/.venv   /app/.venv
COPY --from=builder --chown=appuser:appuser /app/common  /app/common
COPY --from=builder --chown=appuser:appuser /app/.cache  /app/.cache

# Service source
COPY --chown=appuser:appuser services/planning-discovery/src \
                              ./services/planning-discovery/src

USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    HOME=/app

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/api/v1/health', timeout=5)"

CMD ["python", "-m", "uvicorn", "planning_discovery.main:app", \
     "--app-dir", "services/planning-discovery/src", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "1"]
