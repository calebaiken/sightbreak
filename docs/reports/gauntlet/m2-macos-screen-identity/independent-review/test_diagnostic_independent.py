#!/usr/bin/env python3
"""Independent pure Python orchestration checks. Every engine process is mocked."""
import argparse
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
parser=argparse.ArgumentParser()
parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parent/'exact-source-4df02e9')
parser.add_argument('--results',type=Path,default=Path(__file__).resolve().parent/'independent-diagnostic-4df02e9-results.json')
args,rest=parser.parse_known_args()
sys.path.insert(0,str(args.source/'scripts'))
import diagnose_native_input_mode as diagnostic

observations=[]
IDENTITY={'source_commit':'invented-review-commit','source_game_tree':'invented-review-game',
          'source_content_sha256':'invented-review-content','source_validation_sha256':'invented-review-validation',
          'source_dirty':False,'source_game_dirty':False}

class Clock:
    def __init__(self): self.now=0
    def monotonic(self): return self.now

class IndependentDiagnostic(unittest.TestCase):
    def fixture(self,root):
        game=root/'source/game';game.mkdir(parents=True)
        (game/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Synthetic never executed"\n')
        (game/'tests').mkdir();(game/'tests/input_mode_test.gd').write_text('# Synthetic never executed\n')
        original=root/'original';original.mkdir()
        (original/'results.json').write_text(json.dumps([{'suite':'input_mode','exit':0,'clean_log':False}]))
        isolation={'passed':False,'failure':{'message':'input_mode failed; raw output retained'},
                   'source_resources_unchanged':True,'copied_resources_unchanged':True,
                   'temporary_project_removed':True,'finalization_failures':[],
                   'cleanup':[{'removed':True}],'source_resources_sha256':diagnostic.inventory(game)}
        (original/'isolation.json').write_text(json.dumps(isolation))
        (original/'input_mode.log').write_text('WARNING: 2 ObjectDB instances were leaked at exit\n')
        return game,original

    def exercise(self,root,mode='clean',missing=None):
        game,original=self.fixture(root)
        if missing: (original/missing).unlink()
        original_bytes={p.name:p.read_bytes() for p in original.iterdir()}
        state={'commands':[],'waits':[],'reaped':[],'private_projects':set(),'user_namespaces':set()}
        clock=Clock()
        class FakeProcess:
            def __init__(self,command,**kwargs):
                state['commands'].append(command)
                self.pid=74000+len(state['commands'])
                self.returncode=0
                self.command=command
                self.label='unknown'
                if not kwargs.get('start_new_session'): raise AssertionError('Process was not owned by a new session')
                project=Path(command[command.index('--path')+1]);state['private_projects'].add(str(project.parent))
                if '--editor' in command:
                    self.label='private-import'
                    if mode=='import_leak': kwargs['stdout'].write('WARNING: ObjectDB instances leaked at exit\n')
                elif 'res://tests/input_mode_test.gd' in command:
                    self.label='input_mode'
                    if '--verbose' not in command: raise AssertionError('Input mode was not verbose')
                    custom=json.loads(re.search(r'^config/custom_user_dir_name=(.+)$',(project/'project.godot').read_text(),re.M).group(1))
                    user=root/'native-data'/custom;user.mkdir(parents=True,exist_ok=True)
                    (user/'offline_training.json').write_text('{"synthetic":true}\n')
                    kwargs['stdout'].write('Synthetic checks only, no engine executed\n')
                    if mode=='suite_leak':kwargs['stdout'].write('WARNING: 2 ObjectDB instances were leaked at exit\n')
                    if mode=='mutate_original': (original/'input_mode.log').write_text('external synthetic alteration\n')
                else:
                    self.label='producer'
                    if '--verbose' in command:raise AssertionError('Probe command unexpectedly verbose')
                    custom=json.loads(re.search(r'^config/custom_user_dir_name=(.+)$',(project/'project.godot').read_text(),re.M).group(1))
                    user=root/'native-data'/custom;user.mkdir(parents=True,exist_ok=True)
                    state['user_namespaces'].add(str(user.parent))
                    receipt={'data_dir':str(root/'native-data'),'user_data_dir':str(user),
                             'custom_user_dir':custom,'uses_custom_user_dir':True,'project_path':str(project),
                             'profile_exists':(user/'offline_training.json').exists(),'diagnostics_exist':False,
                             'os':'Synthetic no native API'}
                    destination=next(x.split('=',1)[1] for x in command if x.startswith('--receipt='))
                    Path(destination).write_text(json.dumps(receipt))
                    if mode=='probe_leak':kwargs['stdout'].write('WARNING: ObjectDB instances leaked at exit\n')
            def wait(self,timeout):
                state['waits'].append(timeout)
                clock.now+=1
                if mode=='suite_timeout' and self.label=='input_mode':
                    self.returncode=-15
                    raise subprocess.TimeoutExpired(self.command,timeout)
                if mode=='deadline_overrun' and self.label=='input_mode':clock.now=241
            def poll(self):return self.returncode
        def reap(process):
            state['reaped'].append(process.pid)
            return {'pid':process.pid,'owned_group_gone':mode!='cleanup_failure','signals_sent':[], 'exit_code':process.returncode}
        counter={'calls':0}
        def identity():
            counter['calls']+=1
            value=copy.deepcopy(IDENTITY)
            if mode=='dirty_after' and counter['calls']>1:value['source_dirty']=True
            if mode=='sourcecheck_overrun' and counter['calls']>1:clock.now=241
            return value
        inherited_exit = diagnostic.NativeSceneSuites.__exit__
        def finalization(runner,*details):
            result=inherited_exit(runner,*details)
            if mode=='finalization_overrun':clock.now=241
            return result
        with (patch.object(diagnostic.NativeSceneSuites,'__exit__',finalization),
              patch.object(diagnostic.platform,'system',return_value='Darwin'),
              patch.object(diagnostic.platform,'machine',return_value='arm64'),
              patch.object(diagnostic,'source',side_effect=identity),
              patch.object(diagnostic.toolchain,'ROOT',game.parent),
              patch.object(diagnostic.toolchain,'verify_engine',return_value={'synthetic':True}),
              patch.object(diagnostic.toolchain,'binary',return_value='never-executed-engine'),
              patch.object(diagnostic.toolchain,'environment',return_value={}),
              patch.object(diagnostic.subprocess,'Popen',FakeProcess),
              patch.object(diagnostic,'reap',side_effect=reap),
              patch.object(diagnostic.time,'monotonic',side_effect=clock.monotonic),
              contextlib.redirect_stdout(io.StringIO())):
            code=diagnostic.run(original,root/'new')
        report=json.loads((root/'new/diagnostic.json').read_text())
        state['original_unchanged']={p.name:p.read_bytes() for p in original.iterdir()}==original_bytes
        state['private_projects_removed']=all(not Path(p).exists() for p in state['private_projects'])
        state['user_namespace_existence']={p:Path(p).exists() for p in state['user_namespaces']}
        observations.append({'mode':mode,'missing':missing,'exit':code,'state':state,'report':report})
        return code,report,state,root/'new'

    def test_actual_inherited_lifecycle_cleans_only_owned_temp_state_and_retains_produced_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            # Preserve unrelated data beside the uniquely owned namespace.
            unknown=root/'native-data/other-application/save';unknown.parent.mkdir(parents=True)
            unknown.write_text('preserve me')
            code,report,state,out=self.exercise(root)
            self.assertEqual(code,0);self.assertTrue(report['passed'])
            self.assertFalse(report['strict_gate_repaired']);self.assertTrue(state['original_unchanged'])
            self.assertEqual(unknown.read_text(),'preserve me')
            self.assertTrue(state['private_projects_removed'])
            self.assertFalse(any(state['user_namespace_existence'].values()))
            self.assertEqual(len(state['commands']),5)
            self.assertEqual(len(state['reaped']),5)
            self.assertTrue(all(0<t<=240 for t in state['waits']))
            suites=json.loads((out/'repeat/results.json').read_text())
            self.assertEqual(len(suites),1);self.assertEqual(suites[0]['suite'],'input_mode')
            self.assertFalse(suites[0]['before']['profile_exists']);self.assertTrue(suites[0]['after']['profile_exists'])
            produced=out/'repeat/input_mode-userdata/offline_training.json'
            self.assertEqual(suites[0]['produced_files_sha256']['offline_training.json'],hashlib.sha256(produced.read_bytes()).hexdigest())
            self.assertTrue(report['isolation']['source_resources_unchanged'])
            self.assertTrue(report['isolation']['copied_resources_unchanged'])

    def test_leaky_repeat_remains_failed_with_raw_warning_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            code,report,state,out=self.exercise(Path(temporary),'suite_leak')
            self.assertEqual(code,1);self.assertFalse(report['passed']);self.assertEqual(report['status'],'FAILED')
            self.assertFalse(report['strict_gate_repaired']);self.assertTrue(state['original_unchanged'])
            self.assertIn('ObjectDB',(out/'repeat/input_mode.log').read_text())
            self.assertFalse(json.loads((out/'repeat/results.json').read_text())[0]['clean_log'])
            self.assertTrue(state['private_projects_removed']);self.assertFalse(any(state['user_namespace_existence'].values()))

    def test_import_and_probe_warning_failures_stop_before_suite(self):
        for mode in ('import_leak','probe_leak'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                code,report,state,out=self.exercise(Path(temporary),mode)
                self.assertEqual(code,1);self.assertFalse(report['passed'])
                self.assertFalse(any('res://tests/input_mode_test.gd' in command for command in state['commands']))
                self.assertTrue(state['private_projects_removed']);self.assertTrue(state['original_unchanged'])

    def test_suite_timeout_and_deadline_overrun_fail_and_keep_owned_receipts(self):
        for mode in ('suite_timeout','deadline_overrun'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                code,report,state,out=self.exercise(Path(temporary),mode)
                self.assertEqual(code,1);self.assertFalse(report['passed'])
                self.assertTrue(state['private_projects_removed']);self.assertTrue(state['original_unchanged'])
                self.assertFalse(any(state['user_namespace_existence'].values()))
                self.assertEqual(len(state['commands']),len(state['reaped']))
                owned=json.loads((out/'repeat/owned-processes.json').read_text())
                self.assertTrue(all(p['cleanup']['owned_group_gone'] for p in owned))
                self.assertTrue(any(p['timed_out'] for p in owned) if mode=='suite_timeout' else report['seconds']>240)

    def test_failed_owned_process_cleanup_cannot_qualify_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            code,report,state,out=self.exercise(Path(temporary),'cleanup_failure')
            self.assertEqual(code,1);self.assertFalse(report['passed'])
            self.assertTrue(state['private_projects_removed']);self.assertTrue(state['original_unchanged'])
            self.assertIn('group remained',report['failure']['message'])

    def test_final_source_or_original_evidence_mutation_defeats_clean_repeat(self):
        for mode in ('dirty_after','mutate_original'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                code,report,state,out=self.exercise(Path(temporary),mode)
                self.assertEqual(code,1);self.assertFalse(report['passed']);self.assertEqual(report['status'],'FAILED')
                self.assertIn('finalization_failure',report)
                self.assertFalse(report['strict_gate_repaired'])
                self.assertTrue(state['private_projects_removed']);self.assertFalse(any(state['user_namespace_existence'].values()))

    def test_finalization_and_source_receipt_deadlines_cannot_qualify_repeat(self):
        for mode in ('finalization_overrun','sourcecheck_overrun'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temporary:
                code,report,state,out=self.exercise(Path(temporary),mode)
                self.assertEqual(code,1);self.assertFalse(report['passed']);self.assertEqual(report['status'],'FAILED')
                self.assertTrue(state['original_unchanged']);self.assertTrue(state['private_projects_removed'])
                self.assertFalse(any(state['user_namespace_existence'].values()))
                self.assertGreater(report['seconds'],240)

    def test_missing_original_failure_receipt_skips_without_a_process(self):
        for missing in ('results.json','isolation.json','input_mode.log'):
            with self.subTest(missing=missing),tempfile.TemporaryDirectory() as temporary:
                code,report,state,out=self.exercise(Path(temporary),missing=missing)
                self.assertEqual(state['commands'],[]);self.assertTrue(state['original_unchanged'])
                self.assertEqual(code,0)
                self.assertEqual(report['status'],'SKIPPED_DIFFERENT_OR_UNPROVEN_FAILURE')
                self.assertFalse(report['passed']);self.assertFalse(report['strict_gate_repaired'])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IndependentDiagnostic)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    args.results.write_text(json.dumps({'source':str(args.source.resolve()),'tests':result.testsRun,
                                      'runs':len(observations),'failed':len(result.failures)+len(result.errors),
                                      'observations':observations},indent=2,default=lambda item:sorted(item) if isinstance(item,set) else str(item))+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
