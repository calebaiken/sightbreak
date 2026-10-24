"""Replay static/data gates from frozen source; no project imports or processes."""
import array
import ast
import csv
import hashlib
import io
import json
import math
from pathlib import PurePosixPath
import plistlib
import re
import shlex
import stat
import statistics
import struct
import wave
import zipfile

from inspect import EVIDENCE, FROZEN, OUT, git, sha, write, dump
from audit_data import log_failed

SOURCE = json.loads((OUT/'source-object-audit.json').read_bytes())
IDENTITY = SOURCE['identity']
F = {r['path']: r for r in SOURCE['files']}
BUILD_SOURCE = {'source_commit': FROZEN, 'source_game_tree': IDENTITY['game_tree'],
                'source_content_sha256': IDENTITY['runtime_content_sha256'],
                'source_validation_sha256': IDENTITY['content_sha256'],
                'source_game_dirty': False, 'source_dirty': False}
SNAPSHOT = {'commit': FROZEN, 'game_tree': IDENTITY['game_tree'], 'dirty': False, 'status': '',
            'content_sha256': IDENTITY['content_sha256'],
            'source_paths': ['game','scripts','backend','server','.github','.gitignore','README.md'], 'source_files': 362}
ARCHIVES = json.loads((OUT/'archive-byte-audit.json').read_bytes())
OUTER = {k: {r['member']: r for r in v['members']} for k,v in ARCHIVES.items()}

def j(z, name):
    return json.loads(z.read(name))

def clean_receipt(value, code=0):
    return value.get('complete') is True and type(value.get('exit')) is int and value['exit'] == code and value.get('errors') == [] and value.get('posix_cleanup_verified') is True

