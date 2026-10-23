#!/usr/bin/env python3
"""Pure mocked wrapper controls; no child process, Godot, signal or compile."""
from contextlib import ExitStack, nullcontext
import copy
import hashlib
import json
from pathlib import Path
import signal
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_acquisition as acquisition


def process_row(pid=6001,start=111,ppid=42,sid=None):
    return dict(pid=pid,start_ticks=start,ppid=ppid,pgid=sid or pid,sid=sid or pid,
                state='R',comm='Godot',exe=str(acquisition.ENGINE))


class PureInputs(unittest.TestCase):
    def test_complete_strict_log_gate_includes_warning_and_typed_leaks(self):
        for text in ('WARNING: 2 ObjectDB instances were leaked at exit',
                     'Leaked instance: AudioStreamPlaybackWAV:1',
                     'SCRIPT ERROR: bad source','ERROR: failure','Parse Error: invalid'):
            self.assertTrue(acquisition.failed(text),text)

    def test_fixed_budgets_and_suites(self):
        self.assertEqual(acquisition.BLOCKS['candidate'],(240,('bot_exhausted_primary',)))
        self.assertEqual(acquisition.BLOCKS['regressions'],(480,('bot_ai_regression','bot_dry_weapon','bot_squad_symmetry')))

    def test_claim_rejects_other_output_for_same_head_and_block(self):
        with TemporaryDirectory() as tmp:
            source=Path(tmp);head='a'*40
            first=source/'.local/first'
            acquisition.claim(source,head,'candidate',first)
            with self.assertRaises(FileExistsError):
                acquisition.claim(source,head,'candidate',source/'.local/second')
            self.assertFalse((source/'.local/second').exists())
            with self.assertRaisesRegex(RuntimeError,'Existing output'):
                acquisition.claim(source,head,'candidate',first)

    def test_generated_uid_is_distinct_from_original_byte_equality(self):
        original={'game/source.gd':{'sha256':'one','bytes':1}}
        current=dict(original,**{acquisition.NEW_UID:{'sha256':'two','bytes':2}})
        self.assertEqual(acquisition.preparation_sources(original,current),[acquisition.NEW_UID])
        self.assertNotEqual(original,current)
        for bad in ({'game/source.gd':{'sha256':'changed','bytes':1}},
                    dict(current,**{'game/other.gd':{'sha256':'three','bytes':3}}),{}):
            with self.assertRaises(RuntimeError): acquisition.preparation_sources(original,bad)

    def test_native_producer_actual_paths_settings_and_leftovers(self):
        with TemporaryDirectory() as tmp:
            output=Path(tmp);env=acquisition.suite_env(output,'candidate');project=output/'staged/game'
            value=dict(os='Linux',uses_custom_user_dir=False,custom_user_dir='',data_dir=env['XDG_DATA_HOME'],
                       user_data_dir=str(Path(env['XDG_DATA_HOME'])/'godot/app_userdata/SIGHTBREAK'),project_path=str(project),
                       profile_exists=False,diagnostics_exist=False)
            self.assertEqual(acquisition.producer_identity(value,env,project,True),value['user_data_dir'])
            for field,bad in [('user_data_dir','/canonical/player'),('data_dir','/foreign'),('project_path','/foreign'),
                              ('uses_custom_user_dir',True),('custom_user_dir','foreign'),('profile_exists',True),
                              ('diagnostics_exist',True),('os','Windows')]:
                with self.subTest(field=field),self.assertRaises(RuntimeError):
                    acquisition.producer_identity(dict(value,**{field:bad}),env,project,True)

    def test_missing_duplicate_and_failed_existing_markers_reject(self):
        acquisition.completed_suite('bot_ai_regression','BOT_AI_REGRESSION_TESTS_OK\n')
        for text in ('', 'BOT_AI_REGRESSION_TESTS_OK\nBOT_AI_REGRESSION_TESTS_OK\n'):
            with self.assertRaises(RuntimeError): acquisition.completed_suite('bot_ai_regression',text)
        good={'cases':84,'sequence_steps':48,'checks':590,'failures':0,'passed':True}
        acquisition.completed_suite('bot_dry_weapon','BOT_DRY_WEAPON_RESULT '+json.dumps(good))
        with self.assertRaises(RuntimeError):
            acquisition.completed_suite('bot_dry_weapon','BOT_DRY_WEAPON_RESULT '+json.dumps(dict(good,failures=1)))
        acquisition.completed_suite('bot_squad_symmetry','BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion')
        with self.assertRaises(RuntimeError):
            acquisition.completed_suite('bot_squad_symmetry','BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=observation')

    def test_expired_budget_cannot_launch(self):
        with patch.object(acquisition.time,'monotonic',side_effect=[10,251]):
            budget=acquisition.Budget(240)
            with self.assertRaises(acquisition.BoundExceeded): budget.arm()

    def test_finalization_allowance_does_not_reset(self):
        with patch.object(acquisition.time,'monotonic',side_effect=[0,241,241,244]),patch.object(acquisition.signal,'setitimer') as alarm:
            budget=acquisition.Budget(240);budget.finish_alarm();budget.finish_alarm()
            self.assertEqual(budget.finalization_deadline,246)
            self.assertEqual(alarm.call_args_list[-1].args[1],2)


