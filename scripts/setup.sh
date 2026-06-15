#!/usr/bin/env bash
# =============================================================================
# MnemAgent — One-command setup
#   Clones the repo? Run this. That's it.
#
#   bash scripts/setup.sh
#
# Installs prerequisites, starts Docker services, onboards OpenClaw,
# registers the MnemOS MCP toolset, and verifies everything works.
#
# Works on: Linux, macOS, WSL (Windows Subsystem for Linux)
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$HOME/.openclaw}"
WORKSPACE_DIR="$CONFIG_DIR/workspace"
STEP_OK=true

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
BOLD='\033[1m'
NC='\033[0m'

log_green()  { printf "${GREEN}%s${NC}\n" "$*"; }
log_yellow() { printf "${YELLOW}%s${NC}\n" "$*"; }
log_red()    { printf "${RED}%s${NC}\n" "$*"; }
log_cyan()   { printf "${CYAN}%s${NC}\n" "$*"; }
log_gray()   { printf "${GRAY}%s${NC}\n" "$*"; }
log_bold()   { printf "${BOLD}%s${NC}\n" "$*"; }

# ── Step helper ──────────────────────────────────────────────────────────────
step() {
    local name="$1"; shift
    printf "  ${BOLD}>>${NC} %s ... " "$name"
    if "$@"; then
        log_green "OK"
    else
        log_red "FAIL"
        STEP_OK=false
    fi
}

# ── Prerequisite helpers ─────────────────────────────────────────────────────
check_docker()   { docker info >/dev/null 2>&1; }
check_node()     { command -v node >/dev/null 2>&1; }
check_npm()      { command -v npm >/dev/null 2>&1; }
check_python3()  { command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; }
check_openclaw() { command -v openclaw >/dev/null 2>&1; }
check_venv()     { [ -f "$ROOT/.venv/bin/python" ] || [ -f "$ROOT/.venv/Scripts/python" ]; }

python_bin() {
    command -v python3 || command -v python || echo "python3"
}

python_ver() {
    ($(python_bin) --version 2>/dev/null || echo "unknown") | cut -d' ' -f2
}

# ── Read value from .env ─────────────────────────────────────────────────────
get_env() {
    local key="$1"
    local env_file="$ROOT/.env"
    [ -f "$env_file" ] || return 1
    grep -s "^${key}=" "$env_file" | cut -d= -f2- || true
}

