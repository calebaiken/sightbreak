#!/usr/bin/env python3
"""Explicit full-history source audit, separate from maintained shallow tests."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[5]
DIRECTORY = ROOT/'scripts/fixtures/macos_ordinary_source'
reference = json.loads((DIRECTORY/'reference.json').read_text())
commit = reference['source_commit']
helper_command = ['git', 'show', commit+':'+reference['helper_source_path']]
driver_command = ['git', 'show', commit+':'+reference['driver_source_path']]
helper = subprocess.check_output(helper_command, cwd=ROOT)
driver = subprocess.check_output(driver_command, cwd=ROOT)
assert hashlib.sha256(helper).hexdigest() == reference['helper_source_sha256']
assert hashlib.sha256(driver).hexdigest() == reference['driver_source_sha256']
start, end = reference['helper_default_start'].encode(), reference['helper_default_end'].encode()
body = helper[helper.index(start):helper.index(end)]
assert body == (DIRECTORY/reference['helper_default_fixture']).read_bytes()
assert hashlib.sha256(body).hexdigest() == reference['helper_default_sha256']
boundary = reference['driver_gameplay_boundary'].encode()
tail = driver[driver.index(boundary):]
assert hashlib.sha256(tail).hexdigest() == reference['driver_gameplay_tail_sha256']
print(json.dumps({'scope': 'Explicit full-history source audit only; maintained tests invoke no Git history',
                 'reference': reference, 'commands': [helper_command, driver_command],
                 'golden_body_matches_exact_baseline_bytes': True, 'gameplay_tail_hash_matches_exact_baseline_bytes': True}, indent=2))
