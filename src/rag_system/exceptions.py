"""Custom exceptions."""


class RAGSystemError(Exception):
    """Base exception for RAG system."""
    pass


class ConfigurationError(RAGSystemError):
    """Configuration error."""
    pass


class DatabaseError(RAGSystemError):
    """Database error."""
    pass


class ModelError(RAGSystemError):
    """ML model error."""
    pass


class IngestionError(RAGSystemError):
    """Ingestion error."""
    pass


class QueryError(RAGSystemError):
    """Query error."""
    pass


class InsufficientEvidenceError(QueryError):
    """Not enough high-quality sources found."""
    pass
