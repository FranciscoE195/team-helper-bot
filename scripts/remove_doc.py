"""Remove document and all associated data from database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from rag_system.providers.database import get_database_provider

def main():
    """Remove em-atualizacao document."""
    print("Connecting to database...")
    db_provider = get_database_provider()
    
    with db_provider.get_session() as db:
        # Find the document
        result = db.execute(
            text("SELECT doc_id, file_path FROM documents WHERE file_path LIKE '%em-atualizacao%'")
        )
        docs = result.fetchall()
        
        if not docs:
            print("❌ Document 'em-atualizacao' not found")
            return
        
        print(f"Found {len(docs)} document(s) to delete:")
        for doc_id, file_path in docs:
            print(f"  - {file_path} (ID: {doc_id})")
        
        for doc_id, file_path in docs:
            # Get all section IDs for this document
            result = db.execute(
                text("SELECT section_id FROM document_sections WHERE doc_id = :doc_id"),
                {"doc_id": doc_id}
            )
            section_ids = [row[0] for row in result]
            
            # Delete trace citations first
            if section_ids:
                db.execute(
                    text("DELETE FROM trace_citations WHERE section_id = ANY(:section_ids)"),
                    {"section_ids": section_ids}
                )
            
            # Delete sections
            result = db.execute(
                text("DELETE FROM document_sections WHERE doc_id = :doc_id"),
                {"doc_id": doc_id}
            )
            sections_deleted = result.rowcount
            
            # Delete document
            db.execute(
                text("DELETE FROM documents WHERE doc_id = :doc_id"),
                {"doc_id": doc_id}
            )
            
            print(f"✅ Deleted {sections_deleted} sections and document: {file_path}")
        
        db.commit()
        print(f"\n✅ Successfully removed {len(docs)} document(s)!")

if __name__ == "__main__":
    main()
