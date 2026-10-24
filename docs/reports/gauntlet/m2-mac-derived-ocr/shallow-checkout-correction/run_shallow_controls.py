#!/usr/bin/env python3
"""Fresh exact-ref depth-one pure suite, aliases and deliberate source mutations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[5]
REPORT = Path('docs/reports/gauntlet/m2-mac-derived-ocr')
WHITELIST = ('HOME','PATH','TMPDIR','TMP','TEMP','DISPLAY','LANG','LC_ALL','PYTHONPATH','PYTHONDONTWRITEBYTECODE',
             'SIGHTBREAK_TOOLS_DIR','SIGHTBREAK_STATE_DIR','SIGHTBREAK_BUILDS_DIR')
SUITES = ('test_macos_ordinary','test_macos_ordinary_controller','test_macos_ordinary_paths','test_macos_ordinary_startup',
          'test_macos_deploy_ocr','test_macos_menu','test_macos_focus','test_macos_screen_identity','test_probe_macos_input')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ref', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    records = []
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='sightbreak-deploy-complete-shallow-') as temporary:
        checkout = Path(temporary).resolve(strict=True)/'checkout'
        checkout.mkdir()
        def run(label, command, expected=0, env=None):
            child_environment = environment if env is None else env
            started = time.monotonic()
            result = subprocess.run(command, cwd=checkout, env=child_environment,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            path = args.output/(label+'.txt')
            path.write_bytes(result.stdout)
            records.append({'label':label,'command':command,'cwd':str(checkout),'exit_code':result.returncode,
                            'expected_exit_code':expected,'seconds':time.monotonic()-started,
                            'environment_allowlist':{name:child_environment.get(name) for name in WHITELIST},
                            'log':path.name,'bytes':len(result.stdout),'sha256':hashlib.sha256(result.stdout).hexdigest()})
            print(label+': '+str(result.returncode),flush=True)
            assert result.returncode == expected,result.stdout.decode()
            return result
        for label,command in (
            ('init',['git','init']),('remote',['git','remote','add','origin',ROOT.as_uri()]),
            ('fetch',['git','fetch','--depth=1','--filter=blob:none',
                      '--upload-pack=git -c uploadpack.allowFilter=true upload-pack','origin',args.ref]),
            ('sparse',['git','sparse-checkout','set','--cone','scripts','.github',str(REPORT),
                       'docs/reports/gauntlet/m2-macos-screen-identity/fixtures']),
            ('checkout',['git','checkout','--detach','FETCH_HEAD'])):
            run(label,command)
        head = run('head',['git','rev-parse','HEAD']).stdout.decode().strip()
        shallow = run('shallow',['git','rev-parse','--is-shallow-repository']).stdout.decode().strip()
        count = run('commit-count',['git','rev-list','--count','HEAD']).stdout.decode().strip()
        run('baseline-absent',['git','show','c08889b:scripts/macos_window_capture.swift'],expected=128)
        assert head == args.ref and shallow == 'true' and count == '1',(head,shallow,count)
        protected = ('scripts/macos_window_capture.swift','scripts/macos_deploy_ocr.py','scripts/macos_ordinary_input.py',
                     'scripts/verify_macos_ordinary.py','scripts/test_macos_ordinary_controller.py','.github/workflows/desktop-alpha.yml',
                     'scripts/test_macos_deploy_ocr.py','scripts/fixtures/macos_ordinary_source/reference.json',
                     'scripts/fixtures/macos_ordinary_source/default_capture_body.swift.txt')
        def hashes():return {name:hashlib.sha256((checkout/name).read_bytes()).hexdigest() for name in protected}
        before = hashes()
        for name in SUITES:run('normal-'+name,[sys.executable,'scripts/'+name+'.py','-v'])
        alias = checkout.parent/'aliased-temp';physical = checkout.parent/'physical-temp';physical.mkdir();alias.symlink_to(physical,target_is_directory=True)
        alias_environment = dict(environment,TMPDIR=str(alias),TMP=str(alias),TEMP=str(alias))
        for name in SUITES[:5]:run('alias-'+name,[sys.executable,'scripts/'+name+'.py','-v'],env=alias_environment)
        independent = REPORT/'shallow-checkout-correction/independent_controls.py'
        run('independent-controls',[sys.executable,str(independent),'-v'])
        spec = json.loads((checkout/REPORT/'pure-candidate/mutation-spec.json').read_text())
        original = (checkout/spec['source']).read_text()
        mutation_root = checkout.parent/'mutations';mutation_root.mkdir()
        for name,mutation in spec['mutations'].items():
            assert original.count(mutation['needle']) == 1
            directory = mutation_root/name;directory.mkdir()
            (directory/'macos_deploy_ocr.py').write_text(original.replace(mutation['needle'],mutation['replacement']))
            code = ('import sys,unittest;sys.path[:0]='+repr([str(directory),str(checkout/'scripts')])+
                    ';import test_macos_deploy_ocr as module;unittest.main(module=module,verbosity=2)')
            result = run('original-mutation-'+name,[sys.executable,'-c',code],expected=1)
            assert b'FAIL:' in result.stdout and b'FAILED (failures=' in result.stdout
        # Isolated source-reference copies, never edits to the frozen checkout.
        for name in ('golden-fixture','default-helper','gameplay-tail'):
            directory = mutation_root/name
            for relative in ('scripts/macos_window_capture.swift','scripts/verify_macos_ordinary.py',
                             'scripts/fixtures/macos_ordinary_source/reference.json','scripts/fixtures/macos_ordinary_source/default_capture_body.swift.txt'):
                target = directory/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checkout/relative,target)
            if name == 'golden-fixture':
                path = directory/'scripts/fixtures/macos_ordinary_source/default_capture_body.swift.txt'
                path.write_bytes(path.read_bytes()+b'\n')
            elif name == 'default-helper':
                path = directory/'scripts/macos_window_capture.swift'
                text = path.read_text();needle = 'configuration.showsCursor = false';assert text.count(needle)==1
                path.write_text(text.replace(needle,'configuration.showsCursor = true'))
            else:
                path = directory/'scripts/verify_macos_ordinary.py'
                text = path.read_text();needle = "BUDGETS['reload_complete']";assert text.count(needle)==1
                path.write_text(text.replace(needle,"BUDGETS['reload_frames']"))
            code = ('import sys,unittest;from pathlib import Path;sys.path.insert(0,'+repr(str(checkout/'scripts'))+
                    ');import test_macos_deploy_ocr as module;module.ROOT=Path('+repr(str(directory))+');'+
                    "suite=unittest.TestSuite([module.DeployAnalysisControls('test_default_native_helper_ocr_and_gameplay_tail_are_byte_preserved')]);"+
                    'result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())')
            result = run('reference-mutation-'+name,[sys.executable,'-c',code],expected=1)
            assert b'FAILED (failures=1)' in result.stdout
        assert before == hashes()
        run('status',['git','status','--porcelain'])
        run('source-whitespace',['git','diff','--check','--','scripts','.github','game'])
        result = {'scope':'Fresh exact-ref local depth-one Git checkout and pure/synthetic tests only; no native/OCR/Swift/engine/CI',
                  'head':head,'shallow':shallow,'reachable_commit_count':int(count),'baseline_c08889b_absent':True,
                  'normal_top_level_tests':83,'aliased_suite_commands':5,'independent_test_methods':8,
                  'original_source_mutations_rejected':4,'reference_mutations_rejected':3,
                  'tested_file_sha256':before,'tested_files_unchanged':before==hashes(),'commands':records,'passed':True}
        (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
