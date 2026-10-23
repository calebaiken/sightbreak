"""Independent, read-only mobile artifact review; writes only this review directory."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shlex
import shutil
import stat
import struct
import subprocess
import zipfile
from collections import Counter

OUT = Path(__file__).resolve().parent
ROOT = Path('/workspace/sightbreak-v1-mobile6a')
BUILDS = ROOT / 'builds/mobile-preservation'
TOOLS = Path('/workspace/tools')
INSTALL = TOOLS / 'godot-4.7.2'
TEMPLATES = Path('/workspace/sightbreak/.local/data/godot/export_templates/4.7.2.stable')
SDK = TOOLS / 'android-sdk/build-tools/36.0.0'
checks = []
commands = []

def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n')

def digest(path, algorithm='sha256'):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()

def check(name, ok, detail=None, supplemental=False):
    checks.append({'check': name, 'passed': bool(ok), 'detail': detail, 'scope': 'supplemental' if supplemental else 'defined correctness benchmark'})
    print(('PASS ' if ok else 'FAIL ') + name, flush=True)

def run(name, argv, cwd=ROOT, env=None):
    result = subprocess.run(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    (OUT / f'{name}.log').write_bytes(result.stdout)
    commands.append({'label': name, 'cwd': str(cwd), 'argv': [str(s) for s in argv], 'exit_code': result.returncode, 'log': f'{name}.log'})
    save('commands.json', commands)
    check(f'{name} command exit', result.returncode == 0, result.returncode)
    return result.stdout.decode('utf-8', errors='replace')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()

def file_record(path):
    return {'path': path.relative_to(BUILDS).as_posix(), 'bytes': path.stat().st_size,
            'sha256': digest(path), 'mode': stat.S_IMODE(path.stat().st_mode),
            'archive_mode': stat.S_IMODE(path.stat().st_mode) & 0o777}

def canonical_digest(directories, game=False):
    result = hashlib.sha256()
    count = 0
    for directory in directories:
        for path in sorted((ROOT / directory).rglob('*')):
            rel = path.relative_to(ROOT / 'game') if game else path.relative_to(ROOT)
            if not path.is_file():
                continue
            if game and ('.godot' in rel.parts or 'tests' in rel.parts):
                continue
            if not game and (any(p in ('__pycache__', '.godot') for p in path.parts) or path.suffix == '.pyc'):
                continue
            result.update(rel.as_posix().encode() + b'\0' + path.read_bytes() + b'\0')
            count += 1
    return result.hexdigest(), count

def no_developer_paths(names):
    bad = []
    for name in names:
        parts = Path(name.removeprefix('res://')).parts
        if any(p in ('tests', '__pycache__', '.git') or p.startswith('.env') for p in parts) or re.search(r'_test\.(gd|gdc)$', name):
            bad.append(name)
        if Path(name).suffix.lower() in ('.pem', '.key', '.p12', '.pfx', '.keystore', '.mobileprovision'):
            bad.append(name)
    return sorted(set(bad))

def resources(names):
    expected = [('relay_ar.glb-', '.scn'), ('relay_ar_arms.glb-', '.scn'), ('relay_ar_hands.glb-', '.scn')]
    expected += [(f'{name}.png-', '.ctex') for name in ('relay_ar_albedo','relay_ar_normal','relay_ar_orm','relay_ar_arms_albedo','relay_ar_arms_normal','relay_ar_arms_orm')]
    expected += [(f'/{name}', '.gdc') for name in ('state_privacy','snapshot_buffer','movement_prediction','movement_step','peer_lifecycle','reconnect_policy','result_outbox','viewmodel_shading','bot_ai','reload_audio','reload_phases','confirm_sheet')]
    return {prefix+suffix: [n for n in names if prefix in n and n.endswith(suffix)] for prefix,suffix in expected}

def archive_architectures(path):
    """Read every BSD ar member header and Mach-O cputype; no fat-file assumption."""
    counts = Counter()
    other = []
    with path.open('rb') as stream:
        if stream.read(8) != b'!<arch>\n':
            raise ValueError('Expected BSD ar library')
        while header := stream.read(60):
            if len(header) != 60 or header[-2:] != b'`\n':
                raise ValueError('Invalid ar member header')
            name = header[:16].decode().strip()
            size = int(header[48:58])
            start = stream.tell()
            if name.startswith('#1/'):
                name = stream.read(int(name[3:])).rstrip(b'\0').decode()
            data = stream.read(32)
            if data[:4] in (b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe'):
                cpu = struct.unpack_from('<I',data,4)[0]
                counts[hex(cpu)] += 1
            else:
                other.append({'member':name,'magic_hex':data[:4].hex()})
            stream.seek(start+size+(size%2))
    return {'mach_o_cpu_counts':dict(counts),'other_members':other}

started = datetime.datetime.now(datetime.timezone.utc).isoformat()
before_status = git('status', '--porcelain', '--untracked-files=all')
head = git('rev-parse', 'HEAD')
check('frozen source clean at initial inspection', not before_status and head == '6a0d8d5d85b4fb37943903886982f51b4ed230b0', {'head': head, 'status': before_status})
content, content_count = canonical_digest(['game'], game=True)
validation, validation_count = canonical_digest(['scripts','.github','game/tests'])
identity = {'source_commit': head, 'source_game_tree': git('rev-parse','HEAD:game'), 'source_content_sha256': content, 'source_validation_sha256': validation, 'source_dirty': False, 'source_game_dirty': False}
save('source-identity.json', {**identity, 'game_files_hashed': content_count, 'validation_files_hashed': validation_count})
all_payloads = {}
for target in ('android','ios'):
    directory = BUILDS / target
    record = json.loads((directory / 'source.json').read_text())
    check(f'{target} source and completion receipt', all(record.get(k) == v for k,v in identity.items()) and record['export_completed'] and record['version'] == '0.3.3-dev' and record['build_number'] == 6)
    paths = [p for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'source.json' and p.suffix != '.log']
    payloads = [file_record(p) for p in paths]
    all_payloads[target] = payloads
    check(f'{target} payload SHA256, sizes, modes, exact set', payloads == record['payload'] and file_record(BUILDS / record['artifact']['path']) == record['artifact'], {'files': len(payloads), 'bytes': sum(p['bytes'] for p in payloads)})
    check(f'{target} no symlinks or developer files outside resource container', not any(p.is_symlink() for p in directory.rglob('*')) and not no_developer_paths([p.relative_to(directory).as_posix() for p in paths]))
save('payload-inventories.json', all_payloads)

# Pin archival inputs and extracted engine/templates independently; no setup call.
toolchain_text = (ROOT / 'scripts/toolchain.py').read_text()
editor_expected = re.search(r'"Godot_v4\.7\.2-stable_linux\.x86_64", "([a-f0-9]{128})"', toolchain_text)[1]
templates_expected = re.search(r'TEMPLATES_SHA512 = "([a-f0-9]{128})"', toolchain_text)[1]
tool_records = []
for path, expected in [(INSTALL/'godot.zip',editor_expected),(INSTALL/'templates.tpz',templates_expected)]:
    actual = digest(path,'sha512')
    tool_records.append({'path':str(path),'bytes':path.stat().st_size,'sha512':actual,'pinned_sha512':expected})
    check(f'{path.name} pinned SHA512', actual == expected)
with zipfile.ZipFile(INSTALL/'godot.zip') as z:
    binary = INSTALL/'Godot_v4.7.2-stable_linux.x86_64'
    with z.open(binary.name) as stream:
        archived = hashlib.file_digest(stream,'sha256').hexdigest()
    check('installed editor bytes match pinned editor archive', digest(binary) == archived)
with zipfile.ZipFile(INSTALL/'templates.tpz') as z:
    for name in ('android_debug.apk','ios.zip'):
        with z.open('templates/'+name) as stream:
            actual = hashlib.file_digest(stream,'sha256').hexdigest()
        check(f'cached {name} matches pinned template archive', digest(TEMPLATES/name) == actual)
        tool_records.append({'path':str(TEMPLATES/name),'sha256':actual,'bytes':(TEMPLATES/name).stat().st_size})
save('toolchain-hashes.json', tool_records)
version = run('engine-version', [str(binary),'--headless','--version'])
check('engine exact 4.7.2 official identity', version.strip() == '4.7.2.stable.official.ed1daf0bf')

apk = BUILDS/'android/sightbreak-debug.apk'
signature = run('android-signature', [str(SDK/'apksigner'),'verify','--verbose','--print-certs',str(apk)])
check('Android v2 and v3 signature verified with debug certificate', all(s in signature for s in ('Verified using v2 scheme (APK Signature Scheme v2): true','Verified using v3 scheme (APK Signature Scheme v3): true','CN=Android Debug')))
badging = run('android-badging', [str(SDK/'aapt'),'dump','badging',str(apk)])
check('Android package/version/SDK/native architecture badging', all(s in badging for s in ("package: name='com.sightbreak.game'", "versionCode='6'", "versionName='0.3.3-dev'", "sdkVersion:'24'", "targetSdkVersion:'36'", "native-code: 'arm64-v8a' 'x86_64'")))
layout = run('android-manifest', [str(SDK/'aapt'),'dump','xmltree',str(apk),'AndroidManifest.xml'])
check('Android landscape activity and launcher metadata', bool(re.search(r'android:screenOrientation[^\n]*\(type 0x10\)0x0\b',layout)) and all(s in layout for s in ('com.godot.game.GodotAppLauncher','com.godot.game.GodotApp','android.intent.action.MAIN','android.intent.category.LAUNCHER')))
launcher = layout.split('E: activity-alias',1)[1].split('E: meta-data',1)[0]
check('Android launcher alias exported and application debuggable', bool(re.search(r'android:exported[^\n]*0xffffffff',launcher)) and 'application-debuggable' in badging)
check('Android network permissions', all(s in layout for s in ('android.permission.INTERNET','android.permission.ACCESS_NETWORK_STATE')))
run('android-zipalign', [str(SDK/'zipalign'),'-c','-P','16','-v','4',str(apk)])
apk_inventory = []
native = []
with zipfile.ZipFile(apk) as archive, zipfile.ZipFile(TEMPLATES/'android_debug.apk') as template:
    check('APK ZIP CRC integrity and unique names', archive.testzip() is None and len(archive.namelist()) == len(set(archive.namelist())))
    for info in archive.infolist():
        data = archive.read(info)
        apk_inventory.append({'path':info.filename,'bytes':info.file_size,'sha256':hashlib.sha256(data).hexdigest()})
        if info.filename.startswith('lib/') and not info.is_dir():
            arch = info.filename.split('/')[1]
            elf_machine = struct.unpack_from('<H',data,18)[0]
            matches_template = hashlib.sha256(data).digest() == hashlib.sha256(template.read(info.filename)).digest()
            native.append({'path':info.filename,'elf_class':data[4],'machine':elf_machine,'template_match':matches_template})
            check(f'Android native {info.filename}', data[:5] == b'\x7fELF\x02' and elf_machine == {'arm64-v8a':183,'x86_64':62}.get(arch) and matches_template)
    names = [p['path'] for p in apk_inventory if p['path'].startswith('assets/')]
    selected = resources(names)
    check('Android imported models, textures, compiled integration modules', all(selected.values()), {'assets':len(names)})
    check('Android no test or credential resources', not no_developer_paths(archive.namelist()))
    check('Android exact requested native architecture set', {n['path'].split('/')[1] for n in native} == {'arm64-v8a','x86_64'})
    android_resources = names
save('android-entry-inventory.json', apk_inventory)
save('android-native-and-resources.json', {'native':native,'required_resources':selected,'asset_count':len(android_resources)})

ios = BUILDS/'ios'
pck = ios/'sightbreak.pck'
pck_entries = []
with pck.open('rb') as stream:
    magic,fmt,major,minor,patch,flags,base = struct.unpack('<6IQ',stream.read(32))
    directory, = struct.unpack('<Q',stream.read(8))
    check('iOS PCK header declares engine 4.7.2, readable directory', magic == 0x43504447 and fmt == 4 and (major,minor,patch) == (4,7,2) and not flags&1)
    stream.seek(directory)
    count, = struct.unpack('<I',stream.read(4))
    for _ in range(count):
        length, = struct.unpack('<I',stream.read(4))
        name = stream.read(length).rstrip(b'\0').decode()
        offset,size,md5,entry_flags = struct.unpack('<QQ16sI',stream.read(36))
        resume = stream.tell()
        absolute = (base if flags&2 else 0) + offset
        stream.seek(absolute)
        data = stream.read(size)
        pck_entries.append({'path':name,'offset':absolute,'bytes':size,'sha256':hashlib.sha256(data).hexdigest(),'md5':md5.hex(),'md5_match':hashlib.md5(data).digest()==md5,'entry_flags':entry_flags})
        stream.seek(resume)
check('iOS every PCK resource size, bounds, MD5 and unique path', all(e['md5_match'] and e['offset']+e['bytes'] <= pck.stat().st_size and not e['entry_flags']&1 for e in pck_entries) and len(pck_entries) == len({e['path'] for e in pck_entries}), {'resources':len(pck_entries)})
ios_names = [e['path'] for e in pck_entries]
check('iOS imported models, textures, compiled integration modules', all(resources(ios_names).values()))
check('iOS no test or credential resources', not no_developer_paths(ios_names))
save('ios-pck-inventory.json', pck_entries)
android_by_name = {e['path'].removeprefix('assets/'):e for e in apk_inventory if e['path'].startswith('assets/')}
ios_by_name = {e['path'].removeprefix('res://'):e for e in pck_entries}
compiled = sorted(p for p in ios_by_name if p.endswith('.gdc'))
check('compiled gameplay modules byte-identical across Android and iOS', compiled and all(p in android_by_name and android_by_name[p]['sha256'] == ios_by_name[p]['sha256'] for p in compiled), {'compiled_script_count':len(compiled)})
save('cross-platform-resources.json', {'android_only':sorted(android_by_name.keys()-ios_by_name.keys()),'ios_only':sorted(ios_by_name.keys()-android_by_name.keys()),'compiled_script_count':len(compiled),'different_common_resources':sorted(p for p in android_by_name.keys()&ios_by_name.keys() if android_by_name[p]['sha256'] != ios_by_name[p]['sha256'])})

plist = plistlib.loads((ios/'sightbreak/sightbreak-Info.plist').read_bytes())
pbx = (ios/'sightbreak.xcodeproj/project.pbxproj').read_text()
options = plistlib.loads((ios/'sightbreak/export_options.plist').read_bytes())
entitlements = plistlib.loads((ios/'sightbreak/sightbreak.entitlements').read_bytes())
framework = plistlib.loads((ios/'sightbreak.xcframework/Info.plist').read_bytes())
check('iOS landscape phone and iPad metadata and local network explanation', all(plist.get(k) and all('Landscape' in s for s in plist[k]) for k in ('UISupportedInterfaceOrientations','UISupportedInterfaceOrientations~ipad')) and bool(plist.get('NSLocalNetworkUsageDescription')))
check('iOS bundle/build/version/minimum OS/device platform metadata', plist['CFBundleIdentifier'] == '$(PRODUCT_BUNDLE_IDENTIFIER)' and all(s in pbx for s in ('PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;', 'MARKETING_VERSION = 0.3.3;', 'CURRENT_PROJECT_VERSION = 6;', 'IPHONEOS_DEPLOYMENT_TARGET = 15.0;', 'SDKROOT = iphoneos;', 'TARGETED_DEVICE_FAMILY = "1,2";')))
teams = re.findall(r'DEVELOPMENT_TEAM\s*=\s*([^;]*);',pbx)
profiles = re.findall(r'PROVISIONING_PROFILE(?:_SPECIFIER)?\s*=\s*([^;]*);',pbx)
selectors = sorted(set(re.findall(r'CODE_SIGN_IDENTITY\s*=\s*([^;]*);',pbx)))
check('iOS no assigned team, profile or sentinel', teams and all(s.strip() == '""' for s in teams+profiles) and 'UNSIGNED00' not in pbx and options.get('teamID') == '' and all(v == '' for v in options.get('provisioningProfiles',{}).values()) and not no_developer_paths([p.as_posix() for p in ios.rglob('*')]))
check('iOS generic signing selectors only', set(selectors) == {'"Apple Development"','"Apple Distribution"'}, selectors)
check('iOS no IPA, built app or signing material', not any(p.suffix.lower() in ('.ipa','.app','.mobileprovision','.p12','.pfx','.key','.pem') or p.name == '_CodeSignature' for p in ios.rglob('*')))
template_hashes = []
archive_architecture_records = {}
with zipfile.ZipFile(TEMPLATES/'ios.zip') as template:
    template_framework = plistlib.loads(template.read('libgodot.ios.debug.xcframework/Info.plist'))
    for library in sorted((ios/'sightbreak.xcframework').rglob('libgodot.a')):
        relative = library.relative_to(ios/'sightbreak.xcframework').as_posix()
        template_name = 'libgodot.ios.debug.xcframework/'+relative
        with template.open(template_name) as stream:
            template_sha = hashlib.file_digest(stream,'sha256').hexdigest()
        check(f'iOS debug engine library {relative} matches pinned template', digest(library)==template_sha)
        template_hashes.append({'path':str(library.relative_to(ios)),'sha256':template_sha,'template_entry':template_name})
        architectures = archive_architectures(library)
        archive_architecture_records[relative] = architectures
        if relative.startswith('ios-arm64/'):
            check('iOS device archive every Mach-O object arm64', set(architectures['mach_o_cpu_counts']) == {'0x100000c'} and [v['member'] for v in architectures['other_members']] == ['__.SYMDEF'], architectures)
        else:
            check('iOS simulator archive matches both declared architectures', set(architectures['mach_o_cpu_counts']) == {'0x1000007','0x100000c'}, architectures, supplemental=True)
save('ios-metadata.json', {'Info.plist':plist,'export_options.plist':options,'entitlements':entitlements,'xcframework':framework,'pinned_template_xcframework':template_framework,'signing_selector_strings':selectors,'development_team_values':teams,'provisioning_profile_values':profiles,'engine_template_matches':template_hashes,'static_archive_members':archive_architecture_records})
check('iOS XCFramework iOS device arm64 and simulator arm64/x86_64 declarations', len(framework['AvailableLibraries']) == 2 and any(s['SupportedPlatform']=='ios' and s['SupportedArchitectures']==['arm64'] and not s.get('SupportedPlatformVariant') for s in framework['AvailableLibraries']) and any(s['SupportedPlatform']=='ios' and set(s['SupportedArchitectures'])=={'arm64','x86_64'} and s.get('SupportedPlatformVariant')=='simulator' for s in framework['AvailableLibraries']))

# Independently inspect retained logs; warnings remain visible in the summary.
log_records = []
for path in sorted(BUILDS.rglob('*.log')):
    text = path.read_text(errors='replace')
    warnings = [line for line in text.splitlines() if 'WARNING:' in line]
    errors = [line for line in text.splitlines() if re.search(r'(?:SCRIPT ERROR:|^ERROR:|Traceback \(most recent call last\)|Parse Error:)',line)]
    log_records.append({'path':path.relative_to(BUILDS).as_posix(),'bytes':path.stat().st_size,'sha256':digest(path),'warnings':warnings,'error_lines':errors})
check('retained import/export/inspection logs have no engine or Python errors', not any(r['error_lines'] for r in log_records))
save('builder-log-review.json',log_records)
for target in ('android','ios'):
    shutil.copyfile(BUILDS/target/'source.json',OUT/f'{target}-source-receipt.json')
for name in ('results.json','android-signature.log','android-manifest.log','android-layout.log'):
    shutil.copyfile(BUILDS/'verification'/name,OUT/f'builder-{name}')

benchmark_environment = dict(os.environ)
benchmark_environment['SIGHTBREAK_BUILDS_DIR'] = str(BUILDS)
benchmark_environment['PYTHONDONTWRITEBYTECODE'] = '1'
benchmark_code = """import sys,zipfile
sys.path.insert(0,'scripts')
import build_manifest as b
import verify_builds as v
for target in ('android','ios'):
    b.validate_record(target)
    if target == 'android':
        with zipfile.ZipFile(b.BUILDS/'android/sightbreak-debug.apk') as z:
            paths=[n for n in z.namelist() if n.startswith('assets/')]
    else:
        paths=v.packed_paths(b.BUILDS/'ios/sightbreak.pck')
    v.no_test_harnesses(paths)
    v.integrated_resources(paths)
    print(target, 'frozen validate_record/no_test_harnesses/integrated_resources PASS',len(paths))
