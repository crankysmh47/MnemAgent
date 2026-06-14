#!/usr/bin/env bash
# =============================================================================
# MnemAgent — Daily Development Startup
#
# Lightweight startup for day-to-day development after setup.sh has been run.
# Starts Docker services and the OpenClaw gateway, then verifies health.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

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

# ── Helpers ──────────────────────────────────────────────────────────────────
check_docker() { docker info >/dev/null 2>&1; }
check_openclaw() { command -v openclaw >/dev/null 2>&1; }

wait_health() {
    local url="$1" label="$2" timeout="${3:-45}"
    local interval=3 elapsed=0
    while [ "$elapsed" -lt "$timeout" ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            if curl -s "$url" 2>/dev/null | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    sys.exit(0 if d.get('status') == 'ok' else 1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
                log_green "  $label ready"
                return 0
            fi
        fi
        sleep "$interval"
        elapsed=$((elapsed + interval))
    done
    log_red "  $label not healthy within ${timeout}s"
    return 1
}

# ═════════════════════════════════════════════════════════════════════════════
log_cyan ""
log_cyan "╔══════════════════════════════════════════════════════════════╗"
log_cyan "║         MnemAgent — Daily Dev Startup                      ║"
log_cyan "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Prerequisites ────────────────────────────────────────────────────────────
if ! check_docker; then
    log_red "Docker is not running. Start Docker Desktop and try again."
    exit 1
fi

# ── Start Docker services ────────────────────────────────────────────────────
log_cyan "[1/3] Starting MnemOS Docker services..."
(cd "$ROOT" && docker compose up -d --build >/dev/null 2>&1) || {
    log_red "docker compose failed"
    exit 1
}

log_cyan "       Waiting for services ..."
wait_health "http://127.0.0.1:8000/health" "MnemOS memory (:8000)" 60
wait_health "http://127.0.0.1:8001/health" "MnemOS MCP  (:8001)"   45

# ── Gateway ──────────────────────────────────────────────────────────────────
log_cyan "[2/3] OpenClaw gateway..."
if check_openclaw; then
    if openclaw gateway health 2>&1 | grep -qiE 'error|refused|not running'; then
        log_yellow "  Gateway not running — starting..."
        openclaw gateway restart --force >/dev/null 2>&1
        sleep 5
    fi
    if openclaw gateway health 2>&1 | grep -qiE 'error|refused|not running'; then
        log_yellow "  Gateway could not start. Run: openclaw gateway restart --force"
    else
        log_green "  Gateway running"
    fi
else
    log_yellow "  OpenClaw not installed. Run: npm install -g openclaw@latest"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
log_cyan "[3/3] Ready"
echo ""
log_green "  MnemOS is up and running!"
log_gray "    Dashboard:  http://localhost:3000"
log_gray "    Visualizer: http://localhost:3000/visualizer"
log_gray "    Gateway:    http://localhost:18789"
echo ""

if check_openclaw; then
    log_gray "  Commands:"
    log_gray "    openclaw dashboard"
    log_gray "    openclaw agent --agent main --message \"Hello\""
    log_gray "    openclaw mcp probe mnemos"
    echo ""
fi
