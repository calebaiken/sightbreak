#!/usr/bin/env python3
"""Independent pure publication integration challenges; no native effects."""
from contextlib import ExitStack
import copy
import gzip
import hashlib
import json
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ACQUISITION = HERE.parent/'acquisition'
sys.path.insert(0,str(ACQUISITION))
import run_acquisition as a

raw = gzip.decompress((ACQUISITION/'correction-r2/original-independent-controls.py.gz').read_bytes())
assert hashlib.sha256(raw).hexdigest() == 'e6d26dcdbd7935dbb15fcbf7c936969ef732aef61f2e787c9a41a3ddccb5376c'
original = types.ModuleType('immutable_original_controls')
original.__file__ = str(HERE/'immutable_original_controls.py')
exec(compile(raw,original.__file__,'exec'),original.__dict__)

WITNESSES = {}


def publication(block='candidate',costs=None,first_failure=None,read_error=None,
                fail_demotion=False,already_failed=False):
    """Exercise the production publication controller with independent I/O faults."""
    costs = costs or {}
    with TemporaryDirectory() as tmp, ExitStack() as stack:
        output = Path(tmp)
        journal = output/'claim.json'
        seconds = a.BLOCKS[block][0]
        clock = [0.0]
        events,alarms = [],[]
        stack.enter_context(patch.object(a.time,'monotonic',side_effect=lambda:clock[0]))
        stack.enter_context(patch.object(a.signal,'setitimer',side_effect=lambda _which,delay:alarms.append(delay)))
        budget = a.Budget(seconds)
        clock[0] = seconds-1
        report = dict(block=block,expected_source_head='b'*40,passed=first_failure is None,
                      failure=copy.deepcopy(first_failure),finalization_failures=[])
        if already_failed:
            budget.finish_alarm(failed=True)
        real_write,real_read = a.write,a.read_record
        hits = {}

        def event(operation,path,value=None):
            name = operation+'-'+('overall' if path.name=='overall.receipt.json' else 'journal')
            hits[name] = hits.get(name,0)+1
            events.append(dict(name=name,at=clock[0],active_alarm=alarms[-1],
                               passed=None if value is None else value['passed']))
            # Costs apply once to normal I/O; failure-only recovery is separate.
            if hits[name]==1:
                clock[0] += costs.get(name,0)
                if name==read_error:
                    raise OSError('independent readback failure')
            if operation=='write' and fail_demotion and value['passed'] is False:
                raise OSError('independent failure-demotion write refused')

        def write(path,value):
            event('write',path,value)
            real_write(path,value)

        def read(path):
            event('read',path)
            return real_read(path)

        stack.enter_context(patch.object(a,'write',side_effect=write))
        stack.enter_context(patch.object(a,'read_record',side_effect=read))
        returned = a.publish_overall(output,journal,report,budget)
        files = {path.name:json.loads(path.read_text()) for path in (output/'overall.receipt.json',journal) if path.exists()}
        # A terminally failed budget must prevent another native launch entirely.
        with patch.object(a.subprocess,'Popen') as spawn:
            if budget.failed:
                with unittest.TestCase().assertRaises(RuntimeError):
                    a.Runner(output,budget).native('forbidden',['/never-run'],{},30)
                spawn.assert_not_called()
        return dict(report=returned,files=files,events=events,elapsed=clock[0],
                    emergency_deadline=budget.finalization_deadline,budget_failed=budget.failed)


