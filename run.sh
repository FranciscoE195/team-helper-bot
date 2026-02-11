#!/bin/bash
set -e

echo "=== Render Startup Script ==="
echo "Initial working directory: $(pwd)"
echo "Python version: $(python --version)"
echo ""

# Render starts in /opt/render/project/src but we need to be in /opt/render/project
# Go up one directory if we're in the src subdirectory
if [[ "$(pwd)" == */src ]]; then
    cd ..
    echo "Moved up to project root: $(pwd)"
else
    echo "Already in project root: $(pwd)"
fi
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
