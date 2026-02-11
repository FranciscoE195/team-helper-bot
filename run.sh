#!/bin/bash
set -e

echo "=== Render Startup Script ==="
echo "Initial working directory: $(pwd)"
echo "Python version: $(python --version)"
echo ""

# Change to project root (where run.sh is located)
cd "$(dirname "$0")"
echo "Changed to project root: $(pwd)"
echo ""

# Set PYTHONPATH to the src directory
export PYTHONPATH=$(pwd)/src
echo "PYTHONPATH set to: $PYTHONPATH"
echo ""

# Verify rag_system exists
if [ -d "src/rag_system" ]; then
    echo "✓ src/rag_system directory found"
    ls -la src/rag_system/ | head -5
else
    echo "✗ src/rag_system directory NOT FOUND!"
    ls -la src/
    exit 1
fi

echo ""
echo "Starting uvicorn..."
exec python -m uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT
