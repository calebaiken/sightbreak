"""Read/hash scoped evidence, without checkout writes or extra processes."""
import difflib
import hashlib
import json
from pathlib import Path
import platform
import re
import sys

root = Path(__file__).resolve().parent
checkout = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3')
critic = Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-final-ci-critic-20261019T195638920772Z')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(65536):
            value.update(chunk)
    return value.hexdigest()


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path, record):
    with path.open('x', encoding='utf-8') as output:
        json.dump(record, output, indent=2)
        output.write('\n')


matches = []
for path in sorted((root / 'after/source/scripts').iterdir()):
    if path.is_file():
        reviewed, current = digest(path), digest(checkout / 'scripts' / path.name)
        matches.append({'file': 'scripts/' + path.name, 'reviewed_sha256': reviewed,
                        'current_sha256': current, 'match': reviewed == current})
save(root / 'source-match-final.json', matches)
critic_after = [{'Path': str(path), 'Hash': digest(path).upper()}
                for path in sorted(critic.rglob('*')) if path.is_file()]
save(root / 'critic-packet-hashes-after.json', critic_after)
critic_before = load(root / 'critic-packet-hashes-before.json')
old = {item['Path']: item['Hash'] for item in critic_before}
new = {item['Path']: item['Hash'] for item in critic_after}
tests = (root / 'scoped-units.log').read_text(encoding='utf-8', errors='replace')
command = load(root / 'scoped-units.command.json')
owned = ['matrix_process.py', 'test_matrix_process.py', 'godot_process.py', 'test_godot_process.py']
gates = {
    'before_findings_reproduced': load(root / 'before/review.json')['passed'],
    'after_scope_correction_verified': load(root / 'after/review.json')['passed'],
    'scoped_77_tests_passed': command['exit'] == 0 and bool(re.search(r'^Ran 77 tests in ', tests, re.M))
        and bool(re.search(r'^OK$', tests, re.M)),
    'critic_packet_untouched': old == new,
    'unchanged_critic_replayed': digest(root / 'before/critic_controls.py')
        == digest(root / 'after/critic_controls.py') == digest(critic / 'critic_controls.py'),
    'all_reviewed_sources_match_checkout': all(item['match'] for item in matches),
    'nonowned_dependencies_unchanged': all(
        digest(path) == digest(root / 'after/source/scripts' / path.name)
        for path in (root / 'before/source/scripts').iterdir() if path.is_file() and path.name not in owned),
}
summary = {'python': sys.executable, 'version': platform.python_version(),
           'python_sha256': digest(Path(sys.executable)), 'test_command': command,
           'tests': 77, 'gates': gates, 'passed': all(gates.values()),
           'unresolved_limit': 'Linux exceptional supervisor death still cannot recover reparented '
                               'detached descendants; cleanup is explicitly unverified and fails closed.',
           'windows_contract': 'Standalone already-exited roots and failed taskkill cannot verify '
                               'descendant cleanup. Parent-guarded matrix Job Object ownership is unchanged.'}
save(root / 'results.json', summary)
with (root / 'reviewed-change.diff').open('x', encoding='utf-8', newline='\n') as output:
    for name in owned:
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
