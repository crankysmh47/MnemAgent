#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
[[ -f .env.cloud ]] || { echo "Missing .env.cloud" >&2; exit 1; }
namespace="judge-$(date -u +%Y%m%d-%H%M%S)"
echo "Set MNEMOS_DEFAULT_USER_ID=${namespace} in .env.cloud, then redeploy. demo-brain is preserved."
