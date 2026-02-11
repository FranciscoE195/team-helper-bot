#!/bin/sh
# Download required Ollama models
# Run with: docker compose --profile init up model-init

set -e

echo "Installing curl..."
apk add --no-cache curl

echo "Waiting for Ollama to be ready..."
until curl -f http://ollama:11434/api/tags >/dev/null 2>&1; do
    echo "Ollama not ready, waiting..."
    sleep 5
done

echo "Pulling models..."

# LLM model (for answer generation)
echo "Pulling llama3.2:3b..."
curl -X POST http://ollama:11434/api/pull -d '{"name": "llama3.2:3b"}'

# Vision model (for image descriptions)
echo "Pulling llava:7b..."
curl -X POST http://ollama:11434/api/pull -d '{"name": "llava:7b"}'

echo "All models downloaded successfully!"