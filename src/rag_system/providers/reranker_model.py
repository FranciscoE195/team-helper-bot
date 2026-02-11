"""Reranker model provider."""

from functools import lru_cache

from codetiming import Timer
from sentence_transformers import CrossEncoder

from rag_system.config import get_logger, get_settings

logger = get_logger(__name__)


class RerankerProvider:
    """Reranker model provider."""

    def __init__(self) -> None:
        settings = get_settings()
        config = settings.models.reranker

        logger.info(f"Loading reranker model: {config.model_name}")
        
        # Resolve cache_dir to absolute path and determine model path
        from pathlib import Path
        import os
        
        # Set offline environment variables
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        
        # Determine model path - if cache_dir exists, load from local path
        model_path = config.model_name
        if config.cache_dir:
            cache_path = Path(config.cache_dir).resolve()
            local_model_path = cache_path / config.model_name.replace('/', '--').replace('BAAI--', '')
            if not local_model_path.exists():
                # Try without transformation
                local_model_path = cache_path / config.model_name.split('/')[-1]
            
            if local_model_path.exists():
                model_path = str(local_model_path)
                logger.info(f"Loading from local path: {model_path}")
            else:
                logger.warning(f"Local model not found at {local_model_path}, will try online")
        
        with Timer(name="reranker_model_load", text="Reranker model loaded in {:.2f}s", logger=logger.info):
            self.model = CrossEncoder(
                model_path,
                device=config.device,
            )

        self.batch_size = config.batch_size

    def score(self, query: str, text: str) -> float:
        """Score single query-text pair."""
        return self.score_batch(query, [text])[0]

    @Timer(name="rerank_batch", text="Reranked {count} pairs in {:.3f}s", logger=None)
    def score_batch(self, query: str, texts: list[str]) -> list[float]:
        """Score batch of query-text pairs."""
        logger.debug(f"Reranking batch of {len(texts)} texts")
        pairs = [[query, text] for text in texts]
        scores = self.model.predict(
            pairs,
            batch_size=self.batch_size,
            show_progress_bar=False,
        )
        return scores.tolist()


@lru_cache
def get_reranker_provider() -> RerankerProvider:
    """Get cached reranker provider."""
    return RerankerProvider()
