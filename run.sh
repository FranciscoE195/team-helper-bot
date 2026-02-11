#!/bin/bash
set -e

echo "=== Render Startup Script ==="
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"
echo ""

# Set PYTHONPATH
export PYTHONPATH=/opt/render/project/src
echo "PYTHONPATH set to: $PYTHONPATH"
echo ""

# Verify rag_system exists
if [ -d "/opt/render/project/src/rag_system" ]; then
    echo "✓ rag_system directory found"
    ls -la /opt/render/project/src/rag_system/ | head -5
else
    echo "✗ rag_system directory NOT FOUND!"
    ls -la /opt/render/project/src/
    exit 1
fi

echo ""
echo "Starting uvicorn..."
exec python -m uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT
