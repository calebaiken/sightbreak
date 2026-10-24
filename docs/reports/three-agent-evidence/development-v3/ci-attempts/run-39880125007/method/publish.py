"""Publish only a new bounded docs packet; preserve original bytes; no staging."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from inspect import EVIDENCE, FROZEN, OUT, REPO, ENV, PACKET, git, sha, write, dump, snapshot

DEST = REPO / PACKET
LIMIT = 12*1024*1024

def encoded(value):
    return (json.dumps(value,indent=2,ensure_ascii=False)+'\n').encode()

def plan():
    entries={}
    selection=json.loads((OUT/'selection-manifest.json').read_bytes())
    omitted_duplicates={}
    for r in selection:
        archive,member=r['archive'],r['member']
        skip=False
        if archive=='artifact-12470739875.zip' and member.startswith('builds/v3-network/') and member.count('/')==2 and member.endswith('.log'):
            target=member[:-4]+'/summary.json'
            counterpart=next(v for v in selection if v['archive']==archive and v['member']==target)
            assert counterpart['sha256']==r['sha256'] and counterpart['bytes']==r['bytes']
            omitted_duplicates[(archive,member)]={'reason':'byte-identical parent stdout duplicate of published condition summary','same_as':'raw/'+archive[:-4]+'/'+target}
            skip=True
        if archive=='run-logs.zip' and member[0].isdigit() and '/' not in member:
            omitted_duplicates[(archive,member)]={'reason':'aggregate job-log concatenation; individual job-step files retained'}
            skip=True
        if not skip:
            entries['raw/'+r['relative']]={'source':str(OUT/'selected'/r['relative']),'bytes':r['bytes'],'sha256':r['sha256'],
                                          'kind':'original-archive-member','archive':archive,'member':member}
    # Include every collector-selected JSON under its canonical archive name,
    # including the two small receipts not in the broader initial selection.
    for r in json.loads((OUT/'selected-receipt-audit.json').read_bytes()):
        key='raw/'+r['artifact'][:-4]+'/'+r['member']
        if key not in entries:
            with zipfile.ZipFile(EVIDENCE/r['artifact']) as z:
                data=z.read(r['member'])
            rel=r['artifact'][:-4]+'/'+r['member']
            source=OUT/'selected'/rel
            if not source.exists(): write('selected/'+rel,data)
            assert source.read_bytes()==data and sha(data)==r['sha256']
            entries[key]={'source':str(source),'bytes':len(data),'sha256':sha(data),'kind':'original-archive-member','archive':r['artifact'],'member':r['member']}
    def add(dest,source,kind):
        data=source.read_bytes()
        assert dest not in entries
        entries[dest]={'source':str(source),'bytes':len(data),'sha256':sha(data),'kind':kind}
    for name in ('COLLECTION.json','run.json','jobs-001.json','artifacts-001.json'):
        add('transport/'+name,EVIDENCE/name,'original-download-metadata')
    add('transport/SHA256SUMS.collected.txt',EVIDENCE/'SHA256SUMS.txt','original-download-metadata')
    for aid in ('12470681259','12470739875','12470965068'):
        add('transport/artifact-'+aid+'-receipt-index.json',EVIDENCE/('artifact-'+aid+'-receipts')/'receipt-index.json','original-download-metadata')
    for name in ('source-object-audit.json','additional-source-manifest.json','selected-receipt-audit.json',
                 'matrix-audit.json','campaign-audit.json','audio-audit.json','inner-package-audit.json','provenance-and-flow-audit.json'):
        add('derived/'+name,OUT/name,'independent-derived-analysis')
    for p in sorted((OUT/'inner-receipts').rglob('*')):
        if p.is_file(): add('inner-receipts/'+p.relative_to(OUT/'inner-receipts').as_posix(),p,'inner-archive-original-text')
    source_paths=[
        '.github/workflows/v3-development.yml','scripts/godot_process.py','scripts/matrix_process.py','scripts/native_log.py',
        'scripts/build_manifest.py','scripts/validate_matrix.py','scripts/validate.sh','scripts/test_validate_matrix.py',
        'scripts/run_network_campaign.py','scripts/simulate_network.py','scripts/reload_negative_controls.py',
        'scripts/verify_builds.py','scripts/verify_packaged_builds.py','scripts/verify_integration_export.py',
        'scripts/verify_offline_export.py','scripts/offline_hud.py','scripts/export_flow.py','scripts/test_protocol_compat.sh',
        'scripts/fixtures/export_integration.gd','game/tests/network_simulation_probe.gd','game/tests/reload_audio_capture.gd',
        'game/tests/reload_sequence_test.gd','game/tests/weapon_art_test.gd','game/tests/reload_audio_test.gd',
        'game/tests/reload_visibility_test.gd','game/tests/reload_discolour_probe.gd','game/tests/viewmodel_light_probe.gd',
        'docs/reports/media/art-v9/hands/logs/clip_contact.csv']
    for name in source_paths:
        add('frozen/'+name,OUT/'frozen'/name,'frozen-git-object-source')
    for name in ('inspect.py','audit_data.py','verify_findings.py','audit_endpoints.py','publish.py'):
        add('method/'+name,OUT/name,'audit-method-source-not-executed-project-code')
    add('AUDIT.md',OUT/'AUDIT.md','independent-audit-report')
    catalog=json.loads((OUT/'archive-byte-audit.json').read_bytes())
    pub_lookup={(v['archive'],v['member']):k for k,v in entries.items() if v['kind']=='original-archive-member'}
    omitted_count=0
    for archive,info in catalog.items():
        info['external_full_archive']=info.pop('path')
        for member in info['members']:
            key=(archive,member['member'])
            member['published_path']=pub_lookup.get(key)
            if member['published_path'] is None:
                omitted_count+=1
                if key in omitted_duplicates:
                    member['omission']=omitted_duplicates[key]
                else:
                    name=member['member']
                    if name.endswith(('.zip','.apk','.x86_64','.a','.so','.idsig')):
                        reason='binary/package bytes left external; inner packages and payload hashes audited without executable extraction'
                    elif '/state/' in name or '/server-state/' in name:
                        reason='runtime/import/cache state; complete bytes remain in external archive'
                    elif name.startswith('builds/v3-network/') and name.endswith('.json') and ('/client-' in name or name.endswith('/server.json')):
                        reason='large full trajectory JSON read and audited in memory; per-child hashes and scalar assertions in derived/campaign-audit.json'
                    elif name.endswith('.png'):
                        reason='unselected screenshot or fixture media; selected raw failure/flow and all OCR input crops published'
                    elif name.endswith(('.sqlite','.sqlite.lock')):
                        reason='historical database payload not opened; retained external only'
                    else:
                        reason='not selected for bounded packet; full original member retained externally and indexed here'
                    member['omission']={'reason':reason}
    inventory={'source':'Independent complete ZIP member byte/CRC/hash pass; no execution or executable extraction.',
               'external_root':str(EVIDENCE),'audit_external_root':str(OUT),'total_archive_members':2714,
               'published_original_archive_members':len(pub_lookup),'omitted_archive_members':omitted_count,'archives':catalog}
    dump('EXTERNAL_INVENTORY.json',inventory)
    add('EXTERNAL_INVENTORY.json',OUT/'EXTERNAL_INVENTORY.json','external-member-catalog-and-omissions')
    raw=[v for v in entries.values() if v['kind']=='original-archive-member']
    result={'destination':str(DEST),'limit_bytes':LIMIT,'entries':entries,
            'planned_entries':len(entries),'planned_bytes_excluding_final_generated_files':sum(v['bytes'] for v in entries.values()),
            'raw_member_count':len(raw),'raw_member_bytes':sum(v['bytes'] for v in raw),
            'omitted_archive_member_count':omitted_count,'selected_frozen_source_count':len(source_paths),
            'note':'Final workspace comparison, PACKAGE.json, ignore/attributes and SHA256SUMS are added at publication; hard 12 MiB check before and after.'}
    dump('publication-plan.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))

def comparison(before,after):
    b=before['files_excluding_authorized_packet']; a=after['files_excluding_authorized_packet']
    changed=[{'path':p,'before':b.get(p),'after':a.get(p)} for p in sorted(set(b)|set(a)) if b.get(p)!=a.get(p)]
    return {'head_before':before['head'],'head_after':after['head'],'index_unchanged':before['index_sha256']==after['index_sha256'],
            'refs_unchanged':before['refs']==after['refs'],'outside_packet_files_before':len(b),'outside_packet_files_after':len(a),
            'outside_packet_changed_paths':changed,'outside_packet_invariant':not changed and before['head']==after['head'] and before['index_sha256']==after['index_sha256'] and before['refs']==after['refs']}

def publish():
    p=json.loads((OUT/'publication-plan.json').read_bytes())
    assert p['destination']==str(DEST) and not DEST.exists(), 'Never overwrite a packet, even an empty one.'
    assert p['planned_bytes_excluding_final_generated_files']+150000 < LIMIT
    DEST.mkdir(parents=True)
    def put(relative,data):
        path=DEST/relative
        assert path.resolve().is_relative_to(DEST.resolve()) and not path.exists()
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f: f.write(data)
    for relative,row in p['entries'].items():
        data=Path(row['source']).read_bytes()
        assert len(data)==row['bytes'] and sha(data)==row['sha256']
        put(relative,data)
    put('.gitattributes',b'# Preserve every source, receipt, log and image byte across checkout platforms.\n* -text\n')
    put('.gitignore',b'# This bounded historical evidence packet intentionally retains raw logs/builds paths.\n!**/\n!**/*\n')
    # This snapshot excludes the entire authorized packet, including pending
    # generated files. It cannot attribute unrelated concurrent writes to us.
    snapshot('after')
    snapshots={label:json.loads((OUT/(label+'-snapshot.json')).read_bytes()) for label in ('before','pre-publication','after')}
    comparison_report={'scope':'Audit writes only new packet and new external audit directory. No local-clean/invariant claim; concurrent changes observed before first repository write.',
                       'packet_excluded_from_file_snapshots':PACKET,
                       'before_to_prepublication':comparison(snapshots['before'],snapshots['pre-publication']),
                       'prepublication_to_after':comparison(snapshots['pre-publication'],snapshots['after']),
                       'before_to_after':comparison(snapshots['before'],snapshots['after']),
                       'external_snapshot_references':[{ 'label':label,'path':str(OUT/(label+'-snapshot.json')),
                                                         'bytes':(OUT/(label+'-snapshot.json')).stat().st_size,
                                                         'sha256':sha((OUT/(label+'-snapshot.json')).read_bytes()),
                                                         'status_path':str(OUT/(label+'-status.txt')),
                                                         'status_sha256':sha((OUT/(label+'-status.txt')).read_bytes()),
                                                         'utc':snapshots[label]['utc']} for label in snapshots]}
    dump('workspace-read-only-audit.json',comparison_report)
    put('derived/workspace-read-only-audit.json',encoded(comparison_report))
    categories={}
    for relative,row in p['entries'].items():
        key=row['kind']; categories.setdefault(key,{'files':0,'bytes':0})
        categories[key]['files']+=1; categories[key]['bytes']+=row['bytes']
    summary={'run_id':39880125007,'ci_source':FROZEN,'conclusion':'failure','acceptance':False,
             'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'logical_byte_limit':LIMIT,
             'planned_payload_categories_excluding_final_generated_metadata':categories,
             'preserved_archive_members':p['raw_member_count'],'omitted_archive_members':p['omitted_archive_member_count'],
             'all_27_selected_receipts_present_under_original_member_paths':True,
             'matrix':{'rows':83,'passed':82,'failed':1},'campaign':{'conditions':12,'clients_each':10,'seconds_each':18,'child_reports_and_logs':132},
             'audio':{'baseline_groups':10,'baseline_checks':386,'controls_caught':3,'attempts':13,'wav_files':5},
             'packages':{'inner_archives':3,'members':61,'payload_members':58,'receipt_members':3,'native_verifier_process_receipts':5,'packaged_verifier_process_receipts':2},
             'exported_client_failures':2,'no_native_db_network_or_project_execution':True,'staged':False,
             'external_full_evidence_root':str(EVIDENCE),'external_audit_root':str(OUT),
             'integrity':'SHA256SUMS.txt covers every packet file except itself. FINAL_VERIFICATION.json external records its digest, exact complete packet bytes/count and reread verification.',
             'omissions':'EXTERNAL_INVENTORY.json names/hashes every original ZIP member and its exact publication path or omission reason.'}
    put('PACKAGE.json',encoded(summary))
    payload=sorted(f for f in DEST.rglob('*') if f.is_file())
    ledger=''.join(sha(f.read_bytes())+'  '+f.relative_to(DEST).as_posix()+'\n' for f in payload).encode()
    assert sum(f.stat().st_size for f in payload)+len(ledger)<=LIMIT
    put('SHA256SUMS.txt',ledger)
    # Reread every packet file, not only planned originals.
    verified=0
    for line in ledger.decode().splitlines():
        digest,relative=line.split('  ',1)
        assert sha((DEST/relative).read_bytes())==digest
        verified+=1
    archive_verified=0
    for archive in ('artifact-12470681259.zip','artifact-12470739875.zip','artifact-12470965068.zip','run-logs.zip'):
        with zipfile.ZipFile(EVIDENCE/archive) as z:
            for relative,row in p['entries'].items():
                if row.get('archive')==archive:
                    assert (DEST/relative).read_bytes()==z.read(row['member'])
                    archive_verified+=1
    sources={r['path']:r for r in json.loads((OUT/'source-object-audit.json').read_bytes())['files']}
    sources.update({r['path']:r for r in json.loads((OUT/'additional-source-manifest.json').read_bytes())})
    frozen_verified=0
    for relative,row in p['entries'].items():
        if row['kind']=='frozen-git-object-source':
            assert sha((DEST/relative).read_bytes())==sources[relative.removeprefix('frozen/')]['sha256']
            frozen_verified+=1
    files=sorted(f for f in DEST.rglob('*') if f.is_file())
    relative_to_repo=[f.relative_to(REPO).as_posix() for f in files]
    # Read-only attribute/ignore checks do not stage or update the index.
    attrs=subprocess.check_output(['git','-c','core.fsmonitor=false','check-attr','-z','--stdin','text'],cwd=REPO,env=ENV,
                                  input=b''.join(p.encode()+b'\0' for p in relative_to_repo)).split(b'\0')
    assert attrs[-1]==b''
    triples=[attrs[i:i+3] for i in range(0,len(attrs)-1,3)]
    assert len(triples)==len(files) and all(t[1:]==[b'text',b'unset'] for t in triples)
    visible=set(p.decode() for p in git('ls-files','--others','--exclude-standard','-z','--',PACKET).split(b'\0') if p)
    assert visible==set(relative_to_repo), 'All files must be untracked and non-ignored; no staging.'
    assert len(files)==verified+1 and archive_verified==p['raw_member_count']
    total=sum(f.stat().st_size for f in files)
    assert total<=LIMIT
    final={'packet_path':str(DEST),'external_report':str(OUT/'AUDIT.md'),'ledger_path':str(DEST/'SHA256SUMS.txt'),
           'ledger_sha256':sha((DEST/'SHA256SUMS.txt').read_bytes()),'packet_file_count_including_ledger':len(files),
           'ledger_entries_verified':verified,'packet_total_logical_bytes':total,'packet_MiB':total/(1024*1024),'limit_bytes':LIMIT,
           'archive_members_recompared_byte_for_byte':archive_verified,'frozen_source_files_reverified_against_git_hashes':frozen_verified,
           'all_packet_paths_have_text_unset':True,'all_packet_files_untracked_nonignored':True,'no_staging':True,
           'workspace_before_to_after':comparison_report['before_to_after'],
           'workspace_prepublication_to_after':comparison_report['prepublication_to_after'],
           'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    dump('FINAL_VERIFICATION.json',final)
    write('PACKET_SHA256SUMS.txt',ledger)
    print(json.dumps(final,indent=2))

if __name__=='__main__':
    if sys.argv[1:]==['plan']: plan()
    elif sys.argv[1:]==['publish']: publish()
    else: raise SystemExit('Use plan once, then publish once; no overwrites.')
