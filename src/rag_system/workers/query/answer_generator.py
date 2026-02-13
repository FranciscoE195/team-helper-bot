"""Answer generator worker - generates answer using LLM."""

import re

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

        # Clean up markdown formatting
        cleaned_text = self._cleanup_markdown(answer_text)

        # Estimate token count (rough approximation)
        token_count = len(cleaned_text.split())

        return GeneratedAnswer(
            text=cleaned_text.strip(),
            generation_time_ms=generation_time_ms,
            token_count=token_count,
        )

    def _cleanup_markdown(self, text: str) -> str:
        """Clean up markdown formatting for better readability."""
        # Remove standalone horizontal rules (---, ___, ***)
        text = re.sub(r'^\s*[-_*]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove trailing spaces at end of lines
        text = re.sub(r' +$', '', text, flags=re.MULTILINE)
        
        # Fix excessive spacing around headers
        text = re.sub(r'\n{2,}(#{1,6} )', r'\n\n\1', text)  # Max 2 newlines before headers
        text = re.sub(r'(#{1,6} .+)\n{2,}', r'\1\n\n', text)  # Max 2 newlines after headers
        
        # Remove markdown artifacts that don't render well
        text = re.sub(r'^\s*>\s*$', '', text, flags=re.MULTILINE)  # Empty blockquotes
        
        # Clean up list spacing - ensure single newline between list items
        text = re.sub(r'(\n[-*+]\s+.+)\n{2,}(?=[-*+]\s+)', r'\1\n', text)
        
        # Remove any accidental code fence remnants
        text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
        
        return text

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM."""
        return """You are a helpful documentation assistant for a software development team.

Your role:
- Answer questions using ONLY the provided source documents
- Cite sources using [1], [2], [3] notation after each claim (these numbers match the sources in the context)
- Be precise and accurate
- If information is not in the sources, say "Não encontrei informação suficiente nas fontes"
- Keep answers concise but complete
- Always cite ALL sources that support your answer

Formatting guidelines:
- Use markdown for structure (headers, lists, code blocks)
- Keep formatting clean and minimal
- Avoid excessive spacing or decorative elements like horizontal rules (---)
- Use bullet points for lists, not numbered lists unless order matters
- Keep paragraphs concise and separated by single blank lines

Important rules:
- Never make up information
- Always cite your sources using [1], [2], [3], etc
- Use the exact citation numbers from the context
- Cite multiple sources if they all support the same point"""

    def _build_user_prompt(self, question: str, context: str) -> str:
        """Build user prompt with context and question."""
        # Count how many sources are in the context
        source_numbers = re.findall(r'^\[(\d+)\]', context, re.MULTILINE)
        max_source = max([int(n) for n in source_numbers]) if source_numbers else 0
        
        return f"""Based on the following sources, answer the question.

{context}

Question: {question}

Answer (remember to cite sources with [1], [2], [3], etc - you have {max_source} sources available):"""