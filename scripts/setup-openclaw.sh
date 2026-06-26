#!/usr/bin/env bash
# One-command MnemOS + OpenClaw setup (Linux/macOS)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$HOME/.openclaw}"
WORKSPACE_DIR="$CONFIG_DIR/workspace"

echo "=== MnemOS + OpenClaw Setup ==="

command -v node >/dev/null || { echo "Node.js 24+ required"; exit 1; }
echo "Node: $(node --version)"

if ! command -v openclaw >/dev/null 2>&1; then
  echo "Installing OpenClaw..."
  npm install -g openclaw@latest
else
  echo "OpenClaw: $(openclaw --version)"
fi

echo "Installing MnemOS MCP server..."
(cd "$ROOT/mcp-server" && npm install)

mkdir -p "$WORKSPACE_DIR/skills/mnemos-memory"
cp "$ROOT/config/workspace/AGENTS.md" "$WORKSPACE_DIR/"
cp "$ROOT/config/workspace/SOUL.md" "$WORKSPACE_DIR/"
cp "$ROOT/config/workspace/TOOLS.md" "$WORKSPACE_DIR/"
cp "$ROOT/config/workspace/IDENTITY.md" "$WORKSPACE_DIR/"
cp "$ROOT/config/workspace/USER.md" "$WORKSPACE_DIR/"
cp "$ROOT/config/workspace/skills/mnemos-memory/SKILL.md" "$WORKSPACE_DIR/skills/mnemos-memory/"
echo "Workspace files copied to $WORKSPACE_DIR"

MCP_PATH="$ROOT/mcp-server/src/index.js"
openclaw mcp set mnemos "{\"command\":\"node\",\"args\":[\"$MCP_PATH\",\"--transport\",\"stdio\"],\"env\":{\"MNEMOS_URL\":\"http://localhost:8000\"}}" 2>/dev/null || \
  echo "Note: openclaw mcp set failed — register manually"

USER_FILE="$CONFIG_DIR/mnemos-user-id.txt"
if [ ! -f "$USER_FILE" ]; then
  # Resolve canonical user_id from MnemOS so visualizer and agent share the same ID
  CANONICAL_ID=$(curl -s -X POST http://127.0.0.1:8000/api/user/bind \
      -H 'Content-Type: application/json' \
      -d '{"channel":"openclaw","sender_id":"main"}' 2>/dev/null | \
      python3 -c "import sys,json; print(json.load(sys.stdin).get('user_id',''))" 2>/dev/null)
  if [ -n "$CANONICAL_ID" ]; then
    echo "$CANONICAL_ID" > "$USER_FILE"
  else
    uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid > "$USER_FILE"
  fi
fi
echo "Shared user_id: $(cat "$USER_FILE")"

(cd "$ROOT" && docker compose up -d --build)

echo ""
echo "Done. Run: openclaw gateway restart && openclaw dashboard"
