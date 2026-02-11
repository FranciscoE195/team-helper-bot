"""Health check endpoint."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rag_system.models.api import HealthResponse
from rag_system.providers.database import get_db_session
from rag_system.providers.embedder import get_embedder_provider
from rag_system.providers.llm import get_llm_provider
from rag_system.providers.reranker_model import get_reranker_provider

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Annotated[Session, Depends(get_db_session)]) -> HealthResponse:
    """Check system health."""
    checks = {
        "database": False,
        "embedding_model": False,
        "reranker_model": False,
        "llm": False,
    }

    # Check database
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    # Check models (already loaded at startup)
    try:
        get_embedder_provider()
        checks["embedding_model"] = True
    except Exception:
        pass

    try:
        get_reranker_provider()
        checks["reranker_model"] = True
    except Exception:
        pass

    try:
        get_llm_provider()
        checks["llm"] = True
    except Exception:
        pass

    # Determine status
    all_healthy = all(checks.values())
    any_healthy = any(checks.values())

    if all_healthy:
        status = "healthy"
    elif any_healthy:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        database=checks["database"],
        embedding_model=checks["embedding_model"],
        reranker_model=checks["reranker_model"],
        llm=checks["llm"],
        timestamp=datetime.utcnow(),
    )
