#!/usr/bin/env python3
"""Audit the narrow source delta and read retained failure bytes; no engine call."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
REPORT = Path(__file__).resolve().parent
BASE = 'f242a2f20adb3ba1d9c49feb1c6caca1bdbf52b9'
ORIGINAL = Path('/workspace/sightbreak-linux-profile-acquisition')
sys.path.insert(0, str(ROOT / 'scripts'))
import linux_profile_acquire as acquisition


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


fixture = 'scripts/diagnostics/linux_profile_overhead.gd'
wrapper = 'scripts/linux_profile_acquire.py'
old_fixture = git('show', BASE + ':' + fixture)
new_fixture = (ROOT / fixture).read_bytes()
assert old_fixture.count(b'var keys := value.keys()') == 1
assert new_fixture == old_fixture.replace(
    b'var keys := value.keys()', b'var keys: Array = value.keys()')
old_wrapper = git('show', BASE + ':' + wrapper)
expected_wrapper = old_wrapper.replace(
    b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r1'",
    b"OUTPUT = ROOT / 'builds/linux-profile-acquisition-r2'").replace(
        sha(old_fixture).encode(), sha(new_fixture).encode())
assert (ROOT / wrapper).read_bytes() == expected_wrapper
changes = git('diff', '--name-only', BASE, '--').decode().splitlines()
report_prefix = REPORT.relative_to(ROOT).as_posix() + '/'
code_changes = [name for name in changes if not name.startswith(report_prefix)]
assert sorted(code_changes) == sorted([fixture, wrapper])
for name, wanted in acquisition.ACCEPTED.items():
    assert sha((ROOT / name).read_bytes()) == wanted
assert git('rev-parse', 'HEAD', cwd=ORIGINAL).decode().strip() == BASE
assert not git('status', '--porcelain', '--untracked-files=no', cwd=ORIGINAL).strip()
raw_root = ORIGINAL / 'builds/linux-profile-acquisition-r1'
paths = [path for path in raw_root.iterdir() if path.is_file()]
paths += [ORIGINAL / '.local' / name for name in (
    'linux-profile-acquisition-r1-outer-tool-receipt.json',
    'linux-profile-acquisition-r1-wrapper.stdout',
    'linux-profile-acquisition-r1-wrapper.stderr')]
identities = {str(path.relative_to(ORIGINAL)): {
    'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
    for path in sorted(paths)}
raw = (raw_root / '06-import.stderr.log').read_bytes()
failures = acquisition.strict_log(raw.decode(errors='replace'))
assert len(failures) == 2 and 'Cannot infer the type of "keys"' in failures[0]
overall = json.loads((raw_root / 'overall.json').read_text())
imports = [row for row in overall['commands'] if row['label'] == 'import']
assert len(imports) == 1 and imports[0]['exit_code'] == 0 and not overall['passed']
assert not any(row['label'] in ['export', 'block'] for row in overall['commands'])
assert not acquisition.OUTPUT.exists() and not acquisition.OUTPUT.is_symlink()
assert acquisition.WHOLE == 1320 and acquisition.CLEANUP == 5
assert acquisition.FAILURE_PUBLICATION == 10
outer = json.loads((ORIGINAL / '.local' /
                    'linux-profile-acquisition-r1-outer-tool-receipt.json').read_text())
result = {
    'scope': 'Source delta and read-only failure audit; no GDScript compilation or native behavior tested',
    'base_commit': BASE,
    'original_worktree': str(ORIGINAL),
    'original_tracked_status_clean': True,
    'original_head_unchanged': True,
    'allowed_code_changes': code_changes,
    'fixture_only_one_explicit_Array_declaration': True,
    'wrapper_only_fixed_output_and_fixture_pin_changed': True,
    'game_tree': git('rev-parse', BASE + ':game').decode().strip(),
    'accepted_hashes': acquisition.ACCEPTED,
    'preservation': 'Every tracked path outside the two code files and this new report directory has no delta against base',
    'fresh_output': str(acquisition.OUTPUT),
    'fresh_output_absent': True,
    'fresh_claim': str(acquisition.OUTPUT / 'attempt.claim'),
    'phase_caps': acquisition.CAPS,
    'whole_seconds': acquisition.WHOLE,
    'cleanup_seconds': acquisition.CLEANUP,
    'failure_publication_seconds': acquisition.FAILURE_PUBLICATION,
    'retained_failure': {
        'outer_exit': outer['terminal_tool_result']['exit_code'],
        'import_exit': imports[0]['exit_code'],
        'overall_passed': overall['passed'],
        'overall_error': overall['error'],
        'strict_log_rejections': failures,
        'native_condition_count': 0},
    'original_top_level_raw_identities': identities}
(REPORT / 'source-preservation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: result[key] for key in (
    'allowed_code_changes', 'game_tree', 'fresh_output_absent', 'retained_failure')}, indent=2))
