"""Trace logger worker - logs query traces to database."""

from uuid import uuid4

from sqlalchemy.orm import Session

from rag_system.config import get_logger, get_settings
from rag_system.models.database import (
    QueryTraceModel,
    TraceAnswerModel,
    TraceCitationModel,
)
from rag_system.models.domain import FilteredEvidence, GeneratedAnswer

logger = get_logger(__name__)


class TraceLogger:
    """Log query traces for audit trail."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def log(
        self,
        query: str,
        evidence: FilteredEvidence,
        answer: GeneratedAnswer,
        user_id: str | None,
    ) -> str:
        """Log query trace and return trace_id."""
        trace_id = uuid4()

        logger.debug(f"Logging trace: {trace_id}")

        # Create trace record
        trace = QueryTraceModel(
            trace_id=trace_id,
            query_text=query,
            user_id=user_id,
            confidence=evidence.confidence,
            embedding_model=self.settings.models.embedding.model_name,
            reranker_model=self.settings.models.reranker.model_name,
            llm_model=self.settings.models.llm.model,
        )
        self.db.add(trace)

        # Create citations
        for ev in evidence.evidence:
            citation = TraceCitationModel(
                trace_id=trace_id,
                section_id=ev.section.section_id,
                citation_number=ev.citation_number,
                relevance_score=ev.relevance_score,
                doc_title=ev.section.doc_title,
                section_title=ev.section.title,
                url=ev.section.url,
            )
            self.db.add(citation)

        # Create answer record
        answer_record = TraceAnswerModel(
            trace_id=trace_id,
            answer_text=answer.text,
            generation_time_ms=answer.generation_time_ms,
            token_count=answer.token_count,
        )
        self.db.add(answer_record)

        # Commit transaction
        try:
            self.db.commit()
            logger.info(
                "Trace logged successfully",
                extra={
                    "trace_id": str(trace_id),
                    "num_citations": len(evidence.evidence),
                },
            )
        except Exception as e:
            logger.error(f"Failed to log trace: {e}", exc_info=True)
            self.db.rollback()
            raise

        return str(trace_id)