class ProcessControls(unittest.TestCase):
    def phase(self,mode='clean',cap=120,setup_failure=None):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup)
        output=Path(tmp.name);clock=[10.]
        process=SimpleNamespace(pid=6001,returncode=None,alive=True,polls=0)
        signals=[];closed=[]
        def poll():
            process.polls+=1
            if not process.alive: return process.returncode
            if mode not in ('timeout','registration','interrupted','wait_failure') and process.polls>=2:
                process.alive=False;process.returncode=0
            return process.returncode
        process.poll=poll
        def wait(timeout):
            if process.alive: raise subprocess.TimeoutExpired('mock',timeout)
            return process.returncode
        process.wait=wait
        def send_fd(fd,sig):
            signals.append((fd,sig));process.alive=False;process.returncode=-int(sig)
        process.send_signal=lambda sig:send_fd(6001+10000,sig)
        def scan():
            return {6001:process_row()} if process.alive else {}
        def popen(_argv,**kwargs):
            if setup_failure: raise setup_failure
            kwargs['stdout'].write(b'actual mock output\n')
            if mode=='leak': kwargs['stderr'].write(b'WARNING: 2 ObjectDB instances were leaked at exit\n')
            return process
        def sleep(delta):
            clock[0]+=delta
            if mode=='interrupted': raise acquisition.BoundExceeded('mock interrupt')
            if mode=='wait_failure': raise OSError('mock wait/observation failure')
        with ExitStack() as stack:
            for target,value in [('proc_snapshot',scan),('registered_launch',lambda:nullcontext())]:
                stack.enter_context(patch.object(acquisition,target,value))
            stack.enter_context(patch.object(acquisition.subprocess,'Popen',side_effect=popen))
            stack.enter_context(patch.object(acquisition.time,'monotonic',side_effect=lambda:clock[0]))
            stack.enter_context(patch.object(acquisition.time,'sleep',side_effect=sleep))
            stack.enter_context(patch.object(acquisition.signal,'setitimer'))
            stack.enter_context(patch.object(acquisition.os,'pidfd_open',side_effect=PermissionError('mock pidfd creation failure') if mode=='pidfd_failure' else lambda pid:pid+10000))
            stack.enter_context(patch.object(acquisition.signal,'pidfd_send_signal',side_effect=send_fd))
            stack.enter_context(patch.object(acquisition.os,'close',side_effect=closed.append))
            if mode=='registration':
                stack.enter_context(patch.object(acquisition.Owned,'observe',side_effect=OSError('mock registration failure')))
            budget=acquisition.Budget(240);runner=acquisition.Runner(output,budget)
            env={k:'/private/'+k for k in ['SIGHTBREAK_STATE_DIR','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','ANDROID_USER_HOME']}
            error=None
            try: runner.native('mock',[str(acquisition.ENGINE)],env,cap)
            except BaseException as caught: error=caught
            return runner.receipts[0],error,signals,closed,process

    def test_normal_exit_has_identity_and_no_cleanup_signal(self):
        receipt,error,signals,closed,_=self.phase()
        self.assertIsNone(error);self.assertTrue(receipt['passed']);self.assertEqual(signals,[])
        self.assertEqual(receipt['root_identity']['start_ticks'],111)
        self.assertIn(16001,closed)

    def test_exit_zero_leak_remains_failure_with_complete_stderr(self):
        receipt,error,_,_,_=self.phase('leak')
        self.assertIsInstance(error,acquisition.PhaseFailed)
        self.assertTrue(receipt['strict_log_failed']);self.assertEqual(receipt['exit_code'],0)
        self.assertFalse(receipt['passed']);self.assertGreater(receipt['stderr']['bytes'],0)

    def test_timeout_reaps_only_original_pidfd_and_preserves_failure(self):
        receipt,error,signals,_,process=self.phase('timeout',cap=.1)
        self.assertIsInstance(error,acquisition.BoundExceeded);self.assertTrue(receipt['timed_out'])
        self.assertFalse(receipt['passed']);self.assertFalse(process.alive);self.assertTrue(signals)
        self.assertTrue(all(fd==16001 for fd,_ in signals))

    def test_launch_failure_retains_receipt_without_cleanup_claim(self):
        receipt,error,signals,_,_=self.phase(setup_failure=OSError('mock launch failure'))
        self.assertIsInstance(error,OSError);self.assertFalse(receipt['passed']);self.assertEqual(signals,[])
        self.assertNotIn('root_identity',receipt)

    def test_registration_failure_still_reaps_direct_child_and_retains_original(self):
        receipt,error,signals,_,process=self.phase('registration')
        self.assertIsInstance(error,OSError);self.assertIn('registration',str(error))
        self.assertFalse(process.alive);self.assertFalse(receipt['passed']);self.assertTrue(signals)
        self.assertTrue(receipt['cleanup_failures'])

    def test_pidfd_creation_failure_uses_unreaped_child_fallback_and_stays_failed(self):
        receipt,error,signals,_,process=self.phase('pidfd_failure')
        self.assertIsInstance(error,PermissionError);self.assertFalse(receipt['passed'])
        self.assertFalse(process.alive);self.assertTrue(signals)
        self.assertIn('Popen-owned',receipt['signals'][0]['scope'])

    def test_interrupt_and_wait_failure_preserve_raw_and_stop_process(self):
        for mode in ('interrupted','wait_failure'):
            with self.subTest(mode=mode):
                receipt,error,_,_,process=self.phase(mode)
                self.assertIsNotNone(error);self.assertFalse(receipt['passed']);self.assertFalse(process.alive)
                self.assertGreater(receipt['stdout']['bytes'],0)

    def test_pid_reuse_never_becomes_owned_or_signaled(self):
        scans=[{6001:process_row()},{6001:process_row(start=222)}]
        with patch.object(acquisition,'proc_snapshot',side_effect=scans+scans[1:]),patch.object(acquisition.os,'pidfd_open',return_value=12),patch.object(acquisition.os,'close'),patch.object(acquisition.signal,'pidfd_send_signal') as send:
            owned=acquisition.Owned(6001);owned.observe();scan=owned.observe()
            self.assertEqual(owned.remaining(scan),[])
            owned.send(process_row(),signal.SIGTERM,[])
            send.assert_not_called();owned.close()


