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
    echo "Contents of src/rag_system:"
    ls -la src/rag_system/
else
    echo "✗ rag_system directory NOT FOUND!"
    exit 1
fi

# Test the actual import that's failing
echo ""
echo "Testing imports..."
python -c "
import sys
print('Python path:', sys.path)
print('Importing rag_system...')
import rag_system
print('✓ rag_system imported')
print('Importing rag_system.models...')
import rag_system.models
print('✓ rag_system.models imported')
print('Importing rag_system.models.api...')
from rag_system.models.api import HealthResponse
print('✓ rag_system.models.api imported')
" || {
    echo "✗ Failed imports"
    exit 1
}

echo ""
echo "Starting uvicorn..."
exec python -m uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT