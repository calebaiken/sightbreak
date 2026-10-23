# R4B R2: one source-bound A/B acquisition recipe

PREPARED ONLY. Runtime remains held. This packet authorizes no engine, import,
native render, OCR, UID generation, export, live HUD, service or CI execution.
Root must explicitly release the sole local native/CPU lane for this exact
packet. A fresh actual-output critic and separate blind image judge must assess
the resulting evidence; the builder cannot accept it.

The accepted source/method is `b001fc5087960729535f63c896b40d6dc25bd272`,
independent SOURCE ACCEPT `abb837b4`, root source report `960c5fe` and handoff
`548e3569fe9228740c5bb82cae4331bdd60128ae`. The source freeze is unchanged:
`f9d292d7cb04fc129eee7df84fdc1c0591ae14600497bcf63aac0243cd7f2563`.
SOURCE ACCEPT is readiness for acquisition, not rendered-quality acceptance.
R3 FAIL, R4 NO GO and R4B source REJECT remain unchanged.

## Reused controller and fixed bounds

[controller.py](controller.py) is the reviewed R3 controller with only five
string-literal substitutions: three freeze filenames and two analyzer paths.
[controller.diff](controller.diff) records the complete change. No new native
wrapper, retry, timeout adjustment, producer order, environment behavior or
cleanup behavior was added. All non-literal AST structure and every other
literal match the retained R3 controller. The new analyzer is already part of
the accepted 22-file freeze.

| Ordered producer | Exact source/project | Original timeout |
| --- | --- | --- |
| Pinned engine version | Godot 4.7.2, exact version string checked | 30 s |
| Import baseline, then candidate | Separate prepared projects below | 300 s each |
| Fresh shared backgrounds | Baseline only | 300 s |
| Baseline controls, then candidate controls | Same frozen background files | 600 s each |
| touch, then input_mode regression for each source | Each exact prepared project | 300 s each |
| Frozen analyzer | Accepted source and all raw receipts | No explicit timeout in the original controller |

There are at most ten engine invocations and one attempt at each producer.
The sum of the original engine wait caps is 3,330 seconds, excluding startup,
cleanup and analysis. A timeout or engine error stops the acquisition; do not
extend a cap or retry in this directory. The analyzer's nonzero exit is retained
as a quality/method failure and does not turn successful acquisition into a
passing candidate. Its lack of an explicit timeout is disclosed, not amended.

Engine commands retain `taskset -c 0,1,2,3`, `LP_NUM_THREADS=2` and
`OMP_NUM_THREADS=2`. Each producer has fresh private XDG data/config/cache and
`SIGHTBREAK_STATE_DIR` under the new raw root. Xvfb remains the exact reviewed
binary, explicit display `:131`, screen `1280x720x24`, GLX/render enabled,
`-noreset -nolisten tcp`. Rendering remains X11, gl_compatibility, Dummy audio,
1280x720 window and max-fps 60. Record actual engine/renderer from original logs
and capture receipts. Historical llvmpipe identity and timings are not new facts
and do not qualify device FPS.

Prepared projects, not the normal game checkout:

| Variant | Exact original game source | SOURCE.json SHA-256 |
| --- | --- | --- |
| baseline | a52022169241df9ff662039547a375e1c46ac1c5 | 8769df11adb16daefd652d6694b2917cf4ecd95db59e77bccfb99cc5a651788f |
| candidate | b001fc5087960729535f63c896b40d6dc25bd272 | a423eb35530201a0b6090a146a8211c802ea80c99c328d5879d391e28ea03780 |

Their root is
`/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r2`.
Each has 323 original game paths and 327 source/fixture/UID paths. Copied UID
bytes must remain identical. The original source and both staged manifests
remain untouched. The controller checks every one of the 327 paths before and
after every source-bound producer, including imports and regressions. Source
or UID changes stop acquisition, even if the engine exits zero.

## Original matrix and outputs

