#!/bin/bash
# Render startup script

export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

echo "PYTHONPATH set to: $PYTHONPATH"
echo "Starting uvicorn..."

exec uvicorn rag_system.main:app --host 0.0.0.0 --port $PORT
