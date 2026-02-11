## Quick Start with Docker

### Prerequisites
- Docker & Docker Compose
- Access to BPI internal image registry: `repo.gbpiweb.loc`
- VPN connection to BPI network (for DNS resolution)

### Setup
```bash
# 1. Clone and configure
git clone https://gitlab.platform.ks.gbpiweb.loc/docs/teamhelper/team-helper.git
cd bpi-team-helper-bot
cp .env.example .env
cp config/config.example.yaml config/config.yaml
# Edit .env with your settings

# 2. Start all services
docker compose -f docker/docker-compose.yml up -d

# 3. Download AI models (one-time, ~5-10 minutes)
docker compose -f docker/docker-compose.yml --profile init up model-init

# 4. Initialize database
docker compose -f docker/docker-compose.yml exec rag-api python scripts/init_db.py

# 5. Test the API
curl http://localhost:8000/api/health
```

### Images Used (BPI Internal Registry)

All images are pulled from `repo.gbpiweb.loc/public-images/`:

- **PostgreSQL with pgvector**: `pgvector/pgvector:pg16`
- **Ollama (LLM)**: `ollama/ollama:latest`
- **Alpine (init)**: `alpine:latest`
- **Python**: `python:3.11-slim`

### DNS Configuration

Services are configured with BPI internal DNS:
- Primary: `10.165.30.101`
- Secondary: `10.165.158.101`

This enables resolution of internal domains like:
- `gitlab.platform.ks.gbpiweb.loc`
- `repo.gbpiweb.loc`
- `smtp.gbpi.loc`

### Query Documentation
```bash
# Via API
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I test APIs?", "max_sources": 5}'

# Via CLI
docker compose -f docker/docker-compose.yml exec rag-api \
  python -m cli.cli query "How do I test APIs?"
```

### Trigger Ingestion

#### From Local Folder
```bash
# Ingest all markdown files from local team-helper repository
docker compose -f docker/docker-compose.yml exec rag-api \
  python scripts/ingest_local_docs.py /data/docs
```

#### Via Webhook (GitLab Integration)
```bash
curl -X POST http://localhost:8000/webhook/git \
  -H "Content-Type: application/json" \
  -d '{
    "event": "push",
    "repository": "team-helper",
    "branch": "main",
    "changed_files": ["docs/testing.md"]
  }'
```

### Troubleshooting

#### Image Pull Issues
```bash
# Verify access to BPI registry
curl https://repo.gbpiweb.loc

# Login to registry if needed (if using authentication)
docker login repo.gbpiweb.loc
```

#### DNS Issues
```bash
# Verify DNS resolution inside container
docker compose -f docker/docker-compose.yml exec rag-api nslookup gitlab.platform.ks.gbpiweb.loc

# Should resolve to internal IP
```

#### Ollama Model Download Issues
```bash
# Check Ollama service
docker compose -f docker/docker-compose.yml logs ollama

# Manually download models
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3.2:3b
docker compose -f docker/docker-compose.yml exec ollama ollama pull llava:7b

# List downloaded models
docker compose -f docker/docker-compose.yml exec ollama ollama list
```

### Development Mode

For active development with hot-reload:

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up
```

Changes to Python files will automatically reload the API.

### Production Considerations

- Change default passwords in `.env`
- Configure proper backup for PostgreSQL volume
- Set up monitoring and logging
- Consider external LLM provider (OpenAI/Azure) for better performance
- Implement authentication/authorization
- Set resource limits in docker-compose.yml