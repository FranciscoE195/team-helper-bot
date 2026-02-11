"""Embedding model provider."""

from functools import lru_cache

from codetiming import Timer
from sentence_transformers import SentenceTransformer

from rag_system.config import get_logger, get_settings

logger = get_logger(__name__)


class EmbedderProvider:
    """Embedding model provider."""

    def __init__(self) -> None:
        settings = get_settings()
        config = settings.models.embedding

        logger.info(f"Loading embedding model: {config.model_name}")
        
        # Resolve cache_dir to absolute path
        from pathlib import Path
        import os
        
        # Set offline environment variables
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        os.environ['HF_DATASETS_OFFLINE'] = '1'
        
        # Determine model path - if cache_dir exists, load from local path
        model_path = config.model_name
        if config.cache_dir:
            cache_path = Path(config.cache_dir).resolve()
            local_model_path = cache_path / config.model_name.replace('/', '--').replace('intfloat--', '')
            if not local_model_path.exists():
                # Try without transformation
                local_model_path = cache_path / config.model_name.split('/')[-1]
            
            if local_model_path.exists():
                model_path = str(local_model_path)
                logger.info(f"Loading from local path: {model_path}")
            else:
                logger.warning(f"Local model not found at {local_model_path}, will try online")
        
        with Timer(name="embedding_model_load", text="Embedding model loaded in {:.2f}s", logger=logger.info):
            self.model = SentenceTransformer(
                model_path,
                device=config.device,
            )

        self.batch_size = config.batch_size
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def embed(self, text: str) -> list[float]:
        """Embed single text."""
        return self.embed_batch([text])[0]

    @Timer(name="embed_batch", text="Embedded {count} texts in {:.3f}s", logger=None)
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch of texts."""
        logger.debug(f"Embedding batch of {len(texts)} texts")
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


@lru_cache
def get_embedder_provider() -> EmbedderProvider:
    """Get cached embedder provider."""
    return EmbedderProvider()
