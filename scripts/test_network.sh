#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
LOG_DIR=$(mktemp -d)
SERVER_PID=''
CLIENT_A=''
CLIENT_B=''
cleanup() {
  for pid in "$SERVER_PID" "$CLIENT_A" "$CLIENT_B"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
}
trap cleanup EXIT
./scripts/godot.sh --headless --script res://tests/network_probe.gd -- --server >"$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
for attempt in $(seq 1 80); do
  if rg -q 'SIGHTBREAK_SERVER_READY' "$LOG_DIR/server.log"; then break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then cat "$LOG_DIR/server.log"; exit 1; fi
  sleep 0.1
done
./scripts/godot.sh --headless --script res://tests/network_probe.gd >"$LOG_DIR/client-a.log" 2>&1 &
CLIENT_A=$!
./scripts/godot.sh --headless --script res://tests/network_probe.gd >"$LOG_DIR/client-b.log" 2>&1 &
CLIENT_B=$!
RESULT=0
wait "$CLIENT_A" || RESULT=1
wait "$CLIENT_B" || RESULT=1
cat "$LOG_DIR/server.log" "$LOG_DIR/client-a.log" "$LOG_DIR/client-b.log"
if ! rg -q NETWORK_CLIENT_PASS "$LOG_DIR/client-a.log" || ! rg -q NETWORK_CLIENT_PASS "$LOG_DIR/client-b.log"; then RESULT=1; fi
if rg -q '^ERROR:|SCRIPT ERROR|Parse Error' "$LOG_DIR"; then RESULT=1; fi
exit "$RESULT"
