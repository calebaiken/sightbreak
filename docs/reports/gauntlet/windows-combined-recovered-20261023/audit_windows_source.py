"""Reconcile frozen Windows text bytes with native source/resource receipts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

SOURCE='b2e0293a546961230afbd73e5cd2a1a307d69e94'
CRLF={'scripts/diagnostics/render_feature_probe.gd','scripts/fixtures/export_integration.gd',
      'scripts/fixtures/network_soak.gd','game/tests/fixtures/backend_world.json',
      'scripts/fixtures/offline_capture_observations.json','scripts/macos_window_capture.swift'}
READ=lambda p:json.loads(p.read_text())

def audit(checkout,receipts):
    helper=Path(__file__).with_name('recompute_source.py')
    spec=importlib.util.spec_from_file_location('frozen_git_identity',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.CHECKOUT=checkout
    identity=module.source_identity();validation=hashlib.sha256();changed=[]
    for item in identity['files']:
        if item['scope']!='validation':continue
        raw=subprocess.check_output(['git','show',SOURCE+':'+item['path']],cwd=checkout)
        if item['path'] in CRLF:
            raw=raw.replace(b'\n',b'\r\n');changed.append({'path':item['path'],'LF_sha256':item['sha256'],'CRLF_sha256':hashlib.sha256(raw).hexdigest()})
        validation.update(item['path'].encode()+b'\0'+raw+b'\0')
    native={k:identity[k] for k in ('source_commit','source_game_tree','source_content_sha256','source_validation_sha256')};native['source_validation_sha256']=validation.hexdigest()
    receipt=READ(receipts/'evidence/offline-input/results.json')
    resource=READ(receipts/'evidence/regressions/isolation.json')['source_resources_sha256'];bad=[];converted=[]
    for path,expected in resource.items():
        raw=subprocess.check_output(['git','show',SOURCE+':game/'+path],cwd=checkout);actual=hashlib.sha256(raw).hexdigest()
        if actual!=expected and 'game/'+path in CRLF:
            actual=hashlib.sha256(raw.replace(b'\n',b'\r\n')).hexdigest();converted.append(path)
        if actual!=expected:bad.append(path)
    controller=subprocess.check_output(['git','show',SOURCE+':scripts/verify_offline_export.py'],cwd=checkout)
    checks={'source_clean_and_identity_matches_native_bytes':all(receipt['source'][k]==v for k,v in native.items()) and receipt['source']['source_dirty'] is False and receipt['source']['source_game_dirty'] is False,
            'all_native_game_resource_hashes_match':not bad,
            'only_declared_fixture_resource_needs_CRLF':converted==['tests/fixtures/backend_world.json'],
            'actual_controller_digest_matches_frozen_python':receipt.get('controller_sha256')==hashlib.sha256(controller).hexdigest()}
    return {'checks':checks,'all_checks_passed':all(checks.values()),'native_identity':native,'LF_identity':{k:identity[k] for k in native},
            'CRLF_validation_paths':changed,'native_game_resources':len(resource),'game_resource_CRLF_paths':converted,'resource_mismatches':bad,
            'controller_sha256':hashlib.sha256(controller).hexdigest(),'scope':'Independent frozen Git-object byte comparison. Native executable bytes are not supplied by the bounded QA artifact.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('checkout',type=Path);parser.add_argument('receipts',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=audit(args.checkout,args.receipts);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'all_checks_passed':result['all_checks_passed']}))
