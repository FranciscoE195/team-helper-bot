#!/bin/bash
# Render startup script

echo "========================================"
echo "🚀 START.SH IS EXECUTING!"
echo "========================================"
echo "Starting BPI RAG System"
echo "========================================"
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la
echo ""
echo "Python version: $(python --version)"
echo ""
echo "Setting PYTHONPATH..."
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH
echo "PYTHONPATH=$PYTHONPATH"
echo ""
echo "Checking if rag_system module exists..."
ls -la /opt/render/project/src/
echo ""
echo "Starting uvicorn..."
echo "========================================"

exec uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT
