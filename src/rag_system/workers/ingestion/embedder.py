"""Embedding model provider"""

import os
from functools import lru_cache

from codetiming import Timer

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class EmbedderProvider:
    """Embedding model provider - Cloud APIs only."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.embedding
        self.provider = self.config.provider
        self.model = self.config.model

        logger.info(f"Initializing embedding provider: {self.provider}")

        if self.provider == "voyage":
            self._init_voyage()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ModelError(f"Unsupported embedding provider: {self.provider}")

        self.dimension = 1024 if self.provider == "voyage" else 3072
        logger.info(f"Embedding provider configured: {self.provider}:{self.model} ({self.dimension}d)")

    def _init_voyage(self) -> None:
        """Initialize Voyage AI."""
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ModelError("VOYAGE_API_KEY environment variable not set")
        try:
            import voyageai
            self.voyage_client = voyageai.Client(api_key=api_key)
        except ImportError:
            raise ModelError("voyageai package not installed. Run: pip install voyageai")

    def _init_openai(self) -> None:
        """Initialize OpenAI."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ModelError("OPENAI_API_KEY environment variable not set")
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
        except ImportError:
            raise ModelError("openai package not installed. Run: pip install openai")

    def embed(self, text: str) -> list[float]:
        """Embed single text."""
        return self.embed_batch([text])[0]

    @Timer(name="embed_batch", text="Embedded {count} texts in {:.3f}s", logger=None)
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch of texts."""
        logger.debug(f"Embedding batch of {len(texts)} texts with {self.provider}")
        
        if self.provider == "voyage":
            return self._embed_voyage(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)

    def _embed_voyage(self, texts: list[str]) -> list[list[float]]:
        """Embed using Voyage AI."""
        try:
            result = self.voyage_client.embed(
                texts=texts,
                model=self.model,
                input_type="document"
            )
            return result.embeddings
        except Exception as e:
            logger.error(f"Voyage AI embedding failed: {e}", exc_info=True)
            raise ModelError(f"Voyage AI embedding failed: {e}") from e

    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Embed using OpenAI."""
        try:
            response = self.openai_client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}", exc_info=True)
            raise ModelError(f"OpenAI embedding failed: {e}") from e


@lru_cache
def get_embedder_provider() -> EmbedderProvider:
    """Get cached embedder provider."""
    return EmbedderProvider()