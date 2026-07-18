#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python -m pytest -q
npm test --prefix openclaw-harness
npm test --prefix workspace-runner
npm test --prefix workspace-broker
node openclaw-harness/scripts/check-visualizer.mjs
docker build -t "${JUDGE_RUNNER_IMAGE:-mnemagent-judge-runner:local}" workspace-runner
docker compose --env-file "${ENV_FILE:-.env.cloud}" -f docker-compose.yml -f compose.cloud.yml config --quiet

if git grep -nE '(ghp_|github_pat_|sk-or-v1-|AKIA[0-9A-Z]{16})' -- ':!scripts/verify-mnemcode.sh'; then
  echo "Possible committed secret detected." >&2
  exit 1
fi

echo "MnemCode unit, visual, container, configuration, and secret checks passed."