class IndependentR2Controls(unittest.TestCase):
    def test_clean_both_caps_require_complete_readback_set_with_positive_alarm(self):
        for block in a.BLOCKS:
            result = publication(block,costs={name:.1 for name in ('write-overall','write-journal','read-overall','read-journal')})
            self.assertTrue(result['report']['passed'])
            self.assertTrue(result['report']['publication_confirmed'])
            self.assertEqual(len(result['report']['publication_readbacks']),2)
            self.assertEqual([event['name'] for event in result['events']],['write-overall','write-journal','read-overall','read-journal'])
            self.assertTrue(all(event['active_alarm']>0 for event in result['events']))
            self.assertLessEqual(result['elapsed'],a.BLOCKS[block][0])
            self.assertFalse(result['budget_failed'])
            WITNESSES['clean-'+block] = result

    def test_small_cumulative_costs_cannot_cross_either_whole_cap(self):
        for block in a.BLOCKS:
            result = publication(block,costs={'write-overall':.2,'write-journal':.2,'read-overall':.2,'read-journal':.5})
            self.assertFalse(result['report']['passed'])
            self.assertTrue(result['report']['publication_confirmed'])
            self.assertTrue(all(value['passed'] is False for value in result['files'].values()))
            self.assertGreater(result['elapsed'],a.BLOCKS[block][0])
            WITNESSES['cumulative-cost-'+block] = result

    def test_late_journal_write_demotes_earlier_tentative_receipt(self):
        result = publication(costs={'write-journal':2})
        self.assertFalse(result['report']['passed'])
        self.assertTrue(result['report']['publication_confirmed'])
        self.assertFalse(result['files']['overall.receipt.json']['passed'])
        self.assertFalse(result['files']['claim.json']['passed'])
        self.assertEqual(result['emergency_deadline'],246)
        WITNESSES['late-journal'] = result

    def test_unrecoverable_readback_leaves_tentative_success_but_cannot_return_success(self):
        result = publication(read_error='read-journal',fail_demotion=True)
        self.assertTrue(result['files']['overall.receipt.json']['passed'])
        self.assertTrue(result['files']['claim.json']['passed'])
        self.assertFalse(result['report']['passed'])
        self.assertFalse(result['report']['publication_confirmed'])
        self.assertEqual(result['report']['failure']['message'],'independent readback failure')
        self.assertTrue(result['report']['finalization_failures'])
        WITNESSES['tentative-files-are-insufficient'] = result

    def test_original_native_failure_survives_failed_recovery_publication(self):
        first = dict(type='PhaseFailed',message='independent strict ObjectDB leak')
        result = publication(first_failure=first,fail_demotion=True)
        self.assertFalse(result['report']['passed'])
        self.assertFalse(result['report']['publication_confirmed'])
        self.assertEqual(result['report']['failure'],first)
        self.assertEqual(len(result['events']),1)
        self.assertTrue(result['budget_failed'])
        WITNESSES['first-failure'] = result

    def test_failed_budget_cannot_publish_normal_success_or_launch_again(self):
        result = publication(already_failed=True)
        self.assertFalse(result['report']['passed'])
        self.assertTrue(result['report']['publication_confirmed'])
        self.assertIn('cannot resume',result['report']['failure']['message'])
        self.assertTrue(all(value['passed'] is False for value in result['files'].values()))
        WITNESSES['no-promotion'] = result

    def test_final_state_check_failure_cannot_survive_clean_native_sequence(self):
        real_inventory = a.stage_inventory
        def inventory(path,*args,**kwargs):
            if path.name=='private-state':
                raise RuntimeError('independent final private-state check failure')
            return real_inventory(path,*args,**kwargs)
        with patch.object(a,'stage_inventory',side_effect=inventory):
            result = original.replay()
        self.assertEqual(len(result['calls']),4)
        self.assertFalse(result['report']['passed'])
        self.assertTrue(result['report']['publication_confirmed'])
        self.assertFalse(result['stored_report']['passed'])
        self.assertIn('final private-state check failure',result['report']['failure']['message'])
        WITNESSES['final-state-failure'] = result

    def test_full_result_inventory_rejects_cross_suite_failure_and_conflicting_results(self):
        good = 'BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion'
        for extra in ('BOT_DRY_WEAPON_FAILURE x',
                      'BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=1 mode=assertion',
                      'BOT_SQUAD_SYMMETRY_RESULT malformed'):
            with self.subTest(extra=extra),self.assertRaises(RuntimeError):
                a.completed_suite('bot_squad_symmetry',good+'\n'+extra)
        # The full run concatenates stderr before applying this function.
        self.assertFalse(a.failed('BOT_SQUAD_FAILURE contradiction'))
        with self.assertRaises(RuntimeError):
            a.completed_suite('bot_squad_symmetry',good+'\nBOT_SQUAD_FAILURE contradiction')


if __name__=='__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        (HERE/'new-replay-witnesses.json').write_text(json.dumps(WITNESSES,indent=2,sort_keys=True)+'\n')
