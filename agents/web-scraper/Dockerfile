FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY agents/web-scraper/pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi>=0.109.0 \
    "uvicorn[standard]>=0.27.0" \
    aiohttp>=3.9.0 \
    beautifulsoup4>=4.12.0 \
    lxml>=5.0.0 \
    pydantic>=2.5.0 \
    pydantic-settings>=2.1.0 \
    openai>=1.12.0 \
    structlog>=24.1.0

COPY agents/web-scraper/src/ ./src/

ENV PYTHONPATH="/app"

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:3004/health || exit 1

EXPOSE 3004

CMD ["uvicorn", "src.server:app", "--host", "0.0.0.0", "--port", "3004"]
