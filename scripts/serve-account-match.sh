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
# Local durable result worker. No listener/public infrastructure is created.
umask 077
export SIGHTBREAK_RESULT_SPOOL="${SIGHTBREAK_RESULT_SPOOL:-$repo_dir/.local/server-results/spool}"
result_db="${SIGHTBREAK_RESULT_DB:-$repo_dir/.local/server-results/results.sqlite}"
worker_log="${SIGHTBREAK_RESULT_LOG:-$repo_dir/.local/server-results/startup.log}"
mkdir -p "$(dirname "$worker_log")" "$SIGHTBREAK_RESULT_SPOOL"
: >"$worker_log" # Clear a prior READY marker synchronously before background startup.
python3 "$repo_dir/server/result_outbox.py" --database "$result_db" --spool "$SIGHTBREAK_RESULT_SPOOL" \
  "--backend=${SIGHTBREAK_ECONOMY_URL:-http://127.0.0.1:8080}" --log "$(dirname "$worker_log")/delivery.log" >"$worker_log" 2>&1 &
sightbreak_worker_pid=$!
sightbreak_game_pid=''
cleanup() {
  if [[ -n "$sightbreak_game_pid" ]]; then
    kill "$sightbreak_game_pid" 2>/dev/null || true
    wait "$sightbreak_game_pid" 2>/dev/null || true
  fi
  kill "$sightbreak_worker_pid" 2>/dev/null || true
  wait "$sightbreak_worker_pid" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
for attempt in {1..50}; do
  if ! kill -0 "$sightbreak_worker_pid" 2>/dev/null; then
    printf 'Result worker failed; inspect %s\n' "$worker_log" >&2
    exit 1
  fi
  if rg -q OUTBOX_READY "$worker_log"; then break; fi
  sleep 0.1
done
if ! rg -q OUTBOX_READY "$worker_log"; then
  printf 'Result worker readiness timed out.\n' >&2
  exit 1
fi
"$repo_dir/scripts/godot.sh" --headless -- --server --require-accounts \
  "--server-id=${SIGHTBREAK_SERVER_ID:-local-relay}" \
  "--economy-url=${SIGHTBREAK_ECONOMY_URL:-http://127.0.0.1:8080}" \
  "--port=${SIGHTBREAK_GAME_PORT:-27020}" &
sightbreak_game_pid=$!
while kill -0 "$sightbreak_game_pid" 2>/dev/null; do
  if ! kill -0 "$sightbreak_worker_pid" 2>/dev/null; then
    printf 'Result worker stopped unexpectedly; shutting down account match server. Durable results remain queued for restart.\n' >&2
    exit 1
  fi
  sleep 0.5
done
wait "$sightbreak_game_pid"
