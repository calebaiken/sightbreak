#!/usr/bin/env python3
"""Independent frozen-source audit and fake-process falsifiers. No native launch."""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
FROZEN = '12901729f7be29d0f64d87a0d92219a84500f1a6'
PLAN = 'docs/reports/gauntlet/m1-linux-opaque-cost-plan/'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def blob(path):
    return git('show', FROZEN + ':' + path)

ledger = json.loads(blob(PLAN + 'implementation-source.json'))
verified = []
for item in ledger['files']:
    data = (ROOT / item['path']).read_bytes()
    assert data == blob(item['path'])
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    verified.append(item)
assert git('rev-parse', FROZEN + ':game').decode().strip() == ledger['game_tree']
assert not git('diff', ledger['base'], FROZEN, '--', 'game', 'scripts/verify_offline_match.py')
changed = git('diff', '--name-only', ledger['base'], FROZEN).decode().splitlines()
assert all(p.startswith(PLAN) or p in {
    'scripts/linux_profile_overhead.py', 'scripts/test_linux_profile_overhead.py',
    'scripts/diagnostics/linux_profile_overhead.gd',
    'scripts/diagnostics/linux_profile_overhead.tscn'} for p in changed)

sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_overhead as d
import test_linux_profile_overhead as supplied

baseline = [supplied.manual_record(i) for i in range(4)]
assert d.evaluate(baseline, supplied.manual_expected())['comparable']

def dead_display():
    """A racing socket can establish readiness even after the owned server exited."""
    class DeadProcess:
        pid = 43210
        args = ['/fake-xvfb', ':99119']
        returncode = 1
        def poll(self):
            return self.returncode
    process = DeadProcess()
    checks = 0
    actual_exists = Path.exists
    def exists(path):
        nonlocal checks
        if str(path) == '/tmp/.X11-unix/X99119':
            checks += 1
            return checks > 1
        return actual_exists(path)
    with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
        runner = d.NativeRunner('/fake-xvfb', ':99119', temporary)
        stack.enter_context(patch.object(d.subprocess, 'Popen', return_value=process))
        stack.enter_context(patch.object(d, 'pid_start', return_value=12345))
        stack.enter_context(patch.object(Path, 'exists', exists))
        try:
            runner.start()
            accepted = True
        except d.Invalid:
            accepted = False
        finally:
            if runner.log:
                runner.log.close()
    assert accepted and process.poll() == 1
    return {'accepted_readiness': accepted, 'owned_xvfb_exit_code': process.poll(),
            'socket_path_checks': checks, 'native_processes_started': 0}

