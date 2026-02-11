"""API dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from rag_system.providers.database import get_db_session
from rag_system.services.ingestion_service import IngestionService
from rag_system.services.query_service import QueryService


def get_query_service(db: Annotated[Session, Depends(get_db_session)]) -> QueryService:
    """Get query service instance."""
    return QueryService(db)


def get_ingestion_service(db: Annotated[Session, Depends(get_db_session)]) -> IngestionService:
    """Get ingestion service instance."""
    return IngestionService(db)
