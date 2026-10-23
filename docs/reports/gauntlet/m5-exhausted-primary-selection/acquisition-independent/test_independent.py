#!/usr/bin/env python3
"""Independent pure controls. All process, signal and clock effects are mocked."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import signal
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
WRAPPER = ROOT / 'docs/reports/gauntlet/m5-exhausted-primary-selection/acquisition'
sys.path.insert(0, str(WRAPPER))
import run_acquisition as a

WITNESSES = {}


def replay(block='candidate', final_write_delay=0, extra_failure=None, before_finalization=0):
    """Exercise run() itself, real copy/state/UID/checkpoint code, fake natives."""
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_file = root / 'game/project.godot'
        source_file.parent.mkdir()
        source_file.write_bytes(b'[application]\nconfig/name="SIGHTBREAK"\n')
        data = source_file.read_bytes()
        inventory = [dict(path='game/project.godot', present=True, mode='100644',
                          index_stage='0', bytes=len(data),
                          git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                          sha256=hashlib.sha256(data).hexdigest())]
        engine = root / 'mock-engine-bytes'
        engine.write_bytes(b'not executable; never launched')
        output = root / '.local/replay'
        clock = [0.0]
        alarms = []
        calls = []
        events = []
        real_write = a.write

        def write(path, value):
            if path.name == 'overall.receipt.json':
                before = clock[0]
                clock[0] += final_write_delay
                events.append(dict(event='overall-write', before=before, after=clock[0],
                                   active_alarm=alarms[-1] if alarms else None))
            real_write(path, value)

        class Native:
            def __init__(self, destination, budget):
                self.output, self.budget, self.receipts = destination, budget, []

            def native(self, label, command, env, cap):
                self.budget.arm()
                calls.append(dict(label=label, command=command, env={key:env[key] for key in
                    ('HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','ANDROID_USER_HOME') if key in env}, cap=cap))
                events.append(dict(event='native', label=label))
                path_args = [arg for arg in command if arg.startswith('--receipt=')]
                if path_args:
                    Path(path_args[0].split('=',1)[1]).write_text(json.dumps(dict(
                        os='Linux', uses_custom_user_dir=False, custom_user_dir='',
                        data_dir=env['XDG_DATA_HOME'],
                        user_data_dir=env['XDG_DATA_HOME']+'/godot/app_userdata/SIGHTBREAK',
                        project_path=command[command.index('--path')+1],
                        profile_exists=False, diagnostics_exist=False)))
                lines = {
                    'bot_ai_regression':'BOT_AI_REGRESSION_TESTS_OK\n',
                    'bot_dry_weapon':'BOT_DRY_WEAPON_RESULT '+json.dumps(dict(cases=84,sequence_steps=48,checks=590,failures=0,passed=True))+'\n',
                    'bot_squad_symmetry':'BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion\n',
                }
                text = lines.get(label, 'mock native output\n')
                if label == extra_failure:
                    text += 'BOT_SQUAD_FAILURE independently injected contradiction\n'
                (self.output/(label+'.stdout.log')).write_text(text)
                (self.output/(label+'.stderr.log')).write_text('')
                self.receipts.append(dict(label=label, passed=True, failure=None))
                if label == ('bot_exhausted_primary-producer-after' if block=='candidate' else 'bot_squad_symmetry-producer-after'):
                    clock[0] = before_finalization
                return self.receipts[-1]

        def audit(*_):
            events.append(dict(event='audit'))
            return dict(passed=True)

        args = SimpleNamespace(source=root, output=output, expected_head='a'*40, block=block)
        with ExitStack() as stack:
            for name,value in [('ROOT',root),('ENGINE',engine),('ENGINE_SHA',a.sha(engine)),
                               ('Runner',Native),('prepare_identity',lambda *_:None),
                               ('original_inventory',lambda *_:inventory),
                               ('proc_snapshot',lambda:{}),('candidate_audit',audit),('write',write)]:
                stack.enter_context(patch.object(a,name,value))
            stack.enter_context(patch.object(a.time,'monotonic',side_effect=lambda:clock[0]))
            stack.enter_context(patch.object(a.signal,'setitimer',side_effect=lambda _which,seconds:alarms.append(seconds)))
            stack.enter_context(patch.object(a.signal,'signal'))
            stack.enter_context(patch.dict(a.os.environ,{'HOME':'/preserved-fixture-home','HTTPS_PROXY':'https://proxy.invalid'}))
            report = a.run(args)
            return dict(report=report,calls=calls,events=events,actual_seconds=clock[0],
                        stored_report=json.loads((output/'overall.receipt.json').read_text()))


class IndependentControls(unittest.TestCase):
    def test_candidate_success_exact_argv_caps_and_authority_order(self):
        result = replay()
        self.assertTrue(result['report']['passed'])
        calls = result['calls']
        self.assertEqual([row['label'] for row in calls], [
            'bot_exhausted_primary-producer-before','preparation-import',
            'bot_exhausted_primary','bot_exhausted_primary-producer-after'])
        self.assertEqual([row['cap'] for row in calls],[30,120,120,30])
        self.assertEqual(calls[1]['command'][-2:],['--editor','--import'])
        self.assertEqual(calls[2]['command'][-2:],['--script','res://tests/bot_exhausted_primary_test.gd'])
        for row in calls:
            self.assertEqual(row['command'][1:6],['--headless','--audio-driver','Dummy','--path',calls[0]['command'][5]])
        events = result['events']
        self.assertLess(events.index(dict(event='audit')),events.index(dict(event='native',label='bot_exhausted_primary-producer-after')))
        self.assertTrue(result['report']['preparation']['staged_noncache_source_set_equal_to_original'])
        WITNESSES['candidate_success'] = result

    def test_regressions_success_exact_order_and_distinct_real_state_contract(self):
        result = replay('regressions')
        self.assertTrue(result['report']['passed'])
        calls = result['calls']
        self.assertEqual([row['label'] for row in calls], [
            'bot_ai_regression-producer-before','preparation-import','bot_ai_regression',
            'bot_ai_regression-producer-after','bot_dry_weapon-producer-before',
            'bot_dry_weapon','bot_dry_weapon-producer-after','bot_squad_symmetry-producer-before',
            'bot_squad_symmetry','bot_squad_symmetry-producer-after'])
        self.assertEqual(result['report']['whole_bound_seconds'],480)
        self.assertEqual([row['cap'] for row in calls],[30,120,120,30,30,120,30,30,120,30])
        self.assertEqual(len({calls[i]['env']['XDG_DATA_HOME'] for i in (0,4,7)}),3)
        self.assertTrue(all(row['env']['HOME']=='/preserved-fixture-home' for row in calls))
        self.assertFalse(any(row['event']=='audit' for row in result['events']))
        WITNESSES['regressions_success'] = result

    def test_whole_bound_includes_overall_receipt_and_claim_finalization(self):
        result = replay(final_write_delay=2,before_finalization=239)
        WITNESSES['late_overall_write'] = result
        self.assertGreater(result['actual_seconds'],240)
        self.assertFalse(result['report']['passed'], 'run() accepts success after its final receipt write exceeds the 240-second whole bound')

    def test_explicit_squad_failure_must_not_pass_with_success_marker(self):
        result = replay('regressions',extra_failure='bot_squad_symmetry')
        WITNESSES['contradictory_squad_failure'] = result
        self.assertFalse(result['report']['passed'], 'Explicit BOT_SQUAD_FAILURE coexisting with success marker is accepted')

    def test_preparation_rejects_original_deletion_change_and_unexpected_uid(self):
        original = {'game/a.gd':dict(sha256='a',bytes=1)}
        for current in ({}, {'game/a.gd':dict(sha256='b',bytes=1)},
                        dict(original,**{'game/other.gd.uid':dict(sha256='c',bytes=1)})):
            with self.assertRaises(RuntimeError): a.preparation_sources(original,current)
        allowed = dict(original,**{a.NEW_UID:dict(sha256='d',bytes=2)})
        self.assertEqual(a.preparation_sources(original,allowed),[a.NEW_UID])
        self.assertNotEqual(original,allowed)

    def test_native_receipt_write_cannot_exceed_phase_bound_and_stay_passed(self):
        with TemporaryDirectory() as tmp:
            output = Path(tmp)
            clock = [0.0]
            alive = [True]
            process = SimpleNamespace(pid=5001,returncode=None)
            def poll():
                alive[0] = False
                process.returncode = 0
                return 0
            process.poll = poll
            row = dict(pid=5001,ppid=10,pgid=5001,sid=5001,start_ticks=123,
                       state='R',comm='mock',exe='/mock')
            def spawn(*_,**kwargs):
                kwargs['stdout'].write(b'complete success\n')
                return process
            real_write = a.write
            def write(path,value):
                real_write(path,value)
                if path.name=='phase.receipt.json':clock[0] = 121.0
            with ExitStack() as stack:
                stack.enter_context(patch.object(a.subprocess,'Popen',side_effect=spawn))
                stack.enter_context(patch.object(a,'proc_snapshot',side_effect=lambda:{5001:row} if alive[0] else {}))
                stack.enter_context(patch.object(a.time,'monotonic',side_effect=lambda:clock[0]))
                stack.enter_context(patch.object(a.os,'pidfd_open',return_value=99))
                stack.enter_context(patch.object(a.os,'close'))
                stack.enter_context(patch.object(a.signal,'pthread_sigmask',return_value=set()))
                stack.enter_context(patch.object(a.signal,'setitimer'))
                stack.enter_context(patch.object(a,'write',side_effect=write))
                budget = a.Budget(240)
                runner = a.Runner(output,budget)
                env = {key:'/private/'+key for key in ['SIGHTBREAK_STATE_DIR','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','ANDROID_USER_HOME']}
                error = None
                try: runner.native('phase',['/never-launched'],env,120)
                except BaseException as caught:error = repr(caught)
                WITNESSES['late_phase_receipt'] = dict(error=error,actual_seconds=clock[0],receipt=runner.receipts[0])
                self.assertFalse(runner.receipts[0]['passed'], 'Phase receipt reports pass after 121 seconds under a 120-second phase cap')


if __name__=='__main__':
    try:
        unittest.main(verbosity=2)
    finally:
        (Path(__file__).parent/'replay-witnesses.json').write_text(json.dumps(WITNESSES,indent=2,sort_keys=True)+'\n')
