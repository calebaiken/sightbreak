#!/usr/bin/env python3
"""Run every regression group, preserving failures while continuing independent checks.

Use .venv/bin/python for --backend. PostgreSQL test databases are isolated and
removed on completion. Native --render requires a real display (Xvfb is allowed,
explicitly not physical-device/GPU evidence). No failing check is suppressed.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import secrets
import signal
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--backend', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--protocol', action='store_true')
    args = parser.parse_args(); args.out = args.out.resolve(); args.out.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy(); env['SIGHTBREAK_STATE_DIR'] = str(args.out / 'state')
    # Preserve installed templates/settings; tests need no export toolchain.
    for key in ('SIGHTBREAK_RESULT_SPOOL', 'SIGHTBREAK_SERVER_KEY'): env.pop(key, None)
    records = []
    report = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()),
              'platform': platform.platform(), 'python': platform.python_version(), 'checks': records}
    def run(label, command, extra=None, timeout=600):
        start = time.monotonic(); path = args.out / (label + '.log'); code = 1
        try:
            with path.open('w') as log:
                process = subprocess.Popen(command, cwd=ROOT, env={**env, **(extra or {})}, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try: code = process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    raise
        except (OSError, subprocess.TimeoutExpired) as error:
            with path.open('a') as log: log.write('\nHARNESS_ERROR ' + str(error) + '\n')
        text = path.read_text()
        errors = bool(re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|HARNESS_ERROR', text, re.M))
        records.append({'name': label, 'command': command, 'exit': code, 'logged_errors': errors, 'passed': code == 0 and not errors, 'seconds': round(time.monotonic() - start, 3), 'log': path.name})
        (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(f'{label}: {"PASS" if records[-1]["passed"] else "FAIL"} ({records[-1]["seconds"]}s)', flush=True)
    # Keep the maintained suite inventory in validate.sh as the single source.
    for line in (ROOT / 'scripts/validate.sh').read_text().splitlines():
        match = re.search(r'^run_godot (\S+) (.+)$', line)
        if match:
            run(match[1], [str(ROOT / 'scripts/godot.sh'), *shlex.split(match[2])])
        elif line.startswith('SIGHTBREAK_STATE_DIR=') and 'run_godot profile ' in line:
            run('profile', [str(ROOT / 'scripts/godot.sh'), '--headless', '--script', 'res://tests/profile_test.gd'], {'SIGHTBREAK_STATE_DIR': str(args.out / 'profile-state')})
    run('worker-unit', ['python3', '-m', 'unittest', 'discover', '-s', 'server/tests', '-v'])
    run('network', ['bash', 'scripts/test_network.sh'])
    run('network-soak', ['python3', 'scripts/test_network_soak.py', '--out', str(args.out / 'soak')])
    run('network-soak-ten', ['python3', 'scripts/test_network_soak.py', '--clients', '10', '--port', '29840', '--out', str(args.out / 'soak-ten')])
    run('connection-lifecycle', ['python3', 'scripts/test_connection_lifecycle.py', '--out', str(args.out / 'connections')])
    run('bridge-transport', ['python3', 'scripts/test_bridge_transport.py'])
    run('build-manifest', ['python3', 'scripts/test_build_manifest.py'])
    if args.protocol:
        run('protocol-matrix', ['bash', 'scripts/test_protocol_compat.sh', str(args.out / 'protocol')])
        run('hostile-handshake', ['bash', 'scripts/test_handshake_hardening.sh', str(args.out / 'handshake')])
    if args.backend:
        def unavailable(label, error):
            path = args.out / (label + '.log')
            path.write_text('UNAVAILABLE: ' + str(error) + '\n')
            records.append({'name': label, 'passed': False, 'unavailable': True, 'log': path.name})
            (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
            print(label + ': UNAVAILABLE (' + str(error) + ')', flush=True)
        created = False
        database = 'sightbreak_matrix_' + secrets.token_hex(6) + '_test'
        try:
            import psycopg
            from psycopg import sql
            connection = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True, connect_timeout=5)
            with psycopg.connect(**connection) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
            created = True
            run('postgresql', [str(ROOT / '.venv/bin/python'), '-m', 'pytest', 'backend/tests', '-q'], {'PYTHONPATH': 'backend', 'DATABASE_URL': 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database})
        except Exception as error:
            unavailable('postgresql-setup', error)
        finally:
            if created:
                try:
                    with psycopg.connect(**connection) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
                except Exception as error: unavailable('postgresql-cleanup', error)
        for label, script in [('account-protocol', 'test_account_isolated.py'), ('account-capacity', 'test_admission_capacity.py'), ('outbox-crash', 'test_result_outbox.py'), ('native-economy', 'test_native_economy.py')]:
            run(label, [str(ROOT / '.venv/bin/python'), 'scripts/' + script])
        run('account-full-reconnect', [str(ROOT / '.venv/bin/python'), 'scripts/test_full_account_reconnect.py', '--out', str(args.out / 'account-full-reconnect')], timeout=180)
        run('economy-conservation', ['python3', 'backend/simulate.py'])
    if args.render:
        run('native-render-lifecycle', ['bash', 'scripts/test_render.sh'])
        run('native-hud-overflow', [str(ROOT / 'scripts/godot.sh'), '--audio-driver', 'Dummy', '--script', 'res://tests/hud_overflow_test.gd'])
        run('native-paint-visibility', [str(ROOT / 'scripts/godot.sh'), '--audio-driver', 'Dummy', '--script', 'res://tests/paint_visibility_test.gd'])
    failed = [row['name'] for row in records if not row['passed']]
    print(json.dumps({'groups': len(records), 'failed': failed, 'report': str(args.out / 'summary.json')}, indent=2))
    return bool(failed)

if __name__ == '__main__': raise SystemExit(main())
