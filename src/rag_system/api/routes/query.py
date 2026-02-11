"""Query endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from rag_system.api.dependencies import get_query_service
from rag_system.config import get_logger
from rag_system.exceptions import InsufficientEvidenceError, QueryError
from rag_system.models.api import QueryRequest, QueryResponse
from rag_system.services.query_service import QueryService

router = APIRouter()
logger = get_logger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    service: Annotated[QueryService, Depends(get_query_service)],
) -> QueryResponse:
    """Query the documentation."""
    logger.info(
        "Received query request",
        extra={
            "question": request.question[:100],
            "max_sources": request.max_sources,
            "user_id": request.user_id,
        },
    )

    try:
        response = service.query(
            question=request.question,
            max_sources=request.max_sources,
            user_id=request.user_id,
        )
        logger.info(
            "Query completed successfully",
            extra={"trace_id": response.trace_id},
        )
        return response

    except InsufficientEvidenceError as e:
        logger.warning(f"Insufficient evidence: {e}")
        # Return a response with insufficient confidence instead of error
        from datetime import datetime
        return QueryResponse(
            answer=str(e),
            confidence="insufficient",
            evidence=[],
            trace_id="",
            query=request.question,
            timestamp=datetime.now(),
            generation_time_ms=0,
            models_used={"embedding": "", "reranker": "", "llm": ""}
        )

    except QueryError as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {e}")

    except Exception as e:
        logger.error(f"Unexpected error in query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
