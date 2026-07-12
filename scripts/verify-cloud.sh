#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env.cloud ]] || { echo "Missing .env.cloud" >&2; exit 1; }
set -a; source .env.cloud; set +a
: "${MEMORY_DOMAIN:?}"

curl --fail --silent --show-error "https://${MEMORY_DOMAIN}/health" >/dev/null
docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml ps
curl --fail --silent --show-error http://127.0.0.1:8001/health >/dev/null
echo "HTTPS, public health, and loopback-only MCP checks passed."