The fixture is unchanged. Each source has 32 scenes: mobile-min/mobile-max at
960x720 with 32 px left/right safe inset, desktop-min/desktop-max at 1280x720
with zero inset; requested HUD scales 0.7/1.5; white/gray/arena/smoke
backgrounds; idle/held states. The R4B mobile-max effective scale remains the
source-derived 1.4; record requested and effective scales without relabeling.
Held uses the fixed movement (0.65, 0.45) and fire/reload/interact states;
grenade=0 and smoke=1 retain disabled exceptions. No randomized scene,
position, inventory, camera or state may be substituted.

Expected complete output is 2,816 PNGs per source plus sixteen newly rendered
shared backgrounds: 5,648 PNGs total. Per source that is 64 original/wrapped
normal images, 304 x 4 diagnostic images, 352 x 4 whole-action diagnostic
images and 128 isolated layer footprints. Retain all PNGs, not only selected
examples. The 16 backgrounds and their capture receipt are frozen after the
baseline background producer and checked before and after both controls runs.

The capture records the actual nearest-normalized `action_at` winner at every
supported component-footprint pixel center. Native counts, coordinates and
winning identities must match independent replay for both variants, including
all wrong-owner and unclaimed samples. Receipt contradiction invalidates
provenance; accurately recorded bad baseline quality remains comparable. Do
not require the baseline product to pass candidate quality gates.

Original 4.5:1 active-label/count and 3:1 UI gates, full glyph/one-code AA
support, complete visible-footprint and occlusion checks remain fixed. Preserve
all 48 intermediate border rows per source as diagnostics and all 608 gated
rows per source. No hidden-pixel exclusion, footprint shrinking, threshold
change, silent repair or relabeling of an earlier failed attempt is allowed.
The retained final-boundary identifiability limitations still apply; actual
dark surround, heavy plates, glyph collisions, truthful ownership, scene
occlusion and physical reach require separate review.

## Admission after explicit root release only

Do not run this section during preparation. Root's release must identify this
packet and exclusive lane. Copy that actual release text into
`SIGHTBREAK_TOUCH_ROOT_RELEASE`; a nonempty variable is a receipt, not permission.
If root has not released it, stop before these commands.

Use the existing raw-free target exactly once. Do not remove or reuse any
existing raw target, archive, report or staged import cache. An occupied :131,
changed CPU/memory selectors, source/hash/UID mismatch, unexpected `.godot`,
missing tool or different engine blocks admission. Preserve the failed
admission output in a separately named report; ask root to resolve the block,
not to weaken the check. Source-only preparation never creates `lane-start.json`
or the raw directory.

The following admission command performs read-only checks before creating the
new raw root. It does not execute an engine or generate UIDs. Its use is still
held with the rest of runtime admission until root release.

```sh
cd /workspace/sightbreak-touch-contrast-recovered
export SIGHTBREAK_TOUCH_ROOT_RELEASE='<copy the actual explicit root release here>'
python3 - <<'PY'
import datetime, hashlib, json, os, shutil, zipfile
from pathlib import Path
repo = Path.cwd()
packet = repo / 'docs/reports/gauntlet/m6-touch-contrast-recovered/acquisition-r4b-r2'
freeze_path = packet.parent / 'SOURCE_FREEZE-r4b-r2.json'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
release = os.environ.get('SIGHTBREAK_TOUCH_ROOT_RELEASE', '')
assert release and '<copy ' not in release, 'explicit root release is required'
config = json.loads((packet / 'lane-start.template.json').read_text())
raw = Path(config['raw_root'])
stage = Path(config['fixture_root'])
assert not raw.exists() and not raw.with_suffix('.tar.xz').exists()
assert not (packet.parent / 'native-r4b-r2').exists()
assert not Path('/tmp/.X11-unix/X131').exists()
assert not Path('/tmp/.X131-lock').exists()
assert sha(freeze_path) == config['freeze_sha256']
freeze = json.loads(freeze_path.read_text())
frozen = []
for entry in freeze['frozen_files']:
    path = repo / entry['path']
    assert sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'], entry['path']
    frozen.append({'path': entry['path'], 'sha256': sha(path), 'bytes': path.stat().st_size})
assert len(frozen) == 22
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
```

