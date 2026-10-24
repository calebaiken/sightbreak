"""Eight preregistered pure seam controls. Never imports the R2 validator."""
import ast
import copy
import ctypes
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
import unittest
from contextlib import ExitStack
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
ROOT=REPORT.parents[4]
OUT=REPORT/'pure-r1'
TRANSITIONS=[]
raw=(REPORT/'CLOCK_SEAM_V2B_PROPOSAL.py').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='a3fa48aa56900e01ca85a5e12dcb9f6980c9c9764600ec9fc37875a7d39cc34c'
clock_scope={}
exec(compile(raw,'<frozen clock proposal>','exec'),clock_scope)
DeclaredClock=clock_scope['DeclaredClock']
baseline=(ROOT/'scripts/test_windows_shutdown_study.py').read_text()
assert hashlib.sha256(baseline.encode()).hexdigest()=='a2cd1720a9006565c73f4012bb62b752fe7b68319dfa6b7265abdc4c21816010'
replacements=[
    ('        import time\n        from shutdown_evidence_fixtures import fixture_identity,write_complete_trial',
     '        from shutdown_evidence_fixtures import DeclaredClock,fixture_identity,write_complete_trial'),
    ('        owner=owner or Owner();identity=fixture_identity()',
     '        owner=owner or Owner();identity=fixture_identity();clock=DeclaredClock()'),
    ('row.update(monotonic=time.monotonic(),wall_unix_ns=time.time_ns(),job_handle=7,baseline_pid=99,',
     'row.update(monotonic=clock.monotonic(),wall_unix_ns=clock.time_ns(),job_handle=7,baseline_pid=99,'),
    ('client_pid=100+index,reopened_pid=200+index,observer=emit)',
     'client_pid=100+index,reopened_pid=200+index,observer=emit,clock=clock)'),
    ("        result=study.collect_trials(root,identity,owner,driver,identity_reader=read_identity,\n                                    load_evidence=lambda _:dict(strict_passed=evidence))",
     "        with patch.object(study,'time',clock):\n            result=study.collect_trials(root,identity,owner,driver,identity_reader=read_identity,\n                                        load_evidence=lambda _:dict(strict_passed=evidence))")]
applied=baseline
for old,new in replacements:
    assert applied.count(old)==1,old
    applied=applied.replace(old,new)


def helper_nodes(source):
    tree=ast.parse(source)
    owner=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Owner')
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StudyTests')
    helper=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='run_generated')
    return tree,owner,helper


class Harness:
    def __init__(self,collector_error=False):
        self.cleanups=[];self.clocks=[];self.writer_clocks=[];self.callbacks=[];self.identity_reads=0;self.collector_error=collector_error
        self.module=types.ModuleType('shutdown_evidence_fixtures')
        def factory():
            clock=DeclaredClock();self.clocks.append(clock);return clock
        def identity():return dict(source=dict(source_commit='exact'),artifact_record=dict(artifact=dict(sha256='same')),embedded_pck=dict(sha256='same'),host=dict(platform='same'))
        def writer(directory,identity,*,verbose,client_pid,reopened_pid,observer,clock):
            assert clock is self.study.time
            self.writer_clocks.append(clock)
            clock.advance(1.25)
            observer('native_launch',name='client',pid=client_pid)
            clock.advance(.25)
            observer('close_wait_finished',process='client',pid=client_pid)
        self.module.DeclaredClock=factory;self.module.fixture_identity=identity;self.module.write_complete_trial=writer
        self.study=types.SimpleNamespace(time=time,collect_trials=self.collect)
        tree,owner,helper=helper_nodes(applied)
        scope=dict(copy=copy,tempfile=tempfile,Path=Path,study=self.study,patch=patch)
        exec(compile(ast.Module(body=[copy.deepcopy(owner),copy.deepcopy(helper)],type_ignores=[]),'<extracted proposed pure helper>','exec'),scope)
        self.run=types.MethodType(scope['run_generated'],self)
    def addCleanup(self,callback):self.cleanups.append(callback)
    def cleanup(self):
        for callback in reversed(self.cleanups):callback()
    def collect(self,root,identity,owner,driver,*,identity_reader,load_evidence):
        if self.collector_error:raise RuntimeError('pure collector stub exception')
        root.mkdir();queries=[];errors=[]
        for index,arm in enumerate(('ordinary','verbose','verbose','ordinary'),1):
            identity_reader();self.identity_reads+=1
            queries.append(copy.deepcopy(owner.query('trial'+str(index)+'/before')))
            def observe(event,**details):
                outer=self.study.time.monotonic()
                row=owner.query('trial'+str(index)+'/'+event)
                self.callbacks.append(dict(event=event,outer=outer,job=copy.deepcopy(row),details=details))
                if event=='native_launch':owner.capture(details['pid'])
            args=['--output',str(root/str(index))]+(['--reopened-verbose'] if arm=='verbose' else [])
            try:driver(args,observe,root/str(index))
            except RuntimeError as error:errors.append(str(error))
            queries.append(copy.deepcopy(owner.query('trial'+str(index)+'/after')))
            identity_reader();self.identity_reads+=1
        return dict(queries=queries,errors=errors,stub=True)
    def invoke(self,**kwargs):
        with patch.dict(sys.modules,{'shutdown_evidence_fixtures':self.module}):return self.run(**kwargs)


