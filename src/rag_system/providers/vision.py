"""Vision model provider - Anthropic only."""

import base64
import os
from functools import lru_cache
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class VisionProvider:
    """Vision model provider"""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.vision
        self.provider = self.config.provider
        self.model = self.config.model

        logger.info(f"Initializing vision provider: {self.provider}")

        if self.provider != "anthropic":
            raise ModelError(f"Unsupported vision provider: {self.provider}. Only 'anthropic' is supported.")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ModelError("ANTHROPIC_API_KEY environment variable not set")
        
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ModelError("anthropic package not installed. Run: pip install anthropic")

        logger.info(f"Anthropic Vision configured: {self.model}")

    def describe_image(self, image_path: str) -> str:
        """Generate description for image."""
        logger.debug(f"Describing image: {image_path}")

        try:
            description = self._describe_anthropic(image_path)

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _describe_anthropic(self, image_path: str) -> str:
        """Describe using Anthropic Claude Vision with automatic retry."""
        from PIL import Image
        
        # Detect actual image format using PIL
        try:
            with Image.open(image_path) as img:
                img_format = img.format.upper()
                
            format_to_mime = {
                'JPEG': 'image/jpeg',
                'PNG': 'image/png',
                'GIF': 'image/gif',
                'WEBP': 'image/webp',
                'JPG': 'image/jpeg',
            }
            media_type = format_to_mime.get(img_format, 'image/jpeg')
            
        except Exception as e:
            logger.warning(f"Could not detect image format for {image_path}, defaulting to jpeg: {e}")
            media_type = 'image/jpeg'
        
        # Load and encode image
        with Path(image_path).open("rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        message = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "Descreva esta imagem técnica de forma detalhada para documentação. Foque em conteúdo técnico, diagramas, e qualquer texto visível."
                        }
                    ]
                }
            ]
        )
        
        return message.content[0].text


@lru_cache
def get_vision_provider() -> VisionProvider:
    """Get cached vision provider."""
    return VisionProvider()