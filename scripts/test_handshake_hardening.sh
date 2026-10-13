#!/usr/bin/env bash
# Hostile peers against the version handshake, with real separate processes.
#   Server side: the stock dedicated server against game/tests/handshake_attack_probe.gd.
#   Client side: the stock client (protocol_client_probe.gd) against
#                game/tests/handshake_server_probe.gd.
# Prints one RESULT line per scenario and HANDSHAKE_HARDENING PASS|FAIL; exits non-zero
# on any failed expectation. Usage: scripts/test_handshake_hardening.sh [output-dir]
set -uo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="${1:-$(mktemp -d)}"
mkdir -p "$out_dir"
godot_bin="${GODOT_BIN:-${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
run_godot() { # state-dir args...
  local state="$1"; shift
  mkdir -p "$state"
  XDG_DATA_HOME="$state" XDG_CONFIG_HOME="$state" XDG_CACHE_HOME="$state" exec "$godot_bin" --headless --path "$repo_dir/game" "$@"
}
(run_godot "$out_dir/state/import" --import >/dev/null 2>&1)
port=$(( 30200 + (RANDOM % 400) * 8 ))
wait_ready() { for attempt in $(seq 1 100); do grep -q SIGHTBREAK_SERVER_READY "$1" && return 0; sleep 0.1; done; return 1; }
for scenario in spam fractional huge good_then_bad bad_then_good; do
  port=$((port + 1))
  (run_godot "$out_dir/state/server-$scenario" -- --server --port=$port > "$out_dir/attack-$scenario.server.log" 2>&1) &
  server_pid=$!
  if wait_ready "$out_dir/attack-$scenario.server.log"; then
    (run_godot "$out_dir/state/attack-$scenario" --script res://tests/handshake_attack_probe.gd -- --port=$port --scenario=$scenario > "$out_dir/attack-$scenario.client.log" 2>&1)
    sleep 0.5
  fi
  kill "$server_pid" 2>/dev/null; wait "$server_pid" 2>/dev/null
done
for scenario in hang_up reject_then_hang_up accepted_text; do
  port=$((port + 1))
  (run_godot "$out_dir/state/probe-server-$scenario" --script res://tests/handshake_server_probe.gd -- --port=$port --scenario=$scenario > "$out_dir/hostile-$scenario.server.log" 2>&1) &
  server_pid=$!
  if wait_ready "$out_dir/hostile-$scenario.server.log"; then
    (run_godot "$out_dir/state/client-$scenario" --script res://tests/protocol_client_probe.gd -- --port=$port --seconds=8 --name="Hardening client" > "$out_dir/hostile-$scenario.client.log" 2>&1)
  fi
  kill "$server_pid" 2>/dev/null; wait "$server_pid" 2>/dev/null
done
python3 - "$out_dir" <<'PY'
import json, pathlib, re, sys
out = pathlib.Path(sys.argv[1])
failed = False
def result(name, ok, detail):
    global failed
    failed |= not ok
    print(f"RESULT {name} {'PASS' if ok else 'FAIL'} {detail}")
def attack(name):
    log = (out / f"attack-{name}.client.log").read_text(errors="replace") if (out / f"attack-{name}.client.log").exists() else ""
    match = re.search(r"^HANDSHAKE_ATTACK (.*)$", log, re.M)
    server = (out / f"attack-{name}.server.log").read_text(errors="replace")
    return (json.loads(match.group(1)) if match else {}), server
for name in ("spam", "fractional", "huge", "bad_then_good"):
    data, server = attack(name)
    rejected = server.count("PROTOCOL_REJECTED")
    errors = len(re.findall(r"^(ERROR|SCRIPT ERROR)", server, re.M))
    ok = bool(data) and not data["admitted"] and data["replies"] == 1 and 0 < data["dropped_after"] < 1.5 and rejected == 1 and errors == 0
    result(name, ok, f"admitted={data.get('admitted')} replies={data.get('replies')} dropped_after={data.get('dropped_after')}s server_rejections={rejected} server_errors={errors}")
data, server = attack("good_then_bad")
rejected = server.count("PROTOCOL_REJECTED")
errors = len(re.findall(r"^(ERROR|SCRIPT ERROR)", server, re.M))
result("good_then_bad", bool(data) and data["admitted"] and rejected == 0 and errors == 0,
       f"admitted={data.get('admitted')} server_rejections={rejected} server_errors={errors}")
expect = {"hang_up": "closed the connection during the version check",
          "reject_then_hang_up": "closed the connection during the version check",
          "accepted_text": "Version mismatch"}
for name, phrase in expect.items():
    log = (out / f"hostile-{name}.client.log").read_text(errors="replace") if (out / f"hostile-{name}.client.log").exists() else ""
    notices = re.findall(r"^PROTOCOL_NOTICE ([0-9.]+) (.*)$", log, re.M)
    final = notices[-1] if notices else ("", "")
    errors = len(re.findall(r"^SCRIPT ERROR", log, re.M))
    ok = phrase in final[1] and "older SIGHTBREAK release" not in final[1] and errors == 0
    result(name, ok, f"script_errors={errors} last_notice=\"{final[1][:110]}\"")
print("HANDSHAKE_HARDENING " + ("FAIL" if failed else "PASS"))
sys.exit(1 if failed else 0)
PY
