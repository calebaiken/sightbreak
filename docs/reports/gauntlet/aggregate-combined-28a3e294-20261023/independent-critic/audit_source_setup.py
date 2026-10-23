#!/usr/bin/env python3
"""Independent read-only setup audit; no engine, validator or helper launch."""
import ast
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

EXPECTED = '28a3e294c850482475b7ab74067c08538ae6310d'
BUILDER_COMMIT = 'bcfc7c3c57b33ad373b0a9e787eb187bc38d463f'
ROOT = Path('/workspace/sightbreak-aggregate-frozen-28a3e294')
BUILDER = Path('/workspace/sightbreak-aggregate-combined-28a3e294')
RELATIVE = Path('docs/reports/gauntlet/aggregate-combined-28a3e294-20261023')
SCOPES = ['game', 'scripts', '.github', 'backend', 'server',
          'docs/reports/media/art-v9/hands/logs', 'docs/reports/gauntlet/native-layout-ocr']
ENGINE = Path('/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64')
ENGINE_SHA = '8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e'
PORTS = {27991, 29900, 29901, 29902, 33540, 33541, 33542, 33543}
HERE = Path(__file__).resolve().parent
failures = []
checks = 0

def check(value, message):
    global checks
    checks += 1
    if not value:
        failures.append(message)

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])

def sha(data):
    return hashlib.sha256(data).hexdigest()

check(git(ROOT, 'rev-parse', 'HEAD').decode().strip() == EXPECTED, 'runtime exact frozen HEAD')
check(not git(ROOT, 'status', '--porcelain', '--untracked-files=all'), 'whole frozen source clean')
check(git(BUILDER, 'rev-parse', 'HEAD').decode().strip() == BUILDER_COMMIT, 'builder exact committed wrapper')
check(not git(BUILDER, 'status', '--porcelain', '--untracked-files=all'), 'builder source clean')
inventory = []
for raw in git(ROOT, 'ls-tree', '-rz', EXPECTED, '--', *SCOPES).split(b'\0'):
    if not raw:
        continue
    meta, name = raw.split(b'\t', 1)
    mode, kind, blob = meta.decode().split()
    relative = name.decode(); path = ROOT / relative
    check(path.is_file() and not path.is_symlink(), 'tracked regular input present: ' + relative)
    if not path.is_file() or path.is_symlink():
        continue
    data = path.read_bytes()
    actual_blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    check(kind == 'blob' and actual_blob == blob, 'input equals exact committed blob: ' + relative)
    actual_exec = bool(path.stat().st_mode & 0o111)
    check(actual_exec == (mode == '100755'), 'executable mode agrees: ' + relative)
    inventory.append(dict(path=relative, bytes=len(data), sha256=sha(data), git_blob=blob, mode=mode))
check(len(inventory) == 808, 'all 808 tracked input paths')
check(sum(r['path'].endswith('.uid') and r['path'].startswith('game/') for r in inventory) == 138, 'all 138 tracked game UID paths')
for scope in SCOPES:
    check(any(r['path'].startswith(scope + '/') for r in inventory), 'scope populated: ' + scope)
