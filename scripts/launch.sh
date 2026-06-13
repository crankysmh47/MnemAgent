#!/usr/bin/env bash
# Unified MnemAgent launcher with mandatory MnemOS + OpenClaw integration
# Equivalent of launch.ps1 for Linux/macOS/WSL
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_DIR="${OPENCLAW_CONFIG_DIR:-$HOME/.openclaw}"
STEP_OK=true

# ── Color helpers ──────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

log_green()  { printf "${GREEN}%s${NC}\n" "$*"; }
log_yellow() { printf "${YELLOW}%s${NC}\n" "$*"; }
log_red()    { printf "${RED}%s${NC}\n" "$*"; }
log_cyan()   { printf "${CYAN}%s${NC}\n" "$*"; }
log_gray()   { printf "${GRAY}%s${NC}\n" "$*"; }

# ── Step helper ────────────────────────────────────────────────────────────
step() {
    local name="$1"; shift
    printf "  >> %s ... " "$name"
    if "$@"; then
        log_green "OK"
    else
        log_red "FAIL"
        STEP_OK=false
    fi
}

# ── Prerequisite helpers ───────────────────────────────────────────────────
check_docker() {
    docker info >/dev/null 2>&1
}

check_node() {
    command -v node >/dev/null 2>&1
}

check_venv() {
    [ -f "$ROOT/.venv/bin/python" ] || [ -f "$ROOT/.venv/Scripts/python" ]
}

check_openclaw() {
    command -v openclaw >/dev/null 2>&1
}

# Retrieve .env values
get_env() {
    local key="$1"
    local env_file="$ROOT/.env"
    [ -f "$env_file" ] || return 1
    grep -s "^${key}=" "$env_file" | cut -d= -f2- || true
}

# Wait for HTTP health endpoint
wait_health() {
    local url="$1" label="$2" timeout="${3:-60}"
    local interval=3 elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            if curl -s "$url" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('status')=='ok' else 1)" 2>/dev/null; then
                log_green "  $label ready after ${elapsed}s"
                return 0
            fi
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    log_red "  $label not healthy within ${timeout}s"
    return 1
}

# ═══════════════════════════════════════════════════════════════════════════
log_cyan "╔══════════════════════════════════════════════════════════════╗"
log_cyan "║         MnemAgent Unified Launcher                         ║"
log_cyan "║   MnemOS Memory Layer + OpenClaw Integration               ║"
log_cyan "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── 1. PREREQUISITES ──────────────────────────────────────────────────────
log_cyan "[1/6] Checking prerequisites..."

step "Docker running" check_docker

step "Node.js installed" check_node
echo " ($(node --version))"

step "Python virtual environment" check_venv || {
    log_yellow "  .venv not found, creating..."
    (cd "$ROOT" && python3 -m venv .venv)
    pip_install() {
        if [ -f "$ROOT/.venv/bin/pip" ]; then
            "$ROOT/.venv/bin/pip" install -r "$ROOT/requirements.txt" --quiet
        elif [ -f "$ROOT/.venv/Scripts/pip" ]; then
            "$ROOT/.venv/Scripts/pip" install -r "$ROOT/requirements.txt" --quiet
        else
            return 1
        fi
    }
    pip_install
    log_green "  .venv created and packages installed"
}

# ── 2. DOCKER SERVICES ────────────────────────────────────────────────────
log_cyan "[2/6] Starting Docker services..."
(cd "$ROOT" && docker compose up -d --build) || {
    log_red "docker compose failed"
    STEP_OK=false
}

# ── 3. WAIT FOR MNEMOS ────────────────────────────────────────────────────
log_cyan "[3/6] Waiting for MnemOS services..."

MEM_OK=true
wait_health "http://127.0.0.1:8000/health" "MnemOS memory (:8000)" || MEM_OK=false

MCP_OK=true
wait_health "http://127.0.0.1:8001/health" "MnemOS MCP (:8001)" || MCP_OK=false

# Harness (optional)
if curl -sf "http://127.0.0.1:3000/health" >/dev/null 2>&1; then
    log_green "  Harness (:3000) ready"
else
    log_yellow "  Harness (:3000) not responding yet"
fi

# ── 4. OPENCLAW INTEGRATION ───────────────────────────────────────────────
log_cyan "[4/6] OpenClaw integration..."

