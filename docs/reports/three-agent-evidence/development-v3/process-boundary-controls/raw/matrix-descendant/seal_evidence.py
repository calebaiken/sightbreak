"""Seal the retained CPython-only controls; no checkout writes or subprocesses."""
import difflib
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

root = Path(__file__).resolve().parent
before = json.loads((root / 'before/descendant-control/reproduction.json').read_text())
after = json.loads((root / 'after/descendant-control/reproduction.json').read_text())
matches = json.loads((root / 'after/source-match-final.json').read_text(encoding='utf-8-sig'))
tests = []
for filename, expected in [('test_validate_matrix.final.log', 18),
                           ('test_matrix_process.final.log', 15),
                           ('test_source_identity.log', 7),
                           ('test_verify_builds.final.log', 67)]:
    text = (root / filename).read_text(encoding='utf-8', errors='replace')
    count = re.search(r'^Ran (\d+) tests? in ', text, re.M)
    tests.append({'log': filename, 'tests': int(count[1]) if count else None,
                  'expected_tests': expected, 'passed': bool(count and int(count[1]) == expected
                                                            and re.search(r'^OK$', text, re.M))})
gates = {
    'before_reproduced_false_pass': before['bug_reproduced'] is True,
    'after_failed_with_real_root_zero': after['record']['exit'] == 0 and after['record']['passed'] is False,
    'after_harness_error_retained': 'HARNESS_ERROR' in after['raw_log_at_return'],
    'after_no_late_write': after['raw_log_at_return'] == after['raw_log_after_child'],
    'after_child_did_not_finish': after['child_started'] and not after['child_finished'],
    'reviewed_sources_match_checkout': all(item['match'] for item in matches),
    'all_final_tests_pass': all(item['passed'] for item in tests),
}
summary = {'python': sys.executable, 'version': platform.python_version(),
           'python_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
           'tests': tests, 'gates': gates, 'passed': all(gates.values()),
           'runtime_limits': ['Real Windows CPython only; Linux paths mocked.',
                              'Non-Linux POSIX fails closed before launching commands.']}
with (root / 'results.json').open('x', encoding='utf-8') as output:
    json.dump(summary, output, indent=2)
    output.write('\n')
diff = []
for name in ['validate_matrix.py', 'test_validate_matrix.py', 'matrix_process.py', 'test_matrix_process.py']:
    old = root / 'before/source/scripts' / name
    new = root / 'after/source/scripts' / name
    diff.extend(difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],
                                     new.read_text().splitlines(True),
                                     fromfile='before/scripts/' + name, tofile='after/scripts/' + name))
with (root / 'reviewed-change.diff').open('x', encoding='utf-8', newline='\n') as output:
    output.writelines(diff)
with (root / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as output:
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.name not in {'SHA256SUMS.txt', 'seal-console.log'}:
            output.write(hashlib.sha256(path.read_bytes()).hexdigest() + '  '
                         + path.relative_to(root).as_posix() + '\n')
print(json.dumps(summary, indent=2))
raise SystemExit(0 if summary['passed'] else 1)
