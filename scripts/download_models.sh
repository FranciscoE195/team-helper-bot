#!/bin/bash
# Download HuggingFace models using wget
# Run this on a machine with internet access or from home

set -e

MODELS_DIR="models/huggingface"
mkdir -p "$MODELS_DIR"

echo "============================================================"
echo "Downloading Sentence Transformer Models"
echo "============================================================"

# all-MiniLM-L12-v2 (Embedding model)
echo ""
echo "1. Downloading all-MiniLM-L12-v2..."
mkdir -p "$MODELS_DIR/all-MiniLM-L12-v2"
cd "$MODELS_DIR/all-MiniLM-L12-v2"

BASE_URL="https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2/resolve/main"

wget -nc "$BASE_URL/config.json"
wget -nc "$BASE_URL/config_sentence_transformers.json"
wget -nc "$BASE_URL/modules.json"
wget -nc "$BASE_URL/pytorch_model.bin"
wget -nc "$BASE_URL/sentence_bert_config.json"
wget -nc "$BASE_URL/special_tokens_map.json"
wget -nc "$BASE_URL/tokenizer.json"
wget -nc "$BASE_URL/tokenizer_config.json"
wget -nc "$BASE_URL/vocab.txt"

mkdir -p 1_Pooling
cd 1_Pooling
wget -nc "$BASE_URL/1_Pooling/config.json"
cd ../..

echo "✓ all-MiniLM-L12-v2 downloaded"

# ms-marco-MiniLM-L-12-v2 (Reranker model)
echo ""
echo "2. Downloading ms-marco-MiniLM-L-12-v2..."
mkdir -p "$MODELS_DIR/ms-marco-MiniLM-L-12-v2"
cd "$MODELS_DIR/ms-marco-MiniLM-L-12-v2"

BASE_URL="https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-12-v2/resolve/main"

wget -nc "$BASE_URL/config.json"
wget -nc "$BASE_URL/pytorch_model.bin"
wget -nc "$BASE_URL/special_tokens_map.json"
wget -nc "$BASE_URL/tokenizer.json"
wget -nc "$BASE_URL/tokenizer_config.json"
wget -nc "$BASE_URL/vocab.txt"

cd ../../..

echo ""
echo "✓ All HuggingFace models downloaded successfully!"
echo ""
echo "Models saved in: $MODELS_DIR"
echo ""
echo "Next steps:"
echo "1. Download Ollama models (run on machine with Ollama installed):"
echo "   ollama pull llama3.2:3b"
echo "   ollama pull llava:7b"
echo "2. Copy .ollama/models/* to models/ollama/"
echo "3. Copy entire 'models/' directory to restricted environment"
