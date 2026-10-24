"""Finalize the NEW packet after compacting only our generated workspace summary."""
import collections
import datetime
import json
from pathlib import Path
import subprocess
import zipfile

from inspect import OUT, REPO, EVIDENCE, ENV, PACKET, git, sha, write, dump, snapshot
from publish import DEST, LIMIT, comparison, encoded

def main():
    assert DEST.is_dir() and not (DEST/'SHA256SUMS.txt').exists()
    assert not (DEST/'derived/workspace-read-only-audit.json').exists()
    plan=json.loads((OUT/'publication-plan.json').read_bytes())
    # Only our report received a disclosed post-plan clarification. All other
    # planned files, particularly original bytes, must remain untouched.
    for relative,row in plan['entries'].items():
        data=(DEST/relative).read_bytes()
        if relative=='AUDIT.md':
            assert data==(OUT/'AUDIT.md').read_bytes()
        else:
            assert len(data)==row['bytes'] and sha(data)==row['sha256']
    def put(relative,data):
        path=DEST/relative
        assert path.resolve().is_relative_to(DEST.resolve()) and not path.exists()
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as f: f.write(data)
    snapshot('publication-final')
    snapshots={name:json.loads((OUT/(name+'-snapshot.json')).read_bytes()) for name in ('before','pre-publication','after','publication-final')}
    full={name:comparison(snapshots[a],snapshots[b]) for name,a,b in
          [('before_to_prepublication','before','pre-publication'),('prepublication_to_assembly','pre-publication','after'),
           ('assembly_to_final','after','publication-final'),('before_to_final','before','publication-final')]}
    dump('final-workspace-full-comparison.json',full)
    def compact(row):
        changes=row['outside_packet_changed_paths']
        result={k:v for k,v in row.items() if k!='outside_packet_changed_paths'}
        result['outside_packet_changed_or_newly_visible_count']=len(changes)
        result['new_or_newly_visible_count']=sum(r['before'] is None for r in changes)
        result['modified_or_removed_preexisting_paths']=[r for r in changes if r['before'] is not None]
        if len(changes)<=10: result['all_differing_paths']=changes
        result['path_group_counts']=dict(collections.Counter('/'.join(r['path'].split('/')[:6]) for r in changes))
        return result
    full_path=OUT/'final-workspace-full-comparison.json'
    compact_report={'scope':'Only the new authorized docs packet and new external audit directory were written by audit commands. Shared workspace was already dirty and changed concurrently; global invariance is NOT claimed.',
                    'packet_excluded':PACKET,'comparisons':{name:compact(value) for name,value in full.items()},
                    'full_differing_path_hash_records_external':{'path':str(full_path),'bytes':full_path.stat().st_size,'sha256':sha(full_path.read_bytes())},
                    'original_assembly_full_comparison_external':{'path':str(OUT/'workspace-read-only-audit.json'),'bytes':(OUT/'workspace-read-only-audit.json').stat().st_size,'sha256':sha((OUT/'workspace-read-only-audit.json').read_bytes())},
                    'snapshot_references':[{'label':name,'utc':snapshots[name]['utc'],'snapshot_path':str(OUT/(name+'-snapshot.json')),
                                            'snapshot_sha256':sha((OUT/(name+'-snapshot.json')).read_bytes()),
                                            'status_path':str(OUT/(name+'-status.txt')),'status_sha256':sha((OUT/(name+'-status.txt')).read_bytes())} for name in snapshots],
                    'observability_limit':'Newly visible paths can reflect another session changing ignore rules, not necessarily new writes. No outside-scope file was rolled back, repaired, overwritten or deleted.'}
    dump('compact-workspace-read-only-audit.json',compact_report)
    put('derived/workspace-read-only-audit.json',encoded(compact_report))
    put('method/finalize.py',Path(__file__).read_bytes())
    files=sorted(f for f in DEST.rglob('*') if f.is_file())
    categories={}
    for f in files:
        category=f.relative_to(DEST).parts[0] if len(f.relative_to(DEST).parts)>1 else 'root'
        categories.setdefault(category,{'files':0,'bytes':0})
        categories[category]['files']+=1;categories[category]['bytes']+=f.stat().st_size
    adjustment={'purpose':'Finish this NEW packet after initial hard byte-limit gate stopped before producing a ledger.',
                'initial_unfinalized_assembly_bytes_without_ledger':12843010,'limit_bytes_including_ledger':LIMIT,
                'replaced_generated_file':'derived/workspace-read-only-audit.json',
                'original_generated_full_bytes':706814,'full_original_retained_external':str(OUT/'workspace-read-only-audit.json'),
                'raw_receipts_logs_media_unchanged':True,'no_old_packet_overwritten':True,'ci_failed_verdict_unchanged':True,
                'report_clarification':'Explicitly disclose the further 1031 outside-packet changed/newly visible paths during assembly.',
                'current_categories_excluding_this_file_and_ledger':categories,
                'complete_final_counts_and_ledger_sha256':str(OUT/'FINAL_VERIFICATION.json')}
    put('PUBLICATION_FINALIZATION.json',encoded(adjustment))
    payload=sorted(f for f in DEST.rglob('*') if f.is_file())
    ledger=''.join(sha(f.read_bytes())+'  '+f.relative_to(DEST).as_posix()+'\n' for f in payload).encode()
    assert sum(f.stat().st_size for f in payload)+len(ledger)<=LIMIT
    put('SHA256SUMS.txt',ledger)
    # Every published payload gets a second read/hash, and every original
    # archive member gets a fresh byte comparison against its ZIP source.
    for line in ledger.decode().splitlines():
        digest,relative=line.split('  ',1)
        assert sha((DEST/relative).read_bytes())==digest
    archive_verified=0
    for archive in ('artifact-12470681259.zip','artifact-12470739875.zip','artifact-12470965068.zip','run-logs.zip'):
        with zipfile.ZipFile(EVIDENCE/archive) as z:
            for relative,row in plan['entries'].items():
                if row.get('archive')==archive:
                    assert (DEST/relative).read_bytes()==z.read(row['member'])
                    archive_verified+=1
    sources={r['path']:r for r in json.loads((OUT/'source-object-audit.json').read_bytes())['files']}
    sources.update({r['path']:r for r in json.loads((OUT/'additional-source-manifest.json').read_bytes())})
    frozen_verified=0
    for relative,row in plan['entries'].items():
        if row['kind']=='frozen-git-object-source':
            assert sha((DEST/relative).read_bytes())==sources[relative.removeprefix('frozen/')]['sha256']
            frozen_verified+=1
    files=sorted(f for f in DEST.rglob('*') if f.is_file())
    paths=[f.relative_to(REPO).as_posix() for f in files]
    attrs=subprocess.check_output(['git','-c','core.fsmonitor=false','check-attr','-z','--stdin','text'],cwd=REPO,env=ENV,
                                  input=b''.join(p.encode()+b'\0' for p in paths)).split(b'\0')
    assert attrs[-1]==b''
    triples=[attrs[i:i+3] for i in range(0,len(attrs)-1,3)]
    assert len(triples)==len(files) and all(t[1:]==[b'text',b'unset'] for t in triples)
    visible=set(p.decode() for p in git('ls-files','--others','--exclude-standard','-z','--',PACKET).split(b'\0') if p)
    assert visible==set(paths)
    assert len(files)==len(ledger.decode().splitlines())+1 and archive_verified==589
    assert (DEST/'AUDIT.md').read_bytes()==(OUT/'AUDIT.md').read_bytes()
    total=sum(f.stat().st_size for f in files)
    assert total<=LIMIT
    final={'packet_path':str(DEST),'external_report':str(OUT/'AUDIT.md'),'ledger_path':str(DEST/'SHA256SUMS.txt'),
           'ledger_sha256':sha((DEST/'SHA256SUMS.txt').read_bytes()),'packet_file_count_including_ledger':len(files),
           'ledger_entries_verified':len(payload),'packet_total_logical_bytes':total,'packet_MiB':total/(1024*1024),'limit_bytes':LIMIT,
           'preserved_archive_members_recompared_byte_for_byte':archive_verified,'preserved_original_archive_member_bytes':plan['raw_member_bytes'],
           'collector_selected_receipts_verified_and_present':27,'omitted_archive_members_indexed_external':2125,
           'frozen_source_files_reverified_against_git_hashes':frozen_verified,'all_packet_paths_have_text_unset':True,
           'all_packet_files_untracked_nonignored':True,'no_staging':True,
           'matrix':{'rows':83,'passed':82,'failed':1},'campaign':{'conditions':12,'clients_each':10,'measurement_seconds_each':18,'child_pairs':132},
           'audio':{'baseline_groups':10,'baseline_checks':386,'controls_caught':3,'attempts':13,'wav_files':5},
           'inner_packages':{'bundles':3,'members':61,'payloads':58,'source_receipts':3},'failed_client_flows':2,
           'outside_workspace_before_to_final':compact(full['before_to_final']),
           'outside_workspace_assembly_to_final':compact(full['assembly_to_final']),
           'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    dump('FINAL_VERIFICATION.json',final)
    write('PACKET_SHA256SUMS.txt',ledger)
    concise={k:v for k,v in final.items() if not k.startswith('outside_workspace')}
    concise['outside_workspace_assembly_to_final_changed_count']=len(full['assembly_to_final']['outside_packet_changed_paths'])
    print(json.dumps(concise,indent=2))

if __name__=='__main__':
    main()
