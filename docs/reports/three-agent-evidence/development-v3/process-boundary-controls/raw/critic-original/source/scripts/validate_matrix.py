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
import shlex
import subprocess
import sys
import time
from native_log import failed as native_log_failed
from build_manifest import source
from godot_process import (godot_command, godot_environment, is_windows,
                           prepare_output, process_group_options,
                           source_snapshot, source_failures, terminate_process_tree)

ROOT = Path(__file__).resolve().parents[1]


def run_check(label, command, directory, env, commit, timeout=600):
    """Keep the real exit code and raw log; text saying PASS is insufficient."""
    start = time.monotonic()
    path = directory / (label + '.log')
    code = 1
    process = None
    with path.open('x', encoding='utf-8') as log:
        try:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log,
                                       stderr=subprocess.STDOUT, **process_group_options())
            try:
                code = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                terminate_process_tree(process)
                raise
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            log.write('\nHARNESS_ERROR ' + str(error) + '\n')
        finally:
            if process is not None and process.poll() is None:
                terminate_process_tree(process)
    text = path.read_text(encoding='utf-8', errors='replace')
    errors = native_log_failed(text) or 'HARNESS_ERROR' in text
    return {'name': label, 'source_commit': commit, 'command': command, 'exit': code,
            'logged_errors': errors, 'passed': code == 0 and not errors,
            'seconds': round(time.monotonic() - start, 3), 'log': path.name}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--backend', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--protocol', action='store_true')
    args = parser.parse_args(); args.out = prepare_output(args.out)
    env = os.environ.copy(); env['SIGHTBREAK_STATE_DIR'] = str(args.out / 'state')
    # Preserve installed templates/settings; tests need no export toolchain.
    for key in ('SIGHTBREAK_RESULT_SPOOL', 'SIGHTBREAK_SERVER_KEY'): env.pop(key, None)
    records = []
    frozen_source = source()
    frozen_validation = source_snapshot()
    report = {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'dirty': bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip()),
              'source': frozen_source, 'validation_source': frozen_validation,
              'platform': platform.platform(), 'python': platform.python_version(), 'checks': records}
    def save():
        (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    def unavailable(label, error):
        path = args.out / (label + '.log')
        path.write_text('UNAVAILABLE: ' + str(error) + '\n')
        records.append({'name': label, 'source_commit': report['commit'], 'passed': False,
                        'unavailable': True, 'reason': str(error), 'log': path.name})
        save()
        print(label + ': UNAVAILABLE (' + str(error) + ')', flush=True)
    if report['dirty'] or frozen_validation['dirty']:
        unavailable('frozen-source-precondition', 'Commit all source and validation tooling before running a matrix.')
        return 1
    def run(label, command, extra=None, timeout=600):
        child_env = godot_environment(env={**env, **(extra or {})})
        records.append(run_check(label, command, args.out, child_env, report['commit'], timeout))
        save()
        print(f'{label}: {"PASS" if records[-1]["passed"] else "FAIL"} ({records[-1]["seconds"]}s)', flush=True)
    def native(label, arguments, extra=None):
        try:
            command = godot_command(arguments, env=env)
        except OSError as error:
            unavailable(label, error)
            return
        run(label, command, extra)
    def posix(label, command, timeout=600):
        if is_windows():
            unavailable(label, 'This maintained Bash/X11 group requires the Linux CI host; not substituted or waived.')
        else:
            run(label, command, timeout=timeout)
    # Keep the maintained suite inventory in validate.sh as the single source.
    for line in (ROOT / 'scripts/validate.sh').read_text().splitlines():
        match = re.search(r'^(\s*)run_godot (\S+) (.+)$', line)
        if match and (not match[1] or args.render):
            native(match[2], shlex.split(match[3]))
        elif line.startswith('SIGHTBREAK_STATE_DIR=') and 'run_godot profile ' in line:
            native('profile', ['--headless', '--script', 'res://tests/profile_test.gd'], {'SIGHTBREAK_STATE_DIR': str(args.out / 'profile-state')})
    run('account-output-unit', [sys.executable, 'scripts/test_account_network_output.py'])
    run('worker-unit', [sys.executable, '-m', 'unittest', 'discover', '-s', 'server/tests', '-v'])
    posix('network', ['bash', 'scripts/test_network.sh'])
    run('network-soak', [sys.executable, 'scripts/test_network_soak.py', '--out', str(args.out / 'soak')])
    run('network-soak-ten', [sys.executable, 'scripts/test_network_soak.py', '--clients', '10', '--port', '29840', '--out', str(args.out / 'soak-ten')])
    run('connection-lifecycle', [sys.executable, 'scripts/test_connection_lifecycle.py', '--out', str(args.out / 'connections')])
    posix('bridge-transport', [sys.executable, 'scripts/test_bridge_transport.py'])
    run('build-manifest', [sys.executable, 'scripts/test_build_manifest.py'])
    run('matrix-harness-unit', [sys.executable, 'scripts/test_validate_matrix.py'])
    run('network-harness-unit', [sys.executable, 'scripts/test_godot_process.py'])
    run('offline-hud-unit', [sys.executable, 'scripts/test_offline_hud.py'])
    run('export-ui-unit', [sys.executable, 'scripts/test_export_ui.py'])
    run('reload-contact', [sys.executable, 'scripts/test_reload_contact.py'])
    if args.protocol:
        posix('protocol-matrix', ['bash', 'scripts/test_protocol_compat.sh', str(args.out / 'protocol')])
        posix('hostile-handshake', ['bash', 'scripts/test_handshake_hardening.sh', str(args.out / 'handshake')])
    if args.backend:
        run('catalog-fixture', [sys.executable, 'scripts/export_catalog_fixture.py', '--check'])
        created = False
        database = 'sightbreak_matrix_' + secrets.token_hex(6) + '_test'
        try:
            import psycopg
            from psycopg import sql
            connection = dict(host='127.0.0.1', port=55432, user='sightbreak', password='sightbreak_local_only', dbname='postgres', autocommit=True, connect_timeout=5)
            with psycopg.connect(**connection) as db: db.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(database)))
            created = True
            run('postgresql', [sys.executable, '-m', 'pytest', 'backend/tests', '-q'], {'PYTHONPATH': 'backend', 'DATABASE_URL': 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/' + database})
        except Exception as error:
            unavailable('postgresql-setup', error)
        finally:
            if created:
                try:
                    with psycopg.connect(**connection) as db: db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(database)))
                except Exception as error: unavailable('postgresql-cleanup', error)
        for label, script in [('account-protocol', 'test_account_isolated.py'), ('account-capacity', 'test_admission_capacity.py'), ('outbox-crash', 'test_result_outbox.py'), ('native-economy', 'test_native_economy.py')]:
            posix(label, [sys.executable, 'scripts/' + script])
        posix('account-full-reconnect', [sys.executable, 'scripts/test_full_account_reconnect.py', '--out', str(args.out / 'account-full-reconnect')], timeout=180)
        run('economy-conservation', [sys.executable, 'backend/simulate.py'])
    if args.render:
        posix('native-render-lifecycle', ['bash', 'scripts/test_render.sh'])
        native('native-hud-overflow', ['--audio-driver', 'Dummy', '--script', 'res://tests/hud_overflow_test.gd'])
        native('native-paint-visibility', ['--audio-driver', 'Dummy', '--script', 'res://tests/paint_visibility_test.gd'])
    # Child clients can satisfy protocol assertions while leaking at shutdown.
    # Audit retained child logs as well as each top-level command's output.
    leaked = []
    for path in sorted(args.out.rglob('*.log')):
        if re.search(r'ObjectDB.*leaked|Leaked instance', path.read_text(errors='replace')):
            leaked.append(str(path.relative_to(args.out)))
    audit_path = args.out / 'nested-resource-cleanup.json'
    audit_path.write_text(json.dumps({'source_commit': report['commit'], 'leaked_logs': leaked}, indent=2) + '\n')
    records.append({'name': 'nested-resource-cleanup', 'source_commit': report['commit'], 'passed': not leaked, 'log': audit_path.name})
    final_source = source()
    final_validation = source_snapshot()
    final_dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True).strip())
    identity_path = args.out / 'source-identity.json'
    identity_errors = source_failures(frozen_validation, final_validation)
    identity_path.write_text(json.dumps({'before': frozen_source, 'after': final_source, 'validation_before': frozen_validation, 'validation_after': final_validation, 'initial_dirty': report['dirty'], 'final_dirty': final_dirty, 'failures': identity_errors}, indent=2) + '\n')
    records.append({'name': 'frozen-source-identity', 'source_commit': report['commit'], 'passed': not report['dirty'] and not final_dirty and frozen_source == final_source and not identity_errors, 'log': identity_path.name})
    (args.out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
    failed = [row['name'] for row in records if not row['passed']]
    print(json.dumps({'groups': len(records), 'failed': failed, 'report': str(args.out / 'summary.json')}, indent=2))
    return bool(failed)

if __name__ == '__main__': raise SystemExit(main())
