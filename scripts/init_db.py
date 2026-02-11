"""Initialize database schema."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rag_system.providers.database import get_database_provider


def main():
    """Initialize database tables."""
    print("Initializing database...")
    
    db_provider = get_database_provider()
    
    print("Dropping existing tables...")
    db_provider.drop_tables()
    
    print("Creating tables...")
    db_provider.create_tables()
    
    print("Database initialized successfully!")
    print("Tables created:")
    print("  - documents")
    print("  - document_sections")
    print("  - image_cache")
    print("  - document_images")
    print("  - query_traces")
    print("  - trace_citations")
    print("  - trace_answers")
    print("  - trace_section_snapshots")


if __name__ == "__main__":
    main()
