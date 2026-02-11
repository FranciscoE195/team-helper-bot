#!/bin/bash
# Linux/Mac setup script for RAG system

set -e  # Exit on error

echo ""
echo "========================================================"
echo "   RAG System - Linux/Mac Setup"
echo "========================================================"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker not found. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "[OK] Docker found"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose not found."
    exit 1
fi
echo "[OK] Docker Compose found"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found. Install Python 3.11+"
    exit 1
fi
echo "[OK] Python found"

# Install/check uv
if ! command -v uv &> /dev/null; then
    echo "[INFO] Installing uv package manager..."
    python3 -m pip install uv
fi
echo "[OK] uv found"

# Create config if needed
if [ ! -f config/config.yaml ]; then
    if [ -f config/config.example.yaml ]; then
        echo "[INFO] Creating config.yaml from example..."
        cp config/config.example.yaml config/config.yaml
        echo "[WARNING] Edit config/config.yaml and update ingestion.git.local_path"
    fi
fi

# Start Docker services
echo ""
echo "========================================================"
echo "   Starting Docker Services"
echo "========================================================"
cd docker
docker compose up -d postgres ollama
cd ..
echo "[OK] Docker services started"

# Wait for services
echo "[INFO] Waiting for services to start..."
sleep 5

# Initialize database
echo ""
echo "========================================================"
echo "   Initializing Database"
echo "========================================================"
uv run --native-tls python scripts/init_db.py
echo "[OK] Database initialized"

# Install dependencies
echo ""
echo "========================================================"
echo "   Installing Dependencies"
echo "========================================================"
uv sync --native-tls
echo "[OK] Dependencies installed"

# Check models
echo ""
echo "========================================================"
echo "   Checking Models"
echo "========================================================"
if [ ! -d models/huggingface ] || [ -z "$(ls -A models/huggingface 2>/dev/null)" ]; then
    echo "[WARNING] Models not found in models/huggingface/"
    echo ""
    echo "Download models:"
    echo "  - With internet: uv run --native-tls python scripts/download_models.py"
    echo "  - Offline: See DEPLOYMENT.md"
else
    echo "[OK] HuggingFace models found"
fi

docker exec rag-ollama ollama list 2>/dev/null || echo "[WARNING] Cannot check Ollama models. Container may not be ready."

# Final instructions
echo ""
echo "========================================================"
echo "   Setup Complete!"
echo "========================================================"
echo ""
echo "Next Steps:"
echo "  1. Edit config/config.yaml (set ingestion.git.local_path)"
echo "  2. Download models if needed"
echo "  3. Start API: uv run --native-tls uvicorn rag_system.main:app --host 0.0.0.0 --port 8000 --reload"
echo "  4. Visit: http://localhost:8000/docs"
echo ""
read -p "Start the API server now? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting API server..."
    echo "Access at: http://localhost:8000"
    echo "Docs at: http://localhost:8000/docs"
    echo "Press Ctrl+C to stop"
    echo ""
    uv run --native-tls uvicorn rag_system.main:app --host 0.0.0.0 --port 8000 --reload
fi
