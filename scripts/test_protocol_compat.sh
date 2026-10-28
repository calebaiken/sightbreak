#!/usr/bin/env bash
# Mixed-version matrix with real, separate dedicated-server and client processes.
#   release: an untouched `git archive` of RELEASE_REF (default: 0.3.0, e67f2c8)
#   current: this working tree
#   future:  a copy of this tree with PROTOCOL_VERSION bumped, standing in for the
#            next incompatible build (exercises the explicit rejection path)
#   legacy:  the last stack commit before Relay Yard layout 2 (LEGACY_LAYOUT_REF): protocol 6, but
#            a hello with no layout field, so the same protocol over a different collision world
# Only game/tests/protocol_client_probe.gd is added, as an external driver of each
# build's stock client. Writes matrix.md and exits non-zero if any expectation fails.
# Usage: scripts/test_protocol_compat.sh [output-dir]
set -uo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
release_ref="${RELEASE_REF:-e67f2c86777d98d3cb3ad6bc7e851ef1826af26d}"
out_dir="${1:-$(mktemp -d)}"
mkdir -p "$out_dir"
godot_bin="${GODOT_BIN:-${SIGHTBREAK_TOOLS_DIR:-$(dirname "$repo_dir")/tools}/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
probe="$repo_dir/game/tests/protocol_client_probe.gd"
run_godot() { # state-dir project args...
  local state="$1" project="$2"; shift 2
  mkdir -p "$state"
  XDG_DATA_HOME="$state" XDG_CONFIG_HOME="$state" XDG_CACHE_HOME="$state" exec "$godot_bin" --headless --path "$project" "$@"
}
release_dir="$out_dir/release-${release_ref:0:7}"
if [[ ! -f "$release_dir/game/project.godot" ]]; then
  mkdir -p "$release_dir"
  git -C "$repo_dir" archive "$release_ref" | tar -x -C "$release_dir"
fi
# Actual prior published input/RPC contract, not just a synthetic version edit.
legacy_ref="${LEGACY_LAYOUT_REF:-830bf2ba51146d7bd314261ff58044deea259e1b}"
legacy_dir="$out_dir/legacy-${legacy_ref:0:7}"
if [[ ! -f "$legacy_dir/game/project.godot" ]]; then
  mkdir -p "$legacy_dir"
  git -C "$repo_dir" archive "$legacy_ref" game | tar -x -C "$legacy_dir"
fi
previous_ref="89c0e997c9f706d91b02e5ac412853c4d35cd112"
previous_dir="$out_dir/previous-${previous_ref:0:7}"
mkdir -p "$previous_dir"
git -C "$repo_dir" archive "$previous_ref" game | tar -x -C "$previous_dir"
future_dir="$out_dir/future"
rm -rf "$future_dir"; mkdir -p "$future_dir"
(cd "$repo_dir" && tar --exclude=game/.godot -cf - game) | tar -xf - -C "$future_dir"
current_protocol=$(sed -n 's/^const PROTOCOL_VERSION := \([0-9]*\)$/\1/p' "$repo_dir/game/scripts/gameplay/match.gd")
sed -i "s/^const PROTOCOL_VERSION := .*/const PROTOCOL_VERSION := $((current_protocol + 1))/" "$future_dir/game/scripts/gameplay/match.gd"
for build in release previous legacy current future; do
  case "$build" in release) project="$release_dir/game";; previous) project="$previous_dir/game";; legacy) project="$legacy_dir/game";; current) project="$repo_dir/game";; future) project="$future_dir/game";; esac
  (run_godot "$out_dir/state/import-$build" "$project" --import >/dev/null 2>&1)
done
# A fresh port range per run; a port still held by another process fails the combo.
port=$(( 28200 + (RANDOM % 400) * 8 ))
for combo in release:release current:current release:current current:release future:current current:future previous:current current:previous legacy:current current:legacy; do
  client="${combo%%:*}"; server="${combo##*:}"
  name="client-$client.server-$server"
  case "$client" in release) client_project="$release_dir/game";; previous) client_project="$previous_dir/game";; legacy) client_project="$legacy_dir/game";; current) client_project="$repo_dir/game";; future) client_project="$future_dir/game";; esac
  case "$server" in release) server_project="$release_dir/game";; previous) server_project="$previous_dir/game";; legacy) server_project="$legacy_dir/game";; current) server_project="$repo_dir/game";; future) server_project="$future_dir/game";; esac
  port=$((port + 1))
  (run_godot "$out_dir/state/$name-server" "$server_project" -- --server --port=$port > "$out_dir/$name.server.log" 2>&1) &
  server_pid=$!
  for attempt in $(seq 1 100); do
    grep -q SIGHTBREAK_SERVER_READY "$out_dir/$name.server.log" && break
    sleep 0.1
  done
  if grep -q SIGHTBREAK_SERVER_READY "$out_dir/$name.server.log" && ! grep -q "Couldn't create an ENet host" "$out_dir/$name.server.log"; then
    (run_godot "$out_dir/state/$name-client" "$client_project" --script "$probe" -- --port=$port --seconds="${PROBE_SECONDS:-15}" --name="Compat $client" > "$out_dir/$name.client.log" 2>&1)
    sleep 1
  else
    echo "SERVER_FAILED" > "$out_dir/$name.client.log"
  fi
  kill "$server_pid" 2>/dev/null; wait "$server_pid" 2>/dev/null
