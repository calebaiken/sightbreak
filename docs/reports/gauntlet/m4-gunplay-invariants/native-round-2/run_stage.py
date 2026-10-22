from pathlib import Path
import datetime, hashlib, json, os, re, signal, subprocess, sys, time
root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
label, args = sys.argv[1], sys.argv[2:]
env = dict(os.environ)
env.update({'SIGHTBREAK_TOOLS_DIR': '/workspace/tools', 'SIGHTBREAK_STATE_DIR': str(out / 'private-state'), 'GODOT_BIN': '/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64'})
command = [str(root / 'scripts/godot.sh'), *args]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
clock = time.monotonic()
with (out / (label + '.log')).open('wb') as log:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    launch = {'label': label, 'started_utc': started, 'command': command, 'cwd': str(root), 'pid': process.pid, 'pgid': process.pid, 'explicit_environment': {k: env[k] for k in ('SIGHTBREAK_TOOLS_DIR', 'SIGHTBREAK_STATE_DIR', 'GODOT_BIN')}}
    (out / (label + '-launch.json')).write_text(json.dumps(launch, indent=2) + '\n')
    try:
        result = process.wait(timeout=300)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            result = process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            result = process.wait(timeout=10)
raw = (out / (label + '.log')).read_bytes()
text = raw.decode(errors='replace')
errors = re.findall(r'^(?:SCRIPT ERROR|ERROR:|.*Parse Error).*$', text, re.M)
receipt = dict(launch, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), wall_seconds=time.monotonic() - clock, exit_code=result, timed_out=timed_out, detected_errors=errors, log_sha256=hashlib.sha256(raw).hexdigest(), log_bytes=len(raw))
(out / (label + '-result.json')).write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('label', 'pid', 'exit_code', 'timed_out', 'wall_seconds', 'log_bytes', 'detected_errors')}), flush=True)
if label != 'import':
    print('\n'.join(text.splitlines()[-8:]), flush=True)
sys.exit(0 if result == 0 and not timed_out and not errors else 1)
