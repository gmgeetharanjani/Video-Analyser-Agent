#!/bin/bash
# Start the Video Analyzer Agent locally

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

mkdir -p videos

export VIDEO_STORAGE_PATH="$SCRIPT_DIR/videos"
export PYTHONPATH="$SCRIPT_DIR/app"

# Load .env if it exists (using set -a to safely handle special characters)
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Override VIDEO_STORAGE_PATH to use local directory (not Docker /app/videos)
export VIDEO_STORAGE_PATH="$SCRIPT_DIR/videos"

echo "Starting Video Analyzer Agent on port ${PORT:-8080}..."
echo "VIDEO_STORAGE_PATH: $VIDEO_STORAGE_PATH"
echo "PYTHONPATH: $PYTHONPATH"

python3 app/main_local.py --host 0.0.0.0 --port "${PORT:-8080}"