def matrix_audit():
    with zipfile.ZipFile(EVIDENCE/'artifact-12470739875.zip') as z:
        prefix = 'builds/v3-matrix/'
        d = j(z,prefix+'summary.json')
        assert d['commit'] == FROZEN and d['dirty'] is False and d['source'] == BUILD_SOURCE and d['validation_source'] == SNAPSHOT
        expected = []
        for line in (OUT/'frozen/scripts/validate.sh').read_text().splitlines():
            m = re.search(r'^(\s*)run_godot (\S+) (.+)$', line)
            if m:
                expected.append((m[2], ['GODOT', *shlex.split(m[3])]))
            elif line.startswith('SIGHTBREAK_STATE_DIR=') and 'run_godot profile ' in line:
                expected.append(('profile', ['GODOT','--headless','--script','res://tests/profile_test.gd']))
        expected += [
            ('account-output-unit',['PYTHON','scripts/test_account_network_output.py']),
            ('worker-unit',['PYTHON','-m','unittest','discover','-s','server/tests','-v']),
            ('network',['bash','scripts/test_network.sh']),
            ('network-soak',['PYTHON','scripts/test_network_soak.py','--out','ROOT/builds/v3-matrix/soak']),
            ('network-soak-ten',['PYTHON','scripts/test_network_soak.py','--clients','10','--port','29840','--out','ROOT/builds/v3-matrix/soak-ten']),
            ('connection-lifecycle',['PYTHON','scripts/test_connection_lifecycle.py','--out','ROOT/builds/v3-matrix/connections']),
        ]
        for label, script in [('bridge-transport','test_bridge_transport.py'),('build-manifest','test_build_manifest.py'),
                              ('matrix-harness-unit','test_validate_matrix.py'),('matrix-process-unit','test_matrix_process.py'),
                              ('source-identity-unit','test_source_identity.py'),('verifier-unit','test_verify_builds.py'),
                              ('network-harness-unit','test_godot_process.py'),('offline-hud-unit','test_offline_hud.py'),
                              ('export-ui-unit','test_export_ui.py'),('export-flow-unit','test_export_flow.py'),
                              ('negative-audio-harness-unit','test_reload_negative_controls.py'),('reload-contact','test_reload_contact.py')]:
            expected.append((label,['PYTHON','scripts/'+script]))
        expected += [('protocol-matrix',['bash','scripts/test_protocol_compat.sh','ROOT/builds/v3-matrix/protocol']),
                     ('hostile-handshake',['bash','scripts/test_handshake_hardening.sh','ROOT/builds/v3-matrix/handshake']),
                     ('catalog-fixture',['PYTHON','scripts/export_catalog_fixture.py','--check']),
                     ('postgresql',['PYTHON','-m','pytest','backend/tests','-q'])]
        for label, script in [('account-protocol','test_account_isolated.py'),('account-capacity','test_admission_capacity.py'),
                              ('outbox-crash','test_result_outbox.py'),('native-economy','test_native_economy.py')]:
            expected.append((label,['PYTHON','scripts/'+script]))
        expected += [('account-full-reconnect',['PYTHON','scripts/test_full_account_reconnect.py','--out','ROOT/builds/v3-matrix/account-full-reconnect']),
                     ('economy-conservation',['PYTHON','backend/simulate.py']),
                     ('native-render-lifecycle',['bash','scripts/test_render.sh']),
                     ('native-hud-overflow',['GODOT','--audio-driver','Dummy','--script','res://tests/hud_overflow_test.gd']),
                     ('native-paint-visibility',['GODOT','--audio-driver','Dummy','--script','res://tests/paint_visibility_test.gd']),
                     ('nested-resource-cleanup',None),('frozen-source-identity',None)]
        assert len(expected) == len(d['checks']) == 83
        rows = []
        for (name, wanted), row in zip(expected, d['checks'], strict=True):
            assert row['name'] == name and row['source_commit'] == FROZEN
            raw = z.read(prefix+row['log'])
            result = {'name': name, 'recorded_passed': row['passed'], 'log_sha256': sha(raw), 'log': prefix+row['log'], 'inventory_matches_frozen_source': True}
            if wanted is not None:
                command = [x.replace('/home/runner/work/sightbreak/sightbreak','ROOT') for x in row['command']]
                command[0] = 'GODOT' if command[0] == 'ROOT/scripts/godot.sh' else 'PYTHON' if command[0] == 'ROOT/.venv/bin/python' else command[0]
                assert command == wanted, (name,command,wanted)
                receipt = j(z,prefix+name+'.process.json')
                assert clean_receipt(receipt,row['exit'])
                gate = log_failed(raw.decode(errors='replace')) or 'HARNESS_ERROR' in raw.decode(errors='replace')
                assert gate == row['logged_errors'] and row['passed'] == (row['exit'] == 0 and not gate)
                result.update({'command_matches': True, 'exit': row['exit'], 'log_gate': gate, 'process_receipt_complete_clean': True, 'recomputed_passed': row['passed']})
            rows.append(result)
        identity = j(z,prefix+'source-identity.json')
        assert identity == {'before': BUILD_SOURCE, 'after': BUILD_SOURCE, 'validation_before': SNAPSHOT,
                            'validation_after': SNAPSHOT, 'initial_dirty': False,'final_dirty': False,'failures': []}
        assert j(z,prefix+'nested-resource-cleanup.json') == {'source_commit': FROZEN,'leaked_logs': []}
        nested = []
        for name in z.namelist():
            if not name.startswith(prefix) or not name.endswith('.log'):
                continue
            text = z.read(name).decode(errors='replace')
            assert not re.search(r'ObjectDB.*leaked|Leaked instance',text)
            if log_failed(text):
                nested.append({'member':name,'error_lines':re.findall(r'^(?:ERROR:|SCRIPT ERROR).*',text,re.M),
                               'classification':'actual failed Python unit group' if name.endswith('matrix-harness-unit.log') else 'intentional mixed-version pre-handshake rejection context; not a new runtime regression verdict'})
        assert {r['name'] for r in rows if not r['recorded_passed']} == {'matrix-harness-unit'}
        dump('matrix-audit.json', {'source': SNAPSHOT,'groups':83,'passed':82,'failed':1,'rows':rows,
                                  'all_81_process_receipts_clean_complete':True,'source_before_after_match':True,
                                  'nested_log_error_context':nested,
                                  'unit_failure':'18 tests: two StopIteration errors, one Windows-only skip; subprocess.check_output mocking intercepts platform.processor probe. No rerun or waiver.'})
        print('MATRIX audited 83 rows, 82 pass, 1 fail, 81 process receipts')

