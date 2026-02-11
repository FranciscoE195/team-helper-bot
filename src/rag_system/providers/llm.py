"""LLM provider."""

import os
import time
from functools import lru_cache

import httpx

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class LLMProvider:
    """LLM provider supporting Ollama and Groq."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.llm
        self.provider = self.config.provider

        logger.info(f"Initializing LLM provider: {self.provider}")

        if self.provider == "ollama":
            self.client = httpx.Client(base_url=self.config.base_url, timeout=300.0)  # 5 minutes for LLM generation
            logger.info(f"Ollama client configured: {self.config.base_url}")
        elif self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ModelError("GROQ_API_KEY environment variable not set")
            from groq import Groq
            self.groq_client = Groq(api_key=api_key)
            logger.info(f"Groq client configured with model: {self.config.model}")
        else:
            raise ModelError(f"Unsupported LLM provider: {self.provider}. Supported: 'ollama', 'groq'")

    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int]:
        """Generate answer from LLM. Returns (text, generation_time_ms)."""
        start_time = time.time()

        logger.debug(
            "Generating LLM response",
            extra={
                "provider": self.provider,
                "model": self.config.model,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
            },
        )

        try:
            if self.provider == "ollama":
                text = self._generate_ollama(system_prompt, user_prompt)
            elif self.provider == "groq":
                text = self._generate_groq(system_prompt, user_prompt)

            generation_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "LLM generation completed",
                extra={
                    "generation_time_ms": generation_time_ms,
                    "response_length": len(text),
                },
            )

            return text, generation_time_ms

        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise ModelError(f"LLM generation failed: {e}") from e

    def _generate_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Ollama."""
        response = self.client.post(
            "/api/generate",
            json={
                "model": self.config.model,
                "prompt": f"{system_prompt}\n\n{user_prompt}",
                "temperature": self.config.temperature,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]

    def _generate_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Groq API."""
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=2000,
        )
        return chat_completion.choices[0].message.content


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Get cached LLM provider."""
    return LLMProvider()
