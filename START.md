# Quick Start Guide

Run services with Docker Compose (PostgreSQL + Ollama), API with uv on host.

## Prerequisites

- Docker Desktop running
- Python 3.11+ with uv installed
- Your markdown docs at: `C:\Users\102099\Documents\automated-testing\team-helper`

## Step 1: Start Docker Services

```bash
cd docker
docker compose up -d postgres ollama
docker compose --profile init up model-init  # Pull Ollama models (one-time)
```

## Step 2: Check Services

```bash
docker compose ps
docker compose logs postgres
docker compose logs ollama
```

## Step 3: Initialize Database (first time only)

```bash
cd ..
uv run python scripts/init_db.py
```

## Step 4: Start API (on host with uv)

```bash
uv run uvicorn rag_system.main:app --host 0.0.0.0 --port 8000 --reload
```

Wait for models to load. Service at: http://localhost:8000

## Step 5: Ingest Documents (new terminal)

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/webhook/ingest-all
```

## Step 6: Query

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/query `
  -ContentType "application/json" `
  -Body '{"question": "your question", "user_id": "test@example.com"}'
```

Or use: http://localhost:8000/docs

## Stopping

```bash
# Stop API: Ctrl+C in terminal

# Stop Docker services
cd docker
docker compose down
```
