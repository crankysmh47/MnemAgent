#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HARNESS="$(cd "$(dirname "$0")" && pwd)"
CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$HOME/.openclaw}"

echo "=== MnemOS OpenClaw Setup ==="

if command -v openclaw >/dev/null 2>&1; then
  openclaw --version
else
  echo "OpenClaw not found. Install: npm install -g openclaw"
  echo "See https://docs.qwencloud.com/coding-plan/tools/openclaw"
fi

mkdir -p "$CONFIG_DIR"
cp "$HARNESS/openclaw-config/mnemos.config.json" "$CONFIG_DIR/mnemos.config.json"

USER_FILE="$CONFIG_DIR/mnemos-user-id.txt"
if [[ ! -f "$USER_FILE" ]]; then
  uuidgen > "$USER_FILE" 2>/dev/null || python3 -c "import uuid; print(uuid.uuid4())" > "$USER_FILE"
fi
USER_ID="$(cat "$USER_FILE")"
echo "Shared user_id: $USER_ID"

(cd "$HARNESS/mcp-adapter" && npm install)
(cd "$HARNESS" && npm install)

echo "Starting services..."
(cd "$ROOT/mcp-memory-server/src" && uvicorn main:app --host 0.0.0.0 --port 8000) &
(cd "$HARNESS/mcp-adapter" && node server.js) &
(cd "$HARNESS" && node src/index.js) &

sleep 2
echo ""
echo "  Chat UI:      http://localhost:3000"
echo "  Visualizer:   http://localhost:3000/visualizer"
echo "  MnemOS API:   http://localhost:8000"
echo "  MCP Adapter:  http://localhost:8001"
echo "  OpenClaw TUI: openclaw gateway && openclaw tui"
echo ""
echo "Set localStorage mnemos_user_id to $USER_ID for shared memory."
