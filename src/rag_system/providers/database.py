"""Database provider."""

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from rag_system.config import get_logger, get_settings
from rag_system.models.database import Base

logger = get_logger(__name__)


class DatabaseProvider:
    """Database connection provider."""

    def __init__(self) -> None:
        settings = get_settings()

        logger.info("Initializing database connection")
        self.engine = create_engine(
            settings.database.url,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_pre_ping=True,
            echo=False,  # Set to True for SQL query logging
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        logger.info(
            "Database connection established",
            extra={
                "pool_size": settings.database.pool_size,
                "max_overflow": settings.database.max_overflow,
            },
        )

    def get_session(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def drop_tables(self) -> None:
        """Drop all tables."""
        logger.info("Dropping database tables")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped successfully")

    def create_tables(self) -> None:
        """Create all tables."""
        logger.info("Creating database tables")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")


@lru_cache
def get_database_provider() -> DatabaseProvider:
    """Get cached database provider."""
    return DatabaseProvider()


def get_db_session() -> Session:
    """Dependency for FastAPI routes."""
    db = get_database_provider().get_session()
    try:
        yield db
    finally:
        db.close()
