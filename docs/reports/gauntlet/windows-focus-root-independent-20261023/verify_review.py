"""Verify bounded exact-root source review receipts."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
SOURCE = Path('/workspace/reviews/windows-focus-root-a089-source')
FREEZE = 'a089473481ced0f2e7b2a7468bbc5d079f92f0ff'


def main():
    binding = json.loads((OUT / 'source-binding.json').read_text())
    assert binding['source_freeze'] == FREEZE and binding['exact_source_union']
    assert binding['assertion_count'] == 465 and binding['tracked_code_files_bound'] == 431
    assert binding['attempt_limit'] == 1 and not binding['dispatch_performed']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE,text=True).strip() == FREEZE
    assert subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE) == b''
    groups = [('test_native_focus_fence',16,0), ('test_focus_resume_timing',8,0),
        ('test_offline_capture_fences',15,0), ('test_macos_menu',11,0),
        ('test_native_observation',7,3), ('test_offline_export_ocr',5,0),
        ('test_macos_ordinary',14,0), ('test_macos_ordinary_controller',7,0),
        ('test_macos_ordinary_paths',2,0), ('test_macos_ordinary_startup',11,0),
        ('test_build_manifest',24,0), ('test_package_qa_receipts',8,0)]
    tests = []
    for name, count, skips in groups:
        filename = 'test_build_manifest-restored.log' if name == 'test_build_manifest' else name + '.log'
        path = OUT / filename
        text = path.read_text()
        assert re.search(r'Ran ' + str(count) + r' tests? in ', text), name
        assert ('OK (skipped=' + str(skips) + ')' if skips else 'OK') in text.splitlines(), name
        tests.append({'command':['python3','scripts/' + name + '.py','-v'],
            'cwd':str(SOURCE),'source_freeze':FREEZE,'exit':0,'methods':count,'skips':skips,
            'log':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    failed = (OUT / 'test_build_manifest.log').read_text()
    assert 'FAILED (errors=2)' in failed and "KeyError: 'preset.1.options'" in failed
    setup = json.loads((OUT / 'setup-failure.json').read_text())
    assert setup['initial_exit'] == 1 and setup['corrected_exit'] == 0
    assert sum(row['methods'] for row in tests) == 128 and sum(row['skips'] for row in tests) == 3
    receipt = {'source_freeze':FREEZE,'verdict':'ACCEPT_SOURCE_READINESS_ONE_UNCHANGED_WINDOWS_WORKFLOW',
        'scope':'source-only; no dispatch or runtime/living-input/gameplay acceptance',
        'source_identity':binding['source_identity'],'source_audit_assertions':binding['assertion_count'],
        'pure_groups':len(tests),'pure_methods':128,'skips':3,'pure_checks':tests,
        'initial_sparse_setup_failure_retained':True,'setup_failure_receipt':'setup-failure.json',
        'source_checkout_clean':True,'attempt_limit':1,'dispatch_performed':False,
        'retained_files':{path.name:{'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(OUT.iterdir()) if path.is_file() and path.name != 'review-checks.json'}}
    (OUT / 'review-checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({key:value for key,value in receipt.items() if key not in ('retained_files','pure_checks')}))


if __name__ == '__main__':
    main()
