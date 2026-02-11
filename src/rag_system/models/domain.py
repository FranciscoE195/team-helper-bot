"""Domain models."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Section:
    """Document section with metadata."""
    section_id: str
    doc_id: str
    title: str | None
    content: str
    embedding: list[float] | None
    doc_title: str
    url: str | None
    breadcrumb: list[str]
    has_code: bool
    has_images: bool
    relevance_score: float = 0.0


@dataclass
class SearchResult:
    """Search result with score."""
    section: Section
    vector_score: float
    keyword_score: float
    combined_score: float


@dataclass
class RankedSection:
    """Section with reranking score."""
    section: Section
    rerank_score: float


@dataclass
class Evidence:
    """Evidence item for answer generation."""
    section: Section
    relevance_score: float
    citation_number: int


@dataclass
class FilteredEvidence:
    """Filtered evidence with confidence."""
    evidence: list[Evidence]
    confidence: Literal["insufficient", "medium", "high", "very_high"]


@dataclass
class GeneratedAnswer:
    """Generated answer from LLM."""
    text: str
    generation_time_ms: int
    token_count: int | None


@dataclass
class QueryTrace:
    """Complete query trace."""
    trace_id: str
    query: str
    answer: GeneratedAnswer
    evidence: FilteredEvidence
    timestamp: datetime
    user_id: str | None
    models_used: dict[str, str]


@dataclass
class Document:
    """Document metadata."""
    doc_id: str
    title: str
    url: str | None
    file_path: str
    breadcrumb: list[str]
    content_hash: str
    indexed_at: datetime


@dataclass
class ImageDescription:
    """Image with description."""
    image_hash: str
    image_path: str
    description: str
    alt_text: str | None
