#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

[[ -f .env.cloud ]] || { echo "Missing .env.cloud; copy .env.cloud.example and replace every example value." >&2; exit 1; }
for command in docker curl; do command -v "$command" >/dev/null || { echo "Missing required command: $command" >&2; exit 1; }; done
# Compose preserves a trailing carriage return from Windows-authored env files.
# Normalize line endings before validation so database names and credentials are exact.
sed -i 's/\r$//' .env.cloud
if grep -Eq 'replace-with|example\.com' .env.cloud; then echo ".env.cloud still contains example values." >&2; exit 1; fi

docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml config --quiet
set -a; source .env.cloud; set +a
docker build -t "${JUDGE_RUNNER_IMAGE}" workspace-runner
docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml up -d --build
echo "Cloud stack started. Run scripts/verify-cloud.sh after DNS and TLS become ready."
