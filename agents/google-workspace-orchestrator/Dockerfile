FROM --platform=linux/amd64 python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Astral's static binary dispatches `uvx` by argv0 — symlink so workspace-mcp spawn works on loopback.
RUN ln -sf /usr/local/bin/uv /usr/local/bin/uvx

WORKDIR /app

# ── Deps layer (cached unless pyproject.toml / uv.lock change) ───────────────
COPY pyproject.toml uv.lock ./
RUN uv export --no-hashes --frozen --no-dev > /tmp/req.txt && \
    uv pip install --system --no-cache -r /tmp/req.txt && \
    uv pip install --system --no-cache "workspace-mcp~=1.20.0" && \
    python3 -c "import pydantic_core, fastapi" && \
    command -v workspace-mcp

# ── Source layer (only invalidates when code changes) ─────────────────────────
COPY src/ ./src/

# Default: spawn workspace-mcp on loopback (see server lifespan). WORKSPACE_MCP_URL only if MCP runs elsewhere.
EXPOSE 8080
# Lightsail / platform often inject PORT; default 8080 to match EXPOSE.
CMD ["sh", "-c", "exec uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
