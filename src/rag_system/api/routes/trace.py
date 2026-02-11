"""Trace endpoint."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from rag_system.models.api import EvidenceItem, TraceDetail
from rag_system.models.database import QueryTraceModel
from rag_system.providers.database import get_db_session

router = APIRouter()


@router.get("/trace/{trace_id}", response_model=TraceDetail)
async def get_trace(
    trace_id: UUID,
    db: Annotated[Session, Depends(get_db_session)],
) -> TraceDetail:
    """Get trace details by ID."""
    trace = db.query(QueryTraceModel).filter(QueryTraceModel.trace_id == trace_id).first()

    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")

    # Build evidence items
    evidence = [
        EvidenceItem(
            citation_number=cit.citation_number,
            doc_title=cit.doc_title or "",
            section_title=cit.section_title,
            url=cit.url,
            relevance_score=cit.relevance_score or 0.0,
            excerpt="",  # Not stored in trace
        )
        for cit in trace.citations
    ]

    # Get answer
    answer_text = trace.answers[0].answer_text if trace.answers else ""
    generation_time = trace.answers[0].generation_time_ms if trace.answers else 0
    token_count = trace.answers[0].token_count if trace.answers else 0

    return TraceDetail(
        trace_id=str(trace.trace_id),
        query_text=trace.query_text,
        answer_text=answer_text,
        citations=evidence,
        confidence=trace.confidence,
        user_id=trace.user_id,
        timestamp=trace.timestamp,
        models={
            "embedding": trace.embedding_model or "",
            "reranker": trace.reranker_model or "",
            "llm": trace.llm_model or "",
        },
        metrics={
            "generation_time_ms": generation_time,
            "token_count": token_count,
            "num_citations": len(evidence),
        },
    )
