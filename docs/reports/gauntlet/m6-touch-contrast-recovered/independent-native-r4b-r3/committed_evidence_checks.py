#!/usr/bin/env python3
"""Bind original archive parts, outer receipts and locked blind packet to Git."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = Path('/workspace/sightbreak-v1-recovered')
BUILDER = Path('/workspace/sightbreak-touch-contrast-recovered')
COMP = Path('docs/reports/gauntlet/m6-touch-contrast-recovered')
BASE = COMP / 'native-r4b-r3'
BLIND = COMP / 'blind-native-r4b-r3'
started = time.monotonic()
get = lambda commit, path: subprocess.check_output(['git', '-C', str(ROOT), 'show', commit + ':' + str(path)], stderr=subprocess.PIPE)
sha = lambda data: hashlib.sha256(data).hexdigest()
receipt = json.loads(get('3c5e0ad7', BASE / 'ARCHIVE.json'))
manifest = get('3c5e0ad7', BASE / 'payload-manifest.json')
assert sha(manifest) == receipt['payload_manifest_sha256']
assert manifest == (BUILDER / BASE / 'payload-manifest.json').read_bytes()
for row in receipt['parts']:
    data = get('3c5e0ad7', BASE / row['path'])
    assert len(data) == row['bytes'] and sha(data) == row['sha256']
    assert data == (BUILDER / BASE / row['path']).read_bytes()
origins = json.loads(get('3c5e0ad7', BASE / 'root-outer/origins.json'))
origin_rows, gaps = [], []
for row in origins['files']:
    data = Path(row['origin']).read_bytes()
    assert len(data) == row['bytes'] and sha(data) == row['sha256']
    try:
        committed = get('3c5e0ad7', BASE / row['retained'])
        assert committed == data
        origin_rows.append({'origin': row['origin'], 'retained': row['retained'], 'sha256': row['sha256'], 'committed_exact': True})
    except subprocess.CalledProcessError:
        gap = {'origin': row['origin'], 'retained': row['retained'], 'sha256': row['sha256'], 'bytes': row['bytes'], 'original_exists_exact': True, 'committed_at_3c5e0ad7': False}
        gaps.append(gap)
        origin_rows.append(gap)

manifest_data = get('231adbd9', BLIND / 'packet/manifest.json')
neutral = json.loads(manifest_data)
mapping = json.loads(get('231adbd9', BLIND / 'provenance/touch-r4b-r3-blind-map.json'))
reveal = json.loads(get('231adbd9', BLIND / 'provenance/locked-review-reveal.json'))
assert sha(manifest_data) == reveal['manifest_sha256'] == 'c776e0d24f9ff03dadffa8f7dc89901554674cef2becb85bb0a97f704f3d8d74'
assert len(neutral) == len(mapping['rows']) == 64
labels = {(row['scene'], row['label']): row for row in mapping['rows']}
assert len(labels) == 64
cases = set()
for row in neutral:
    mapped = labels[(row['scene'], row['label'])]
    data = get('231adbd9', BLIND / 'packet' / row['file'])
    assert sha(data) == row['sha256'] == mapped['sha256']
    assert data == Path(mapped['origin']).read_bytes()
    assert list(Image.open(io.BytesIO(data)).size) == row['dimensions']
    cases.add(mapped['case'])
assert len(cases) == 32
for scene in {row['scene'] for row in neutral}:
    pair = [row for row in neutral if row['scene'] == scene]
    assert len(pair) == 2 and {row['label'] for row in pair} == {'A', 'B'}
    assert all(pair[0][key] == pair[1][key] for key in ('layout', 'scale', 'background', 'state', 'dimensions'))
    pair_mapping = [labels[(row['scene'], row['label'])] for row in pair]
    assert len({row['case'] for row in pair_mapping}) == 1 and {row['variant'] for row in pair_mapping} == {'baseline', 'candidate'}
for row in reveal['review_files']:
    data = get('231adbd9', BLIND / row['path'])
    assert len(data) == row['bytes'] and sha(data) == row['sha256']
    assert data == Path(row['origin']).read_bytes()
assert reveal['counts'] == {'tie': 8, 'candidate': 24}
assert reveal['mapping_revealed_after_committed_review'] is True
result = {'kind': 'INDEPENDENT_COMMITTED_EVIDENCE_BINDING', 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'original_native_handoff': '3c5e0ad7', 'committed_parts_exact': len(receipt['parts']), 'committed_manifest_exact': True, 'outer_origin_rows': origin_rows, 'initial_outer_retention_gaps': gaps, 'original_raw_archive_parts_preservation_pass': True, 'blind_retention_commit': '231adbd9', 'all_64_blind_packet_images_exact_original_bytes_and_native_dimensions': True, 'all_32_pairs_exact_comparable_cases': True, 'locked_review_files_exact': True, 'blind_choice_counts': reveal['counts'], 'blind_review_scope': 'Independent visual preference only; not this source-aware critic and no numeric/ownership/cleanup override.', 'wall_seconds': time.monotonic() - started}
(OUT / 'committed-evidence-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'outer_origin_rows'}))
raise SystemExit(bool(gaps))
