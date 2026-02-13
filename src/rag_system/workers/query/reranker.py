"""Reranker model provider - Cohere only."""

import os
from functools import lru_cache

from codetiming import Timer

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class RerankerProvider:
    """Reranker model provider - Cohere only."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.reranker
        self.provider = self.config.provider
        self.model = self.config.model

        logger.info(f"Initializing reranker provider: {self.provider}")

        if self.provider != "cohere":
            raise ModelError(f"Unsupported reranker provider: {self.provider}. Only 'cohere' is supported.")

        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ModelError("COHERE_API_KEY environment variable not set")
        
        try:
            import cohere
            self.cohere_client = cohere.Client(api_key=api_key)
        except ImportError:
            raise ModelError("cohere package not installed. Run: pip install cohere")

        logger.info(f"Cohere reranker configured: {self.model}")

    def score(self, query: str, text: str) -> float:
        """Score single query-text pair."""
        return self.score_batch(query, [text])[0]

    @Timer(name="rerank_batch", text="Reranked {count} pairs in {:.3f}s", logger=None)
    def score_batch(self, query: str, texts: list[str]) -> list[float]:
        """Score batch of query-text pairs."""
        logger.debug(f"Reranking batch of {len(texts)} texts with Cohere")
        
        try:
            results = self.cohere_client.rerank(
                model=self.model,
                query=query,
                documents=texts,
                top_n=len(texts),
                return_documents=False
            )
            
            # Create score map maintaining original order
            score_map = {result.index: result.relevance_score for result in results.results}
            scores = [score_map.get(i, 0.0) for i in range(len(texts))]
            return scores
            
        except Exception as e:
            logger.error(f"Cohere reranking failed: {e}", exc_info=True)
            raise ModelError(f"Cohere reranking failed: {e}") from e


@lru_cache
def get_reranker_provider() -> RerankerProvider:
    """Get cached reranker provider."""
    return RerankerProvider()