class StopPolicyControls(unittest.TestCase):
    def acquire(self,block='candidate',failure=None,audit_failure=False,receipt_failure=False,corrupt_import=False,claim_delay=False):
        tmp=TemporaryDirectory();self.addCleanup(tmp.cleanup);source=Path(tmp.name)
        game=source/'game';game.mkdir();(game/'project.godot').write_text('source config\n')
        engine=source/'fake-engine';engine.write_bytes(b'pure mock binary')
        data=(game/'project.godot').read_bytes()
        inventory=[dict(path='game/project.godot',present=True,mode='100644',index_stage='0',
                        git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),
                        sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))]
        calls=[]
        class FakeRunner:
            def __init__(self,output,budget):self.output=output;self.receipts=[]
            def native(self,label,command,env,cap):
                calls.append(label)
                if label==failure:
                    if receipt_failure:
                        self.receipts.append({'failure':dict(type='PhaseFailed',message='mock original strict failure')})
                        raise OSError('mock later receipt write failure')
                    raise acquisition.PhaseFailed('mock strict failure: '+label)
                if '--receipt='+str(self.output/'unused') in command: raise AssertionError('unused')
                receipt_args=[arg for arg in command if arg.startswith('--receipt=')]
                if receipt_args:
                    value=dict(os='Linux',uses_custom_user_dir=False,custom_user_dir='',data_dir=env['XDG_DATA_HOME'],
                               user_data_dir=str(Path(env['XDG_DATA_HOME'])/'godot/app_userdata/SIGHTBREAK'),
                               project_path=command[command.index('--path')+1],profile_exists=False,diagnostics_exist=False)
                    Path(receipt_args[0].split('=',1)[1]).write_text(json.dumps(value))
                markers={'bot_ai_regression':'BOT_AI_REGRESSION_TESTS_OK\n',
                         'bot_dry_weapon':'BOT_DRY_WEAPON_RESULT '+json.dumps(dict(cases=84,sequence_steps=48,checks=590,failures=0,passed=True)),
                         'bot_squad_symmetry':'BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion'}
                (self.output/(label+'.stdout.log')).write_text(markers.get(label,'mock stdout\n'))
                if corrupt_import and label=='preparation-import':
                    (Path(command[command.index('--path')+1])/'project.godot').write_text('corrupted staging source')
                return dict(passed=True)
        args=SimpleNamespace(source=source,output=source/'.local/result',expected_head='a'*40,block=block)
        with ExitStack() as stack:
            stack.enter_context(patch.object(acquisition,'ROOT',source))
            stack.enter_context(patch.object(acquisition,'ENGINE',engine))
            stack.enter_context(patch.object(acquisition,'ENGINE_SHA',hashlib.sha256(engine.read_bytes()).hexdigest()))
            stack.enter_context(patch.object(acquisition,'prepare_identity'))
            stack.enter_context(patch.object(acquisition,'original_inventory',return_value=copy.deepcopy(inventory)))
            stack.enter_context(patch.object(acquisition,'proc_snapshot',return_value={}))
            stack.enter_context(patch.object(acquisition,'Runner',FakeRunner))
            stack.enter_context(patch.object(acquisition.signal,'setitimer'))
            if claim_delay:
                clock=[10.];real_claim=acquisition.claim
                def slow_claim(*args):
                    value=real_claim(*args);clock[0]+=250;return value
                stack.enter_context(patch.object(acquisition.time,'monotonic',side_effect=lambda:clock[0]))
                stack.enter_context(patch.object(acquisition,'claim',side_effect=slow_claim))
            audit=stack.enter_context(patch.object(acquisition,'candidate_audit',side_effect=RuntimeError('mock authority failure') if audit_failure else None,return_value={'passed':True}))
            report=acquisition.run(args)
            return report,calls,audit.call_count

    def test_import_failure_stops_before_candidate_and_after_probe(self):
        report,calls,_=self.acquire(failure='preparation-import')
        self.assertFalse(report['passed'])
        self.assertEqual(calls,['bot_exhausted_primary-producer-before','preparation-import'])

    def test_strict_candidate_failure_only_gets_non_native_diagnostic_audit(self):
        report,calls,audits=self.acquire(failure='bot_exhausted_primary')
        self.assertFalse(report['passed']);self.assertIn('strict failure',report['failure']['message'])
        self.assertEqual(calls,['bot_exhausted_primary-producer-before','preparation-import','bot_exhausted_primary'])
        self.assertEqual(audits,1);self.assertTrue(report['candidate_builder_audit']['passed'])

    def test_authority_audit_failure_stops_before_after_producer_and_is_not_retried(self):
        report,calls,audits=self.acquire(audit_failure=True)
        self.assertFalse(report['passed']);self.assertEqual(audits,1)
        self.assertNotIn('bot_exhausted_primary-producer-after',calls)

    def test_clean_candidate_has_exact_four_native_stages(self):
        report,calls,audits=self.acquire()
        self.assertTrue(report['passed']);self.assertEqual(audits,1)
        self.assertEqual(calls,['bot_exhausted_primary-producer-before','preparation-import','bot_exhausted_primary','bot_exhausted_primary-producer-after'])

    def test_first_regression_failure_stops_all_later_native_stages(self):
        report,calls,_=self.acquire('regressions',failure='bot_ai_regression')
        self.assertFalse(report['passed'])
        self.assertEqual(calls,['bot_ai_regression-producer-before','preparation-import','bot_ai_regression'])

    def test_regression_block_has_one_import_three_suites_and_actual_before_after_probes(self):
        report,calls,audits=self.acquire('regressions')
        self.assertTrue(report['passed']);self.assertEqual(audits,0)
        self.assertEqual(len(calls),10);self.assertEqual(calls.count('preparation-import'),1)
        self.assertEqual(report['whole_bound_seconds'],480)

    def test_import_source_corruption_stops_before_candidate(self):
        report,calls,_=self.acquire(corrupt_import=True)
        self.assertFalse(report['passed']);self.assertIn('Original copied source changed',report['failure']['message'])
        self.assertEqual(calls,['bot_exhausted_primary-producer-before','preparation-import'])

    def test_original_phase_failure_survives_later_receipt_failure(self):
        report,_,_=self.acquire(failure='preparation-import',receipt_failure=True)
        self.assertEqual(report['failure']['message'],'mock original strict failure')
        self.assertTrue(any('later receipt write' in row['message'] for row in report['finalization_failures']))

    def test_whole_budget_includes_claim_and_setup_cost(self):
        report,calls,_=self.acquire(claim_delay=True)
        self.assertFalse(report['passed']);self.assertEqual(calls,[])
        self.assertGreaterEqual(report['wall_seconds'],250)


if __name__=='__main__':
    unittest.main(verbosity=2)