def campaign_audit():
    with zipfile.ZipFile(EVIDENCE/'artifact-12470739875.zip') as z:
        prefix = 'builds/v3-network/'
        campaign = j(z,prefix+'campaign.json')
        conditions = [(f'rtt-{r}',{'rtt_ms':r},['--rtt-ms',str(r)]) for r in (0,50,100,150,200)]
        impaired = {'rtt_ms':100,'jitter_ms':20,'loss':.03,'reorder':.05}
        args = ['--rtt-ms','100','--jitter-ms','20','--loss','0.03','--reorder','0.05']
        conditions += [('jitter',{'rtt_ms':100,'jitter_ms':20},['--rtt-ms','100','--jitter-ms','20']),
                       ('loss',{'rtt_ms':100,'loss':.03},['--rtt-ms','100','--loss','0.03']),
                       ('reorder',{'rtt_ms':100,'reorder':.05},['--rtt-ms','100','--reorder','0.05']),
                       ('impaired',impaired,args),('blackout',{'rtt_ms':100,'blackout_at':4,'blackout_seconds':2},['--rtt-ms','100','--blackout-at','4','--blackout-seconds','2']),
                       ('reconnect',{**impaired,'blackout_at':4,'blackout_seconds':2,'reconnect_at':8},[*args,'--blackout-at','4','--blackout-seconds','2','--reconnect-at','8']),
                       ('prediction-disabled',{'rtt_ms':100,'no_prediction':True},['--rtt-ms','100','--no-prediction'])]
        rows = []
        assert len(campaign) == len(conditions) == 12
        root = '/home/runner/work/sightbreak/sightbreak'
        for index, (row,(name, extra, argv)) in enumerate(zip(campaign,conditions,strict=True)):
            assert row['name'] == name and row['exit'] == 0 and row['passed'] is True and row['failures'] == []
            expected_cmd = [root+'/.venv/bin/python',root+'/scripts/simulate_network.py','--clients','10','--seconds','18.0','--port',str(39000+20*index),'--reconnect-delay','2','--out',root+'/builds/v3-network/'+name,*argv]
            assert row['command'] == expected_cmd
            summary = j(z,prefix+name+'/summary.json')
            assert row['summary'] == summary and summary['passed'] is True and summary['failures'] == [] and summary['source_unchanged'] is True
            assert row['source_before'] == row['source_after'] == summary['source_before'] == summary['source_after'] == SNAPSHOT
            assert {k:summary['source'][k] for k in SNAPSHOT} == SNAPSHOT
            expected_conditions = {'rtt_ms':0,'jitter_ms':0,'loss':0,'reorder':0,'clients':10,'seconds':18.0,'seed':7301,
                                   'port':39000+20*index,'out':root+'/builds/v3-network/'+name,'no_prediction':False,
                                   'account_tickets':False,'render_client':-1,'blackout_at':-1,'blackout_seconds':0,'reconnect_at':-1,'reconnect_delay':2.0,**extra}
            assert summary['conditions'] == expected_conditions
            receipt = j(z,prefix+name+'.process.json')
            assert clean_receipt(receipt)
            assert summary['measurement_duration_seconds'] == 18 and summary['shared_stop_reached'] is True
            children, reports = [], {}
            for role in ['server',*[f'client-{n}' for n in range(10)]]:
                member = prefix+name+'/'+role+'.json'
                raw = z.read(member)
                data = json.loads(raw)
                reports[role] = data
                log = z.read(prefix+name+'/'+role+'.log').decode()
                assert not log_failed(log) and 'HARNESS_ERROR' not in log and 'ERROR:' not in log and 'SCRIPT ERROR' not in log
                marker = re.findall(r'^NETWORK_SIMULATION (\{.*\})$',log,re.M)
                assert len(marker) == 1 and log.startswith('Godot Engine v4.7.2.stable.official.ed1daf0bf')
                log_result = json.loads(marker[0])
                assert data['role'] == log_result['role'] == ('server' if role == 'server' else 'client')
                for key in ('joined','last_snapshot_age_seconds','max_displacement'):
                    assert data[key] == log_result[key]
                assert data['snapshots'] == log_result['snapshots']
                # Godot JSON serializes the large epoch with fewer decimal digits
                # than Python. Preserve and disclose the delta; do not call it exact.
                epoch_delta = data['measurement_start_epoch'] - summary['measurement_start_epoch']
                assert abs(epoch_delta) <= .000006
                assert data['wall_elapsed_seconds'] >= 18 and data['measurement_stop_lateness_seconds'] >= 0
                gates = {}
                if role != 'server':
                    gates = {'joined':data['joined'] is True,'connected':data['state']=='connected',
                             'received_fresh':data['last_snapshot_age_seconds']<.750,'received_count':data['snapshots']>=10,
                             'moved':data['max_displacement']>.1,'accepted_count':data['accepted_snapshots']>=10,
                             'accepted_fresh':data['last_accepted_age_seconds']<.750,
                             'reconnect_identity':name!='reconnect' or data['reconnect_passed'] is True,
                             'prediction_setting':data['prediction_enabled'] == (name!='prediction-disabled')}
                    assert all(gates.values()), (name,role,gates)
                    assert data['render_metrics']['native'] is False
                    if name == 'reconnect':
                        assert data['reconnect_requested'] is True and data['initial_id'] == data['final_id']
                children.append({'role':role,'member':member,'raw_sha256':sha(raw),'raw_bytes':len(raw),'native_log_matches_report':True,
                                 'gates':gates,'wall_elapsed_seconds':data['wall_elapsed_seconds'],
                                 'start_offset_seconds':data['measurement_start_offset_seconds'],
                                 'serialized_epoch_delta_seconds':epoch_delta,
                                 'stop_lateness_seconds':data['measurement_stop_lateness_seconds'],
                                 **{k:data[k] for k in ('joined','state','snapshots','last_snapshot_age_seconds','accepted_snapshots','last_accepted_age_seconds','max_displacement','reconnect_passed','initial_id','final_id','recovery_seconds')}})
            server = reports['server']
            occupancy = server['occupancy']
            assert occupancy
            for occ in occupancy:
                ids = [v['actor'] for v in occ['bindings']]
                assert len(occ['enet'])<=10 and len(ids)<=10 and len(set(ids))==len(ids)
            last = occupancy[-1]['bindings']
            assert len(last) == 10 and all(b['idle_msec']<750 and b['input_ack']>=10 for b in last)
            assert summary['final_authority'] == last
            assert summary['max_enet_occupancy'] == max(len(v['enet']) for v in occupancy)
            assert len(summary['processes']) == 11 and len(summary['per_client_traffic']) == 10
            for direction in ('up','down'):
                for key,value in summary['traffic'][direction].items():
                    vals = [r[direction][key] for r in summary['per_client_traffic']]
                    assert value == (max(vals) if key == 'max_datagram_bytes' else sum(vals))
            wrapper_log = z.read(prefix+name+'.log').decode()
            assert json.loads(wrapper_log) == summary and not log_failed(wrapper_log) and 'HARNESS_ERROR' not in wrapper_log
            rows.append({'name':name,'conditions':expected_conditions,'recorded_passed':True,'independent_data_gates_passed':True,
                         'outer_process_receipt':receipt,'source_before_after_match':True,'server_capacity_and_fresh_authority':True,
                         'measurement_start_epoch':summary['measurement_start_epoch'],'traffic_window_seconds':summary['traffic_window_seconds'],
                         'children':children,'traffic':summary['traffic'],
                         'largest_child_stop_lateness_seconds':max(r['stop_lateness_seconds'] for r in children),
                         'child_exit_evidence':'No individual Godot exit-code receipts retained. Frozen simulate_network.py:209-221 gates poll()!=0 and logs after cleanup; outer complete exit-0 receipt and empty failures corroborate, not an independent runtime replay.'})
        final = j(z,prefix+'source.json')
        assert final == {'source_before':SNAPSHOT,'source_after':SNAPSHOT,'source_unchanged':True,'passed':True,'failures':[]}
        dump('campaign-audit.json',{'conditions':12,'clients_per_condition':10,'measurement_seconds_each':18,'native_child_report_pairs':132,
                                    'client_report_pairs':120,'conditions_audit':rows,'final_source_gate':final,
                                    'serialized_epoch_comparison':'Godot child epoch decimals differ from Python proxy epoch by at most 6 microseconds; delta retained per child, not claimed byte/numeric-exact.',
                                    'limits':'Headless guest loopback impairment fixture; no physical WAN/cellular/touch/rendered frame-rate or sustained full-match claim.'})
        print('CAMPAIGN audited 12 x 10 clients x 18s; 132 child reports/logs; gates match')