# ── Wait for HTTP health endpoint (with countdown) ───────────────────────────
wait_health() {
    local url="$1" label="$2" timeout="${3:-90}"
    local interval=3 elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            # Verify JSON { "status": "ok" }
            if curl -s "$url" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    sys.exit(0 if d.get('status') == 'ok' else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
                log_green "  $label ready after ${elapsed}s"
                return 0
            fi
        fi
        # Print countdown (only every 6s to avoid spam)
        if [ $((elapsed % 6)) -eq 0 ]; then
            printf "\r  Waiting for %-30s ... %ds" "$label" "$((timeout - elapsed))"
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    printf "\r  %-50s\n" ""
    log_red "  $label not healthy within ${timeout}s"
    return 1
}

# ═════════════════════════════════════════════════════════════════════════════
log_cyan ""
log_cyan "╔══════════════════════════════════════════════════════════════╗"
log_cyan "║                                                             ║"
log_cyan "║            MnemAgent — One-Command Setup                    ║"
log_cyan "║     MnemOS Memory Layer  +  OpenClaw AI Agent              ║"
log_cyan "║                                                             ║"
log_cyan "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# STEP 0 — PREREQUISITES
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[0/7] Checking prerequisites ..."

step "Docker (Desktop / Engine) running" check_docker
step "Node.js installed"               check_node
echo " ($(node --version))"
step "npm installed"                   check_npm
echo " ($(npm --version))"
step "Python 3.11+ available"          check_python3
echo " ($(python_ver))"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — ENVIRONMENT FILE
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[1/7] Environment configuration ..."

if [ ! -f "$ROOT/.env" ]; then
    cp "$ROOT/config/env.template" "$ROOT/.env"
    log_green "  Created .env from template"
    log_yellow ""
    log_yellow "  ┌────────────────────────────────────────────────────────────┐"
    log_yellow "  │  FIRST-TIME SETUP                                         │"
    log_yellow "  │                                                            │"
    log_yellow "  │  1. Get a free API key:  https://openrouter.ai/keys       │"
    log_yellow "  │  2. Edit .env and set your QWEN_API_KEY                   │"
    log_yellow "  │  3. Run setup again:     bash scripts/setup.sh            │"
    log_yellow "  │                                                            │"
    log_yellow "  │  OR continue now (OpenClaw will use the placeholder and   │"
    log_yellow "  │  you can update .env later, then re-onboard).             │"
    log_yellow "  └────────────────────────────────────────────────────────────┘"
    echo ""
else
    log_gray "  .env exists (skipped)"
fi

# Warn if API key is still a placeholder
API_KEY=$(get_env "QWEN_API_KEY" || echo "")
if echo "$API_KEY" | grep -qiE "xxxx|sk-or-v1-xxxxxxxx"; then
    log_yellow "  WARNING: QWEN_API_KEY is still a placeholder — edit .env to use agents"
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — PYTHON VIRTUAL ENVIRONMENT
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[2/7] Python virtual environment ..."

if ! check_venv; then
    step "Creating .venv" bash -c "
        cd '$ROOT'
        $(python_bin) -m venv .venv
    "
    step "Installing Python dependencies" bash -c "
        cd '$ROOT'
        if [ -f '.venv/bin/pip' ]; then
            .venv/bin/pip install -r requirements.txt --quiet
        elif [ -f '.venv/Scripts/pip' ]; then
            .venv/Scripts/pip install -r requirements.txt --quiet
        fi
    "
    log_green "  .venv ready with $(wc -l < "$ROOT/requirements.txt") packages"
else
    log_gray "  .venv exists (skipped)"
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — DOCKER SERVICES
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[3/7] Starting MnemOS Docker services ..."

step "Building and starting containers" bash -c "
    cd '$ROOT' && docker compose up -d --build >/dev/null 2>&1
"

MEM_OK=true
MCP_OK=true

log_cyan "       Waiting for services (this may take a moment) ..."
wait_health "http://127.0.0.1:8000/health" "MnemOS memory (:8000)" 120 || MEM_OK=false
wait_health "http://127.0.0.1:8001/health" "MnemOS MCP  (:8001)"   90  || MCP_OK=false
wait_health "http://127.0.0.1:3000/health" "Visualizer  (:3000)"   90  || true

# Seed demo-brain for visualizer (~62 beliefs, hub-linked graph)
seed_demo_brain() {
    curl -sf -X POST "http://127.0.0.1:3000/api/demo/seed" \
        -H "Content-Type: application/json" \
        -d '{"force":false}' >/dev/null 2>&1 || return 1
}
step "Seed demo-brain visualizer" seed_demo_brain

if [ "$MEM_OK" = false ] || [ "$MCP_OK" = false ]; then
    log_red "  Some Docker services failed to start."
    log_yellow "  Check logs: docker compose logs"
    STEP_OK=false
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — OPENCLAW INSTALL
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[4/7] OpenClaw installation ..."

if ! check_openclaw; then
    step "Installing OpenClaw (global)" bash -c "npm install -g openclaw@latest >/dev/null 2>&1"
    log_green "  OpenClaw: $(openclaw --version 2>/dev/null)"
else
    log_gray "  OpenClaw: $(openclaw --version 2>/dev/null) (already installed)"
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — OPENCLAW ONBOARD
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[5/7] OpenClaw onboarding ..."

OPENCLAW_CONFIG_FILE="$CONFIG_DIR/openclaw.json"
BASE_URL="${QWEN_BASE_URL:-$(get_env QWEN_BASE_URL || echo 'https://openrouter.ai/api/v1')}"

# Use API key from env var or .env
if [ -z "$API_KEY" ] || echo "$API_KEY" | grep -qiE "xxxx|sk-or-v1-xxxxxxxx"; then
    ONBOARD_KEY="${QWEN_API_KEY:-}"
    [ -z "$ONBOARD_KEY" ] && ONBOARD_KEY="sk-or-v1-placeholder"
else
    ONBOARD_KEY="$API_KEY"
fi

do_onboard() {
    if [ -f "$OPENCLAW_CONFIG_FILE" ]; then
        log_gray "  Config exists — skipping onboard"
        return 0
    fi
    openclaw onboard \
        --non-interactive \
        --accept-risk \
        --flow quickstart \
        --auth-choice custom-api-key \
        --custom-api-key "$ONBOARD_KEY" \
        --custom-base-url "$BASE_URL" \
        --custom-model-id "openrouter/free" \
        --custom-compatibility openai \
        --custom-provider-id openrouter \
        --skip-channels \
        --skip-skills \
        --skip-search \
        --skip-hooks \
        --install-daemon \
        --gateway-bind loopback \
        --gateway-port 18789 >/dev/null 2>&1
}

step "Onboarding OpenClaw" do_onboard

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — MNEMOS MCP INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[6/7] Integrating MnemOS MCP tools ..."

MCP_JS="$ROOT/mcp-server/src/index.js"

# Install MCP server npm deps
step "MCP server npm dependencies" bash -c "
    cd '$ROOT/mcp-server' && npm install --silent 2>/dev/null
"

# Register MnemOS MCP (stdio transport)
register_mcp() {
    openclaw mcp unset mnemos 2>/dev/null || true
    openclaw mcp add mnemos \
        --command node \
        --arg "$MCP_JS" \
        --arg "--transport" \
        --arg "stdio" \
        --env "MNEMOS_URL=http://localhost:8000" \
        --timeout 120 \
        --connect-timeout 30 >/dev/null 2>&1
}
step "Register MnemOS MCP tools" register_mcp

# Apply free model bundle (OpenRouter free tier fallbacks)
FREE_PATCH="$ROOT/config/openclaw/free-models.patch.json"
apply_free_patch() {
    if [ -f "$FREE_PATCH" ]; then
        cat "$FREE_PATCH" | openclaw config patch --stdin >/dev/null 2>&1
        openclaw config set gateway.auth.mode none >/dev/null 2>&1
    fi
}
if [ -f "$FREE_PATCH" ]; then
    step "Apply free model bundle" apply_free_patch
fi

# Copy workspace files to ~/.openclaw/workspace/
copy_workspace() {
    mkdir -p "$WORKSPACE_DIR/skills/mnemos-memory"
    cp -r "$ROOT/config/workspace/"* "$WORKSPACE_DIR/" 2>/dev/null || true
    # Fix the placeholder path in .mcp.json
    if [ -f "$WORKSPACE_DIR/.mcp.json" ]; then
        if [[ "$(uname)" == "Darwin" ]]; then
            sed -i '' "s|REPLACE_WITH_REPO_PATH|$ROOT|g" "$WORKSPACE_DIR/.mcp.json" 2>/dev/null || true
        else
            sed -i "s|REPLACE_WITH_REPO_PATH|$ROOT|g" "$WORKSPACE_DIR/.mcp.json" 2>/dev/null || true
        fi
    fi
}
step "Copy workspace files" copy_workspace

# Generate a persistent user ID
USER_FILE="$CONFIG_DIR/mnemos-user-id.txt"
if [ ! -f "$USER_FILE" ]; then
    uuidgen 2>/dev/null > "$USER_FILE" 2>/dev/null || \
        python3 -c "import uuid; print(uuid.uuid4())" > "$USER_FILE" 2>/dev/null || \
        date +%s | md5sum | head -c 32 > "$USER_FILE"
fi
USER_ID=$(cat "$USER_FILE" 2>/dev/null || echo "your-user-id")

# ═════════════════════════════════════════════════════════════════════════════
# STEP 7 — GATEWAY START + VERIFY
# ═════════════════════════════════════════════════════════════════════════════
log_cyan "[7/7] Starting gateway and verifying ..."

start_gateway() {
    openclaw gateway restart --force >/dev/null 2>&1
    sleep 6
    # Verify it's running
    if openclaw gateway health 2>&1 | grep -qiE 'error|refused|not running'; then
        sleep 6
        openclaw gateway health >/dev/null 2>&1 || true
    fi
}
step "Starting OpenClaw gateway" start_gateway

# Verify MnemOS MCP probe (expect 7 tools)
verify_mcp() {
    local output
    output=$(openclaw mcp probe mnemos 2>&1)
    local count
    count=$(echo "$output" | grep -oE '[0-9]+' | head -1)
    if [ -z "$count" ] || [ "$count" -lt 7 ]; then
        log_yellow "  Found ${count:-0} tools (expected 7) — check: openclaw mcp list"
        return 1
    fi
    echo " ($count tools available)"
    return 0
}
step "Verify MnemOS MCP (7 tools)" verify_mcp

# ── SUMMARY ──────────────────────────────────────────────────────────────────
echo ""
log_cyan "╔══════════════════════════════════════════════════════════════╗"
log_cyan "║                                                             ║"
if [ "$STEP_OK" = true ]; then
    log_green "║           MNEMAGENT SETUP COMPLETE                         ║"
else
    log_yellow "║           Setup completed with warnings                   ║"
fi
log_cyan "║                                                             ║"
log_cyan "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo -e "  ${BOLD}Services Running${NC}"
log_gray "    o Memory API:  http://localhost:8000/docs"
log_gray "    o MCP Server:  http://localhost:8001/health"
log_gray "    o Web Harness: http://localhost:3000?user=demo-brain"
log_gray "    o Visualizer:  http://localhost:3000?user=demo-brain"
log_gray "    o Gateway:     http://localhost:18789"
echo ""

echo -e "  ${BOLD}Quick-Start Commands${NC}"
log_gray "    o Chat (CLI):   openclaw agent --agent main --message \"Hello\""
log_gray "    o Dashboard:    openclaw dashboard"
log_gray "    o MCP Verify:   openclaw mcp probe mnemos"
log_gray "    o TUI (chat):   openclaw tui"
echo ""

echo -e "  ${BOLD}Daily Startup${NC}"
log_gray "    bash scripts/dev.sh"
echo ""

echo -e "  ${BOLD}Your MnemOS User ID${NC}"
log_gray "    $USER_ID"
echo ""

# Try to open the visualizer in the browser
if [ "$STEP_OK" = true ]; then
    if [[ "$(uname)" == "Darwin" ]]; then
        open "http://localhost:3000?user=demo-brain" 2>/dev/null || true
    elif [[ "$(uname)" == "Linux" ]]; then
        xdg-open "http://localhost:3000?user=demo-brain" 2>/dev/null || true
    fi
fi
