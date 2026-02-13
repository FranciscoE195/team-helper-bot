"""Embedding model provider."""

import os
import time
import logging
from functools import lru_cache

from codetiming import Timer
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class VoyageRateLimiter:
    """Rate limiter for Voyage AI free tier (3 RPM, 10K TPM)."""
    
    def __init__(self, calls_per_minute: int = 3):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_called = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit."""
        elapsed = time.time() - self.last_called
        wait_time = self.min_interval - elapsed
        
        if wait_time > 0 and self.last_called > 0:
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s (Voyage AI: {self.calls_per_minute} RPM)")
            time.sleep(wait_time)
        
        self.last_called = time.time()


class EmbedderProvider:
    """Embedding model provider supporting local (HuggingFace) and cloud (Voyage, OpenAI)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.embedding
        self.provider = self.config.provider
        self.model = self.config.model
        self.voyage_limiter = VoyageRateLimiter(calls_per_minute=3)

        if self.provider == "voyage":
            self._init_voyage()
        elif self.provider == "openai":
            self._init_openai()
        else:
            raise ModelError(f"Unsupported embedding provider: {self.provider}")

        self.dimension = 1024 if self.provider == "voyage" else 3072
        logger.info(f"Embedding provider configured: {self.provider}:{self.model} ({self.dimension}d)")

    def _init_voyage(self) -> None:
        """Initialize Voyage AI embedding model."""
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise ModelError("VOYAGE_API_KEY environment variable not set")
        try:
            import voyageai
            self.voyage_client = voyageai.Client(api_key=api_key)
            logger.info(f"Voyage AI configured with model: {self.model}")
        except ImportError:
            raise ModelError("voyageai package not installed. Run: pip install voyageai")

    def _init_openai(self) -> None:
        """Initialize OpenAI embedding model."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ModelError("OPENAI_API_KEY environment variable not set")
        try:
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=api_key)
            logger.info(f"OpenAI configured with model: {self.model}")
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
        else:
            raise ModelError(f"Unsupported embedding provider: {self.provider}")

    def _embed_voyage(self, texts: list[str]) -> list[list[float]]:
        """
        Embed using Voyage AI (batch, rate limit).
        """
        try:
            # Batch size to avoid overwhelming API
            batch_size = 8  # Conservative batch size for free tier
            all_embeddings = []
            
            total_batches = (len(texts) + batch_size - 1) // batch_size
            logger.info(f"Embedding {len(texts)} texts in {total_batches} batches (Voyage AI)")
            
            for i in range(0, len(texts), batch_size):
                batch_num = (i // batch_size) + 1
                batch = texts[i:i + batch_size]
                
                # Apply rate limiting before each batch
                self.voyage_limiter.wait_if_needed()
                
                logger.debug(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")
                
                # Call API with retry (decorator handles retries)
                embeddings = self._voyage_api_call(batch)
                all_embeddings.extend(embeddings)
                
                logger.debug(f"✓ Batch {batch_num}/{total_batches} complete")
            
            logger.info(f"✓ Successfully embedded {len(all_embeddings)} texts")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Voyage AI embedding failed: {e}", exc_info=True)
            raise ModelError(f"Voyage AI embedding failed: {e}") from e

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True
    )
    def _voyage_api_call(self, texts: list[str]) -> list[list[float]]:
        """
        Make Voyage AI API call with automatic retry.
        
        The @retry decorator handles:
        - Connection errors (RemoteDisconnected)
        - Rate limit errors
        - Timeouts
        """
        try:
            result = self.voyage_client.embed(
                texts=texts,
                model=self.model,
                input_type="document"
            )
            return result.embeddings
        except Exception as e:
            # Log for debugging, then let retry decorator handle it
            logger.debug(f"Voyage API call error (will retry): {type(e).__name__}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True
    )
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