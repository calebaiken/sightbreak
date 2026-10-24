"""Run the maintained aggregate once; retain source, exits and scoped cleanup."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

repo = Path(sys.argv[1]).resolve()
expected = sys.argv[2]
out = Path(sys.argv[3]).resolve()
out.mkdir(parents=True, exist_ok=False)
shutil.copyfile(__file__, out / 'runner.py')
sys.path.insert(0, str(repo / 'scripts'))
import build_manifest
import toolchain


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(name, value):
    (out / name).write_text(json.dumps(value, indent=2) + '\n')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def processes(session=None):
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():
            continue
        try:
            data = (path / 'stat').read_text()
            values = data[data.rindex(')') + 2:].split()
            argv = (path / 'cmdline').read_bytes()
            comm = (path / 'comm').read_text().strip()
            own_engine = comm.lower().startswith('godot') and os.fsencode(str(repo)) in argv
            if not own_engine and (session is None or int(values[3]) != session):
                continue
            found.append(dict(pid=int(path.name), ppid=int(values[1]), pgid=int(values[2]),
                              sid=int(values[3]), start_ticks=int(values[19]), state=values[0],
                              comm=comm, argv_sha256=hashlib.sha256(argv).hexdigest()))
        except (OSError, ValueError, IndexError):
            continue
    return found


def listeners():
    found = []
    for kind in ('udp', 'udp6', 'tcp', 'tcp6'):
        for line in (Path('/proc/net') / kind).read_text().splitlines()[1:]:
            fields = line.split()
            port = int(fields[1].rsplit(':', 1)[1], 16)
            if port in (27991, 29900, 29901, 29902) and (kind.startswith('udp') or fields[3] == '0A'):
                found.append(dict(kind=kind, port=port, state=fields[3], inode=fields[9]))
    return found


before = build_manifest.source()
write('source-before.json', before)
if before['source_commit'] != expected or before['source_dirty'] or before['source_game_dirty']:
    raise RuntimeError('Expected committed clean frozen source')
scopes = ['game', 'scripts', '.github', 'backend', 'server',
          'docs/reports/media/art-v9/hands/logs', 'docs/reports/gauntlet/native-layout-ocr']
tracked = subprocess.check_output(['git', 'ls-files', '-z', *scopes], cwd=repo).split(b'\0')
# Missing sparse files must fail rather than disappear from the inventory.
write('tracked-inputs.json', {os.fsdecode(p): digest(repo / os.fsdecode(p)) for p in tracked if p})
write('engine.json', dict(path=toolchain.binary(), sha256=digest(Path(toolchain.binary()))))
initial_processes, initial_listeners = processes(), listeners()
write('preflight-resources.json', dict(processes=initial_processes, listeners=initial_listeners))
if initial_processes or initial_listeners:
    raise RuntimeError('Frozen checkout engine or required test port already in use')
env = dict(os.environ)
env.pop('DISPLAY', None)
env.update(SIGHTBREAK_TOOLS_DIR='/workspace/tools', SIGHTBREAK_STATE_DIR=str(repo / '.local/aggregate-state'),
           SIGHTBREAK_BACKEND_PYTHON='/workspace/sightbreak/.venv/bin/python',
           DATABASE_URL='postgresql+psycopg://fixture:fixture@127.0.0.1:1/fixture')
selectors = ('DISPLAY', 'SIGHTBREAK_TOOLS_DIR', 'SIGHTBREAK_STATE_DIR', 'SIGHTBREAK_BACKEND_PYTHON',
             'GODOT_BIN', 'SIGHTBREAK_TEST_TIMEOUT', 'LP_NUM_THREADS', 'LIBGL_ALWAYS_SOFTWARE')
command = ['./scripts/validate.sh']
record = dict(command=command, cwd=str(repo), started_utc=now(), timeout_seconds=1200,
              environment={k: env.get(k) for k in selectors}, runner_sha256=digest(Path(__file__)))
write('command.json', record)
process = None
seen = {}
failure = None
started = time.monotonic()
try:
    with (out / 'aggregate.log').open('w') as log:
        process = subprocess.Popen(command, cwd=repo, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        record.update(pid=process.pid, pgid=os.getpgid(process.pid))
        write('command.json', record)
        while process.poll() is None:
            for row in processes(process.pid):
                seen[(row['pid'], row['start_ticks'])] = row
            if time.monotonic() - started >= 1200:
                raise subprocess.TimeoutExpired(command, 1200)
            time.sleep(.25)
        record['exit_code'] = process.wait()
        if record['exit_code']:
            raise RuntimeError('Maintained aggregate exited nonzero')
except BaseException as error:
    failure = dict(type=type(error).__name__, message=str(error))
    if process is not None and process.poll() is None:
        # Only signal the still-owned original session; escaped descendants are
        # outside this supervisor's qualified cleanup and fail a terminal scan.
        os.killpg(process.pid, signal.SIGKILL)
        record['forced_group_cleanup'] = True
        record['terminated_wait_status'] = process.wait(timeout=15)
finally:
    after = build_manifest.source()
    remaining = processes(process.pid if process is not None else None)
    ports = listeners()
    write('source-after.json', after)
    write('observed-processes.json', list(seen.values()))
    write('cleanup.json', dict(observed_utc=now(), remaining=remaining, listeners=ports,
          scope='original session and Godot argv bound to frozen checkout; not arbitrary escaped descendants'))
    record.update(completed_utc=now(), seconds=time.monotonic() - started,
                  source_unchanged=before == after, failure=failure)
    write('result.json', dict(record, passed=failure is None and before == after and not remaining and not ports))
    print(json.dumps(dict(exit_code=record.get('exit_code'), failure=failure,
                          seconds=record['seconds'], source_unchanged=before == after,
                          remaining=len(remaining), listeners=len(ports))), flush=True)
if failure or before != after or remaining or ports:
    raise SystemExit(1)
