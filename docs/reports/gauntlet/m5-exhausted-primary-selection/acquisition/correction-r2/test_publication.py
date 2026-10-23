#!/usr/bin/env python3
"""Source-only publication boundary controls; no real process or signal."""
from contextlib import ExitStack
import copy
import json
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import run_acquisition as a


class PublicationControls(unittest.TestCase):
    def publish(self,block='candidate',point=None,delay=0,error=None,first_failure=None,repeat=False,mismatch=False):
        with TemporaryDirectory() as tmp, ExitStack() as stack:
            output=Path(tmp);journal=output/'claim.json';clock=[0.];alarms=[];events=[]
            stack.enter_context(patch.object(a.time,'monotonic',side_effect=lambda:clock[0]))
            stack.enter_context(patch.object(a.signal,'setitimer',side_effect=lambda _s,t:alarms.append(t)))
            seconds=a.BLOCKS[block][0];budget=a.Budget(seconds);clock[0]=seconds-1
            report=dict(block=block,expected_source_head='a'*40,passed=first_failure is None,
                        failure=copy.deepcopy(first_failure),finalization_failures=[])
            real_write,real_read=a.write,a.read_record
            triggered=[False]
            def event(operation,path):
                label=operation+('-overall' if path.name=='overall.receipt.json' else '-journal')
                events.append(dict(event=label,elapsed=clock[0],active_alarm=alarms[-1] if alarms else None))
                if label==point and (repeat or not triggered[0]):
                    triggered[0]=True;clock[0]+=delay
                    if error:raise error
            def write(path,value):
                event('write',path);real_write(path,value)
            def read(path):
                event('read',path);value=real_read(path)
                if mismatch and path.name=='overall.receipt.json':value['tampered']=True
                return value
            stack.enter_context(patch.object(a,'write',side_effect=write))
            stack.enter_context(patch.object(a,'read_record',side_effect=read))
            a.publish_overall(output,journal,report,budget)
            files={path.name:json.loads(path.read_text()) for path in (output/'overall.receipt.json',journal) if path.exists()}
            return report,files,events,budget,clock[0]

    def test_success_confirms_both_artifacts_under_both_original_caps(self):
        for block in a.BLOCKS:
            with self.subTest(block=block):
                report,files,events,budget,now=self.publish(block)
                self.assertTrue(report['passed']);self.assertTrue(report['publication_confirmed'])
                self.assertEqual(report['wall_seconds'],a.BLOCKS[block][0]-1)
                self.assertEqual(len(report['publication_readbacks']),2)
                self.assertEqual([row['event'] for row in events],['write-overall','write-journal','read-overall','read-journal'])
                self.assertTrue(all(row['active_alarm']>0 for row in events))
                self.assertNotIn('wall_seconds',files['overall.receipt.json'])
                self.assertEqual(files['overall.receipt.json']['wall_seconds_before_publication'],now)
                self.assertIsNone(budget.finalization_deadline)

    def test_each_late_write_and_readback_demotes_both_artifacts(self):
        for block in a.BLOCKS:
            for point in ('write-overall','write-journal','read-overall','read-journal'):
                with self.subTest(block=block,point=point):
                    report,files,_,budget,now=self.publish(block,point,delay=2)
                    self.assertFalse(report['passed']);self.assertTrue(report['publication_confirmed'])
                    self.assertEqual(report['failure']['type'],'BoundExceeded')
                    self.assertGreater(now,a.BLOCKS[block][0]);self.assertEqual(report['wall_seconds'],now)
                    self.assertTrue(budget.failed)
                    self.assertTrue(all(value['passed'] is False for value in files.values()))

    def test_publication_interrupt_and_io_error_are_terminal(self):
        for error in (KeyboardInterrupt('injected interrupt'),OSError('injected I/O failure')):
            for point in ('write-overall','write-journal','read-overall','read-journal'):
                with self.subTest(error=type(error).__name__,point=point):
                    report,files,_,_,_=self.publish(point=point,error=error)
                    self.assertFalse(report['passed']);self.assertTrue(report['publication_confirmed'])
                    self.assertEqual(report['failure']['type'],type(error).__name__)
                    self.assertTrue(all(value['passed'] is False for value in files.values()))

    def test_first_failure_is_preserved_if_emergency_publication_fails(self):
        original=dict(type='PhaseFailed',message='original strict leak')
        report,_,events,budget,_=self.publish(point='write-journal',error=OSError('receipt failure'),first_failure=original,repeat=True)
        self.assertFalse(report['passed']);self.assertFalse(report['publication_confirmed'])
        self.assertEqual(report['failure'],original)
        self.assertTrue(any('receipt failure' in row['message'] for row in report['finalization_failures']))
        self.assertEqual(sum(row['event']=='write-overall' for row in events),1)
        self.assertTrue(budget.failed)

    def test_repeated_slow_failure_publication_cannot_reset_allowance(self):
        report,files,events,budget,now=self.publish(point='write-overall',delay=6,repeat=True)
        self.assertFalse(report['passed']);self.assertFalse(report['publication_confirmed'])
        self.assertEqual(budget.finalization_deadline,a.BLOCKS['candidate'][0]-1+6+5)
        self.assertGreater(now,budget.finalization_deadline)
        self.assertEqual(sum(row['event']=='write-overall' for row in events),2)
        self.assertFalse(files['overall.receipt.json']['passed'])

    def test_mismatched_readback_is_not_confirmed_success(self):
        report,files,_,_,_=self.publish(mismatch=True)
        self.assertFalse(report['passed']);self.assertFalse(report['publication_confirmed'])
        self.assertIn('readback differs',report['failure']['message'])
        self.assertTrue(all(value['passed'] is False for value in files.values()))

    def test_emergency_allowance_cannot_publish_success_or_resume_normal_work(self):
        with TemporaryDirectory() as tmp,patch.object(a.time,'monotonic',return_value=0),patch.object(a.signal,'setitimer'):
            budget=a.Budget(240)
            with self.assertRaisesRegex(RuntimeError,'cannot publish success'):budget.finish_alarm(failed=False)
            deadline=budget.finish_alarm(failed=True)
            with self.assertRaisesRegex(RuntimeError,'failure-only'):
                a.checked_publication([(Path(tmp)/'bad.json',dict(passed=True))],budget,deadline,failed_publication=True)
            with self.assertRaisesRegex(RuntimeError,'cannot resume'):budget.arm()