def pck_paths(data, embedded=False):
    stream = io.BytesIO(data)
    start = 0
    if embedded:
        stream.seek(-12,2)
        size, magic = struct.unpack('<QI',stream.read(12))
        assert magic == 0x43504447
        start = len(data)-12-size
        stream.seek(start)
    magic,version,major,minor,patch,flags,base = struct.unpack('<6IQ',stream.read(32))
    assert magic == 0x43504447 and version in (3,4) and not flags&1
    directory, = struct.unpack('<Q',stream.read(8))
    stream.seek(start+directory)
    count, = struct.unpack('<I',stream.read(4))
    names = []
    for _ in range(count):
        size, = struct.unpack('<I',stream.read(4))
        names.append(stream.read(size).rstrip(b'\0').decode())
        stream.seek(36,1)
    return names

def integrated(paths):
    assert paths and not any('tests/' in p or '_test.gdc' in p for p in paths)
    for b in ('relay_ar.glb-','relay_ar_arms.glb-','relay_ar_hands.glb-'):
        assert any(b in p and p.endswith('.scn') for p in paths)
    for b in ('relay_ar_albedo.png-','relay_ar_normal.png-','relay_ar_orm.png-',
              'relay_ar_arms_albedo.png-','relay_ar_arms_normal.png-','relay_ar_arms_orm.png-'):
        assert any(b in p and p.endswith('.ctex') for p in paths)
    for b in ('state_privacy','snapshot_buffer','movement_prediction','movement_step','peer_lifecycle','reconnect_policy','result_outbox','viewmodel_shading','bot_ai','reload_audio','reload_phases','confirm_sheet'):
        assert any(p.endswith('/'+b+'.gdc') for p in paths)

