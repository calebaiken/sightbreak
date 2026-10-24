"""Read/hash the reviewed sources and controls; never write into the checkout."""
import ctypes
import difflib
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

root = Path(__file__).resolve().parent
checkout = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
critic = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\critic-after-controller-20261019T193151501897Z')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(65536):
            value.update(chunk)
    return value.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, indent=2)
        output.write('\n')


matches = []
for source in sorted((root / 'after/source/scripts').iterdir()):
    if source.is_file():
        reviewed = digest(source)
        current = digest(checkout / 'scripts' / source.name)
        matches.append({'file': 'scripts/' + source.name, 'reviewed_sha256': reviewed,
                        'current_sha256': current, 'match': reviewed == current})
save(root / 'after/source-match-final.json', matches)
critic_before = load(root / 'critic-packet-hashes-before.json')
critic_after = [{'Path': str(path), 'Hash': digest(path).upper()}
                for path in sorted(critic.rglob('*')) if path.is_file()]
save(root / 'critic-packet-hashes-after.json', critic_after)
before_hashes = {item['Path']: item['Hash'] for item in critic_before}
after_hashes = {item['Path']: item['Hash'] for item in critic_after}

before = load(root / 'before/entry-descendant-control/after-observation.json')
after_case = root / 'after/entry-descendant-control'
after = load(after_case / 'after-observation.json')
receipt = load(after_case / 'evidence/watchdog.process.json')
pid = load(after_case / 'child-started.json')['pid']
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
kernel.OpenProcess.restype = ctypes.c_void_p
kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
kernel.WaitForSingleObject.restype = ctypes.c_ulong
kernel.CloseHandle.argtypes = [ctypes.c_void_p]
kernel.CloseHandle.restype = ctypes.c_int
handle = kernel.OpenProcess(0x100000, False, pid)
if handle:
    try:
        child_stopped = kernel.WaitForSingleObject(handle, 0) == 0
    finally:
        kernel.CloseHandle(handle)
else:
    child_stopped = ctypes.get_last_error() == 87

tests = []
for name, count in [('test_export_flow.retry', 27), ('test_matrix_process.final', 15)]:
    command = load(root / (name + '.command.json'))
    text = (root / (name + '.log')).read_text(encoding='utf-8', errors='replace')
    match = re.search(r'^Ran (\d+) tests? in ', text, re.M)
    tests.append({'log': name + '.log', 'command': command,
                  'tests': int(match[1]) if match else None,
                  'passed': command['exit'] == 0 and bool(match and int(match[1]) == count
                                                        and re.search(r'^OK$', text, re.M))})

gates = {
    'before_false_pass_reproduced': before['false_pass_reproduced'] is True,
    'after_entry_failed_preserving_worker_zero': after['entry_exit'] == 1
        and after['result_at_return']['watchdog']['worker_exit'] == 0,
    'after_persisted_failure': after['persisted_result_passed'] is False,
    'after_harness_error_retained': 'HARNESS_ERROR' in after['log_at_return'],
    'after_log_stable': after['log_at_return'] == after['log_after_child']
        == (after_case / 'evidence/watchdog.log').read_text(),
    'after_child_stopped': child_stopped and not after['child_finished_later']
        and not (after_case / 'child-finished.txt').exists(),
    'containment_receipt_failed_with_real_zero': receipt['exit'] == 0
        and any('descendants survived' in error for error in receipt['errors']),
    'controller_source_hash_matches': after['result_at_return']['watchdog']['controller_sha256']
        == digest(root / 'after/synthetic_descendant_entry.py'),
    'identical_before_after_control_programs': all(
        digest(root / 'before' / name) == digest(root / 'after' / name)
        for name in ['run_descendant_entry.py', 'synthetic_descendant_entry.py']),
    'critic_packet_untouched': before_hashes == after_hashes,
    'reviewed_sources_match_checkout': all(item['match'] for item in matches),
    'shared_modules_unchanged': all(
        digest(root / 'before/source/scripts' / name) == digest(root / 'after/source/scripts' / name)
        for name in ['matrix_process.py', 'test_matrix_process.py', 'godot_process.py']),
    'final_tests_pass': all(item['passed'] for item in tests),
}
summary = {'python': sys.executable, 'version': platform.python_version(),
           'python_sha256': digest(Path(sys.executable)), 'tests': tests,
           'gates': gates, 'descendant_pid': pid, 'passed': all(gates.values())}
save(root / 'results.json', summary)
with (root / 'reviewed-change.diff').open('x', encoding='utf-8', newline='\n') as output:
    for name in ['export_flow.py', 'test_export_flow.py']:
        output.writelines(difflib.unified_diff(
            (root / 'before/source/scripts' / name).read_text().splitlines(True),
            (root / 'after/source/scripts' / name).read_text().splitlines(True),
            fromfile='before/scripts/' + name, tofile='after/scripts/' + name))
with (root / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as output:
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.name not in {'SHA256SUMS.txt', 'seal-console.log'}:
            output.write(digest(path) + '  ' + path.relative_to(root).as_posix() + '\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary['passed'] else 1)
