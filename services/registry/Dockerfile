# Multi-stage Dockerfile for Registry Service
# Build optimized for production use

# ============================================================================
# Stage 1: Base image with uv and Python
# ============================================================================
FROM python:3.12-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# ============================================================================
# Stage 2: Dependencies
# ============================================================================
FROM base AS dependencies

# Copy workspace configuration
COPY pyproject.toml uv.lock ./

# Copy common packages
COPY common/database ./common/database
COPY common/proto ./common/proto
COPY common/utils ./common/utils

# Copy service package
COPY services/registry/pyproject.toml ./services/registry/

# Install dependencies
RUN uv sync --frozen --no-dev

# ============================================================================
# Stage 3: Builder (Generate Prisma client and gRPC stubs)
# ============================================================================
FROM dependencies AS builder

# Generate Prisma client
WORKDIR /app/common/database
RUN uv run prisma generate

# Generate gRPC stubs
WORKDIR /app/common/proto
RUN uv run python -m grpc_tools.protoc \
    -I./src \
    --python_out=./src \
    --grpc_python_out=./src \
    ./src/registry.proto

WORKDIR /app

# ============================================================================
# Stage 4: Runtime
# ============================================================================
FROM base AS runtime

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy installed dependencies from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/common /app/common

# Copy service source code
COPY --chown=appuser:appuser services/registry/src ./services/registry/src
COPY --chown=appuser:appuser services/registry/.env.example ./services/registry/.env.example

# Switch to non-root user
USER appuser

# Set Python path
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH"

# Expose ports
EXPOSE 8000 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health', timeout=5)"

# Start the service
CMD ["python", "-m", "uvicorn", "services.registry.src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
