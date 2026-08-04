FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY agents/search-agent/pyproject.toml ./
RUN pip install --no-cache-dir \
    "mcp[cli]>=1.3.0" \
    "fastmcp>=2.0.0" \
    "httpx>=0.27.0" \
    "uvicorn[standard]>=0.30.0" \
    "python-dotenv>=1.0.0"

COPY agents/search-agent/server.py ./

ENV PYTHONPATH="/app"
ENV PORT=3007

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:3007/health || exit 1

EXPOSE 3007

CMD ["python", "server.py"]
