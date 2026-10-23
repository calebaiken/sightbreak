#!/usr/bin/env python3
"""Independent read-only identities plus owned-worktree mutation controls; no engine."""
from contextlib import ExitStack, contextmanager, redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPORT = HERE.parent
ROOT = HERE.parents[5]
BASE = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
CANDIDATE = '216d39ada8f9d11e2d8544d01fde42da49607b14'
PREREG = 'a1c45578'
BUILDER = Path('/workspace/sightbreak-linux-profile-fixture-native-types')
ORIGINAL = Path('/workspace/sightbreak-linux-profile-acquisition')
OLD_REVIEW = Path('/workspace/reviews/linux-profile-acquisition-native/docs/reports/gauntlet/m1-linux-profile-acquisition/native-independent')
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acq
import linux_profile_overhead as diagnostic

checks = []


def check(name, condition, detail=None):
    checks.append({'name': name, 'passed': bool(condition), 'detail': detail})
    if not condition:
        raise AssertionError(name)


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd)


def identity(path):
    raw = Path(path).read_bytes()
    return {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def raw_snapshot():
    registry = json.loads((OLD_REVIEW / 'raw-registry.json').read_text())
    raw = ORIGINAL / 'builds/linux-profile-acquisition-r1'
    paths = list(raw.rglob('*'))
    check('old raw no symlinks', not any(p.is_symlink() for p in paths))
    actual = {p.relative_to(raw).as_posix(): identity(p) for p in paths if p.is_file()}
    check('all 224 old raw identities unchanged', actual == registry['files'], len(actual))
    check('old raw bytes unchanged', sum(v['bytes'] for v in actual.values()) == 178615722)
    outer = {p.name: identity(p) for p in (ORIGINAL / '.local').glob('linux-profile-acquisition-r1-*')}
    expected_outer = {'linux-profile-acquisition-r1-' + k: v for k, v in registry['outer'].items()}
    check('three old external wrapper records unchanged', outer == expected_outer, len(outer))
    check('old HEAD unchanged', git('rev-parse', 'HEAD', cwd=ORIGINAL).decode().strip() == BASE)
    check('old tracked source clean', not git('status', '--porcelain', '--untracked-files=no', cwd=ORIGINAL).strip())
    inventory = json.loads((raw / 'original-before.json').read_text())
    check('all 430 original source files retain recorded SHA and Git blob', len(inventory) == 430 and all(
        identity(ORIGINAL / row['path']) == {key: row[key] for key in ('bytes', 'sha256')}
        and git('show', BASE + ':' + row['path']) == (ORIGINAL / row['path']).read_bytes()
        for row in inventory))
    return actual, outer


def builder_audit():
    """Run the unmodified audit, redirecting its sole generated receipt into this review."""
    real_write = Path.write_text
    def write(path, data, *args, **kwargs):
        if path == REPORT / 'source-preservation.json':
            return real_write(HERE / 'builder-audit-generated.json', data, *args, **kwargs)
        raise AssertionError('Unexpected audit write: ' + str(path))
    captured = io.StringIO()
    with patch.object(Path, 'write_text', write), redirect_stdout(captured):
        runpy.run_path(str(REPORT / 'audit_source.py'), run_name='independent_audit')
    return captured.getvalue()


@contextmanager
def changed(path, old, new):
    raw = path.read_bytes()
    assert old in raw and old != new
    path.write_bytes(raw.replace(old, new, 1))
    try:
        yield
    finally:
        path.write_bytes(raw)
        assert path.read_bytes() == raw


def admission_control(kind):
    """Only main's real one-shot admission runs; all native processes are forbidden."""
    called, errors = [], io.StringIO()
    class ForbiddenExecution(acq.Acquisition):
        def execute(self):
            called.append('execute')
            raise AssertionError('Admission must reject before execution')
    with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
        root = Path(temporary)
        output = root / 'builds/attempt'
        if kind == 'parent-symlink':
            (root / 'elsewhere').mkdir()
            output.parent.symlink_to(root / 'elsewhere', target_is_directory=True)
        else:
            output.parent.mkdir()
            if kind in ('empty-output', 'partial-output', 'claimed-output'):
                output.mkdir()
                if kind == 'partial-output':
                    (output / 'import.stdout').write_text('retain original partial bytes')
                if kind == 'claimed-output':
                    (output / 'attempt.claim').write_text(BASE + '\n')
            else:
                target = root / 'target'
                if kind == 'output-symlink':
                    target.mkdir()
                output.symlink_to(target, target_is_directory=True)
        before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        for name, value in [('ROOT', root), ('OUTPUT', output), ('Acquisition', ForbiddenExecution),
                            ('LANE_LOCK', root / 'lane'), ('ACQUISITION_LOCK', root / 'exclusive')]:
            stack.enter_context(patch.object(acq, name, value))
        stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('No process authorized')))
        stack.enter_context(patch('sys.argv', ['review', '--execute-frozen-source', CANDIDATE]))
        handlers = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}
        try:
            with redirect_stderr(errors), redirect_stdout(io.StringIO()):
                code = acq.main()
        finally:
            for number, handler in handlers.items():
                signal.signal(number, handler)
        after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
        check('admission rejects ' + kind, code == 1 and not called and before == after, errors.getvalue().strip())


