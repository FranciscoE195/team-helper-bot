# Pre-Downloaded Models

This directory contains pre-downloaded models for offline/restricted network environments.

## Directory Structure

```
models/
├── ollama/          # Ollama models (LLM and vision)
└── huggingface/     # HuggingFace models (embeddings and reranker)
```

## Setup Instructions

### 1. Ollama Models (llama3.2:3b, llava:7b)

**On a machine with internet access:**

```bash
# Install Ollama and pull models
ollama pull llama3.2:3b
ollama pull llava:7b

# Copy the models directory
# Linux/Mac: ~/.ollama/models/
# Windows: %USERPROFILE%\.ollama\models\
```

**Copy to this project:**

Copy the entire `.ollama/models` directory contents to `models/ollama/` in this project.

Expected structure:
```
models/ollama/
├── manifests/
│   └── registry.ollama.ai/
│       └── library/
│           ├── llama3.2/
│           └── llava/
└── blobs/
    └── sha256-*
```

### 2. HuggingFace Models

**On a machine with internet access:**

```python
# Download embedding model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
model.save('all-MiniLM-L12-v2')

# Download reranker model  
from sentence_transformers import CrossEncoder
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
reranker.save('ms-marco-MiniLM-L-12-v2')
```

**Copy to this project:**

Copy both model directories to `models/huggingface/`:

```
models/huggingface/
├── all-MiniLM-L12-v2/
│   ├── config.json
│   ├── pytorch_model.bin
│   └── ...
└── ms-marco-MiniLM-L-12-v2/
    ├── config.json
    ├── pytorch_model.bin
    └── ...
```

### 3. Alternative: Download Script

Run this on a machine with internet access and copy the entire `models/` folder:

```python
import os
from sentence_transformers import SentenceTransformer, CrossEncoder

# Set cache directory
os.makedirs('models/huggingface', exist_ok=True)

# Download models
print("Downloading embedding model...")
embedding = SentenceTransformer('sentence-transformers/all-MiniLM-L12-v2')
embedding.save('models/huggingface/all-MiniLM-L12-v2')

print("Downloading reranker model...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
reranker.save('models/huggingface/ms-marco-MiniLM-L-12-v2')

print("Done! Copy the 'models/' directory to your restricted environment.")
```

## Docker Configuration

The docker-compose.yml mounts these directories:
- `./models/ollama` → `/root/.ollama/models` (Ollama container)
- `./models/huggingface` → `/app/cache/huggingface` (API container)

## Verification

After copying models, verify:

```bash
# Check Ollama models
docker exec rag-ollama ollama list

# Should show:
# NAME            ID      SIZE    MODIFIED
# llama3.2:3b     ...     2.0 GB  ...
# llava:7b        ...     4.7 GB  ...
```

For HuggingFace models, the API will load them from the mounted directory on startup.
