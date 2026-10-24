#!/usr/bin/env python3
"""Independent, read-only byte/source audit. Does not run an engine or workload."""
import hashlib
import json
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
FROZEN = '8b0598c40efaa98883ec2ef3f5f74cd499ebf3ce'
PLAN = 'docs/reports/gauntlet/m1-linux-opaque-cost-plan/'
RETAINED = Path('/workspace/sightbreak-linux-opaque-cost/.local/godot-opaque-source')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def blob(path):
    return git('show', FROZEN + ':' + path)

def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

ledger = json.loads(blob(PLAN + 'source-references.json'))
assert git('rev-parse', FROZEN).decode().strip() == FROZEN
assert git('rev-parse', FROZEN + ':game').decode().strip() == ledger['game_tree']
assert not git('diff', FROZEN, ledger['game_matches_source'], '--', 'game')
assert not git('diff', FROZEN, ledger['base'], '--', 'game')
repo = []
for row in ledger['repo_sources']:
    actual = identity(blob(row['path']))
    actual['git_blob'] = git('rev-parse', FROZEN + ':' + row['path']).decode().strip()
    assert all(actual[k] == row[k] for k in ('bytes', 'sha256', 'git_blob'))
    repo.append({'path': row['path'], **actual, 'matches_ledger': True})

upstream = []
sources = {}
for row in ledger['upstream_sources']:
    path = RETAINED / row['source']
    data = path.read_bytes()
    actual = identity(data)
    assert all(actual[k] == row[k] for k in ('bytes', 'sha256'))
    compared = []
    for key in ('retained_path', 'retained_critic_original_path'):
        if row.get(key):
            original = Path(row[key])
            assert original.read_bytes() == data
            compared.append(str(original))
    upstream.append({'source': row['source'], 'inspected_path': str(path), **actual,
                     'matches_ledger': True, 'original_bytes_compared': compared})
    sources[row['source']] = data.decode()

# Recompute the shipping digest from Git blobs, independently of the builder's script.
shipping = hashlib.sha256()
paths = git('ls-tree', '-rz', '--name-only', FROZEN, '--', 'game').split(b'\0')
shipping_files = []
for raw in sorted(p for p in paths if p):
    path = raw.decode()
    relative = Path(path).relative_to('game')
    if '.godot' in relative.parts or 'tests' in relative.parts:
        continue
    shipping.update(relative.as_posix().encode() + b'\0' + blob(path) + b'\0')
    shipping_files.append(path)
assert shipping.hexdigest() == ledger['shipping_content_sha256']

# Preserve source spans for independent inspection, rather than derive timing from row names.
def span(path, lo, hi):
    lines = sources[path].splitlines()
    return {'source': path, 'first_line': lo, 'last_line': hi,
            'lines': [f'{n}: {lines[n-1]}' for n in range(lo, hi+1)]}
anchors = [span(*item) for item in [
    ('main/main.cpp', 1982, 1983),
    ('main/main.cpp', 3571, 3573),
    ('servers/rendering/rendering_server_default.cpp', 364, 367),
    ('servers/rendering/storage/utilities.h', 159, 171),
    ('drivers/gles3/rasterizer_gles3.cpp', 112, 122),
    ('drivers/gles3/storage/utilities.cpp', 329, 367),
    ('servers/rendering/rendering_server_default.cpp', 129, 140),
    ('servers/rendering/rendering_server_default.cpp', 190, 209),
    ('servers/rendering/rendering_server_default.cpp', 213, 230),
    ('main/main.cpp', 5086, 5096),
    ('main/main.cpp', 5174, 5178),
]]
rs = sources['servers/rendering/rendering_server_default.cpp']
assert rs.index('_run_post_draw_steps();') < rs.index('if (print_gpu_profile) {')
assert 'glGetQueryObjectui64v(frames[frame].queries[i], GL_QUERY_RESULT, &temp);' in sources['drivers/gles3/storage/utilities.cpp']

previous_path = 'docs/reports/gauntlet/m1-linux-gles-profile-recovered/native-r1/native-plant/results.json'
previous_bytes = blob(previous_path)
previous = json.loads(previous_bytes)
assert previous['passed'] is False and previous['error'] == 'Objective scenario live phase'
assert previous['partial_checks'] == {} and previous['cleanup_errors'] == []
assert previous['source']['source_commit'] == 'b1a131ab4790ac84371b54ee236441a66faf4125'

# Mathematical counterexample only. These are invented samples, not runtime evidence.
off = [1_000 / 60] * 64
on = off.copy()
on[31] += 200
counterexample = {'kind': 'synthetic estimator counterexample; no engine execution',
                  'off_samples_ms': off, 'on_samples_ms': on,
                  'median_ratio': statistics.median(on) / statistics.median(off),
                  'mean_ratio': statistics.mean(on) / statistics.mean(off)}
assert counterexample['median_ratio'] == 1.0 and counterexample['mean_ratio'] > 1.10

result = {
    'reviewed_commit': FROZEN,
    'review_scope': 'read-only Git/retained-byte inspection and synthetic arithmetic; no engine, compile, export, workload, OCR, service, or native gameplay',
    'game_tree': ledger['game_tree'],
    'shipping_content_sha256': shipping.hexdigest(),
    'shipping_file_count': len(shipping_files),
    'game_equals_base_and_b2e0293': True,
    'repo_sources': repo, 'upstream_sources': upstream, 'timing_anchors': anchors,
    'previous_attempt': {'path': previous_path, **identity(previous_bytes),
                         'source': previous['source']['source_commit'],
                         'passed': previous['passed'], 'error': previous['error'],
                         'elapsed_seconds': previous['elapsed_seconds'],
                         'partial_checks': previous['partial_checks'],
                         'cleanup_errors': previous['cleanup_errors']},
    'sparse_print_counterexample': counterexample,
}
(OUT / 'recomputed.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'reviewed_commit': FROZEN, 'repo_sources_verified': len(repo),
                  'upstream_sources_verified': len(upstream),
                  'shipping_files_verified': len(shipping_files),
                  'shipping_content_sha256': shipping.hexdigest(),
                  'synthetic_median_ratio': counterexample['median_ratio'],
                  'synthetic_mean_ratio': counterexample['mean_ratio'],
                  'previous_attempt_still_failed': True}, indent=2))
