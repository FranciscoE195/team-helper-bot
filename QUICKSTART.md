# Quick Start

**Single command to start everything:**

```bash
cd docker && docker compose up -d
```

That's it! Everything runs in Docker:
- ✅ PostgreSQL with pgvector
- ✅ Ollama with models
- ✅ FastAPI application

**API available at:** `http://localhost:8000/docs`

---

## First Time Setup

### 1. Check/Download Models (One-time)

**Check if models already exist:**
```bash
# Check Ollama models
docker exec rag-ollama ollama list

# Check HuggingFace models
ls -la models/huggingface/
```

**If models are missing, download them:**

```bash
# Download Ollama models (~9.4GB)
cd docker
docker compose --profile init up model-init

# Download HuggingFace models (~4.5GB)
# Note: Models will be downloaded automatically on first API start
# Or manually trigger download inside container:
docker exec rag-api python -c "
from sentence_transformers import SentenceTransformer, CrossEncoder
import os
os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/app/cache/huggingface'
print('Downloading models...')
SentenceTransformer('intfloat/multilingual-e5-large', cache_folder='/app/cache/huggingface')
CrossEncoder('BAAI/bge-reranker-v2-m3')
print('Models ready!')
"
```

### 2. Configure Document Path

Edit `config/config.yaml`:
```yaml
ingestion:
  git:
    local_path: "C:/path/to/your/markdown/docs/"  # Update this
```

### 3. Initialize Database

Database schema is auto-created on first start via `init-db.sql`.

To manually re-initialize:
```bash
docker exec rag-api python scripts/init_db.py
```

---

## Usage

### Ingest Documents

```bash
curl -X POST http://localhost:8000/webhook/ingest-all
```

### Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"How to deploy?","session_id":"test"}'
```

### Interactive API Docs

Open `http://localhost:8000/docs` in your browser.

---

## Management

### View Logs

```bash
cd docker

# All services
docker compose logs -f

# Specific service
docker compose logs -f rag-api
docker compose logs -f ollama
docker compose logs -f postgres
```

### Check Status

```bash
docker compose ps

# Check Ollama models
docker exec rag-ollama ollama list

# Check HuggingFace models
ls -la ../models/huggingface/
```

### Stop System

```bash
cd docker
docker compose down

# Stop and remove volumes (WARNING: deletes database)
docker compose down -v
```

### Restart Services

```bash
cd docker

# Restart all
docker compose restart

# Restart specific service
docker compose restart rag-api
```

---

## Model Configuration

Models are configured in `config/config.yaml`:

```yaml
models:
  embedding:
    model_name: "intfloat/multilingual-e5-large"
    cache_dir: "./models/huggingface"
  
  reranker:
    model_name: "BAAI/bge-reranker-v2-m3"
    cache_dir: "./models/huggingface"
  
  llm:
    model: "qwen2.5:7b"  # Ollama model
  
  vision:
    model: "llava:7b"    # Ollama model
```

After changing models, restart the API:
```bash
docker compose restart rag-api
```

---

## Offline Deployment

For machines without internet access:

1. **On a machine with internet**, run the setup above to download all models
2. **Copy the entire `models/` directory** (~13GB) to target machine
3. **On target machine**, just run `docker compose up -d`

All models are loaded from local `models/` directory via volume mounts.

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete offline deployment guide.