class ClockControls(unittest.TestCase):
    def test_01_reads_are_pure_with_distinct_origins(self):
        c=DeclaredClock();state=vars(c).copy()
        for _ in range(4):self.assertEqual((c.monotonic(),c.time_ns(),c.perf_counter()),(1000.0,1792800000*10**9,200000.0))
        self.assertEqual(vars(c),state)
    def test_02_explicit_nanosecond_advances(self):
        c=DeclaredClock();expected=c.origin_ns
        for duration in (0,.1,.3,1e-9,300):
            expected+=round(duration*10**9);c.advance(duration)
            self.assertEqual(c.now_ns,expected);self.assertTrue(math.isfinite(c.monotonic()));self.assertTrue(math.isfinite(c.perf_counter()))
            self.assertEqual(c.time_ns()-c.wall_origin_ns,expected-c.origin_ns)
        self.assertAlmostEqual(c.perf_counter()-200000,c.monotonic()-1000,places=9)
    def test_03_wall_steps_only_affect_wall(self):
        c=DeclaredClock();mono=c.monotonic();perf=c.perf_counter();wall=c.time_ns()
        c.step_wall(-1000);self.assertEqual(c.time_ns(),wall-1000);c.step_wall(3000)
        self.assertEqual(c.time_ns(),wall+2000);self.assertEqual(c.monotonic(),mono);self.assertEqual(c.perf_counter(),perf)
        for bad in (True,.5,'1',None):
            before=vars(c).copy()
            with self.assertRaises(ValueError):c.step_wall(bad)
            self.assertEqual(vars(c),before)
    def test_04_invalid_durations_reject_without_mutation(self):
        c=DeclaredClock()
        for bad in (-1,True,'1',None,float('nan'),float('inf'),float('-inf')):
            before=vars(c).copy()
            with self.assertRaises(ValueError):c.advance(bad)
            self.assertEqual(vars(c),before)
    def test_05_finite_read_failure_does_not_commit_invalid_state(self):
        c=DeclaredClock();huge=10**308
        c.advance(huge);self.assertTrue(math.isfinite(c.monotonic()));self.assertTrue(math.isfinite(c.perf_counter()))
        before=vars(c).copy();error=None
        try:c.advance(huge)
        except (ValueError,OverflowError) as caught:error=type(caught).__name__+': '+str(caught)
        TRANSITIONS.append(dict(case='finite integer cumulative overflow',error=error,before=before,after=vars(c).copy(),plausible_study_schedule=False))
        self.assertIsNotNone(error)
        self.assertEqual(vars(c),before,'Rejected advancement must leave the usable clock unchanged')
    def test_06_only_five_registered_helper_sites_change(self):
        old,old_owner,old_helper=helper_nodes(baseline);new,new_owner,new_helper=helper_nodes(applied)
        dump=lambda n:ast.dump(n,include_attributes=False)
        self.assertEqual(dump(old_owner),dump(new_owner))
        for tree in (old,new):
            cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='StudyTests')
            cls.body=[n for n in cls.body if not isinstance(n,ast.FunctionDef) or n.name!='run_generated']
        self.assertEqual(dump(old),dump(new))
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(new)),113)
    def test_07_one_clock_for_four_trials_and_facade_restores(self):
        h=Harness();self.addCleanup(h.cleanup);original=(time.monotonic,time.time_ns,time.perf_counter)
        result,calls,owner,root=h.invoke()
        self.assertEqual(len(h.clocks),1);self.assertEqual(len(h.writer_clocks),4)
        self.assertTrue(all(c is h.clocks[0] for c in h.writer_clocks));self.assertEqual(h.identity_reads,8)
        self.assertEqual(len(calls),4);self.assertEqual(result['errors'],[])
        self.assertEqual(h.clocks[0].monotonic(),1006.0)
        times=[row['monotonic'] for row in result['queries']];self.assertEqual(times,sorted(times))
        self.assertTrue(all(row['outer']==row['job']['monotonic'] for row in h.callbacks))
        self.assertIs(h.study.time,time);self.assertEqual((time.monotonic,time.time_ns,time.perf_counter),original)
    def test_08_exception_restores_and_failed_arm_has_no_future_writer(self):
        failed=Harness(collector_error=True);self.addCleanup(failed.cleanup)
        with self.assertRaisesRegex(RuntimeError,'pure collector stub exception'):failed.invoke()
        self.assertIs(failed.study.time,time);self.assertEqual(failed.clocks[0].monotonic(),1000.0)
        h=Harness();self.addCleanup(h.cleanup)
        result,calls,owner,root=h.invoke(failures=(1,),observe=True)
        self.assertEqual(result['errors'],['preserved failure 1']);self.assertEqual(len(h.writer_clocks),3)
        self.assertEqual((root/'1/original-failure.bin').read_bytes(),bytes([1])*7)
        self.assertEqual((root/'1/results.json').read_bytes(),b'{"passed":false}\n')
        self.assertEqual([row['event'] for row in h.callbacks[:1]],['native_launch'])
        self.assertEqual(h.callbacks[0]['outer'],1000.0);self.assertEqual(h.clocks[0].monotonic(),1004.5)


def forbidden(*args,**kwargs):raise AssertionError('Real effect forbidden in clock controls')


def main():
    assert os.sched_getaffinity(0)=={4};assert not OUT.exists();OUT.mkdir()
    (OUT/'PROPOSED_HELPER_APPLIED_ONLY.py').write_text(applied)
    stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((subprocess,'Popen'),(subprocess,'run'),(os,'kill'),(os,'killpg'),(ctypes,'CDLL')):
            guard.enter_context(patch.object(obj,name,forbidden))
        if hasattr(ctypes,'WinDLL'):guard.enter_context(patch.object(ctypes,'WinDLL',forbidden))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ClockControls))
    (OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),successful=result.wasSuccessful(),failure_names=[t.id() for t,_ in result.failures],error_names=[t.id() for t,_ in result.errors],transitions=TRANSITIONS,proposal_imported_for_controls=True,compiled_clock_only=True,R2_validator_or_actual_collector_executed=False,native_API_helper_process_CI_trials=0)
    (OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
