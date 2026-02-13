"""Query service - orchestrates the query pipeline."""

from datetime import datetime

from codetiming import Timer
from sqlalchemy.orm import Session

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import InsufficientEvidenceError
from rag_system.models.api import EvidenceItem, QueryResponse
from rag_system.models.domain import RankedSection
from rag_system.workers.query.answer_generator import AnswerGenerator
from rag_system.workers.query.context_builder import ContextBuilder
from rag_system.workers.query.evidence_filter import EvidenceFilter
from rag_system.workers.query.hybrid_searcher import HybridSearcher
from rag_system.workers.query.reranker import get_reranker_provider
from rag_system.workers.query.trace_logger import TraceLogger

logger = get_logger(__name__)


class QueryService:
    """Query service orchestrating the full pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

        # Initialize workers
        self.searcher = HybridSearcher(db)
        self.reranker = get_reranker_provider()
        self.filter = EvidenceFilter()
        self.context_builder = ContextBuilder(db)
        self.generator = AnswerGenerator()
        self.trace_logger = TraceLogger(db)

    @Timer(name="query_pipeline", text="Query pipeline completed in {:.2f}s", logger=logger.info)
    def query(self, question: str, max_sources: int, user_id: str | None) -> QueryResponse:
        """Execute full query pipeline."""
        start_time = datetime.utcnow()

        logger.info(
            "Starting query pipeline",
            extra={
                "question": question,
                "max_sources": max_sources,
                "user_id": user_id,
            },
        )

        # Step 1: Hybrid search
        logger.debug("Step 1: Hybrid search")
        with Timer(name="hybrid_search", text="Hybrid search: {:.3f}s", logger=logger.debug):
            search_results = self.searcher.search(question)
        logger.info(f"Found {len(search_results)} candidate sections")

        # Step 2: Rerank
        logger.debug("Step 2: Reranking")
        with Timer(name="rerank", text="Reranking: {:.3f}s", logger=logger.debug):
            # Prepara textos para reranking
            texts = [s.section.content for s in search_results]
            scores = self.reranker.score_batch(question, texts)
            # Cria RankedSection para EvidenceFilter
            ranked_sections = [
                RankedSection(section=s.section, rerank_score=score)
                for s, score in zip(search_results, scores)
            ]
        logger.info(f"Reranked to {len(ranked_sections)} top sections")

        # Step 3: Filter evidence
        logger.debug("Step 3: Evidence filtering")
        filtered_evidence = self.filter.filter(ranked_sections, max_sources)
        logger.info(
            f"Filtered to {len(filtered_evidence.evidence)} evidence items",
            extra={
                "confidence": filtered_evidence.confidence,
                "citation_numbers": [ev.citation_number for ev in filtered_evidence.evidence],
                "scores": [round(ev.relevance_score, 3) for ev in filtered_evidence.evidence]
            },
        )

        # Check if we have enough evidence
        if filtered_evidence.confidence == "insufficient":
            logger.warning("Insufficient evidence to answer question")
            raise InsufficientEvidenceError(
                "Não encontrei evidências suficientes para responder à sua pergunta. Por favor, tente reformular ou fornecer mais detalhes."
            )

        # Step 4: Build context
        logger.debug("Step 4: Building context")
        with Timer(name="context_build", text="Context building: {:.3f}s", logger=logger.debug):
            context = self.context_builder.build(filtered_evidence.evidence)
        logger.debug(f"Context built: {len(context)} characters")

        # Step 5: Generate answer
        logger.debug("Step 5: Generating answer")
        with Timer(name="answer_generation", text="Answer generation: {:.3f}s", logger=logger.debug):
            generated_answer = self.generator.generate(question, context)
        logger.info(
            "Answer generated",
            extra={
                "generation_time_ms": generated_answer.generation_time_ms,
                "token_count": generated_answer.token_count,
            },
        )
        # print everything in generated_answer for debugging
        logger.info(f"Generated answer details: {generated_answer.text}")

        # Step 6: Log trace
        logger.debug("Step 6: Logging trace")
        trace_id = self.trace_logger.log(
            query=question,
            evidence=filtered_evidence,
            answer=generated_answer,
            user_id=user_id,
        )
        logger.info(f"Trace logged: {trace_id}")

        # Step 7: Package response
        evidence_items = [
            EvidenceItem(
                citation_number=ev.citation_number,
                doc_title=ev.section.doc_title,
                section_title=ev.section.title or "",
                url=ev.section.url,
                relevance_score=ev.relevance_score,
                excerpt=ev.section.content[:500] + "..." if len(ev.section.content) > 500 else ev.section.content,
            )
            for ev in filtered_evidence.evidence
        ]

        response = QueryResponse(
            trace_id=trace_id,
            query=question,
            answer=generated_answer.text,
            evidence=evidence_items,
            confidence=filtered_evidence.confidence,
            timestamp=start_time,
            generation_time_ms=generated_answer.generation_time_ms,
            models_used={
                "embedding": self.settings.models.embedding.model,
                "reranker": self.settings.models.reranker.model,
                "llm": self.settings.models.llm.model,
            },
        )

        logger.info("Query pipeline completed successfully")
        return response
