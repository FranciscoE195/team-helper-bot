"""Reranker worker - uses cross-encoder for accurate relevance scoring."""

from rag_system.config import get_settings
from rag_system.models.domain import RankedSection, SearchResult
from rag_system.providers.reranker_model import get_reranker_provider


class Reranker:
    """Reranker using cross-encoder model."""

    def __init__(self):
        self.settings = get_settings()
        self.reranker = get_reranker_provider()
        self.top_k = self.settings.search.rerank.top_k

    def rerank(self, query: str, search_results: list[SearchResult]) -> list[RankedSection]:
        """Rerank search results using cross-encoder."""
        if not search_results:
            return []

        # Extract sections and contents
        sections = [result.section for result in search_results]
        contents = [section.content for section in sections]

        # Score all sections with reranker
        scores = self.reranker.score_batch(query, contents)

        # Create ranked sections
        ranked = [
            RankedSection(section=section, rerank_score=float(score))
            for section, score in zip(sections, scores)
        ]

        # Sort by rerank score and take top k
        ranked.sort(key=lambda x: x.rerank_score, reverse=True)

        return ranked[: self.top_k]
