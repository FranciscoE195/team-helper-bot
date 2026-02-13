"""Evidence filter worker - filters sections by quality threshold."""

from typing import Literal

from rag_system.config import get_settings
from rag_system.models.domain import Evidence, FilteredEvidence, RankedSection


class EvidenceFilter:
    """Filter evidence based on quality thresholds."""

    def __init__(self):
        self.settings = get_settings()
        self.config = self.settings.search.evidence

    def filter(
        self,
        ranked_sections: list[RankedSection],
        max_sources: int,
    ) -> FilteredEvidence:
        """Filter sections and determine confidence level."""
        # Filter by minimum score
        high_quality = [
            section
            for section in ranked_sections
            if section.rerank_score >= self.config.min_score
        ]

        # Determine confidence based on number of sources
        num_sources = len(high_quality)
        confidence = self._determine_confidence(num_sources)

        # Limit to max_sources
        limited = high_quality[: min(max_sources, self.config.max_sources)]

        # Create evidence items with citation numbers
        evidence = [
            Evidence(
                section=ranked.section,
                relevance_score=ranked.rerank_score,
                citation_number=i + 1,
            )
            for i, ranked in enumerate(limited)
        ]

        return FilteredEvidence(
            evidence=evidence,
            confidence=confidence,
        )

    def _determine_confidence(self, num_sources: int) -> Literal["insufficient", "medium", "high", "very_high"]:
        """Determine confidence level based on number of sources.
        
        Logic:
        - insufficient: < insufficient_threshold (e.g., 0 sources if threshold=1)
        - medium: >= insufficient_threshold AND < medium_threshold
        - high: >= medium_threshold AND < high_threshold  
        - very_high: >= high_threshold
        """
        if num_sources <= self.config.insufficient_threshold:
            return "insufficient"
        if num_sources < self.config.medium_threshold:
            return "medium"
        if num_sources < self.config.high_threshold:
            return "high"
        return "very_high"