def late_condition():
    """Real condition + block code accepts each virtual client past its hard bound.

    The fake client becomes ready after 178 s startup, publishes correct metrics
    1.947 s after begin.ack, and waits 1.1 s for end observation/finish.ack. Both
    fixture holds stay below 15 s. The controller's driver read crosses 180 s;
    the completed client then satisfies wait(timeout=.001). No real delay or
    process is used, and all four conditions use this same causal schedule.
    """
    clock = {'now': 0.0}
    registry = {}
    current = {}
    completed = []
    host = supplied.manual_record(0)['host_begin']
    original_ack = d.acknowledge
    class Process:
        def __init__(self, args, env, output):
            self.args, self.env, self.output = args, env, output
            self.pid = 44000 + len(registry)
            self.returncode = None
            self.started = clock['now']
            self.token = next(a[8:] for a in args if a.startswith('--token='))
            self.report = supplied.manual_report(self.token)
            clock_offset = round(self.started * 1_000_000) + 178_000_000
            def offset_clocks(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key == 'clock_usec':
                            value[key] += clock_offset
                        else:
                            offset_clocks(item)
                elif isinstance(value, list):
                    for item in value:
                        offset_clocks(item)
            offset_clocks(self.report)
            self.report['construction_settled'] = {
                'clock_usec': clock_offset, 'counter': 10, 'callback': 1}
            proof = b'synthetic proof, no renderer'
            (output / 'proof.png').write_bytes(proof)
            self.report['png_sha256'] = hashlib.sha256(proof).hexdigest()
            registry[self.pid] = self
            current['process'] = self
            clock['now'] += 178.0
            ready = {key: value for key, value in self.report.items() if key not in {
                'cold_before', 'anchor', 'warm', 'measured', 'readback', 'readback_after', 'png_sha256'}}
            d.write(output / 'ready.json', ready)
        def poll(self):
            return self.returncode
        def wait(self, timeout):
            assert self.returncode == 0
            completed.append({'elapsed_virtual_seconds': clock['now'] - self.started,
                              'wait_timeout_seconds': timeout})
            return self.returncode
    def launch(args, **kwargs):
        process = Process(args, kwargs['env'], Path(kwargs['cwd']))
        kwargs['stdout'].write(b'GPU PROFILE (total 20ms): \n\t-Render Opaque Pass: 18ms\n'
                               if '--gpu-profile' in args else b'Synthetic OFF\n')
        return process
    def ack(path, token):
        original_ack(path, token)
        process = current['process']
        if path.name == 'begin.ack':
            clock['now'] += 1.947
            d.write(process.output / 'metrics.json', process.report)
        else:
            process.returncode = 0
    def snapshot(pid):
        process = registry[pid]
        if (process.output / 'metrics.json').exists():
            clock['now'] += 1.1
        return deepcopy(host)
    def owned(pid, selected):
        process = registry[pid]
        return process.args[3:], {key: process.env[key] for key in selected}
    class Runner(d.NativeRunner):
        def start(self):
            pass
        def stop(self):
            return {'pid_absent': True, 'group_absent': True, 'forced': True}
    with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
        root = Path(temporary)
        payload = root / 'payload'
        payload.write_bytes(b'synthetic payload, never executable or launched')
        expected = supplied.manual_expected(d.digest(payload), str(payload))
        stack.enter_context(patch.object(d.subprocess, 'Popen', side_effect=launch))
        stack.enter_context(patch.object(d, 'pid_start', side_effect=lambda pid: pid * 2))
        stack.enter_context(patch.object(d, 'owned_launch_state', side_effect=owned))
        stack.enter_context(patch.object(d, 'host_snapshot', side_effect=snapshot))
        stack.enter_context(patch.object(d, 'cgroup_snapshot', return_value=deepcopy(host)))
        stack.enter_context(patch.object(d, 'absent', side_effect=lambda pid, group=False: registry[pid].returncode is not None))
        stack.enter_context(patch.object(d, 'acknowledge', side_effect=ack))
        stack.enter_context(patch.object(d.time, 'monotonic', side_effect=lambda: clock['now']))
        runner = Runner('/fake-xvfb', ':99108', root / 'block')
        summary = d.run_block(expected, root / 'block', [2, 3], runner)
    assert summary['passed'], summary.get('error')
    assert len(completed) == 4 and all(row['elapsed_virtual_seconds'] > d.BOUND for row in completed)
    return {'block_passed': summary['passed'], 'conditions': completed,
            'declared_hard_bound_seconds': d.BOUND, 'native_processes_started': 0}

def invalid_cold_clock():
    rows = deepcopy(baseline)
    rows[0]['fixture']['cold_before']['clock_usec'] = float('-inf')
    result = d.evaluate(rows, supplied.manual_expected())
    assert result['comparable'] and result['conditions'][0]['cold_anchor_ms'] == float('inf')
    return {'evaluator_comparable': True, 'nonfinite_cold_anchor': 'inf',
            'full_run_block_acceptance_claimed': False,
            'scope': 'Evaluator only; later strict JSON publication rejects infinity.'}

def upstream_identities():
    references = json.loads(blob(PLAN + 'source-references.json'))
    retained = Path('/workspace/sightbreak-linux-opaque-cost/.local/godot-opaque-source')
    identities = []
    for row in references['upstream_sources']:
        data = (retained / row['source']).read_bytes()
        assert len(data) == row['bytes']
        assert hashlib.sha256(data).hexdigest() == row['sha256']
        identities.append({'path': row['source'], 'bytes': len(data), 'sha256': row['sha256']})
    return identities

pure = subprocess.run([sys.executable, 'scripts/test_linux_profile_overhead.py', '-v'], cwd=ROOT,
                      capture_output=True, text=True)
(OUT / 'pure-controls.txt').write_text(pure.stdout + pure.stderr)
assert pure.returncode == 0
result = {'frozen_commit': FROZEN, 'verified_implementation_files': verified,
          'shipping_game_tree': ledger['game_tree'], 'shipping_game_and_original_controller_unchanged': True,
          'upstream_identities': upstream_identities(), 'supplied_pure_exit_code': pure.returncode,
          'dead_xvfb_socket_readiness': dead_display(), 'hard_deadline_bypass': late_condition(),
          'nonfinite_cold_clock': invalid_cold_clock(),
          'engine_import_compile_export_uid_native_ocr_service_runs': 0}
(OUT / 'recomputed.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
print(json.dumps(result, indent=2, allow_nan=False))
