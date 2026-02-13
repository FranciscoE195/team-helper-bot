"""FastAPI application entry point."""
import os
from dotenv import load_dotenv
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag_system.api.routes import health, query, trace, webhook
from rag_system.config import get_logger, get_settings, setup_logging
from rag_system.providers.database import get_database_provider
from rag_system.providers.embedder import get_embedder_provider
from rag_system.providers.reranker_model import get_reranker_provider
from rag_system.providers.llm import get_llm_provider
from rag_system.providers.vision import get_vision_provider
from rag_system.workers.query.query_validator import get_query_validator

logger = get_logger(__name__)

load_dotenv()

version = "0.1.0"

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

        # Preload ML models at startup
        logger.info("Loading ML models...")
        
        # Load embedding model
        embedder = get_embedder_provider()
        model_name = f"{embedder.provider}:{embedder.model}"
        logger.info(f"✓ Embedding model loaded: {model_name}")
        
        # Load reranker model
        reranker = get_reranker_provider()
        reranker_name = f"{reranker.provider}:{reranker.model}"
        logger.info(f"✓ Reranker model loaded: {reranker_name}")
        
        # Load LLM
        llm = get_llm_provider()
        llm_name = f"{llm.provider}:{llm.model}"
        logger.info(f"✓ LLM provider initialized: {llm_name}")
        
        # Load Vision
        vision = get_vision_provider()
        vision_name = f"{vision.provider}:{vision.model}"
        logger.info(f"✓ Vision provider initialized: {vision_name}")
        
        # Load Query Validator
        validator = get_query_validator()
        if validator.enabled:
            validator_name = f"{validator.config.provider}:{validator.model}"
            logger.info(f"✓ Query validator initialized: {validator_name}")
        else:
            logger.info("✓ Query validator: disabled")
        
        logger.info("RAG System ready to accept requests")

    except Exception as e:
        logger.error(f"Failed to start RAG System: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down RAG System...")


app = FastAPI(
    title="BPI RAG System API",
    description="Retrieval-Augmented Generation system for team documentation",
    version=version,
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
        "version": version,
        "docs": "/docs",
    }