def packages_audit():
    name = 'artifact-12470681259.zip'
    with zipfile.ZipFile(EVIDENCE/name) as z:
        manifest = j(z,'manifest.json')
        assert z.read('manifest.json') == z.read('packaging.json')
        assert all(manifest[k]==v for k,v in BUILD_SOURCE.items())
        assert (manifest['game'],manifest['version'],manifest['engine'],manifest['build_type']) == ('SIGHTBREAK','0.3.2-dev','Godot 4.7.2','debug')
        checksums = {}
        for line in z.read('checksums.txt').decode().splitlines():
            digest,path = line.split('  ',1)
            assert path not in checksums
            checksums[path] = digest
        assert checksums == {a['path']:a['sha256'] for a in manifest['artifacts']}
        for artifact in manifest['artifacts']:
            path = artifact['path']
            physical = path if path in OUTER[name] else 'v3-package-verification/extracted/'+path
            actual = OUTER[name][physical]
            assert actual['bytes']==artifact['bytes'] and actual['sha256']==artifact['sha256']
        native = j(z,'verification/results.json')
        packaged = j(z,'v3-package-verification/results.json')
        for prefix,report in [('verification/',native),('v3-package-verification/',packaged)]:
            assert report['passed'] is True and report['completed'] is True and report['status']=='passed' and report['failures']==[]
            assert report['source_before']==report['source_after']==BUILD_SOURCE and report['source_unchanged'] is True
            for process in report['processes']:
                assert process['passed'] is True and process['exit']==0 and process['failures']==[] and process['timed_out'] is False
                receipt = j(z,prefix+process['process_receipt'])
                assert receipt == process['receipt'] and clean_receipt(receipt)
                text = z.read(prefix+process['log']).decode()
                assert not log_failed(text) and 'HARNESS_ERROR' not in text
                if 'menu' in process['label'] or 'wrapper' in process['label']:
                    assert 'SIGHTBREAK_MAIN_READY screen=menu' in text
            for field in ('physical_device_installation','device_performance','xcode_build'):
                assert report[field]=='NOT TESTED'
        assert native['export_receipts'] == {r['target']:r for r in manifest['exports']}
        assert packaged['artifact_source']==manifest and packaged['manifest_sha256']==sha(z.read('manifest.json')) and packaged['checksums_sha256']==sha(z.read('checksums.txt'))
        rows,resources = [],{}
        for record in manifest['exports']:
            target = record['target']
            assert all(record[k]==v for k,v in BUILD_SOURCE.items()) and record['export_completed'] is True
            receipt_bytes = z.read(target+'/source.json')
            assert json.loads(receipt_bytes)==record
            expected = {p['path']:p for p in record['payload']}
            expected[target+'/source.json'] = {'path':target+'/source.json','bytes':len(receipt_bytes),'sha256':sha(receipt_bytes),'mode':0o644}
            archive_name = f"sightbreak-{target}-{'xcode-project' if target=='ios' else 'debug'}.zip"
            raw = z.read(archive_name)
            assert sha(raw)==checksums[archive_name]
            mem = {}
            with zipfile.ZipFile(io.BytesIO(raw)) as inner:
                entries = inner.infolist()
                assert len(entries)==len(set(inner.namelist())) and set(inner.namelist())==set(expected)
                for item in entries:
                    path = PurePosixPath(item.filename)
                    assert item.orig_filename==item.filename and '\\' not in item.filename and ':' not in item.filename and not path.is_absolute()
                    assert path.as_posix()==item.filename and path.parts[0]==target and all(v not in ('.','..') for v in path.parts)
                    assert not item.is_dir() and item.create_system==3 and stat.S_ISREG(item.external_attr>>16)
                    exp=expected[item.filename]
                    assert stat.S_IMODE(item.external_attr>>16)==exp['mode']
                    h,size=hashlib.sha256(),0
                    keep = item.filename.endswith(('.pck','.x86_64','.apk','.plist','project.pbxproj','.sh','source.json'))
                    chunks=[]
                    with inner.open(item) as stream:
                        while chunk:=stream.read(1024*1024):
                            h.update(chunk); size+=len(chunk)
                            if keep: chunks.append(chunk)
                    assert size==exp['bytes'] and h.hexdigest()==exp['sha256']
                    extracted = OUTER[name]['v3-package-verification/extracted/'+item.filename]
                    assert extracted['bytes']==size and extracted['sha256']==h.hexdigest()
                    if keep: mem[item.filename]=b''.join(chunks)
                    rows.append({'archive':archive_name,**exp,'posix_mode':oct(exp['mode']),'regular_file':True,'crc_bytes_hash_mode_match':True,'outer_extracted_bytes_match':True})
                assert inner.read(target+'/source.json')==receipt_bytes
            assert packaged['archives_verified'][target]['members']==list(expected.values())
            assert all(packaged['archives_verified'][target][k] is True for k in ('byte_hashes_verified','archive_modes_verified','extracted_modes_verified'))
            if target=='linux':
                data=mem['linux/sightbreak.x86_64']
                assert data[:6]==b'\x7fELF\x02\x01' and struct.unpack('<HH',data[16:20])[0] in (2,3) and struct.unpack('<HH',data[16:20])[1]==62
                paths=pck_paths(data,True); integrated(paths); resources['linux']=paths
                assert expected['linux/sightbreak.x86_64']['mode']==expected['linux/sightbreak.sh']['mode']==0o755
                resources['linux_wrapper_text']=mem['linux/sightbreak.sh'].decode()
                write('inner-receipts/linux-console-wrapper.sh.txt',mem['linux/sightbreak.sh'])
            if target=='android':
                apk=mem['android/sightbreak-debug.apk']
                assert sha(apk)==OUTER[name]['android/sightbreak-debug.apk']['sha256']
                with zipfile.ZipFile(io.BytesIO(apk)) as az:
                    assets=[n for n in az.namelist() if n.startswith('assets/')]
                    integrated(assets); resources['android']=assets
                    resources['android_library_abis']=sorted({PurePosixPath(n).parts[1] for n in az.namelist() if n.startswith('lib/') and n.endswith('.so')})
                sig=z.read('verification/android-signature.log').decode()
                assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in sig and 'Verified using v3 scheme (APK Signature Scheme v3): true' in sig
                badging=z.read('verification/android-manifest.log').decode()
                for want in ("package: name='com.sightbreak.game'","versionCode='5'","versionName='0.3.2-dev'","sdkVersion:'24'","targetSdkVersion:'36'","'arm64-v8a'","'x86_64'"):
                    assert want in badging
            if target=='ios':
                paths=pck_paths(mem['ios/sightbreak.pck']);integrated(paths);resources['ios']=paths
                plist=plistlib.loads(mem['ios/sightbreak/sightbreak-Info.plist'])
                assert plist['CFBundleIdentifier']=='$(PRODUCT_BUNDLE_IDENTIFIER)' and plist['NSLocalNetworkUsageDescription'] and plist['UISupportedInterfaceOrientations']
                assert all('Landscape' in v for v in plist['UISupportedInterfaceOrientations'])
                project=mem['ios/sightbreak.xcodeproj/project.pbxproj'].decode()
                for want in ('DEVELOPMENT_TEAM = "";','PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;','MARKETING_VERSION = 0.3.2;','CURRENT_PROJECT_VERSION = 5;'):
                    assert want in project
                assert 'UNSIGNED00' not in project
                write('inner-receipts/ios-Info.plist',mem['ios/sightbreak/sightbreak-Info.plist'])
                write('inner-receipts/ios-project.pbxproj.txt',mem['ios/sightbreak.xcodeproj/project.pbxproj'])
            write('inner-receipts/'+target+'-source.json',receipt_bytes)
        assert len(rows)==61
        dump('inner-package-audit.json',{'bundles':3,'members':61,'payload_members':58,'source_receipts':3,'rows':rows,
                                        'five_manifest_artifact_hashes_match':True,'manifest_equals_packaging_bytes':True,
                                        'all_inner_and_outer_extracted_receipts_identical':True,
                                        'native_verifier_process_receipts':5,'packaged_verifier_process_receipts':2,
                                        'native_verifier_pass_qualified':True,'packaged_verifier_pass_qualified':True,
                                        'static_resources':resources,
                                        'limits':'No executable extracted or run. Signatures/Android aapt metadata corroborated against retained tool output, not newly cryptographically reverified. Inner POSIX modes verified in ZIPs; outer upload modes are transport metadata, not original Linux modes. CI extracted-mode checks remain receipt evidence.'})
        print('PACKAGES audited three inner ZIPs, 61 members, five manifest artifacts, seven native process receipts')

