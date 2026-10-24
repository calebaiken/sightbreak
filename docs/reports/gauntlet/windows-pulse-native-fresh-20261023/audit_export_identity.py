"""Join transferred native export, embedded-pack inspection and runtime receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re

READ=lambda p:json.loads(p.read_text())
KEYS=('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')


def audit(root, identity):
    base=root/'evidence'
    manifest=READ(base/'manifest.json')
    source=READ(base/'windows/source.json')
    verification=READ(base/'verification/results.json')
    exports=manifest['exports']
    current=lambda r:all(r.get(k)==identity[k] for k in KEYS) and r.get('source_dirty') is False and r.get('source_game_dirty') is False
    windows=[r for r in exports if r['target']=='windows']
    checks={'manifest_current_clean_source':current(manifest),
            'one_current_completed_export':len(windows)==1 and current(windows[0]) and windows[0]['export_completed'] is True,
            'native_export_source_record_matches':current(source),
            'native_verification_source_record_matches':current(verification),
            'debug_development_scope':manifest['build_type']=='debug' and manifest['engine']=='Godot 4.7.2'}
    artifact=windows[0]['artifact']
    checks['manifest_embedded_executable_identity_join']=artifact in manifest['artifacts'] and artifact in windows[0]['payload']
    runtime=[]
    for path in sorted(base.rglob('results.json')):
        result=READ(path)
        if isinstance(result,dict) and 'executable_sha256' in result:
            digest=result['executable_sha256']
            checks['same_native_executable:'+path.relative_to(base).as_posix()]=digest==artifact['sha256']
            runtime.append({'path':path.relative_to(base).as_posix(),'executable_sha256':digest})
    target=verification['targets']['windows']
    checks['actual_embedded_PCK_inspection_receipt']=target['artifact_inspection'] is True and type(target['pck_resources']) is int and target['pck_resources']>0
    checks['startup_headless_and_graphical_receipts']=target['native_execution']=='PASS (headless startup only)' and target['native_graphical_menu']=='PASS'
    checks['three_clean_native_startup_commands']=len(verification['runs'])==3 and all(r['exit_code']==0 and r['clean_log'] is True for r in verification['runs'])
    scans=[]
    for path in sorted((base/'verification').glob('*.log')):
        text=path.read_text(errors='replace')
        bad=[line for line in text.splitlines() if re.search(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|Orphan StringName:|StringName: [1-9][0-9]* unclaimed string names at exit\.',line)]
        scans.append({'path':path.relative_to(base).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'failure_lines':bad})
    checks['actual_startup_strict_logs_clean']=len(scans)==3 and all(not r['failure_lines'] for r in scans)
    return {'checks':checks,'all_checks_passed':all(checks.values()),'native_executable_receipt':artifact,
            'embedded_PCK_resource_count_receipt':target['pck_resources'],'runtime_executable_joins':runtime,'verification_logs':scans,
            'native_executable_bytes_independently_transferred':False,'PCK_bytes_or_directory_independently_reparsed':False,
            'scope':'Source/manifest/runtime hash joins and original native embedded-PCK inspection receipt; native binary above transfer cap is not downloaded or independently reparsed.'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('identity',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=audit(a.root,READ(a.identity)['native_identity']);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'all_checks_passed':r['all_checks_passed'],'failed_checks':[k for k,v in r['checks'].items() if not v]}))
