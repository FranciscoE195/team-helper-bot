#!/usr/bin/env python3
"""Download HuggingFace models for offline deployment."""

from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder

# Create models directory
models_dir = Path("models/huggingface")
models_dir.mkdir(parents=True, exist_ok=True)

# Download embedding model
print("\n1. Downloading multilingual-e5-large (~2.2GB)...")
embedding_path = models_dir / "multilingual-e5-large"
embedding = SentenceTransformer('intfloat/multilingual-e5-large')
embedding.save(str(embedding_path))
print(f"   Saved to: {embedding_path}")

# Download reranker model
print("\n2. Downloading bge-reranker-v2-m3 (~2.0GB)...")
reranker_path = models_dir / "bge-reranker-v2-m3"
reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')
reranker.save(str(reranker_path))
print(f"   Saved to: {reranker_path}")

print("\nAll models downloaded successfully!")
print(f"\nModels saved in: {models_dir.absolute()}")