"""
run('frozen-benchmark-readback', ['python3','-c',benchmark_code], env=benchmark_environment)

check('source checkout still clean and frozen at conclusion', git('rev-parse','HEAD') == head and git('status','--porcelain','--untracked-files=all') == before_status)
summary = {'started_at_utc':started,'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':identity,'benchmark':'Frozen source build_manifest.py source/payload contract, export_presets.cfg and verify_builds.py Android/iOS correctness criteria; independently recomputed with added native/template/PCK integrity checks. No presentation benchmark or visual score applies.','checks':checks,'defined_benchmark_passed':all(c['passed'] for c in checks if c['scope'] == 'defined correctness benchmark'),'passed':all(c['passed'] for c in checks),'limitations':['No physical Android installation, launch, play, performance, touch, suspend/resume or LAN permission observation.','No macOS/Xcode compiler, iOS compilation, IPA, signing, installation, launch or play.','No archive packaging/reproducibility claim; inspected preserved debug APK and Xcode project export tree.','APK debug certificate is public test identity; iOS generic Apple Development/Distribution selector strings are present but no actual team/profile/private identity is bundled.','Review binds source6a0d8d5 only; later source requires its own exports and verification.']}
save('inspection-results.json',summary)
raise SystemExit(0 if summary['passed'] else 1)