prepared = json.loads((BUILDER / RELATIVE / 'preparation-r3/source-before.json').read_text())
check({r['path']:dict(bytes=r['bytes'],sha256=r['sha256']) for r in inventory} == prepared['inputs'], 'independent input inventory equals builder preparation')
shipping, validation = hashlib.sha256(), hashlib.sha256()
for path in sorted((ROOT/'game').rglob('*')):
    relative = path.relative_to(ROOT/'game')
    if path.is_file() and '.godot' not in relative.parts and 'tests' not in relative.parts:
        shipping.update(relative.as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
for directory in ('scripts','.github','game/tests'):
    for path in sorted((ROOT/directory).rglob('*')):
        if path.is_file() and not any(part in ('__pycache__','.godot') for part in path.parts) and path.suffix != '.pyc':
            validation.update(path.relative_to(ROOT).as_posix().encode()+b'\0'+path.read_bytes()+b'\0')
check(shipping.hexdigest() == prepared['source']['source_content_sha256'], 'independent shipping digest')
check(validation.hexdigest() == prepared['source']['source_validation_sha256'], 'independent validation digest')
check(git(ROOT,'rev-parse','HEAD:game').decode().strip() == prepared['source']['source_game_tree'], 'independent game tree')
check((ROOT/'docs/reports/media/art-v9/hands/logs/clip_contact.glb.sha256').read_text().split()[0] == sha((ROOT/'game/assets/weapons/relay_ar/relay_ar_arms.glb').read_bytes()), 'hands contact stamp matches shipped GLB')
wrapper = {}
for name in ('run_aggregate.py','archive_originals.py','test_acquisition.py','PREREGISTRATION.md'):
    path = BUILDER / RELATIVE / name; data=path.read_bytes()
    check(data == git(BUILDER,'show',BUILDER_COMMIT+':'+str(RELATIVE/name)), 'wrapper committed bytes: '+name)
    wrapper[name]=dict(bytes=len(data),sha256=sha(data))
engine_bytes = ENGINE.read_bytes(); archive = ENGINE.parent/'godot.zip'
check(sha(engine_bytes) == ENGINE_SHA, 'installed pinned engine SHA256 without executing it')
assignments = {node.targets[0].id:node.value for node in ast.parse((ROOT/'scripts/toolchain.py').read_text()).body
               if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)}
pins = ast.literal_eval(assignments['EDITORS'])
archive_sha512=hashlib.sha512(archive.read_bytes()).hexdigest()
check(archive_sha512 == pins['linux'][2], 'archive SHA512 equals exact source pin')
with zipfile.ZipFile(archive) as bundle:
    check(bundle.read(ENGINE.name) == engine_bytes, 'installed engine equals archive executable member')
backend=Path('/workspace/sightbreak/.venv/bin/python')
check(backend.is_file() and os.access(backend,os.X_OK), 'required catalog interpreter executable exists')
for path in (ROOT/'game/.godot',ROOT/'.local/aggregate-state-r1',ROOT/'builds/aggregate-combined-r1'):
    check(not path.exists(), 'fresh unused runtime path: '+str(path))
check(not list((ROOT/'.local/validation').glob('run-*')), 'no previous runtime aggregate directory')
processes=[]
for path in Path('/proc').iterdir():
    if not path.name.isdigit():
        continue
    try:
        argv=(path/'cmdline').read_bytes();comm=(path/'comm').read_text().strip()
        if comm.lower().startswith('godot') and os.fsencode(str(ROOT)) in argv:
            processes.append(dict(pid=int(path.name),comm=comm,argv_sha256=sha(argv)))
    except (OSError,ValueError):
        pass
sockets=[]
for family in ('tcp','tcp6','udp','udp6'):
    for line in Path('/proc/net',family).read_text().splitlines()[1:]:
        fields=line.split();port=int(fields[1].rsplit(':',1)[1],16)
        if port in PORTS and (family.startswith('udp') or fields[3]=='0A'):
            sockets.append(dict(family=family,port=port,state=fields[3],inode=fields[9]))
check(not processes and not sockets,'independent actual frozen-engine/eight-port preflight empty')
report=dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), passed=not failures, checks=checks,failures=failures,
            expected_source=EXPECTED,builder_commit=BUILDER_COMMIT,inventory=inventory,
            source_game_tree=prepared['source']['source_game_tree'],source_content_sha256=shipping.hexdigest(),
            source_validation_sha256=validation.hexdigest(),validate_sha256=sha((ROOT/'scripts/validate.sh').read_bytes()),
            wrapper=wrapper,engine=dict(path=str(ENGINE),sha256=sha(engine_bytes),archive_sha512=archive_sha512),
            backend=dict(path=str(backend),resolved=str(backend.resolve()),sha256=sha(backend.read_bytes())),
            processes=processes,listeners=sockets,checked_ports=sorted(PORTS),
            scope='Read-only Git/file/archive/proc/socket source setup audit. No engine, validator, helper, OCR, service or CI executed; no signals sent.')
(HERE/'pre-run-source-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('passed','checks','failures')}))
raise SystemExit(bool(failures))