def audio_audit():
    with zipfile.ZipFile(EVIDENCE/'artifact-12470965068.zip') as z:
        before=j(z,'raw/sources-before.json'); after=j(z,'raw/sources-after.json')
        assert before['baseline_skipped'] is False and before['only']==['A5','A6','A7']
        assert after['sources']==before['sources'] and after['byte_restored'] is True and after['error'] is None
        for field in ('sources','tooling'):
            for path,digest in before[field].items():
                relative=path.split('/sightbreak-v3-controls/',1)[1]
                assert F[relative]['sha256']==digest
        assert j(z,'source-before.json')==j(z,'source-after.json')==BUILD_SOURCE
        result=j(z,'raw/result.json')
        assert result['exit']==0 and result['baseline_skipped'] is False and result['controls']==[['A5','caught'],['A6','caught'],['A7','caught']]
        tree=ast.parse((OUT/'frozen/scripts/reload_negative_controls.py').read_text())
        source_node=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SOURCE' for t in n.targets))
        path_vars={'ACTOR':'game/scripts/gameplay/actor.gd','AUDIO':'game/scripts/gameplay/reload_audio.gd','CAPTURE_SCRIPT':'game/tests/reload_audio_capture.gd'}
        mutation_rows=[]
        for control in source_node.elts:
            cid=ast.literal_eval(control.elts[0])
            if cid not in ('A5','A6','A7'): continue
            record=j(z,'raw/control-'+cid+'.json'); pending={}; expected=[]
            for edit in control.elts[2].elts:
                path=path_vars[edit.elts[0].id]
                data=pending.get(path)
                if data is None: data=git('show',FROZEN+':'+path)
                old,new=ast.literal_eval(edit.elts[1]).encode(),ast.literal_eval(edit.elts[2]).encode()
                assert data.count(old)==1
                changed=data.replace(old,new,1)
                expected.append({'path':'/home/runner/work/_temp/sightbreak-v3-controls/'+path,'old':old.decode(),'new':new.decode(),
                                 'matches':1,'newlines':'LF','before_sha256':sha(data),'after_sha256':sha(changed)})
                pending[path]=changed
            assert record['control']==cid and record['description']==ast.literal_eval(control.elts[1]) and record['edits']==expected
            mutation_rows.append({'control':cid,'edit_chain_matches_frozen_source':True,'edits':expected})
        prefixes=sorted({n.rsplit('/',1)[0] for n in z.namelist() if n.startswith('raw/') and n.endswith('/attempt.json')})
        assert len(prefixes)==13
        rows=[]
        unsafe=re.compile(r'HARNESS_ERROR|SCRIPT ERROR|(?:Parse|Parser|Compile) Error|Failed to (?:load script|compile)|Error parsing|\bleak(?:ed|s|ing)?\b|(?:resources?|RIDs?)[^\r\n]*still in use|Orphan StringName|unclaimed string names|FATAL|CRASH|Segmentation fault|signal (?:6|11)\b',re.I)
        for prefix in prefixes:
            attempt=j(z,prefix+'/attempt.json'); assessment=j(z,prefix+'/assessment.json'); receipt=j(z,prefix+'/process.json'); command=j(z,prefix+'/command.json')
            log=z.read(prefix+'/native.log').decode(); mutant=attempt['role']=='mutant'; code=1 if mutant else 0
            assert clean_receipt(receipt,code) and attempt['exit']==code and attempt['command']==command['command'] and attempt['containment_and_artifact_errors']==[]
            assert not unsafe.search(log)
            summaries=re.findall(r'^(?:RELOAD_SEQUENCE_TEST|WEAPON_ART_TEST|RELOAD_AUDIO_TEST|RELOAD_AUDIO_CAPTURE|RELOAD_VISIBILITY_TEST|RELOAD_DISCOLOUR_TEST|VIEWMODEL_LIGHT_TEST|RELOAD_CONTACT_TEST)\b[^\r\n]*',log,re.M)
            assert summaries==[assessment['summary']['line']]
            checks=int(re.search(r'\bchecks=(\d+)',summaries[0])[1]); failures=int(re.search(r'\bfailures=(\d+)',summaries[0])[1])
            assert checks==assessment['summary']['checks'] and failures==assessment['summary']['failures'] and checks>0
            error_lines=re.findall(r'^ERROR:[^\r\n]*',log,re.M)
            if mutant:
                assert assessment['state']=='FAILED' and failures=={'A5':6,'A6':1,'A7':1}[attempt['control']]
                fail_lines=re.findall(r'^FAIL[ \t]+([^\r\n]+)',log,re.M)
                assert len(error_lines)==len(fail_lines)==failures
                assert set(v.removeprefix('ERROR:').strip() for v in error_lines)==set(fail_lines)
                assert all('at: push_error' in block for block in log.split('ERROR:')[1:])
            else:
                assert failures==0 and not error_lines and assessment['state']=='passed' and assessment['errors']==[]
            captures=[]
            for filename,digest in attempt['capture_sha256'].items():
                raw=z.read(prefix+'/capture/'+filename)
                assert sha(raw)==digest
                captures.append({'name':filename,'sha256':digest,'bytes':len(raw)})
            wavs=[v for v in captures if v['name'].endswith('.wav')]
            wave_evidence=None
            if wavs:
                raw=z.read(prefix+'/capture/'+wavs[0]['name'])
                with wave.open(io.BytesIO(raw),'rb') as w:
                    assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==44100
                    count=w.getnframes(); pcm=array.array('h',w.readframes(count))
                    assert count==len(pcm)
                peak=max(abs(v) for v in pcm)/32767
                voice_csv=next(v['name'] for v in captures if v['name'].startswith('voices_'))
                voices=list(csv.DictReader(io.StringIO(z.read(prefix+'/capture/'+voice_csv).decode())))
                report_name=next(v['name'] for v in captures if v['name'].startswith('report_'))
                report=z.read(prefix+'/capture/'+report_name).decode()
                assert all(line in log for line in report.splitlines())
                frame_count=int(re.search(r'captured (\d+) frames per bus at 44100 Hz',log)[1])
                assert frame_count==count
                early_limit=max(0,int(voices[0]['cue_capture_frame'])-int(.060*44100))
                early_peak=max(abs(v) for v in pcm[:early_limit])/32767
                wave_evidence={'frames':count,'rate':44100,'mono_pcm16':True,'duration_seconds':count/44100,'peak':peak,
                               'early_window_end_frame':early_limit,'early_mix_peak':early_peak,'voices':voices}
                if attempt['control']=='A5':
                    assert peak==0 and all(int(v['onset_capture_frame'])==-1 and float(v['peak'])==0 for v in voices)
                elif attempt['control']=='A7':
                    assert early_peak>.0008
                elif not mutant and 'cancel' not in prefix:
                    assert early_peak<.0008
                assert len(voices)==(4 if 'cancel' in prefix else 6)
            rows.append({'attempt':prefix,'name':assessment['name'],'control':attempt['control'],'role':attempt['role'],
                         'checks':checks,'failures':failures,'exit':code,'independent_classification':'expected assertion catch' if mutant else 'baseline pass',
                         'containment_clean':True,'captures':captures,'wav_observations':wave_evidence})
        assert len(result['baseline'])==10 and sum(r['checks'] for r in rows if r['role']=='baseline')==386
        dump('audio-audit.json',{'baseline_groups':10,'baseline_checks':386,'baseline_failures':0,'attempts':13,'controls_caught':3,
                                'mutant_assertion_failures':8,'captures':15,'wav_files':5,
                                'eight_source_snapshots_four_tool_hashes_match_git':True,'source_restored':True,
                                'thresholds':{'onset_level':.012,'timing_tolerance_ms':90,'silent':.0008,'cancel_fraction':.63,'max_latency_seconds':.120},
                                'mutations':mutation_rows,'rows':rows,
                                'limits':'Only summed mono PCM16 WAVs retained, not all per-voice float arrays or cancel-frame counters. Cannot independently recompute every per-voice assertion or A6 exact post-cancel window. Raw reports/voice CSV/native logs and exact mutation/restoration hashes corroborate original catches. No listening, speaker, physical output-latency or subjective audio-quality acceptance.'})
        print('AUDIO audited 10 baseline groups/386 checks, 13 attempts, 3 catches/8 assertions, 15 captures, restoration')

if __name__=='__main__':
    matrix_audit()
    campaign_audit()
    packages_audit()
    audio_audit()
