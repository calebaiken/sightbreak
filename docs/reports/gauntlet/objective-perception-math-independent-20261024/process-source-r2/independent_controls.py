#!/usr/bin/env python3
"""Pure process-state models plus local Git metadata; no engine or real signals."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(os.environ['REVIEW_PROCESS_SOURCE']).resolve()
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
import acquire_fov_math_reference as acquisition
import fov_math_reference as reference
import test_fov_math_reference as fixtures

SOURCE='b6f25804cddc3e48faeec613a2daa7f392fb1990'
RESULTS={}


class IndependentProcessControls(unittest.TestCase):
    def test_bound_root_remains_owned_without_children_discovery(self):
        clock=fixtures.FakeClock();kernel=fixtures.FakeKernel();kernel.children=lambda pid:[]
        process=fixtures.FakeProcess(clock,kernel);tree=acquisition.OwnedTree(kernel,process.pid)
        tree.bind_root()
        result=acquisition.cleanup(process,tree,clock()+5,clock=clock,sleep=clock.sleep)
        self.assertTrue(result['root_birth_bound']);self.assertTrue(result['root_popen_waited'])
        self.assertIsNotNone(result['root_exit_code']);self.assertFalse(kernel.table)
        self.assertTrue(result['signals']) # Forced cleanup still cannot qualify acquisition.
        tree.close();RESULTS['direct_root_empty_discovery']=result

    def test_stale_children_pid_with_unrelated_parent_is_never_owned_or_signaled(self):
        kernel=fixtures.FakeKernel()
        kernel.table[200]=dict(pid=200,state='R',ppid=999,pgrp=777,session=777,start_ticks=456)
        kernel.children=lambda pid:[200] if pid==kernel.supervisor else []
        tree=acquisition.OwnedTree(kernel,100);tree.bind_root()
        tree.observe();seen=[dict(entry['identity']) for entry in tree.seen.values()]
        tree.signal_all(15)
        RESULTS['stale_child_parent']=dict(seen=seen,fake_signals=kernel.sent,unrelated_pid=200,actual_parent=999)
        tree.close()
        self.assertNotIn(200,[r['pid'] for r in seen])
        self.assertFalse(any(pid==200 for pid,signum in kernel.sent))

    def test_queued_owned_parent_reuse_cannot_import_unrelated_descendants(self):
        kernel=fixtures.FakeKernel()
        kernel.table[200]=dict(pid=200,state='R',ppid=100,pgrp=100,session=100,start_ticks=456)
        kernel.table[300]=dict(pid=300,state='R',ppid=200,pgrp=777,session=777,start_ticks=789)
        def children(pid):
            if pid==kernel.supervisor:return [100]
            if pid==100:return [200]
            if pid==200:
                # The native parent may reap its child while the observer queues it.
                # Its numeric PID is reused by an unrelated parent before recursion.
                kernel.table[200].update(ppid=999,start_ticks=457,pgrp=777,session=777)
                return [300]
            return []
        kernel.children=children
        tree=acquisition.OwnedTree(kernel,100);tree.bind_root();tree.observe()
        seen=[dict(entry['identity']) for entry in tree.seen.values()]
        tree.signal_all(15)
        RESULTS['queued_parent_reuse']=dict(seen=seen,fake_signals=kernel.sent,unrelated_child_pid=300,reused_parent_pid=200)
        tree.close()
        self.assertNotIn(300,[r['pid'] for r in seen])
        self.assertFalse(any(pid==300 for pid,signum in kernel.sent))

    def test_observer_exception_fails_and_reaps_fake_known_popen(self):
        trial=fixtures.SupervisorControls(methodName='test_one_isolated_pinned_invocation_and_complete_success')
        trial.raw=fixtures.encoded(fixtures.declared_records())
        tmp,out,report,calls,kernel,process,clock=trial.trial(observer_error=True)
        try:
            self.assertFalse(report['passed']);self.assertEqual(len(calls),1)
            self.assertEqual(report['spawned_pid'],100);self.assertTrue(process.killed)
            self.assertIsNotNone(process.returncode);self.assertFalse(kernel.table)
            self.assertTrue(report['failure_log_coverage_complete'])
            RESULTS['observer_exception']=dict(error=report.get('error'),cleanup_error=report.get('cleanup_error'),
                                               fake_returncode=process.returncode,
                                               terminal_code_persisted='native_exit' in report or 'cleanup' in report)
        finally:tmp.cleanup()

    def test_original_failed_input_roundtrip_remains_rejected(self):
        raw=HERE.parent/'actual-r1/originals'
        payload=json.loads((raw/'project/cases.json').read_text())
        with self.assertRaisesRegex(ValueError,'input scalar roundtrip'):
            reference.parse_output((raw/'stdout.log').read_bytes(),payload,
                                   cases_sha256=hashlib.sha256((raw/'project/cases.json').read_bytes()).hexdigest(),
                                   program_sha256=hashlib.sha256((raw/'project/reference.gd').read_bytes()).hexdigest())
        RESULTS['original_scalar_failure_preserved']=True

    def test_physical_source_bytes_and_modes_cannot_hide_behind_git_flags(self):
        if os.environ.get('REVIEW_REAL_GIT_MUTATIONS')!='1':
            self.skipTest('Real Git mutations run only in the new owned exact source view')
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),SOURCE)
        baseline=acquisition.source_binding(SOURCE,deadline=160.,clock=lambda:100.)
        controls=[]
        variants=[('component-byte','tools/fov_math_reference/reference.gd',False),
                  ('component-mode','tools/fov_math_reference/project.godot',True),
                  ('imported-native-log-byte','scripts/native_log.py',False)]
        for name,relative,mode_only in variants:
            path=ROOT/relative;original=path.read_bytes();mode=path.stat().st_mode & 0o777
            subprocess.run(['git','update-index','--assume-unchanged','--',relative],cwd=ROOT,check=True)
            try:
                if mode_only:path.chmod(mode ^ 0o111)
                else:path.write_bytes(original+b'\n# Independent benign physical source-binding control.\n')
                status=subprocess.check_output(['git','status','--porcelain=v1','--',relative],cwd=ROOT,text=True)
                diff=subprocess.run(['git','diff','--quiet','--',relative],cwd=ROOT).returncode
                caught=None;binding=None
                try:binding=acquisition.source_binding(SOURCE,deadline=160.,clock=lambda:100.)
                except (RuntimeError,ValueError,subprocess.SubprocessError) as error:caught=type(error).__name__+': '+str(error)
                controls.append(dict(name=name,path=relative,git_status=status,git_diff_exit=diff,
                                     physical_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                     expected_sha256=hashlib.sha256(original).hexdigest(),
                                     physical_mode=oct(path.stat().st_mode & 0o777),expected_mode=oct(mode),
                                     guard_rejected=caught is not None,error=caught,
                                     returned_binding_equal_to_baseline=binding==baseline))
                with self.subTest(name=name):self.assertIsNotNone(caught,'hidden physical source/mode change accepted')
            finally:
                path.write_bytes(original);path.chmod(mode)
                subprocess.run(['git','update-index','--no-assume-unchanged','--',relative],cwd=ROOT,check=True)
        RESULTS['physical_source_controls']=controls
        self.assertEqual(acquisition.source_binding(SOURCE,deadline=160.,clock=lambda:100.),baseline)
        self.assertEqual(subprocess.check_output(['git','status','--porcelain=v1'],cwd=ROOT),b'')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentProcessControls))
    report=dict(source=str(ROOT),methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
                scope='Pure fake states and own local Git metadata; no engine/process/helper/proc probe or real signal',results=RESULTS)
    Path(os.environ['REVIEW_PROCESS_OUTPUT']).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},sort_keys=True))
    sys.exit(not result.wasSuccessful())
