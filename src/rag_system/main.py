"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_system.api.routes import health, query, trace, webhook
from rag_system.config import get_logger, get_settings, setup_logging
from rag_system.providers.database import get_database_provider

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    settings = get_settings()

    # Setup logging
    setup_logging(settings.logging)
    logger.info("Starting RAG System...")

    try:
        # Initialize database
        db_provider = get_database_provider()
        logger.info("Database connected successfully")

        # Note: ML models are loaded lazily on first request to avoid startup timeout
        logger.info("RAG System ready to accept requests (models will load on first use)")

    except Exception as e:
        logger.error(f"Failed to start RAG System: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG System...")


app = FastAPI(
    title="BPI RAG System API",
    description="Retrieval-Augmented Generation system for team documentation",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(trace.router, prefix="/api", tags=["trace"])
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "service": "BPI RAG System",
        "version": "0.1.0",
        "docs": "/docs",
    }
