#!/bin/bash
set -e

echo "=== Render Startup Script ==="
echo "Initial working directory: $(pwd)"
echo "Python version: $(python --version)"
echo ""

# We're in /opt/render/project/src (repo root)
# The actual rag_system is in src/rag_system
export PYTHONPATH=$(pwd)/src
echo "PYTHONPATH set to: $PYTHONPATH"
echo ""

# Verify rag_system exists
if [ -d "src/rag_system" ]; then
    echo "✓ rag_system directory found at: $(pwd)/src/rag_system"
else
    echo "✗ rag_system directory NOT FOUND!"
    echo "Current directory contents:"
    ls -la
    echo ""
    echo "Contents of src/:"
    ls -la src/ || echo "src/ doesn't exist"
    exit 1
fi

# Verify Python can import rag_system
echo "Testing Python import..."
python -c "import sys; print('Python path:', sys.path); import rag_system; print('✓ rag_system imported successfully')" || {
    echo "✗ Failed to import rag_system"
    exit 1
}

echo ""
echo "Starting uvicorn..."
exec python -m uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT