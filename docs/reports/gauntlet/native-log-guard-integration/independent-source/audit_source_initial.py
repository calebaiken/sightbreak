#!/usr/bin/env python3
"""Read-only independent integration, native-byte and provenance assertions."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = '358b240ebadb8f32b581922ab99baec11ff9ed81'
SOURCE = '64a7afbad452d9559a39844bde7f25026029c97b'
HANDOFF = 'd4e6b0be66afd5400a6a9bfd78d3884b7d429c78'
ACCEPTED = 'aae1f0a5e963a01dceb4aed1d9c3b0c40520c76f'
REPORT = 'docs/reports/gauntlet/native-log-guard-integration/'
checks = []


def require(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    assert value, name


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def blob(commit, path):
    return git('show', commit + ':' + path)


def digest(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def tree(commit):
    return dict((x.split(b'\t', 1)[1].decode(), x.split(b'\t', 1)[0].decode())
                for x in git('ls-tree', '-rz', commit).split(b'\0') if x)


base, source, handoff = map(tree, (BASE, SOURCE, HANDOFF))
changed = {p for p in base.keys() | source.keys() if base.get(p) != source.get(p)}
existing = {p for p in changed if p in base}
require('exact existing-file edit set', existing == {
    'scripts/native_log.py', 'scripts/validate.sh', '.github/workflows/desktop-alpha.yml'})
additions = {p for p in changed if p not in base}
allowed_additions = {'scripts/test_native_log.py', 'scripts/fixtures/native_log/.gitattributes',
                     'scripts/fixtures/native_log/input-mode.log', 'scripts/fixtures/native_log/provenance.json'}
require('all additions component scoped', all(p in allowed_additions or p.startswith(REPORT) for p in additions))
require('no removed paths', not base.keys() - source.keys())
require('handoff changes only component reports', all(p.startswith(REPORT) for p in source.keys() | handoff.keys()
        if source.get(p) != handoff.get(p)))
require('all implementation handoff bytes exact', all(source[p] == handoff[p] for p in source if not p.startswith(REPORT)))
require('unchanged exact game tree', git('rev-parse', SOURCE + ':game').decode().strip()
        == git('rev-parse', BASE + ':game').decode().strip() == '55691684d31d44f1680141954bbe530443de9d1f')
for path, insertion in [('scripts/validate.sh', b'python3 scripts/test_native_log.py -v\n'),
    ('.github/workflows/desktop-alpha.yml', b'      - name: Strict native log failure controls\n        run: python scripts/test_native_log.py -v\n')]:
    current = blob(SOURCE, path)
    require(path + ' exact one registration', current.count(insertion) == 1)
    require(path + ' all existing bytes preserved', current.replace(insertion, b'') == blob(BASE, path))
matcher = blob(SOURCE, 'scripts/native_log.py')
require('accepted matcher byte exact', matcher == blob(ACCEPTED, 'scripts/native_log.py'))
require('all checked-out implementation bytes exact', all((ROOT / p).read_bytes() == blob(SOURCE, p)
        for p in allowed_additions | existing))
test = ast.parse(blob(SOURCE, 'scripts/test_native_log.py'))
require('five standalone test methods', len([n for n in ast.walk(test) if isinstance(n, ast.FunctionDef)
        and n.name.startswith('test_')]) == 5)
imports = {n.module if isinstance(n, ast.ImportFrom) else a.name for n in ast.walk(test)
           if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
require('only stdlib and matcher imports', imports == {'hashlib', 'json', 'pathlib', 'unittest', 'native_log'})
require('no execution or history calls', not any(isinstance(n, ast.Name) and n.id in
        {'exec', 'eval', 'subprocess', 'system', 'popen', 'compile', '__import__'} for n in ast.walk(test)))
prereg = '23e91c300a472bab3cd624981684ee49c2107eeb'
require('ordered builder prereg implementation handoff',
        git('rev-parse', SOURCE + '^').decode().strip() == prereg and
        git('rev-parse', prereg + '^').decode().strip() == BASE and
        git('rev-parse', HANDOFF + '^').decode().strip() == SOURCE)
fixture = blob(SOURCE, 'scripts/fixtures/native_log/input-mode.log')
provenance = json.loads(blob(SOURCE, 'scripts/fixtures/native_log/provenance.json'))
original = Path(provenance['corpus']['original_path'])
require('original complete corpus exact', fixture == original.read_bytes())
require('original corpus bytes hash lines', digest(fixture) == {
    'bytes': 2000315, 'sha256': 'a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218'}
    and len(fixture.splitlines()) == 7292)
require('corpus provenance exact', all(provenance['corpus'][k] == digest(fixture)[k] for k in ('bytes', 'sha256')))
lines = fixture.splitlines(keepends=True)
orphans = [x for x in lines if x.startswith(b'Orphan StringName: ')]
require('exact original orphan range', len(orphans) == 353 and orphans == lines[6938:7291])
require('original summary exact', lines[7291] == b'StringName: 353 unclaimed string names at exit.\n')
require('diagnostic hash and length exact', digest(b''.join(lines[6938:])) == {
    k: provenance['diagnostics'][k] for k in ('bytes', 'sha256')})
require('native orphan formats all exact', all(re.fullmatch(
    rb'Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\n', x) for x in orphans))
metadata = provenance['original_source']
records = metadata['source_manifests'] + [metadata['input_receipt'], metadata['overall'],
    provenance['engine']['version_log'], provenance['engine']['version_receipt']]
for record in records:
    require('original metadata hash ' + Path(record['path']).name,
            digest(Path(record['path']).read_bytes()) == {k: record[k] for k in ('bytes', 'sha256')})
receipt = json.loads(Path(metadata['input_receipt']['path']).read_bytes())
overall = json.loads(Path(metadata['overall']['path']).read_bytes())
require('historical native receipt unchanged false clean', receipt['clean_log'] is True
        and receipt['exit'] == 0 and receipt['command'] == metadata['command']
        and receipt['log_sha256'] == digest(fixture)['sha256'] and receipt['log_bytes'] == len(fixture))
require('historical acquisition reject strict fail preserved', overall['source_commit'] == metadata['commit']
        and overall['passed'] is False and overall['acquisition_integrity'] is False
        and overall['sample_strict_clean'] is False)
require('original source tree metadata exact', git('rev-parse', metadata['commit'] + ':game').decode().strip()
        == metadata['game_tree'])
require('engine bytes hash exact', digest(Path(provenance['engine']['executable']).read_bytes())['sha256']
        == provenance['engine']['executable_sha256'])
require('original engine version exact', Path(provenance['engine']['version_log']['path']).read_text().strip()
        == provenance['engine']['version'])
archive_meta = provenance['independent_actual_review']['original_archive']
archive = Path('/workspace/reviews/audio-owner-r1-native') / archive_meta['path']
require('original critic archive exact', digest(archive.read_bytes()) == {k: archive_meta[k] for k in ('bytes', 'sha256')})
archive_members = 0
with tarfile.open(archive) as package:
    for member in package:
        if member.isfile():
            archive_members += 1
            require('archive member original bytes ' + member.name,
                    package.extractfile(member).read() == (original.parent / member.name).read_bytes())
    require('archived complete native corpus exact', package.extractfile('input-mode.log').read() == fixture)
require('archive member count', archive_members == 375)
upstream = provenance['engine']['native_format_source']
with urllib.request.urlopen(upstream['url'], timeout=30) as response:
    fetched = response.read()
    retrieval = {'url': upstream['url'], 'status': response.status, **digest(fetched)}
require('pinned upstream source hash exact', digest(fetched) == {k: upstream[k] for k in ('bytes', 'sha256')})
upstream_lines = fetched.decode().splitlines()
require('upstream orphan emission exact', 'print_line("Orphan StringName: " + name + " (static: " + itos(E->static_count) + ", total: " + itos(refs) + ")");'
        in upstream_lines[upstream['orphan_format_line'] - 1])
require('upstream summary emission exact', 'print_line("StringName: " + itos(loststrings) + " unclaimed string names at exit.");'
        in upstream_lines[upstream['summary_format_line'] - 1])
(OUT / 'upstream-retrieval.json').write_text(json.dumps(retrieval, indent=2) + '\n')
baseline = {}
candidate = {}
exec(blob(BASE, 'scripts/native_log.py'), baseline)
exec(matcher, candidate)
require('old root full corpus false clean retained', baseline['failed'](fixture.decode()) is False)
require('candidate full corpus rejects', candidate['failed'](fixture.decode()) is True)
binding = json.loads(blob(HANDOFF, REPORT + 'source-binding.json'))
require('builder binding matches exact source', all(digest(blob(SOURCE, p)) == expected
        for p, expected in binding['implementation'].items()))
for name in ('pure-command-receipts.json', 'shallow-verification.json'):
    records = json.loads(blob(HANDOFF, REPORT + name))
    if isinstance(records, dict):
        records = records['commands']
    for record in records:
        for stream in ('stdout', 'stderr'):
            require('builder output ' + record['label'] + '.' + stream,
                    digest(blob(HANDOFF, REPORT + record['label'] + '.' + stream))['sha256'] == record[stream + '_sha256'])
red = json.loads(blob(HANDOFF, REPORT + 'baseline-red.json'))
require('retained expected red baseline receipt', red['exit'] == 1 and red['source'] == BASE
        and b'AssertionError: False is not true' in blob(HANDOFF, REPORT + 'baseline-red.stderr'))
require('retained sparse setup failure', b'export_presets.cfg' in blob(HANDOFF, REPORT + 'build-manifest.stderr')
        and b'FAILED (errors=2)' in blob(HANDOFF, REPORT + 'build-manifest.stderr'))
require('retained manifest passing rerun', b'Ran 24 tests' in blob(HANDOFF, REPORT + 'build-manifest-restored.stderr')
        and blob(HANDOFF, REPORT + 'build-manifest-restored.stderr').rstrip().endswith(b'OK'))
result = {'base': BASE, 'implementation': SOURCE, 'handoff': HANDOFF, 'matcher': digest(matcher),
          'fixture': digest(fixture), 'changed_paths': sorted(changed), 'protected_paths_unchanged': len(base) - len(existing),
          'archive_members_original_byte_exact': archive_members, 'assertions': len(checks), 'checks': checks}
(OUT / 'source-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k not in ('checks', 'changed_paths')}, indent=2))
