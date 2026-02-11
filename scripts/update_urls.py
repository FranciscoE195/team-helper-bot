"""Update document URLs in database without re-ingesting."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from rag_system.providers.database import get_database_provider

BASE_URL = "https://472-teamhelper-v1-5358d3.pages.platform.ks.gbpiweb.loc"
LOCAL_PATH = "C:/Users/102099/Documents/automated-testing/team-helper/"

def main():
    """Update URLs for all documents."""
    print("Connecting to database...")
    db_provider = get_database_provider()
    
    with db_provider.get_session() as db:
        # Get all documents
        result = db.execute(text("SELECT doc_id, file_path FROM documents"))
        documents = result.fetchall()
        
        print(f"Found {len(documents)} documents to update")
        
        updated = 0
        for doc_id, file_path in documents:
            # Convert file path to URL
            try:
                # Normalize path separators
                normalized = file_path.replace("\\", "/")
                
                # Find where the meaningful path starts (after team-helper/)
                if "team-helper/" in normalized:
                    rel_path = normalized.split("team-helper/", 1)[1]
                elif LOCAL_PATH.replace("\\", "/") in normalized:
                    rel_path = normalized.replace(LOCAL_PATH.replace("\\", "/"), "")
                else:
                    # Fallback: use the path as-is
                    rel_path = normalized
                
                # Remove leading slash if present
                rel_path = rel_path.lstrip("/")
                
                # Convert .md to .html
                html_path = rel_path.replace(".md", ".html")
                
                # Build full URL
                url = f"{BASE_URL}/{html_path}"
                
                # Update in database
                db.execute(
                    text("UPDATE documents SET url = :url WHERE doc_id = :doc_id"),
                    {"url": url, "doc_id": doc_id}
                )
                
                updated += 1
                if updated % 10 == 0:
                    print(f"Updated {updated} documents...")
                    
            except Exception as e:
                print(f"Error updating {file_path}: {e}")
                continue
        
        db.commit()
        print(f"\n✅ Successfully updated {updated} document URLs!")

if __name__ == "__main__":
    main()