class PhasePublicationControls(unittest.TestCase):
    def phase(self,point):
        with TemporaryDirectory() as tmp,ExitStack() as stack:
            output=Path(tmp);clock=[0.];alive=[True]
            process=SimpleNamespace(pid=5001,returncode=None)
            def poll():alive[0]=False;process.returncode=0;return 0
            process.poll=poll
            row=dict(pid=5001,ppid=10,pgid=5001,sid=5001,start_ticks=123,state='R',comm='mock',exe='/mock')
            def spawn(*_,**kw):kw['stdout'].write(b'complete success\n');return process
            real_write,real_read,real_failed=a.write,a.read_record,a.failed
            def write(path,value):
                real_write(path,value)
                if point=='write' and path.name=='phase.receipt.json':clock[0]=121
            def read(path):
                value=real_read(path)
                if point=='read' and path.name=='phase.receipt.json':clock[0]=121
                return value
            def failed(text):
                value=real_failed(text)
                if point=='classification':clock[0]=121
                return value
            for target,value in [('proc_snapshot',lambda:{5001:row} if alive[0] else {}),('write',write),('read_record',read),('failed',failed)]:
                stack.enter_context(patch.object(a,target,value))
            stack.enter_context(patch.object(a.subprocess,'Popen',side_effect=spawn))
            stack.enter_context(patch.object(a.time,'monotonic',side_effect=lambda:clock[0]))
            stack.enter_context(patch.object(a.os,'pidfd_open',return_value=99))
            stack.enter_context(patch.object(a.os,'close'))
            stack.enter_context(patch.object(a.signal,'pthread_sigmask',return_value=set()))
            stack.enter_context(patch.object(a.signal,'setitimer'))
            runner=a.Runner(output,a.Budget(240));error=None
            env={key:'/private/'+key for key in ('SIGHTBREAK_STATE_DIR','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','ANDROID_USER_HOME')}
            try:runner.native('phase',['/never-launched'],env,120)
            except BaseException as caught:error=caught
            return runner.receipts[0],json.loads((output/'phase.receipt.json').read_text()),error

    def test_phase_classification_write_and_readback_costs_count(self):
        for point in ('classification','write','read'):
            with self.subTest(point=point):
                report,stored,error=self.phase(point)
                self.assertFalse(report['passed']);self.assertFalse(stored['passed'])
                self.assertIsNotNone(error);self.assertEqual(report['wall_seconds'],121)


class ResultInventoryControls(unittest.TestCase):
    GOOD=dict(bot_ai_regression='BOT_AI_REGRESSION_TESTS_OK',
              bot_dry_weapon='BOT_DRY_WEAPON_RESULT '+json.dumps(dict(cases=84,sequence_steps=48,checks=590,failures=0,passed=True)),
              bot_squad_symmetry='BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion')

    def test_all_explicit_failure_prefixes_reject_beside_each_success(self):
        for suite,success in self.GOOD.items():
            for failure in ('BOT_AI_REGRESSION_FAILURE x','BOT_DRY_WEAPON_FAILURE x','BOT_SQUAD_FAILURE x'):
                with self.subTest(suite=suite,failure=failure),self.assertRaises(RuntimeError):
                    a.completed_suite(suite,success+'\n'+failure)

    def test_duplicate_extra_and_malformed_result_inventory_rejects(self):
        for suite,success in self.GOOD.items():
            extras=[success,success.split(' ',1)[0]+' malformed']
            if suite=='bot_ai_regression':extras+=['BOT_AI_REGRESSION_TESTS_FAILED','BOT_AI_REGRESSION_RESULT malformed']
            for extra in extras:
                with self.subTest(suite=suite,extra=extra),self.assertRaises((RuntimeError,ValueError,IndexError)):
                    a.completed_suite(suite,success+'\n'+extra)


if __name__=='__main__':unittest.main(verbosity=2)
