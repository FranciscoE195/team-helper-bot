# Scripts

Simple utility scripts for managing the RAG system.

## Available Scripts

### `init_db.py`
Initialize the database schema (run once).

```bash
uv run python scripts/init_db.py
```

Creates all necessary tables: documents, document_sections, image_cache, query_traces, etc.

## Typical Workflow

1. First time setup:
   ```bash
   uv run python scripts/init_db.py
   ```

2. Start the service:
   ```bash
   uv run uvicorn rag_system.main:app --reload
   ```

3. In another terminal, ingest documents:
   ```powershell
   Invoke-RestMethod -Method Post -Uri http://localhost:8000/webhook/ingest-all
   ```

4. Query via API or web UI at http://localhost:8000/docs
