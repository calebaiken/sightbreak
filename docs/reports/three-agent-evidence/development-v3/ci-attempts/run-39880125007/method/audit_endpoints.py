"""Bind downloaded metadata, frozen controllers, retained failures and audit scope."""
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile

from inspect import EVIDENCE, FROZEN, OUT, git, sha, write, dump
from verify_findings import BUILD_SOURCE, F, clean_receipt

def main():
    run=json.loads((EVIDENCE/'run.json').read_bytes())
    jobs=json.loads((EVIDENCE/'jobs-001.json').read_bytes())
    artifacts=json.loads((EVIDENCE/'artifacts-001.json').read_bytes())
    collection=json.loads((EVIDENCE/'COLLECTION.json').read_bytes())
    byte_audit=json.loads((OUT/'archive-byte-audit.json').read_bytes())
    assert run['id']==39880125007 and run['head_sha']==FROZEN and run['status']=='completed' and run['conclusion']=='failure'
    assert run['run_attempt']==1 and run['path']=='.github/workflows/v3-development.yml'
    assert jobs['total_count']==len(jobs['jobs'])==3 and artifacts['total_count']==len(artifacts['artifacts'])==3
    assert collection['collection_complete'] is True and collection['validation_accepted'] is False and collection['run_conclusion']=='failure'
    assert collection['jobs']==jobs['jobs']
    for job in jobs['jobs']:
        assert job['head_sha']==FROZEN and job['run_id']==39880125007 and job['status']=='completed'
    expected={'native-development-packages':'failure','full-matrix-and-network':'failure','adversarial-audio-controls':'success'}
    assert {j['name']:j['conclusion'] for j in jobs['jobs']}==expected
    rows=[]
    for a in artifacts['artifacts']:
        record=byte_audit[f"artifact-{a['id']}.zip"]
        assert a['workflow_run']['id']==39880125007 and a['workflow_run']['head_sha']==FROZEN
        assert a['digest']=='sha256:'+record['sha256'] and a['size_in_bytes']==record['bytes']
        rows.append({'id':a['id'],'name':a['name'],'bytes':record['bytes'],'sha256':record['sha256'],
                     'digest_matches_downloaded_GitHub_metadata':True,'workflow_source_matches':True,
                     'url':a['url'],'zip_url':a['archive_download_url'],
                     'browser_url':f"https://github.com/calebaiken/sightbreak/actions/runs/39880125007/artifacts/{a['id']}",
                     'expires_at_as_recorded':a['expires_at']})
    with zipfile.ZipFile(EVIDENCE/'run-logs.zip') as z:
        for job in expected:
            checkout=next(n for n in z.namelist() if n.startswith(job+'/2_'))
            text=z.read(checkout).decode()
            assert FROZEN in text
    with zipfile.ZipFile(EVIDENCE/'artifact-12470681259.zip') as z:
        network=json.loads(z.read('v3-export-network/results.json'))
        offline=json.loads(z.read('v3-export-offline/results.json'))
        authority=json.loads(z.read('v3-export-network/authority.json'))
        assert network['passed'] is False and network['status']=='incomplete' and network['stage']=='watchdog-start'
        assert network['watchdog']['seconds']==240.141 and network['watchdog']['timeout_seconds']==240
        assert offline['passed'] is False and offline['source']==BUILD_SOURCE and offline['watchdog']['seconds']==48.805
        assert network['watchdog']['controller_sha256']==F['scripts/verify_integration_export.py']['sha256']
        assert offline['controller_sha256']==offline['watchdog']['controller_sha256']==F['scripts/verify_offline_export.py']['sha256']
        assert offline['executable_sha256']=='58b72b4ed0a67619f7b39e20c60b20214f6976e59b60934bc1cdf9babceaf8aa'
        network_process=json.loads(z.read('v3-export-network/watchdog.process.json'))
        offline_process=json.loads(z.read('v3-export-offline/watchdog.process.json'))
        assert network_process['complete'] is True and network_process['exit']==1 and len(network_process['errors'])==1 and network_process['posix_cleanup_verified'] is True
        assert 'timed out' in network_process['errors'][0]
        assert clean_receipt(offline_process,1)
        assert authority['passed'] is True and authority['shots']==6 and authority['lowest_ammo']==24 and authority['largest_ack']==95
        assert authority['reload_command_seen'] is True and authority['reload_completed'] is True and authority['reload_trigger']=='native client input'
        server=z.read('v3-export-network/server.log').decode()
        assert len(re.findall(r'^EXPORT_UI_SHOT ',server,re.M))==6 and 'EXPORT_UI_RELOAD_COMMAND actor=1' in server
        assert 'EXPORT_UI_RELOAD_COMPLETED ammo=30' in server
        ocr={}
        for stage in ('05-after-fire','06-after-reload'):
            for kind in ('status','ammo'):
                path=f'v3-export-offline/{stage}-{kind}-ocr.stdout.txt'
                ocr[stage+'-'+kind]=z.read(path).decode()
        assert '100' in ocr['05-after-fire-status'] and re.search(r'14\s*/\s*60',ocr['05-after-fire-ammo'])
        assert 'ELIMINATED' in ocr['06-after-reload-status'] and 'RELOADING 0.1s' in ocr['06-after-reload-ammo']
        screenshots=[]
        for name in z.namelist():
            if not name.startswith(('v3-export-network/','v3-export-offline/')) or not name.endswith('.png') or '/state/' in name:
                continue
            data=z.read(name)
            assert data[:8]==b'\x89PNG\r\n\x1a\n' and data[12:16]==b'IHDR'
            w,h=struct.unpack('>II',data[16:24])
            if '.input.png' not in name: assert (w,h)==(1280,720)
            screenshots.append({'member':name,'bytes':len(data),'sha256':sha(data),'dimensions':[w,h]})
        native=json.loads(z.read('verification/results.json'))
        packaged=json.loads(z.read('v3-package-verification/results.json'))
        static=json.loads((OUT/'inner-package-audit.json').read_bytes())['static_resources']
        assert len(static['linux'])==native['linux_pck_resources']==packaged['linux_pck_resources']==130
        assert len(static['ios'])==native['ios_pck_resources']==130
        assert len(static['android'])==native['android_assets']==132
        xml=z.read('verification/android-layout.log').decode()
        assert re.search(r'android:screenOrientation[^\n]*\(type 0x10\)0x0\b',xml)
        alias=xml.split('E: activity-alias',1)[1].split('E: meta-data',1)[0]
        for s in ('"com.godot.game.GodotAppLauncher"','"com.godot.game.GodotApp"','"android.intent.action.MAIN"','"android.intent.category.LAUNCHER"'):
            assert s in alias
        assert re.search(r'android:exported[^\n]*0xffffffff',alias)
    supplement=[]
    for path in ('game/tests/reload_sequence_test.gd','game/tests/weapon_art_test.gd','game/tests/reload_audio_test.gd',
                 'game/tests/reload_visibility_test.gd','game/tests/reload_discolour_probe.gd','game/tests/viewmodel_light_probe.gd',
                 'docs/reports/media/art-v9/hands/logs/clip_contact.csv','scripts/fixtures/export_integration.gd'):
        data=git('show',FROZEN+':'+path)
        write('frozen/'+path,data)
        supplement.append({'path':path,'git_blob':git('rev-parse',FROZEN+':'+path).decode().strip(),'sha256':sha(data),'bytes':len(data)})
    dump('additional-source-manifest.json',supplement)
    python=Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe')
    dump('provenance-and-flow-audit.json',{'run_url':run['html_url'],'run_id':39880125007,'run_attempt':1,'source_commit':FROZEN,
                                         'run_conclusion':'failure','job_conclusions':expected,'downloaded_artifact_metadata_matches':rows,
                                         'checkout_logs_contain_frozen_commit':True,'network':{'passed':False,'status':'incomplete','wall_seconds':240.141,
                                         'authority_substep':authority,'process_receipt':network_process,
                                         'controller_source_hash_matches':True,'limit':'No final client/server clean-exit/unchanged-export success receipt. Screenshots and source-authority success are not overall flow acceptance. Stalled stage/cause not proven by offline evidence.'},
                                         'offline':{'passed':False,'wall_seconds':48.805,'process_receipt':offline_process,'controller_source_hash_matches':True,
                                         'ocr_raw':ocr,'visual_review':'05 shows 100 HEALTH and SIDEARM 14 / 60; 06 shows ELIMINATED SPECTATING, RELOADING 0.1s. Actual rendered death, not a mistaken positive-health parser failure.',
                                         'limit':'No completed living-player fire/reload/movement flow or final source/clean-exit success receipt.'},
                                         'screenshots':screenshots,'python_path':str(python),'python_sha256':sha(python.read_bytes()),
                                         'audit_execution_scope':'Only approved CPython stdlib parsing/hashing and read-only git inspections. No imported project modules, native game/SDK jobs, DB, sockets/network/GitHub requests, staging, commits or owner branch mutations.',
                                         'provenance_limit':'Comparison against already downloaded GitHub metadata and logs; offline audit does not independently authenticate the remote service or re-observe CI execution.'})
    print('PROVENANCE raw run/jobs/artifact metadata match; both actual client failures retained; controllers hash match')

if __name__=='__main__':
    main()
