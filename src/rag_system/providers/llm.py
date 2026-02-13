"""LLM provider."""

import os
import time
from functools import lru_cache

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from rag_system.config import get_logger, get_settings
from rag_system.exceptions import ModelError

logger = get_logger(__name__)


class LLMProvider:
    """LLM provider - Cloud APIs only."""

    def __init__(self) -> None:
        settings = get_settings()
        self.config = settings.models.llm
        self.provider = self.config.provider
        self.model = self.config.model

        logger.info(f"Initializing LLM provider: {self.provider}")

        if self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "groq":
            self._init_groq()
        else:
            raise ModelError(f"Unsupported LLM provider: {self.provider}")

        logger.info(f"LLM provider configured: {self.provider}:{self.model}")

    def _init_anthropic(self) -> None:
        """Initialize Anthropic Claude."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ModelError("ANTHROPIC_API_KEY environment variable not set")
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
        except ImportError:
            raise ModelError("anthropic package not installed. Run: pip install anthropic")

    def _init_groq(self) -> None:
        """Initialize Groq."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ModelError("GROQ_API_KEY environment variable not set")
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=api_key)
        except ImportError:
            raise ModelError("groq package not installed. Run: pip install groq")

    def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int]:
        """Generate answer from LLM. Returns (text, generation_time_ms)."""
        start_time = time.time()

        logger.debug(
            "Generating LLM response",
            extra={
                "provider": self.provider,
                "model": self.model,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
            },
        )

        try:
            if self.provider == "anthropic":
                text = self._generate_anthropic(system_prompt, user_prompt)
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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _generate_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Anthropic Claude API with automatic retry."""
        message = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        return message.content[0].text

    def _generate_groq(self, system_prompt: str, user_prompt: str) -> str:
        """Generate using Groq API."""
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return chat_completion.choices[0].message.content


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Get cached LLM provider."""
    return LLMProvider()