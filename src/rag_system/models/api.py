"""API request/response models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Request models
class QueryRequest(BaseModel):
    """Query request."""
    question: str = Field(..., min_length=1, max_length=1000)
    max_sources: int = Field(default=5, ge=1, le=10)
    user_id: str | None = None


class WebhookGitRequest(BaseModel):
    """Git webhook request."""
    event: Literal["push", "merge_request"]
    repository: str
    branch: str
    changed_files: list[str]
    commit_sha: str | None = None


# Response models
class EvidenceItem(BaseModel):
    """Single piece of evidence."""
    citation_number: int
    doc_title: str
    section_title: str | None
    url: str | None
    relevance_score: float
    excerpt: str


class QueryResponse(BaseModel):
    """Query response."""
    trace_id: str
    query: str
    answer: str
    evidence: list[EvidenceItem]
    confidence: Literal["insufficient", "medium", "high", "very_high"]
    timestamp: datetime
    generation_time_ms: int
    models_used: dict[str, str]


class TraceDetail(BaseModel):
    """Detailed trace information."""
    trace_id: str
    query_text: str
    answer_text: str
    citations: list[EvidenceItem]
    confidence: str
    user_id: str | None
    timestamp: datetime
    models: dict[str, str]
    metrics: dict[str, int | float]


class HealthResponse(BaseModel):
    """Health check response."""
    status: Literal["healthy", "degraded", "unhealthy"]
    database: bool
    embedding_model: bool
    reranker_model: bool
    llm: bool
    timestamp: datetime


class IngestionResponse(BaseModel):
    """Ingestion response."""
    success: bool
    message: str
    processed_files: int
    updated_sections: int
    added_sections: int
    deleted_sections: int
    duration_seconds: float