before_raw = raw_snapshot()
manifest = json.loads((REPORT / 'source.json').read_text())
check('20 artifact manifest identities exact', len(manifest['files']) == 20 and all(
    identity(ROOT / name) == wanted for name, wanted in manifest['files'].items()))
for name, wanted in manifest['files'].items():
    check('candidate Git-bound artifact ' + name, git('show', CANDIDATE + ':' + name) == (ROOT / name).read_bytes())
check('preregistration before implementation', subprocess.run(['git', 'merge-base', '--is-ancestor',
    manifest['preregistration_commit'], manifest['implementation_commit']], cwd=ROOT).returncode == 0)
check('review preregistration parent is exact candidate', git('rev-parse', PREREG + '^').decode().strip() == CANDIDATE)
fixture, wrapper = 'scripts/diagnostics/linux_profile_overhead.gd', 'scripts/linux_profile_acquire.py'
old_fixture = git('show', BASE + ':' + fixture)
new_fixture = (ROOT / fixture).read_bytes()
check('one explicit Array declaration only', new_fixture == old_fixture.replace(b'var keys := value.keys()', b'var keys: Array = value.keys()')
      and old_fixture.count(b'var keys := value.keys()') == 1)
old_wrapper = git('show', BASE + ':' + wrapper)
expected_wrapper = old_wrapper.replace(b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r1'", b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r2'").replace(
    hashlib.sha256(old_fixture).hexdigest().encode(), hashlib.sha256(new_fixture).hexdigest().encode())
check('wrapper changes only r2 identity and exact fixture pin', (ROOT / wrapper).read_bytes() == expected_wrapper)
delta = git('diff', '--name-only', BASE, CANDIDATE).decode().splitlines()
prefix = REPORT.relative_to(ROOT).as_posix() + '/'
check('all other tracked source reports and game identical', sorted(p for p in delta if not p.startswith(prefix)) == sorted([fixture, wrapper]))
check('shipping game tree exact', git('rev-parse', CANDIDATE + ':game').decode().strip() == '55691684d31d44f1680141954bbe530443de9d1f')
check('whole caps and cleanup unchanged', acq.WHOLE == 1320 and acq.CLEANUP == 5 and acq.FAILURE_PUBLICATION == 10 and
      acq.CAPS == dict(zip(('preflight', 'stage', 'version', 'import', 'import-inventory', 'export', 'artifact', 'seal', 'block', 'finalize'),
                          (60, 45, 15, 120, 30, 120, 60, 30, 750, 60))))
check('fixed condition order samples and strict bound', diagnostic.ORDER == (False, True, True, False) and
      (diagnostic.WARM, diagnostic.SAMPLES, diagnostic.BOUND) == (32, 64, 180))
pins = json.loads((ROOT / 'docs/reports/gauntlet/m1-linux-profile-acquisition/pins.json').read_text())
check('fixed CPU and display pins', pins['cpus'] == [0, 1] and pins['display'] == ':99127')
for root in (ROOT, BUILDER):
    check('fresh r2 output absent ' + str(root), not (root / 'builds/linux-profile-acquisition-r2').exists()
          and not (root / 'builds/linux-profile-acquisition-r2').is_symlink())
    check('fresh outer recipe paths absent ' + str(root), not list((root / '.local').glob('linux-profile-acquisition-r2-*')))
check('exact source builder remains clean', git('rev-parse', 'HEAD', cwd=BUILDER).decode().strip() == CANDIDATE and not
      git('status', '--porcelain', '--untracked-files=all', cwd=BUILDER).strip())
old_overall = json.loads((ORIGINAL / 'builds/linux-profile-acquisition-r1/overall.json').read_text())
old_outer = json.loads((ORIGINAL / '.local/linux-profile-acquisition-r1-outer-tool-receipt.json').read_text())
check('old outer exit 1 and strict import failure retained', old_outer['terminal_tool_result']['exit_code'] == 1
      and not old_overall['passed'] and old_overall['error'] == 'Strict native log gate: 06-import')
