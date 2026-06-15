# Multi-stage Dockerfile for Gateway Service

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
COPY common/utils ./common/utils

COPY services/gateway/pyproject.toml ./services/gateway/

RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 3: Builder (Generate Prisma client + fetch engine binary)
# ============================================================================
FROM dependencies AS builder

WORKDIR /app/common/database
RUN uv run prisma generate && uv run prisma py fetch

WORKDIR /app

# ============================================================================
# Stage 4: Runtime
# ============================================================================
FROM base AS runtime

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/common /app/common

COPY --chown=appuser:appuser services/gateway/src ./services/gateway/src
COPY --chown=appuser:appuser services/gateway/.env.example ./services/gateway/.env.example

USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8080/health', timeout=5)"

CMD ["python", "-m", "uvicorn", "gateway.main:app", \
     "--app-dir", "services/gateway/src", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "1"]