Announce lane start to root with the actual admission path/time, then invoke
only the existing controller, with no outer timeout or retry:

```sh
python3 /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/controller.py > /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/controller.log 2>&1
SIGHTBREAK_TOUCH_CONTROLLER_EXIT=$?
export SIGHTBREAK_TOUCH_CONTROLLER_EXIT
python3 - <<'PY'
import datetime, json, os
from pathlib import Path
p = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/controller-exit.json')
assert not p.exists()
p.write_text(json.dumps({'exit_code': int(os.environ['SIGHTBREAK_TOUCH_CONTROLLER_EXIT']),
    'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}, indent=2) + '\n')
PY
```

These shell commands assume no `set -e`: the exit receipt must be written even
when acquisition stops. Do not run later producers manually after a STOP.
The controller invokes the accepted analyzer once itself; do not run a second
analyzer with different thresholds or inputs to replace that result.

## Cleanup, immutable evidence and review

The unchanged controller owns process groups for every launched engine and
Xvfb. On error or completion it SIGTERMs remaining groups, waits five seconds,
then SIGKILLs and waits if necessary. `lane-end.json` records every owned PID,
actual exit, `/proc` absence and :131 socket/lock absence. Check those actual
receipts and announce producer end to root. Never kill another lane's process
or delete an unrelated display lock. Cleanup failure blocks archival completion
and lane release until the owned process is resolved, with all attempts retained.

Before packaging, repeat the admission's 22-file and both 327-path checks into
a NEW `post-source.json` receipt, compare every saved background hash, and
record actual PNG counts and producer exits. Record source changes and count
shortfalls as failures rather than overwriting receipts. If the producer failed,
leave all partial outputs and failed logs in place. A missing `lane-end.json`
is an unresolved interrupted attempt, not an excuse to invent one.

The concrete post-acquisition command writes observed failures before returning
nonzero. Its exit cannot turn a failed attempt into a passing one or discard it:

```sh
python3 - <<'PY'
import datetime, hashlib, json, os
from pathlib import Path
raw = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2')
repo = Path('/workspace/sightbreak-touch-contrast-recovered')
config = json.loads((raw / 'lane-start.json').read_text())
admission = json.loads((raw / 'admission-source.json').read_text())
stage = Path(config['fixture_root'])
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
errors, frozen, staged = [], [], []
def check(path, expected):
    actual = sha(path) if path.is_file() else None
    if actual != expected:
        errors.append({'path': str(path), 'expected_sha256': expected, 'actual_sha256': actual})
    return actual
for entry in admission['frozen_files']:
    frozen.append([entry['path'], check(repo / entry['path'], entry['sha256'])])
check(raw / 'SOURCE_FREEZE-r4b-r2.json', config['freeze_sha256'])
for source in admission['staged']:
    root = stage / source['name']
    check(root / 'SOURCE.json', source['manifest_sha256'])
    rows = [[path, check(root / path, expected)] for path, expected in source['actual_path_hashes']]
    staged.append({'name': source['name'], 'checked_paths': len(rows), 'actual_path_hashes': rows})
backgrounds = raw / 'backgrounds'
background_freeze = raw / 'background-freeze.json'
if background_freeze.is_file():
    expected = json.loads(background_freeze.read_text())['files']
    observed = {str(p.relative_to(backgrounds)) for p in backgrounds.rglob('*') if p.is_file()}
    if observed != set(expected):
        errors.append({'background_missing': sorted(set(expected) - observed),
                       'background_extra': sorted(observed - set(expected))})
    for name, digest in expected.items():
        check(backgrounds / name, digest)
else:
    errors.append({'background_freeze_missing': True})
counts = {name: sum(1 for p in (raw / name).rglob('*.png'))
          for name in ('baseline', 'candidate', 'backgrounds')}
for name, expected in (('baseline', 2816), ('candidate', 2816), ('backgrounds', 16)):
    if counts[name] != expected:
        errors.append({'png_count': name, 'expected': expected, 'actual': counts[name]})
end_path = raw / 'lane-end.json'
end = json.loads(end_path.read_text()) if end_path.is_file() else None
if end is None:
    errors.append({'lane_end_missing': True})
else:
    if not end['acquisition_complete']:
        errors.append({'acquisition_complete': False, 'error': end['error']})
    for process in end['owned_cleanup']:
        if not process['proc_path_absent'] or Path('/proc/' + str(process['pid'])).exists():
            errors.append({'cleanup_not_confirmed': process})
    if not end['display_socket_absent'] or not end['display_lock_absent']:
        errors.append({'display_cleanup_not_confirmed': True})
for path in ('/tmp/.X11-unix/X131', '/tmp/.X131-lock'):
    if Path(path).exists():
        errors.append({'display_path_still_present': path})
receipt = {'time': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'frozen_files': frozen, 'staged': staged, 'png_counts': counts, 'errors': errors,
           'actual_affinity': sorted(os.sched_getaffinity(0)),
           'actual_cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip(),
           'actual_memory_max': Path('/sys/fs/cgroup/memory.max').read_text().strip()}
out = raw / 'post-source.json'
assert not out.exists()
out.write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'post_source': str(out), 'png_counts': counts, 'errors': errors}))
raise SystemExit(bool(errors))
PY
```