check('old no export or native block commands', not any(r['label'] in ('export', 'block') for r in old_overall['commands']))
strict = acq.strict_log((ORIGINAL / 'builds/linux-profile-acquisition-r1/06-import.stderr.log').read_text())
check('old exact compiler and load errors still reject', len(strict) == 2 and 'Cannot infer the type of "keys"' in strict[0])
check('builder sparse failure retained', 'Ran 31 tests' in (REPORT / 'pure-controls/acquisition-missing-sparse-game.txt').read_text()
      and 'FAILED (errors=1)' in (REPORT / 'pure-controls/acquisition-missing-sparse-game.txt').read_text())
check('builder first source audit failure retained', 'AssertionError' in (REPORT / 'pure-controls/SOURCE-AUDIT-SETUP-NOTE.md').read_text())
(HERE / 'builder-audit.stdout.txt').write_text(builder_audit())
check('unmodified saved builder audit passes', True)

mutations = [
    (fixture, b'var keys: Array = value.keys()', b'var keys := value.keys()', 'revert failed inference'),
    (fixture, b'var keys: Array = value.keys()', b'var keys: Array[int] = value.keys()', 'restrict key type'),
    (fixture, b' < str(typeof(b))', b' > str(typeof(b))', 'reverse canonical comparator'),
    (fixture, b'HashingContext.HASH_SHA256', b'HashingContext.HASH_SHA1', 'alter fingerprint hash'),
    (wrapper, b'builds/linux-profile-acquisition-r2', b'builds/linux-profile-acquisition-r1', 'reuse r1 output'),
    (wrapper, b'builds/linux-profile-acquisition-r2', b'builds/linux-profile-acquisition-r3', 'arbitrary output'),
    (wrapper, hashlib.sha256(new_fixture).hexdigest().encode(), hashlib.sha256(old_fixture).hexdigest().encode(), 'stale fixture pin'),
    (wrapper, b'= 1320, 5, 10', b'= 1321, 5, 10', 'extend whole budget'),
    (wrapper, b"'import': 120", b"'import': 121", 'extend phase cap'),
    (wrapper, b"'-c', '0,1'", b"'-c', '0,2'", 'change native affinity'),
    (wrapper, b"LP_NUM_THREADS='2'", b"LP_NUM_THREADS='3'", 'change LP threads'),
    (wrapper, b"self.display == ':99127'", b"self.display == ':99128'", 'change display'),
    (wrapper, b'export/convert_text_resources_to_binary=false', b'export/convert_text_resources_to_binary=true', 'alter export amendment'),
    ('scripts/linux_profile_overhead.py', b'WARM, SAMPLES, BOUND = 32, 64, 180', b'WARM, SAMPLES, BOUND = 32, 64, 181', 'extend condition bound'),
    ('scripts/linux_profile_overhead.py', b'WARM, SAMPLES, BOUND = 32, 64, 180', b'WARM, SAMPLES, BOUND = 33, 64, 180', 'alter sampling'),
    ('scripts/diagnostics/linux_profile_overhead.tscn', b'[gd_scene', b'; reviewer mutation\n[gd_scene', 'alter scene'),
    ('game/project.godot', b'config/name=', b'config/description="review mutation"\nconfig/name=', 'alter shipping game'),
    ('docs/reports/gauntlet/m1-linux-profile-acquisition/pins.json', b'":99127"', b'":99128"', 'alter fixed pins'),
]
for name, old, new, label in mutations:
    with changed(ROOT / name, old, new):
        rejected = False
        try:
            builder_audit()
        except AssertionError:
            rejected = True
        check('saved exact source audit rejects ' + label, rejected)
for kind in ('empty-output', 'partial-output', 'claimed-output', 'output-symlink', 'dangling-symlink', 'parent-symlink'):
    admission_control(kind)
check('all 20 manifest identities restored after mutations', all(identity(ROOT / name) == wanted for name, wanted in manifest['files'].items()))
check('all old raw and outer records unchanged after review', raw_snapshot() == before_raw)
result = {'scope': 'Source and conditional recipe only; no engine/import/export/native/CI run',
          'candidate': CANDIDATE, 'base': BASE, 'preregistration': PREREG,
          'passed': True, 'checks': checks, 'check_count': len(checks),
          'source_mutations_rejected': len(mutations), 'reuse_admission_controls': 6}
(HERE / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ('scope', 'passed', 'check_count', 'source_mutations_rejected', 'reuse_admission_controls')}, indent=2))
