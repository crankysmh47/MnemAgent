#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
metadata='http://100.100.100.200/latest/meta-data/instance/spot/termination-time'
if termination="$(curl --silent --fail --max-time 2 "$metadata" 2>/dev/null)" && [[ -n "$termination" ]]; then
  install -m 600 /dev/null .judge-runs-blocked
  docker compose --env-file .env.cloud -f docker-compose.yml -f compose.cloud.yml exec -T postgres \
    pg_dump -U "${POSTGRES_USER:-mnemagent}" "${POSTGRES_DB:-mnemagent}" | gzip > "backup-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
  echo "Spot interruption detected for $termination; new judge runs blocked and database backed up."
fi
