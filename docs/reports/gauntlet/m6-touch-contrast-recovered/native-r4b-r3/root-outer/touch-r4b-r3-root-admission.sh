cd /workspace/sightbreak-touch-contrast-recovered
export SIGHTBREAK_TOUCH_ROOT_RELEASE='# One touch R4B R3 native acquisition release

Recorded 2026-10-23 09:57:32 UTC before admission. The aggregate at exact
28a3e294 has exited 0; its evidence is committed in 2250af3c. The independent
critic has completed heavy verification and explicitly cleared the native/CPU
lane. Its final limited-scope report is being committed separately.

Release ONE exact prepared R4B R3 recipe from builder handoff b9bd7e62.
Product/source 108d1cdc6cf471daa7390298c234bb1c087ae865 is independently
source-accepted by 95703781. Fresh actual criteria 86c2c9b3 and source admission
e439aa93 precede this release. Separate blind visual criteria are retained in
ef5c4231 before any new capture, with candidate identity withheld from that judge.

Use only the frozen acquisition-r4b-r3 PLAN admission, existing controller,
post-source receipt and packager at /workspace/sightbreak-touch-contrast-recovered.
The freeze SHA256 is 4282c67c984b1840ca43158b16c0ecb03f4254d01e5cb300478682cc8adbe921.
Root readback confirms the new raw target and display :131 socket/lock are absent.

Preserve both 327-path/138-UID prepared projects, all 24 frozen files, pinned
Godot 4.7.2 and engine archive, CPUs 0–3, LP/OMP threads 2, display :131,
private producer state, fixed ordering, geometry, backgrounds and original
30/300/600-second producer limits. There is no original hard whole cap for
analysis/final waits/archival; the 3330-second sum is not a whole bound. No outer
timeout, retry, manual producer continuation, budget/source/threshold change or
overwrite is released. Preserve any STOP and all partial output.

Root copies this actual release text into SIGHTBREAK_TOUCH_ROOT_RELEASE as the
recipe requires. Stale PENDING labels in the immutable template remain unchanged;
this record identifies the actual later source and admission approvals. Admission
and controller get separate actual tool/exit receipts. The existing controller
invokes its analyzer once. Every native stream must also be independently scanned
for orphan/unclaimed StringNames, including forms missed by older helpers.

Expected complete output is 5648 PNGs and both full native ownership/contrast
records, with all regressions, original logs, source/UID fences and cleanup.
Actual quality is unobserved. Numeric gates, native interaction ownership,
strict cleanup and independent blinded preference remain separate requirements.
Earlier R3 numeric failure and R4B R2 import failure remain unchanged. Physical
reach, live/custom HUD, CS2 parity, whole accessibility and v1.0 stay open.
'
python3 - <<'PY'
import datetime, hashlib, json, os, shutil, zipfile
from pathlib import Path
repo = Path.cwd()
packet = repo / 'docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r3'
freeze_path = packet.parent / 'SOURCE_FREEZE-r4b-r3.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
release = os.environ.get('SIGHTBREAK_TOUCH_ROOT_RELEASE', '')
assert release and '<copy ' not in release, 'explicit root release is required'
config = json.loads((packet / 'lane-start.template.json').read_text())
raw = Path(config['raw_root'])
stage = Path(config['fixture_root'])
assert not raw.exists() and not raw.with_suffix('.tar.xz').exists()
assert not (packet.parent / 'native-r4b-r3').exists()
assert not Path('/tmp/.X11-unix/X131').exists()
assert not Path('/tmp/.X131-lock').exists()
assert sha(freeze_path) == config['freeze_sha256']
freeze = json.loads(freeze_path.read_text())
frozen = []
for entry in freeze['frozen_files']:
    path = repo / entry['path']
    assert sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'], entry['path']
    frozen.append({'path': entry['path'], 'sha256': sha(path), 'bytes': path.stat().st_size})
assert len(frozen) == 24
staged = []
for expected in freeze['fixtures']:
    root = stage / expected['name']
    assert not (root / 'game/.godot').exists()
    assert sha(root / 'SOURCE.json') == expected['manifest_sha256']
    receipt = json.loads((root / 'SOURCE.json').read_text())
    assert receipt['source'] == expected['source_full']
    rows = receipt['files'] + receipt['fixture'] + [
        {'path': 'game/tests/touch_contrast_instrumented.gd', 'sha256': receipt['instrumented_sha256']},
        {'path': 'game/tests/touch_contrast_instrumented.gd.uid', 'sha256': receipt['instrumented_uid_sha256']}]
    assert len(receipt['files']) == 323 and len(rows) == 327
    assert len({x['path'] for x in rows}) == 327
    for entry in rows:
        assert sha(root / entry['path']) == entry['sha256'], entry['path']
    uids = [(root / x['path']).read_text().strip() for x in rows if x['path'].endswith('.uid')]
    assert len(uids) == len(set(uids)) == 138
    staged.append({'name': expected['name'], 'source': receipt['source'],
                   'manifest_sha256': sha(root / 'SOURCE.json'), 'checked_paths': len(rows),
                   'actual_path_hashes': [[x['path'], sha(root / x['path'])] for x in rows],
                   'unique_uids': len(uids), 'preimport_cache_absent': True})
engine = Path(config['engine'])
archive = Path(config['engine_archive'])
assert sha(engine) == config['engine_sha256']
assert hashlib.sha512(archive.read_bytes()).hexdigest() == config['engine_archive_sha512']
with zipfile.ZipFile(archive) as bundle:
    member = bundle.read('Godot_v4.7.2-stable_linux.x86_64')
    assert hashlib.sha256(member).hexdigest() == config['engine_sha256']
assert os.access(engine, os.X_OK)
assert os.access('/workspace/tools/xvfb/usr/bin/Xvfb', os.X_OK)
assert shutil.which('taskset')
affinity = sorted(os.sched_getaffinity(0))
assert set(config['taskset']).issubset(affinity)
cpu_max = Path('/sys/fs/cgroup/cpu.max').read_text().strip()
memory_max = Path('/sys/fs/cgroup/memory.max').read_text().strip()
assert cpu_max == '400000 100000' and memory_max == '17179869184'
verified = json.loads((packet / 'verification.json').read_text())
for name in ('controller.py', 'package_evidence.py', 'lane-start.template.json'):
    assert sha(packet / name) == verified['packet_files'][name]['sha256'], name
raw.mkdir()
for name in ('controller.py', 'package_evidence.py'):
    shutil.copyfile(packet / name, raw / name)
shutil.copyfile(freeze_path, raw / freeze_path.name)
config.update(status='RELEASED_SINGLE_ATTEMPT', root_release=release,
              start_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              engine_archive_member_matches_binary=True, affinity=affinity,
              cpu_max=cpu_max, memory_max=memory_max,
              disk_free_bytes=shutil.disk_usage(raw).free)
(raw / 'lane-start.json').write_text(json.dumps(config, indent=2) + '\n')
(raw / 'admission-source.json').write_text(json.dumps(
    {'frozen_files': frozen, 'staged': staged, 'packet_verification': verified}, indent=2) + '\n')
print('ADMITTED', raw, config['start_utc'])
PY