done
python3 - "$out_dir" "$current_protocol" "$legacy_ref" <<'PY'
import json, pathlib, re, sys
out, protocol, legacy_ref = pathlib.Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
expect = {
    'release:release': 'join', 'current:current': 'join',
    'release:current': 'server drops pre-handshake client', 'current:release': 'client reports missing handshake',
    'future:current': 'explicit mismatch', 'current:future': 'explicit mismatch',
    'previous:current': 'explicit mismatch', 'current:previous': 'explicit mismatch',
    # Same protocol, different yard. A legacy client is refused by this server; this client refuses a legacy
    # server that admitted it on the protocol number alone (the server never has a rejection to log).
    'legacy:current': 'explicit mismatch', 'current:legacy': 'client refuses server layout',
}
rows, failures = [], []
for combo, wanted in expect.items():
    client, server = combo.split(':')
    name = f'client-{client}.server-{server}'
    client_log = (out / f'{name}.client.log').read_text(errors='replace')
    server_log = (out / f'{name}.server.log').read_text(errors='replace')
    match = re.search(r'^PROTOCOL_CLIENT (\{.*\})$', client_log, re.M)
    if not match:
        failures.append(f'{combo}: no client summary'); rows.append((combo, wanted, 'no summary', '', '')); continue
    summary = json.loads(match.group(1))
    failed_at = [float(m.group(1)) for m in re.finditer(r'^PROTOCOL_STATE ([0-9.]+) failed$', client_log, re.M)]
    drops = [float(m.group(1)) for m in re.finditer(r'^PROTOCOL_NOTICE ([0-9.]+) Server disconnected', client_log, re.M)]
    first_notice = re.search(r'^PROTOCOL_NOTICE ([0-9.]+) ', client_log, re.M)
    origin = float(first_notice.group(1)) if first_notice else 0.0
    admitted = server_log.count('joined Relay Yard')
    ok = True
    if wanted == 'join':
        ok = summary['joined'] and summary['final_state'] == 'connected' and admitted >= 1
        outcome = f"joined after {summary['joined_after']:.2f} s"
    elif wanted == 'server drops pre-handshake client':
        # The stock 0.3.0 client cannot show a new message; the server must drop it fast.
        timeouts = server_log.count('PROTOCOL_TIMEOUT')
        first_drop = drops[0] - origin if drops else None
        ok = not summary['joined'] and admitted == 0 and timeouts >= 1 and first_drop is not None and first_drop <= 6.5
        outcome = f"never admitted; dropped {timeouts}x by the server, first after {first_drop:.1f} s; 0.3.0 client retries on its own" if first_drop is not None else 'not dropped'
    elif wanted == 'client reports missing handshake':
        ok = summary['final_state'] == 'failed' and any('No version handshake' in n for n in summary['notices']) and failed_at and failed_at[0] <= 6.5 and admitted == 0
        outcome = f"failed after {failed_at[0]:.1f} s, no retries" if failed_at else 'did not fail'
    elif wanted == 'client refuses server layout':
        ok = summary['final_state'] == 'failed' and any('Version mismatch' in n and 'Relay Yard layout' in n for n in summary['notices']) and bool(failed_at) and failed_at[0] <= 2.0 and admitted == 0
        outcome = f"refused after {failed_at[0]:.1f} s with the layout reason shown" if failed_at else 'not refused'
    else:
        ok = summary['final_state'] == 'failed' and any('Version mismatch' in n for n in summary['notices']) and failed_at and failed_at[0] <= 2.0 and admitted == 0 and 'PROTOCOL_REJECTED' in server_log
        outcome = f"rejected after {failed_at[0]:.1f} s with the reason shown" if failed_at else 'not rejected'
    shown = next((n for n in summary['notices'] if 'handshake' in n or 'mismatch' in n.lower()), summary['notices'][-1] if summary['notices'] else '')
    rows.append((combo, wanted, outcome, 'PASS' if ok else 'FAIL', shown))
    if not ok:
        failures.append(f'{combo}: expected {wanted}, got {outcome}')
lines = ['| Client | Server | Expected | Observed | Result | Last message shown to the player |', '| --- | --- | --- | --- | --- | --- |']
label = {'legacy': f'stack before layout 2 (protocol {protocol}, {legacy_ref[:7]})', 'previous': 'published PR8 (protocol5,89c0e9)', 'release': '0.3.0 (e67f2c8)', 'current': f'this branch (protocol {protocol})', 'future': f'next build (protocol {protocol + 1})'}
for combo, wanted, outcome, result, shown in rows:
    client, server = combo.split(':')
    lines.append(f'| {label[client]} | {label[server]} | {wanted} | {outcome} | {result} | {shown} |')
(out / 'matrix.md').write_text('\n'.join(lines) + '\n')
print('\n'.join(lines))
print('PROTOCOL_COMPAT ' + ('PASS' if not failures else 'FAIL ' + '; '.join(failures)))
sys.exit(1 if failures else 0)
PY
