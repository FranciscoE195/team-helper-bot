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

# The actual code is in src/src/rag_system, so PYTHONPATH needs to be project_root/src/src
export PYTHONPATH=$(pwd)/src/src
echo "PYTHONPATH set to: $PYTHONPATH"
echo ""

# Verify rag_system exists
if [ -d "src/src/rag_system" ]; then
    echo "✓ src/src/rag_system directory found"
else
    echo "✗ src/src/rag_system directory NOT FOUND!"
    find . -name "rag_system" -type d 2>/dev/null || echo "Not found anywhere"
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
