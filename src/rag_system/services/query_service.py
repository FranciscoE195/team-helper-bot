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
from rag_system.workers.query.query_validator import get_query_validator
from rag_system.workers.query.reranker import get_reranker_provider
from rag_system.workers.query.trace_logger import TraceLogger

logger = get_logger(__name__)


class QueryService:
    """Query service orchestrating the full pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

        # Initialize workers
        self.validator = get_query_validator()
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

        # Step 0: Validate query scope
        logger.debug("Step 0: Query validation")
        self.validator.validate(question)  # Raises InsufficientEvidenceError if out-of-scope

        # Step 1: Hybrid search
        logger.debug("Step 1: Hybrid search")
        with Timer(name="hybrid_search", text="Hybrid search: {:.3f}s", logger=logger.debug):
            search_results = self.searcher.search(question)
        logger.info(f"Found {len(search_results)} candidate sections")

        # Step 2: Rerank
        logger.debug("Step 2: Reranking")
        with Timer(name="rerank", text="Reranking: {:.3f}s", logger=logger.debug):
            texts = [s.section.content for s in search_results]
            scores = self.reranker.score_batch(question, texts)
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
                "Não tenho informação suficiente nas fontes disponíveis para responder a essa pergunta com confiança. "
                "Tente reformular a pergunta ou use termos mais específicos relacionados com a documentação técnica."
            )

        # Step 4: Build context
        logger.debug("Step 4: Context building")
        context = self.context_builder.build(filtered_evidence.evidence)

        # Step 5: Generate answer
        logger.debug("Step 5: Answer generation")
        with Timer(name="answer_generation", text="Answer generation: {:.3f}s", logger=logger.debug):
            answer = self.generator.generate(question, context)

        # Step 6: Log trace
        logger.debug("Step 6: Trace logging")
        trace_id = self.trace_logger.log(question, filtered_evidence, answer, user_id)

        # Build response - sort evidence by relevance (highest first)
        sorted_evidence = sorted(
            filtered_evidence.evidence,
            key=lambda ev: ev.relevance_score,
            reverse=True
        )
        
        # Create mapping from old citation numbers to new ones
        citation_mapping = {
            ev.citation_number: new_num + 1
            for new_num, ev in enumerate(sorted_evidence)
        }
        
        # Update citation numbers in the answer text
        answer_text = answer.text
        for old_num, new_num in sorted(citation_mapping.items(), reverse=True):
            # Replace [old] with [new], but use temporary placeholders to avoid conflicts
            answer_text = answer_text.replace(f'[{old_num}]', f'[TEMP_{new_num}]')
        
        # Replace temporary placeholders with final numbers
        for new_num in citation_mapping.values():
            answer_text = answer_text.replace(f'[TEMP_{new_num}]', f'[{new_num}]')
        
        evidence_items = [
            EvidenceItem(
                citation_number=new_num + 1,  # Use new sequential numbering
                doc_title=ev.section.doc_title,
                section_title=ev.section.title,
                excerpt=ev.section.content,
                url=ev.section.url,
                relevance_score=ev.relevance_score,
            )
            for new_num, ev in enumerate(sorted_evidence)
        ]

        response = QueryResponse(
            answer=answer_text,  # Use updated answer with renumbered citations
            evidence=evidence_items,
            confidence=filtered_evidence.confidence,
            trace_id=trace_id,
            generation_time_ms=answer.generation_time_ms,
            query=question,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            models_used={
                "embedder": f"{self.settings.models.embedding.provider}:{self.settings.models.embedding.model}",
                "reranker": f"{self.settings.models.reranker.provider}:{self.settings.models.reranker.model}",
                "llm": f"{self.settings.models.llm.provider}:{self.settings.models.llm.model}",
                "vision": f"{self.settings.models.vision.provider}:{self.settings.models.vision.model}",
                "validator": f"{self.settings.models.validator.provider}:{self.settings.models.validator.model}"
            }
        )

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            "Query pipeline completed successfully",
            extra={
                "elapsed_seconds": round(elapsed, 2),
                "num_evidence": len(evidence_items),
                "confidence": filtered_evidence.confidence,
            },
        )

        return response