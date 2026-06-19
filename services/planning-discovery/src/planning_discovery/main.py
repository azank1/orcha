"""Main entry point for the Planning & Discovery service."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.llm.src import (
    LLMConfig,
    LLMProviderType,
    SplitLLMProvider,
    create_llm_provider,
)
from common.utils.src.logging_config import setup_logging

from .api import v1_router
from .api.middleware.error_handler import ErrorHandlerMiddleware
from .config import settings
from .db.pool import AsyncpgPool
from .db.prisma import prisma
from .manifest_processing.consumer import ManifestConsumer
from .manifest_processing.embedding_generator import TDWAEmbeddingGenerator
from .manifest_processing.storage import EmbeddingStorage
from .planning.pipeline import OptimizedPlanningPipeline

logger = setup_logging(
    settings.service_name,
    settings.log_level,
    extra_namespaces=["planning_discovery"],
)

# Module-level singletons (populated during lifespan startup)
_pool: AsyncpgPool | None = None
_consumer: ManifestConsumer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and graceful shutdown."""
    global _pool, _consumer

    logger.info("Starting %s v%s", settings.service_name, settings.service_version)

    # 1. Prisma (standard CRUD)
    logger.info("Connecting Prisma client…")
    await prisma.connect()
    logger.info("Prisma connected")

    # 2. asyncpg pool (vector operations)
    logger.info("Creating asyncpg connection pool…")
    _pool = AsyncpgPool(
        dsn=settings.database_url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
    )
    await _pool.connect()
    app.state.pool = _pool
    logger.info("asyncpg pool ready")

    # 3. LLM provider — split: completions on one backend, embeddings on another.
    logger.info(
        "Initialising completion provider (%s) + embedding provider (%s)…",
        settings.llm_completion_provider,
        settings.llm_embedding_provider,
    )
    completion_provider = create_llm_provider(
        LLMConfig(
            provider=LLMProviderType(settings.llm_completion_provider),
            api_key=settings.openrouter_api_key,
            ollama_base_url=settings.ollama_base_url,
            embedding_dimension=settings.llm_embedding_dimension,
        )
    )
    embedding_provider = create_llm_provider(
        LLMConfig(
            provider=LLMProviderType(settings.llm_embedding_provider),
            api_key=settings.openrouter_api_key,
            ollama_base_url=settings.ollama_base_url,
            embedding_dimension=settings.llm_embedding_dimension,
        )
    )
    llm_provider = SplitLLMProvider(
        completion=completion_provider,
        embedding=embedding_provider,
    )

    # 4. Planning pipeline (stateless — reused per-request)
    pipeline = OptimizedPlanningPipeline(
        llm_provider=llm_provider,
        pool=_pool,
        decomposition_model=settings.llm_decomposition_model,
        fallback_model=settings.llm_fallback_model,
        embedding_model=settings.llm_embedding_model,
        validation_model=settings.llm_validation_model,
        top_k_candidates=settings.top_k_candidates,
        similarity_threshold=settings.similarity_threshold,
        confidence_threshold=settings.llm_confidence_threshold,
    )
    app.state.pipeline = pipeline
    logger.info("Planning pipeline initialised")

    # Pre-load cross-encoder in a thread so the first planning request isn't slow.
    # run_in_executor keeps the event loop unblocked while the model loads from disk.
    logger.info("Warming up cross-encoder…")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, pipeline._search.warm_up)
    logger.info("Cross-encoder warm-up complete")

    # 5. Manifest processing components — shared with HTTP test endpoint
    embedding_gen = TDWAEmbeddingGenerator(
        llm_provider=llm_provider,
        embedding_model=settings.llm_embedding_model,
    )
    embedding_storage = EmbeddingStorage(_pool)
    app.state.embedding_gen = embedding_gen
    app.state.embedding_storage = embedding_storage

    # 6. Manifest consumer — BaseKafkaConsumer.start() already spawns the
    #    internal consume-loop task; we just need to keep a reference so the
    #    lifespan can cancel it on shutdown.
    logger.info("Starting manifest Kafka consumer…")
    _consumer = ManifestConsumer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_manifest_group_id,
        pool=_pool,
        embedding_generator=embedding_gen,
    )
    await _consumer.start()
    logger.info("Manifest consumer started")

    # 7. Catch-up indexing — index any active HEALTHY agents that have no
    #    embedding row yet (covers Kafka gaps from restarts or missed events).
    await _catchup_index_missing_embeddings(_pool, embedding_gen, embedding_storage)

    logger.info("%s is ready", settings.service_name)

    # ── Yield — app is running ─────────────────────────────────────────────
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    logger.info("Shutting down %s…", settings.service_name)

    if _consumer:
        await (
            _consumer.stop()
        )  # cancels the internal task and closes the aiokafka consumer
        logger.info("Manifest consumer stopped")

    if _pool:
        await _pool.disconnect()
        logger.info("asyncpg pool closed")

    await prisma.disconnect()
    logger.info("Prisma disconnected")

    logger.info("%s shutdown complete", settings.service_name)


async def _catchup_index_missing_embeddings(
    pool: AsyncpgPool,
    embedding_gen: TDWAEmbeddingGenerator,
    storage: EmbeddingStorage,
) -> None:
    """Index any active HEALTHY agents that have no embedding row.

    Runs once at startup to recover from Kafka gaps — e.g. PnD was down when
    an agent was registered, or the consumer loop crashed before committing.
    """
    from .manifest_processing.template_generator import SemanticTemplateGenerator

    template_gen = SemanticTemplateGenerator()

    sql = """
        SELECT a.id, a.name, a.description, a.tags,
               a.protocol_type::text AS protocol_type,
               a.health_status::text AS health_status,
               a.version, a.provider,
               json_agg(json_build_object(
                   'name', c.name, 'type', c.type::text, 'description', c.description
               )) FILTER (WHERE c.name IS NOT NULL) AS capabilities
        FROM agents a
        LEFT JOIN capabilities c ON c.agent_id = a.id
        WHERE a.is_active = true
          AND a.health_status::text = 'HEALTHY'
          AND a.id NOT IN (SELECT agent_id FROM agent_embeddings)
        GROUP BY a.id
    """
    import json as _json

    rows = await pool.fetch(sql)
    if not rows:
        logger.info("Catch-up indexing: all active agents already have embeddings")
        return

    logger.info(
        "Catch-up indexing: %d agent(s) missing embeddings — indexing now", len(rows)
    )
    for row in rows:
        agent_id = row["id"]
        try:
            caps = row["capabilities"]
            if isinstance(caps, str):
                caps = _json.loads(caps)
            manifest = {
                "name": row["name"],
                "description": row["description"],
                "tags": list(row["tags"] or []),
                "protocol_type": row["protocol_type"],
                "capabilities": caps or [],
            }
            templated = template_gen.generate(manifest)
            embeddings = await embedding_gen.generate(manifest)
            await storage.upsert(agent_id, templated, embeddings)
            logger.info("Catch-up indexed agent %s", agent_id)
        except Exception:
            logger.exception(
                "Catch-up indexing failed for agent %s — skipping", agent_id
            )


# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MetaOrcha Planning & Discovery Service",
    description=(
        "Converts natural-language queries into validated multi-agent workflow DAGs "
        "and maintains semantic embeddings for registered agents."
    ),
    version=settings.service_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(v1_router, prefix="/api")


@app.get("/")
async def root():
    """Service root — basic info."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
