"""Vision model provider."""

from functools import lru_cache
from pathlib import Path

import httpx

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class VisionProvider:
    """Vision model provider for image descriptions (Ollama only for now)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.vision
        self.provider = self.config.provider

        logger.info(f"Initializing vision provider: {self.provider}")

        if self.provider == "ollama":
            self.client = httpx.Client(base_url=self.config.base_url, timeout=300.0)  # 5 minutes for vision
            logger.info(f"Ollama vision client configured: {self.config.base_url}")
        else:
            raise ModelError(f"Unsupported vision provider: {self.provider}. Only 'ollama' is currently supported.")

    def describe_image(self, image_path: str) -> str:
        """Generate description for image."""
        logger.debug(f"Describing image: {image_path}")

        try:
            description = self._describe_ollama(image_path)

            logger.info(
                "Image description generated",
                extra={
                    "image_path": image_path,
                    "description_length": len(description),
                },
            )

            return description

        except Exception as e:
            logger.error(f"Image description failed for {image_path}: {e}", exc_info=True)
            raise ModelError(f"Image description failed: {e}") from e

    def _describe_ollama(self, image_path: str) -> str:
        """Describe using Ollama LLaVA."""
        # Load and encode image as base64
        import base64
        with Path(image_path).open("rb") as f:
            image_data = base64.b64encode(f.read()).decode()

        response = self.client.post(
            "/api/generate",
            json={
                "model": self.config.model,
                "prompt": "Describe this image in detail for documentation purposes. Focus on technical content, diagrams, and any text visible.",
                "images": [image_data],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]


@lru_cache
def get_vision_provider() -> VisionProvider:
    """Get cached vision provider."""
    return VisionProvider()
