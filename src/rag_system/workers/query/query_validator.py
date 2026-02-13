"""Query validator - uses Claude to filter out-of-scope questions."""

import os
from functools import lru_cache

from rag_system.config import get_logger
from rag_system.exceptions import InsufficientEvidenceError

logger = get_logger(__name__)


class QueryValidator:
    """Validates if queries are within documentation scope using Claude."""

    CLASSIFICATION_PROMPT = """You are a query classifier for a technical documentation RAG system about BPI's automated testing.

Your job: Determine if a user query is IN-SCOPE (about technical documentation) or OUT-OF-SCOPE (greetings, chitchat, personal questions).

**IN-SCOPE examples:**
- "Como executar testes no Jenkins?"
- "O que é o Robot Framework?"
- "Como integrar com RTC?"
- "Quais são os pré-requisitos?"
- "Como fazer deploy?"

**OUT-OF-SCOPE examples:**
- "olá" / "oi" / "como estás?"
- "quem és tu?"
- "obrigado" / "adeus"
- "conta-me uma piada"
- "qual é a capital de França?"

Respond with ONLY ONE WORD:
- "IN-SCOPE" if the query is about technical documentation
- "OUT-OF-SCOPE" if it's a greeting, chitchat, or unrelated question

Query: {query}

Classification:"""

    def __init__(self):
        from rag_system.config import get_settings
        self.settings = get_settings()
        self.config = self.settings.models.validator
        self.enabled = self.config.enabled
        self.model = self.config.model
        self.anthropic_client = None
        if self.enabled:
            self._init_anthropic()

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set, query validation will be skipped")
            return
        
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=api_key)
            logger.info(f"Query scope validation enabled with {self.model}")
        except ImportError:
            logger.warning("anthropic package not installed, query validation will be skipped")

    def validate(self, query: str) -> None:
        """Validate if query is within scope using Claude.
        
        Raises:
            InsufficientEvidenceError: If query is out of scope
        """
        if not self.enabled:
            # Query validation disabled in config
            return
            
        if not self.anthropic_client:
            # If Claude not available, skip validation
            logger.warning("Query validator enabled but Anthropic client not initialized")
            return

        classification = self._classify_query(query)
        
        if classification == "OUT-OF-SCOPE":
            logger.info(f"Query rejected as out-of-scope: {query}")
            raise InsufficientEvidenceError(
                "Não tenho informação suficiente para responder a essa pergunta. "
                "Por favor, faça perguntas sobre a documentação técnica interna."
            )

    def _classify_query(self, query: str) -> str:
        """Classify query as IN-SCOPE or OUT-OF-SCOPE using Claude."""
        try:
            message = self.anthropic_client.messages.create(
                model=self.model,  # Use model from config
                max_tokens=10,  # Only need 1-2 words
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": self.CLASSIFICATION_PROMPT.format(query=query)
                    }
                ]
            )
            
            response = message.content[0].text.strip().upper()
            
            # Parse response
            if "OUT-OF-SCOPE" in response or "OUT OF SCOPE" in response:
                return "OUT-OF-SCOPE"
            else:
                return "IN-SCOPE"
                
        except Exception as e:
            logger.warning(f"Query classification failed, allowing query: {e}")
            # On error, be permissive - let the query through
            return "IN-SCOPE"


@lru_cache
def get_query_validator() -> QueryValidator:
    """Get cached query validator."""
    return QueryValidator()