#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -z "${SIGHTBREAK_SERVER_KEY:-}" ]]; then
  key_file="$repo_dir/.local/secrets/server.key"
  if [[ ! -r "$key_file" ]]; then
    printf 'Start backend/dev-api.sh first to initialize the local server identity.\n' >&2
    exit 1
  fi
  SIGHTBREAK_SERVER_KEY="$(cat "$key_file")"
  export SIGHTBREAK_SERVER_KEY
fi
exec "$repo_dir/scripts/godot.sh" --headless -- --server --require-accounts \
  "--server-id=${SIGHTBREAK_SERVER_ID:-local-relay}" \
  "--economy-url=${SIGHTBREAK_ECONOMY_URL:-http://127.0.0.1:8080}" \
  "--port=${SIGHTBREAK_GAME_PORT:-27020}"