[package_evidence.py](package_evidence.py) reuses the reviewed R3 archival
algorithm, source/report literals changed. One necessary evidence-only change
allows an honestly recorded failed acquisition to be archived, adding its
boolean and error to the manifest. It still requires actual owned-process and
display cleanup, refuses an existing archive/report, includes every original
raw file and re-reads every archive member's hash/size. The
[complete diff](package_evidence.diff) exposes this narrow change. It launches
no engine and does not alter native output.

After those checks, the concrete bounded archival command is:

```sh
taskset -c 0,1,2,3 python3 /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2/package_evidence.py > /workspace/sightbreak-touch-contrast-native-recovered-r4b-r2-packaging.log 2>&1
```

The packaging log is outside the frozen raw payload so it cannot change while
being hashed; retain it in the component report afterward. The archive contains
the embedded full payload manifest and original raw tree. Split parts are at
most 24 MiB, with full archive/part hashes. Verify every part hash and the
reassembled full hash, not just the archive members. Preserve the original raw
directory and tar.xz alongside the committed bounded parts. No third-party
reference pixels or protected assets enter Git.

Retain command/result/log receipts, engine/archive identity, actual renderer,
CPU/cgroup/display/private-state selectors, all before/after source/UID fences,
background freeze, capture/scene/ownership receipts, all 5,648 expected originals
or every partial original, analyzer stdout/exit/JSON and cleanup. Make an honest
builder summary of actual counts and failures; successful acquisition is not
numeric or visual acceptance. Commit/push the immutable archive and exact
handoff before requesting evaluation.

Root assigns a fresh read-only actual-output critic to verify complete source,
matrix, image/background hashes, native ownership/replay reconciliation,
selected raw pixel witnesses and every reported failure. A separate fork-none
blind visual judge receives only neutral comparable normal-image pairs at
original size, including small mobile and maximum mobile clusters across all
four backgrounds and both states. Keep the variant key outside that packet and
do not message the judge. Blind preference cannot override numerical failure.

No product, geometry, method, cap or scene changes are allowed during this
attempt. Any follow-up requires a new source preregistration/freeze/review and
separate raw root. Live HUD, dynamic joystick, editing/custom layouts, physical
touch/reach, complete accessibility and shipped-title parity remain open. CS2
reference-host restrictions stay explicit; this bounded engineering comparison
cannot establish shipped-game parity.
