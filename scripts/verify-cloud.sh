#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env.cloud ]] || { echo "Missing .env.cloud" >&2; exit 1; }
set -a; source .env.cloud; set +a
: "${MEMORY_DOMAIN:?}"

curl --fail --silent --show-error "https://${MEMORY_DOMAIN}/health" >/dev/null
docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml ps
docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml exec -T openclaw-harness openclaw --version >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8001/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8010/health >/dev/null
if curl --fail --silent --show-error "https://${MEMORY_DOMAIN}/api/graph/not-a-judge" >/dev/null 2>&1; then
  echo "Unexpected public archive access." >&2; exit 1
fi
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT
login_json="$(printf '{"accessCode":"%s"}' "$JUDGE_ACCESS_CODE")"
curl --fail --silent --show-error -c "$tmp_dir/cookies" -H "Content-Type: application/json" -H "Origin: https://${MEMORY_DOMAIN}" --data "$login_json" "https://${MEMORY_DOMAIN}/judge/session" >"$tmp_dir/session.json"
node -e "const s=require(process.argv[1]); if(!/^judge-[a-f0-9]{16}$/.test(s.namespace)||s.quota.chatTurnsRemaining!==30||s.quota.codingRunsRemaining!==5||s.quota.publicationsRemaining!==5) process.exit(1)" "$tmp_dir/session.json"
curl --fail --silent --show-error -b "$tmp_dir/cookies" "https://${MEMORY_DOMAIN}/api/judge/session" >/dev/null
curl --fail --silent --show-error "https://${MEMORY_DOMAIN}/" | grep -q 'data-judge-chat'
echo "HTTPS, OpenClaw, signed judge session, sponsored quota, UI, archive policy, MCP, and broker checks passed."
