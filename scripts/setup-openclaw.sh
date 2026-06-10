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
cp "$ROOT/workspace-config/AGENTS.md" "$WORKSPACE_DIR/"
cp "$ROOT/workspace-config/SOUL.md" "$WORKSPACE_DIR/"
cp "$ROOT/workspace-config/TOOLS.md" "$WORKSPACE_DIR/"
cp "$ROOT/workspace-config/IDENTITY.md" "$WORKSPACE_DIR/"
cp "$ROOT/workspace-config/USER.md" "$WORKSPACE_DIR/"
cp "$ROOT/workspace-config/skills/mnemos-memory/SKILL.md" "$WORKSPACE_DIR/skills/mnemos-memory/"
echo "Workspace files copied to $WORKSPACE_DIR"

MCP_PATH="$ROOT/mcp-server/src/index.js"
openclaw mcp set mnemos "{\"command\":\"node\",\"args\":[\"$MCP_PATH\",\"--transport\",\"stdio\"],\"env\":{\"MNEMOS_URL\":\"http://localhost:8000\"}}" 2>/dev/null || \
  echo "Note: openclaw mcp set failed — register manually"

USER_FILE="$CONFIG_DIR/mnemos-user-id.txt"
if [ ! -f "$USER_FILE" ]; then
  uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid > "$USER_FILE"
fi
echo "Shared user_id: $(cat "$USER_FILE")"

(cd "$ROOT" && docker compose up -d --build)

echo ""
echo "Done. Run: openclaw gateway restart && openclaw dashboard"
