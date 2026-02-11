"""Answer generator worker - generates answer using LLM."""

from rag_system.models.domain import GeneratedAnswer
from rag_system.providers.llm import get_llm_provider


class AnswerGenerator:
    """Generate answer using LLM."""

    def __init__(self):
        self.llm = get_llm_provider()

    def generate(self, question: str, context: str) -> GeneratedAnswer:
        """Generate answer from question and context."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, context)

        # Call LLM
        answer_text, generation_time_ms = self.llm.generate(system_prompt, user_prompt)

        # Estimate token count (rough approximation)
        token_count = len(answer_text.split())

        return GeneratedAnswer(
            text=answer_text.strip(),
            generation_time_ms=generation_time_ms,
            token_count=token_count,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM."""
        return """You are a helpful documentation assistant for a software development team.

Your role:
- Answer questions using ONLY the provided source documents
- Cite sources using [1], [2], [3] notation after each claim (these numbers match the sources in the context)
- Be precise and accurate
- If information is not in the sources, say "Não encontrei informação suficiente nas fontes que me foram indexadas como contexto".
- Keep answers concise but complete
- Always cite ALL sources that support your answer

Important rules:
- Never make up information
- Always cite your sources using [1], [2], [3], etc
- Use the exact citation numbers from the context
- Cite multiple sources if they all support the same point"""

    def _build_user_prompt(self, question: str, context: str) -> str:
        """Build user prompt with context and question."""
        # Count how many sources are in the context
        import re
        source_numbers = re.findall(r'^\[(\d+)\]', context, re.MULTILINE)
        max_source = max([int(n) for n in source_numbers]) if source_numbers else 0
        
        return f"""Based on the following sources, answer the question.

{context}

Question: {question}

Answer (remember to cite sources with [1], [2], [3], etc - you have {max_source} sources available):"""
