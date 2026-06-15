FROM python:3.12-slim as builder

# Install uv for fast dependency resolution
RUN pip install uv

WORKDIR /build

# Copy dependency files
COPY agents/notion-research/pyproject.toml .

# Install dependencies
RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv pip install --target=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy installed packages
COPY --from=builder /install /usr/local/lib/python3.12/site-packages/

# Set up application
WORKDIR /app
COPY agents/notion-research/src/ /app/src/

# Set ownership
RUN chown -R appuser:appuser /app

USER appuser

# Health check — HTTP probe on A2A port
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3006/health')" || exit 1

EXPOSE 3006

# Run A2A server via uvicorn
CMD ["python", "-m", "uvicorn", "src.a2a_server:app", "--host", "0.0.0.0", "--port", "3006"]
