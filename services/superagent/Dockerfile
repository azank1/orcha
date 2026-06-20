# Multi-stage Dockerfile for SuperAgent Service

# ============================================================================
# Stage 1: Base image with uv and Python
# ============================================================================
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base AS dependencies

COPY pyproject.toml uv.lock ./

COPY common/database ./common/database
COPY common/kafka ./common/kafka
COPY common/llm ./common/llm
COPY common/pricing ./common/pricing
COPY common/proto ./common/proto
COPY common/utils ./common/utils
COPY common/internal-commons ./common/internal-commons
COPY common/emerge-tools ./common/emerge-tools

COPY services/superagent/pyproject.toml ./services/superagent/

RUN uv sync --frozen --no-dev --package superagent

# ============================================================================
# Stage 3: Builder (Generate Prisma client + fetch engine binary)
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

# System libs for mcp-document-converter (WeasyPrint → PDF/HTML); Python wheels ship the rest.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/.cache && chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/common /app/common
COPY --from=builder --chown=appuser:appuser /app/.cache /app/.cache

COPY --chown=appuser:appuser services/superagent/src ./services/superagent/src
COPY --chown=appuser:appuser services/superagent/.env.example ./services/superagent/.env.example

# Platform MCP manifests + servers (e.g. Chomper) for PlatformToolSeeder
COPY --chown=appuser:appuser common/emerge-tools /app/common/emerge-tools

USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    HOME=/app

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8002/health', timeout=5)"

CMD ["python", "-m", "uvicorn", "superagent.main:app", \
     "--app-dir", "services/superagent/src", \
     "--host", "0.0.0.0", \
     "--port", "8002", \
     "--workers", "1"]
