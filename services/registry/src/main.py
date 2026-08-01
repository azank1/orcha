"""Main entry point for Registry service."""

from contextlib import asynccontextmanager

import grpc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.kafka.src import KafkaProducer, KafkaProducerConfig
from common.proto.src import registry_pb2_grpc
from common.utils.src.logging_config import setup_logging

from .api import v1_router
from .api.dependencies import db
from .background import HealthMonitor
from .config import settings
from .grpc_server import RegistryServicer

# Setup logging
logger = setup_logging(settings.service_name, settings.log_level)

# Global references
grpc_server = None
health_monitor = None
kafka_producer: KafkaProducer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown of:
    - Database connection
    - gRPC server
    - Kafka producer (optional — skipped if KAFKA_BOOTSTRAP_SERVERS not set)
    """
    global grpc_server, health_monitor, kafka_producer

    logger.info(f"Starting {settings.service_name} v{settings.service_version}")

    # 1. Connect to database
    logger.info("Connecting to database...")
    await db.connect()
    logger.info("✓ Database connected")

    # 2. Start gRPC server
    logger.info(f"Starting gRPC server on port {settings.grpc_port}...")
    grpc_server = grpc.aio.server()
    registry_pb2_grpc.add_RegistryServiceServicer_to_server(
        RegistryServicer(db), grpc_server
    )
    grpc_server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    await grpc_server.start()
    logger.info(f"✓ gRPC server started on port {settings.grpc_port}")

    # 3. Start health monitor
    logger.info("Starting health monitor...")
    health_monitor = HealthMonitor(db)
    await health_monitor.start()
    logger.info("✓ Health monitor started")

    # 4. Start Kafka producer (optional — degrades gracefully if not configured)
    if settings.kafka_enabled and settings.kafka_bootstrap_servers:
        logger.info("Starting Kafka producer...")
        kafka_producer = KafkaProducer(
            KafkaProducerConfig(bootstrap_servers=settings.kafka_bootstrap_servers)
        )
        await kafka_producer.start()
        logger.info("✓ Kafka producer started")
    else:
        logger.info(
            "Kafka disabled (KAFKA_ENABLED=false or KAFKA_BOOTSTRAP_SERVERS not set) "
            "— agent registration events will not be emitted"
        )

    app.state.kafka_producer = kafka_producer

    logger.info(f"✓ {settings.service_name} ready to accept requests")

    # Application is running
    yield

    # Shutdown
    logger.info("Shutting down...")

    # Stop Kafka producer
    if kafka_producer:
        await kafka_producer.stop()
        logger.info("✓ Kafka producer stopped")

    # Stop health monitor
    if health_monitor:
        await health_monitor.stop()

    # Stop gRPC server
    if grpc_server:
        await grpc_server.stop(grace=5)
        logger.info("✓ gRPC server stopped")

    # Disconnect database
    await db.disconnect()
    logger.info("✓ Database disconnected")

    logger.info(f"✓ {settings.service_name} shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Orcha Registry Service",
    description="Agent registration and manifest management service",
    version=settings.service_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(v1_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
