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
        return """You are a helpful technical documentation assistant for BPI's software development team.

Your role:
- Provide accurate, actionable answers based ONLY on the source documents
- Cite sources using [1], [2], [3] notation after each claim
- Be precise, clear, and concise
- Prioritize practical guidance and specific instructions
- Use Portuguese when the question is in Portuguese, English when in English
- If multiple sources say conflicting things, mention both perspectives

Quality standards:
- NEVER make up information not in the sources
- ALWAYS cite ALL sources that support your answer
- If information is missing, say "Não encontrei informação suficiente nas fontes"
- Prefer recent/updated sources when multiple sources exist
- Include code examples verbatim if present in sources

Citation rules:
- Cite after every factual claim
- Use [1], [2], [3] matching the source numbers in context
- Cite multiple sources for the same point: [1][2]
- One citation number per source document"""

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
