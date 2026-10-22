"""Evidence driver for one owned, bounded native PostgreSQL qualification.

This does not modify production code or the existing test suite. Credentials
remain in memory and the disposable runtime; they never enter evidence files.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from uuid import uuid4
import xml.etree.ElementTree as ET

import psycopg

ROOT = Path(__file__).resolve().parents[4]
REPORT = Path(__file__).resolve().parent
PYTHON = '/workspace/sightbreak/.venv/bin/python'
BASE = 'a3b7070f7739ae854e643f905230ae2b6f1a85cb'
IMAGE = 'postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3'
RUN = 'sightbreak-backend-regression-' + uuid4().hex[:12]
DB = 'sb_backend_' + RUN.rsplit('-', 1)[1] + '_test'
ROLE = 'sb_regression'
LABEL_KEY = 'io.sightbreak.qualification'
OWNER_KEY = 'io.sightbreak.owner'
OWNER = 'backend_regression_builder'
OUT = ROOT / 'builds' / RUN
OUT.mkdir(parents=True, exist_ok=False)
PASSWORD = secrets.token_urlsafe(36)
ENV = dict(os.environ)
for key in ('DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'):
    ENV.pop(key, None)
DOCKER = ['docker', '--host=unix:///var/run/docker.sock']
STATE = {'run': RUN, 'database': DB, 'role': ROLE, 'output': str(OUT),
         'started_utc': datetime.now(timezone.utc).isoformat(), 'steps': []}
CID = None
VOLUME = None
PORT = None
POSTMASTER = None


def clean(value):
    return str(value).replace(PASSWORD, '[REDACTED_EPHEMERAL_PASSWORD]')


def dump(name, value):
    (OUT / name).write_text(clean(json.dumps(value, indent=2, sort_keys=True, default=str)) + '\n')


def proc_identity(pid):
    try:
        # Linux stat comm may contain spaces. Everything after its final ')' has
        # fixed indices: state=0, ppid=1, pgrp=2, starttime=19.
        tail = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()
        return {'pid': pid, 'state': tail[0], 'ppid': int(tail[1]),
                'pgrp': int(tail[2]), 'start_ticks': int(tail[19])}
    except FileNotFoundError:
        return None


def group_members(group):
    found = []
    for path in Path('/proc').iterdir():
        if path.name.isdigit():
            item = proc_identity(int(path.name))
            if item and item['pgrp'] == group and item['state'] != 'Z':
                found.append(item)
    return found


def command(name, args, timeout=30, env=None, cwd=ROOT, check=True):
    started = time.monotonic()
    process = subprocess.Popen(args, cwd=cwd, env=env or ENV,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, start_new_session=True)
    identity = proc_identity(process.pid)
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(process.pid, signal.SIGTERM)
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate(timeout=5)
    record = {'name': name, 'argv': args, 'cwd': str(cwd), 'timeout_seconds': timeout,
              'duration_seconds': time.monotonic() - started, 'exit_code': process.returncode,
              'timed_out': timed_out, 'process': identity,
              'remaining_live_group_members': group_members(process.pid)}
    STATE['steps'].append(record)
    (OUT / (name + '.log')).write_text(clean(output))
    dump('state.json', STATE)
    if check:
        assert not timed_out and process.returncode == 0, f'{name} failed; inspect preserved log'
        assert not record['remaining_live_group_members'], f'{name} left live children'
    return output, record


def docker(name, args, **kwargs):
    return command(name, DOCKER + args, **kwargs)


def snapshot(name):
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=ROOT, env=ENV, text=True).strip()
    paths = git('ls-files', 'backend', 'game', 'scripts', 'server', '.github', '.claude').splitlines()
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    harness = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (REPORT / 'CRITERIA.md', Path(__file__).resolve())}
    value = {'head': git('rev-parse', 'HEAD'), 'head_tree': git('rev-parse', 'HEAD^{tree}'),
             'branch': git('branch', '--show-current'), 'status': git('status', '--porcelain'),
             'base_ancestor': subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], cwd=ROOT).returncode == 0,
             'trees': {p: git('rev-parse', 'HEAD:' + p) for p in ('backend', 'game', 'scripts', 'server', '.github', '.claude')},
             'base_trees': {p: git('rev-parse', BASE + ':' + p) for p in ('backend', 'game', 'scripts', 'server', '.github', '.claude')},
             'backend_sha256': {p: h for p, h in hashes.items() if p.startswith('backend/')},
             'production_file_count': len(hashes),
             'production_content_sha256': hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest(),
             'harness_sha256': harness}
    dump(name, value)
    assert value['status'] == '', 'Source must be clean'
    assert value['base_ancestor'] and value['trees'] == value['base_trees'], 'Production source must match exact base'
    return value


SQL = """SELECT current_database(), current_user, version(),
inet_server_addr()::text, inet_server_port(), pg_postmaster_start_time()::text,
(SELECT system_identifier::text FROM pg_control_system())"""


def identity(name):
    # Use TCP for the internal witness too: inet_server_port() is NULL on a
    # Unix-domain connection. Pass the ephemeral secret only through memory.
    container, _ = docker(name + '-container-sql', ['exec', '-e', 'PGPASSWORD', CID, 'psql', '-h', '127.0.0.1', '-X', '-At', '-F', '|', '-U', ROLE, '-d', DB, '-c', SQL],
                          env=dict(ENV, PGPASSWORD=PASSWORD))
    with psycopg.connect(host='127.0.0.1', port=PORT, user=ROLE, password=PASSWORD,
                         dbname=DB, connect_timeout=5, application_name=RUN) as connection:
        row = connection.execute(SQL).fetchone()
    keys = ['database', 'role', 'version', 'server_address', 'server_port', 'postmaster_started', 'system_identifier']
    value = dict(zip(keys, row))
    value.update(external_host='127.0.0.1', external_port=PORT,
                 verified_container_id=CID, checked_utc=datetime.now(timezone.utc).isoformat(),
                 identity_checks_passed=False)
    dump(name + '.json', value)
    internal = container.strip().split('|')
    assert value['database'] == DB and DB.endswith('_test') and value['role'] == ROLE
    assert internal[0:2] == [DB, ROLE] and internal[6] == value['system_identifier']
    assert value['server_port'] == 5432 and internal[4] == '5432'
    assert value['postmaster_started'] == internal[5]
    value['identity_checks_passed'] = True
    dump(name + '.json', value)
    return value


def selected_container(name):
    raw, _ = docker(name, ['inspect', '--format', '{{json .Id}}\n{{json .Name}}\n{{json .Image}}\n{{json .Config.Labels}}\n{{json .NetworkSettings.Ports}}\n{{json .State.Pid}}\n{{json .Mounts}}', CID])
    values = [json.loads(line) for line in raw.splitlines()]
    result = dict(zip(['id', 'name', 'image_id', 'labels', 'ports', 'pid', 'mounts'], values))
    assert result['id'] == CID and result['labels'][LABEL_KEY] == RUN and result['labels'][OWNER_KEY] == OWNER
    assert result['name'] == '/' + RUN
    dump(name + '.json', result)
    return result


def cleanup():
    result = {}
    if CID:
        owned = selected_container('container-before-cleanup')
        result['verified_container_id'] = owned['id']
        docker('remove-owned-container', ['rm', '-f', '-v', CID], timeout=30)
        _, absent = docker('container-absence', ['inspect', '--format', '{{.Id}}', CID], check=False)
        result['container_absent'] = absent['exit_code'] == 1
        listed, _ = docker('owned-label-container-absence', ['ps', '-aq', '--filter', f'label={LABEL_KEY}={RUN}'])
        result['label_containers_absent'] = not listed.strip()
    if VOLUME:
        raw, _ = docker('volume-before-cleanup', ['volume', 'inspect', '--format', '{{json .Name}}\n{{json .Labels}}', VOLUME])
        name, labels = [json.loads(line) for line in raw.splitlines()]
        assert name == VOLUME and labels[LABEL_KEY] == RUN and labels[OWNER_KEY] == OWNER
        docker('remove-owned-volume', ['volume', 'rm', VOLUME])
        _, absent = docker('volume-absence', ['volume', 'inspect', '--format', '{{.Name}}', VOLUME], check=False)
        result['volume_absent'] = absent['exit_code'] == 1
    if PORT:
        with socket.socket() as sock:
            sock.settimeout(2)
            result['port_connect_ex'] = sock.connect_ex(('127.0.0.1', PORT))
        listener, _ = command('port-after-cleanup', ['ss', '-ltnp', f'sport = :{PORT}'])
        result['listener_absent'] = len(listener.strip().splitlines()) == 1
        assert result['port_connect_ex'] != 0 and result['listener_absent']
    if POSTMASTER:
        current = proc_identity(POSTMASTER['pid'])
        result['postmaster_before'] = POSTMASTER
        result['postmaster_after'] = current
        result['postmaster_identity_gone'] = current is None or current['start_ticks'] != POSTMASTER['start_ticks']
        assert result['postmaster_identity_gone']
    assert all(result.get(k, True) for k in ('container_absent', 'label_containers_absent', 'volume_absent'))
    dump('cleanup.json', result)
    return result


try:
    before = snapshot('source-before.json')
    dump('runtime.json', {'python': sys.version, 'executable': sys.executable,
                          'dependencies': {name: importlib.metadata.version(name) for name in
                                           ('pytest', 'sqlalchemy', 'psycopg', 'fastapi', 'httpx', 'argon2-cffi')},
                          'child_environment_policy': {'DATABASE_URL': 'overridden: ephemeral owned loopback database',
                                                       'SIGHTBREAK_SERVER_ID': 'local-relay',
                                                       'SIGHTBREAK_SERVER_KEY': 'removed',
                                                       'PYTEST_ADDOPTS': 'removed',
                                                       'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'}})
    image_raw, _ = docker('image-before', ['image', 'inspect', '--format', '{{json .Id}}\n{{json .RepoDigests}}', IMAGE])
    image_id, digests = [json.loads(line) for line in image_raw.splitlines()]
    assert 'postgres@sha256:' + IMAGE.rsplit('sha256:', 1)[1] in digests
    VOLUME = RUN + '-data'
    docker('create-owned-volume', ['volume', 'create', '--label', f'{LABEL_KEY}={RUN}', '--label', f'{OWNER_KEY}={OWNER}', VOLUME])
    run_env = dict(ENV, POSTGRES_PASSWORD=PASSWORD)
    raw, _ = docker('start-owned-container', ['run', '-d', '--pull=never', '--name', RUN,
                         '--label', f'{LABEL_KEY}={RUN}', '--label', f'{OWNER_KEY}={OWNER}',
                         '-p', '127.0.0.1::5432', '-e', 'POSTGRES_PASSWORD',
                         '-e', 'POSTGRES_USER=' + ROLE, '-e', 'POSTGRES_DB=' + DB,
                         '-v', VOLUME + ':/var/lib/postgresql/data', IMAGE], env=run_env)
    CID = raw.strip()
    owned = selected_container('container-before')
    assert owned['image_id'] == image_id
    ports = owned['ports']['5432/tcp']
    assert len(ports) == 1 and ports[0]['HostIp'] == '127.0.0.1'
    PORT = int(ports[0]['HostPort'])
    assert PORT != 55432
    POSTMASTER = proc_identity(owned['pid'])
    assert POSTMASTER
    for attempt in range(30):
        _, ready = docker(f'readiness-{attempt:02d}', ['exec', CID, 'pg_isready', '-h', '127.0.0.1', '-U', ROLE, '-d', DB], check=False)
        if ready['exit_code'] == 0:
            break
        time.sleep(1)
    else:
        raise RuntimeError('Owned PostgreSQL did not become ready within 30 attempts')
    identity('identity-before-migration')
    child_env = dict(ENV, DATABASE_URL=f'postgresql+psycopg://{ROLE}:{PASSWORD}@127.0.0.1:{PORT}/{DB}',
                     SIGHTBREAK_SERVER_ID='local-relay', PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    child_env.pop('SIGHTBREAK_SERVER_KEY', None)
    child_env.pop('PYTEST_ADDOPTS', None)
    command('migration', [PYTHON, '-B', 'migrate.py'], timeout=60, env=child_env, cwd=ROOT / 'backend')
    docker('schema-after-migration', ['exec', CID, 'pg_dump', '--schema-only', '--no-owner', '--no-privileges', '-U', ROLE, '-d', DB])
    collected, _ = command('collection', [PYTHON, '-B', '-m', 'pytest', '--collect-only', '-q', '-p', 'no:cacheprovider', 'tests/test_economy.py'],
                           timeout=60, env=child_env, cwd=ROOT / 'backend')
    nodes = [line for line in collected.splitlines() if line.startswith('tests/test_economy.py::')]
    tree = ast.parse((ROOT / 'backend/tests/test_economy.py').read_text())
    functions = sorted(node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'))
    assert len(functions) == 44 and len(nodes) == 61 and len(set(nodes)) == 61
    assert sorted({node.split('::')[1].split('[')[0] for node in nodes}) == functions
    dump('test-inventory.json', {'function_count': len(functions), 'case_count': len(nodes), 'functions': functions, 'nodes': nodes})
    identity('identity-before-tests')
    command('pytest', [PYTHON, '-B', '-m', 'pytest', '-vv', '-rA', '-p', 'no:cacheprovider',
                       '--junitxml=' + str(OUT / 'pytest-junit.xml'), 'tests/test_economy.py'],
             timeout=300, env=child_env, cwd=ROOT / 'backend')
    junit = ET.parse(OUT / 'pytest-junit.xml').getroot()
    cases = junit.findall('.//testcase')
    assert len(cases) == 61
    assert not list(junit.iter('failure')) and not list(junit.iter('error')) and not list(junit.iter('skipped'))
    identity('identity-after-tests')
    docker('container-processes-after-tests', ['top', CID, '-eo', 'pid,ppid,user,args'])
    STATE['benchmark_result'] = 'PASS: all 44 functions / 61 cases'
except BaseException:
    STATE['failure'] = clean(traceback.format_exc())
finally:
    try:
        cleanup()
        STATE['cleanup_result'] = 'PASS'
    except BaseException:
        STATE['cleanup_failure'] = clean(traceback.format_exc())
    try:
        after = snapshot('source-after.json')
        assert before == after, 'Source changed during qualification'
        STATE['source_result'] = 'PASS: before equals after'
    except BaseException:
        STATE['source_failure'] = clean(traceback.format_exc())
    STATE['finished_utc'] = datetime.now(timezone.utc).isoformat()
    STATE['accepted_by_builder'] = False
    STATE['independent_review'] = 'PENDING'
    dump('state.json', STATE)
    print(clean(json.dumps({'output': str(OUT), 'benchmark': STATE.get('benchmark_result'),
                           'cleanup': STATE.get('cleanup_result'), 'source': STATE.get('source_result'),
                           'failures': [key for key in STATE if 'failure' in key]}, indent=2)))

sys.exit(0 if STATE.get('benchmark_result') and STATE.get('cleanup_result') and STATE.get('source_result')
         and not any('failure' in key for key in STATE) else 1)