if check_openclaw; then
    log_gray "  OpenClaw: $(openclaw --version 2>/dev/null)"

    # MCP server dependencies
    step "MCP server npm dependencies" \
        bash -c "cd '$ROOT/mcp-server' && npm install --silent 2>/dev/null"

    # Register MnemOS MCP
    step "Register MnemOS MCP tools" bash -c "
        MCP_PATH='$ROOT/mcp-server/src/index.js'
        openclaw mcp unset mnemos 2>/dev/null
        openclaw mcp add mnemos \
            --command node \
            --arg \"\$MCP_PATH\" \
            --arg '--transport' \
            --arg 'stdio' \
            --env 'MNEMOS_URL=http://localhost:8000' \
            --timeout 120 \
            --connect-timeout 30 >/dev/null 2>&1
    "

    # Free model bundle
    FREE_PATCH="$ROOT/config/openclaw/free-models.patch.json"
    if [ -f "$FREE_PATCH" ]; then
        step "Apply free model bundle" bash -c "
            cat '$FREE_PATCH' | openclaw config patch --stdin >/dev/null 2>&1
            openclaw config set gateway.auth.mode none >/dev/null 2>&1
        "
    fi

    # Gateway management
    step "Gateway health check" bash -c "
        if openclaw gateway health 2>&1 | grep -qiE 'error|refused|not running'; then
            log_yellow '  Gateway not running, starting...'
            openclaw gateway restart --force >/dev/null 2>&1
            sleep 5
        fi
        if openclaw gateway health 2>&1 | grep -qiE 'error|refused|not running'; then
            exit 1
        fi
    "

    # Verify MCP probe
    step "Verify MnemOS MCP probe" bash -c "
        probe=\$(openclaw mcp probe mnemos 2>&1)
        if ! echo \"\$probe\" | grep -qE '[0-9]+ tool'; then
            exit 1
        fi
        echo \" (\$(echo \"\$probe\" | tr -d '\\n'))\"
    "

    # Fix device scopes if script exists
    FIX_SCRIPT="$ROOT/scripts/fix-openclaw-device-scopes.ps1"
    if [ -f "$FIX_SCRIPT" ]; then
        # Bash can't run PS1 directly; note for user
        log_gray "  Note: run $FIX_SCRIPT manually on Windows if device scope issues arise"
    fi
else
    log_yellow "  OpenClaw not installed. Install with: npm install -g openclaw@latest"
fi

# ── 5. SERVICE SUMMARY ────────────────────────────────────────────────────
log_cyan "[5/6] Service summary..."
echo ""

# Build status strings
mem_status="Unknown"; [ "$MEM_OK" = true ] && mem_status="Running" || mem_status="FAILED"
mcp_status="Unknown"; [ "$MCP_OK" = true ] && mcp_status="Running" || mcp_status="FAILED"
harness_status="Unknown"
curl -sf "http://127.0.0.1:3000/health" >/dev/null 2>&1 && harness_status="Running" || harness_status="Unknown"

print_service_row() {
    local name="$1" port="$2" status="$3"
    local color="$GREEN"
    [ "$status" = "FAILED" ] && color="$RED"
    [ "$status" = "Unknown" ] && color="$YELLOW"
    printf "  | %-16s | %6s | " "$name" "$port"
    printf "${color}%-29s${NC}" "$status"
    printf "|\n"
}

echo "  +------------------+--------+-------------------------------+"
echo "  | Service          | Port   | Status                        |"
echo "  +------------------+--------+-------------------------------+"
print_service_row "MnemOS Memory API" "8000" "$mem_status"
print_service_row "MnemOS MCP Server" "8001" "$mcp_status"
print_service_row "Web Harness"      "3000" "$harness_status"
if check_openclaw; then
    if openclaw gateway health 2>&1 | grep -qiE "error|refused|not running"; then
        print_service_row "OpenClaw Gateway" "18789" "Stopped"
    else
        print_service_row "OpenClaw Gateway" "18789" "Running"
    fi
fi
echo "  +------------------+--------+-------------------------------+"

# ── 6. QUICK-START ────────────────────────────────────────────────────────
log_cyan "[6/6] Quick-start commands"
echo ""

echo -e "  ${GRAY}MnemOS Services Running:${NC}"
[ "$MEM_OK" = true ] && log_gray "    o Memory API:  http://localhost:8000/docs"
[ "$MCP_OK" = true ] && log_gray "    o MCP Server:  http://localhost:8001/health"
log_gray "    o Web Harness: http://localhost:3000"
log_gray "    o Visualizer:  http://localhost:3000/visualizer"
echo ""

if check_openclaw; then
    USER_FILE="$CONFIG_DIR/mnemos-user-id.txt"
    uid="your-user-id"
    [ -f "$USER_FILE" ] && uid="$(cat "$USER_FILE")"
    echo -e "  ${GRAY}OpenClaw Agent Commands:${NC}"
    log_gray "    o Chat (CLI):   openclaw agent --agent main --message \"Hello\""
    log_gray "    o Dashboard:    openclaw dashboard"
    log_gray "    o MCP Verify:   openclaw mcp probe mnemos"
    log_gray "    o MnemOS User:  $uid"
    echo ""
fi

echo -e "  ${GRAY}Demo & Test:${NC}"
log_gray "    o Seed demo:   bash scripts/start-demo.ps1  (or .\\scripts\\start-demo.ps1 on Windows)"
log_gray "    o Proof test:  pwsh scripts/prove-openclaw.ps1"
log_gray "    o Verify all:  pwsh scripts/submission-test.ps1"
echo ""

# ── FINAL ─────────────────────────────────────────────────────────────────
if [ "$STEP_OK" = true ]; then
    log_green "╔════════════════════════════════════════════════════════╗"
    log_green "║     MNEMAGENT LAUNCH COMPLETE                         ║"
    log_green "╚════════════════════════════════════════════════════════╝"
else
    log_yellow "╔════════════════════════════════════════════════════════╗"
    log_yellow "║  Launch completed with warnings.                     ║"
    log_yellow "║  Review messages above and fix issues.               ║"
    log_yellow "╚════════════════════════════════════════════════════════╝"
    exit 1
fi
