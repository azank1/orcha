FROM --platform=linux/amd64 python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# ── Deps layer (cached unless pyproject.toml / uv.lock change) ───────────────
COPY pyproject.toml uv.lock ./
RUN uv export --no-hashes --frozen --no-dev > /tmp/req.txt && \
    uv pip install --system --no-cache -r /tmp/req.txt && \
    python3 -c "import pydantic_core, fastapi"

# ── Source layer (only invalidates when code changes) ─────────────────────────
COPY core/ ./core/
COPY tools/ ./tools/
COPY integrations/ ./integrations/
COPY onboarding/ ./onboarding/
COPY main.py agent_card.json ./

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
