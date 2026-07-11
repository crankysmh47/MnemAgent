#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env.cloud ]] || { echo "Missing .env.cloud" >&2; exit 1; }
set -a; source .env.cloud; set +a
: "${MEMORY_DOMAIN:?}" "${AGENT_DOMAIN:?}"

curl --fail --silent --show-error "https://${MEMORY_DOMAIN}/health" >/dev/null
status="$(curl --silent --output /dev/null --write-out '%{http_code}' "https://${AGENT_DOMAIN}/")"
[[ "$status" == 401 ]] || { echo "Agent UI must reject unauthenticated requests; got HTTP $status" >&2; exit 1; }
docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml ps
echo "HTTPS, public health, and OpenClaw authentication checks passed."
