#!/usr/bin/env python3
"""Mocked process/file controls only; never launches an engine or service."""
import hashlib
import json
from pathlib import Path
import signal
import tempfile
import time
import unittest
from unittest.mock import patch, Mock

import acquire_audio_lifecycle as acquisition
import analyze_audio_lifecycle as analysis


def synthetic_suite(leak=True, driver='Dummy'):
    rows = [{'kind':'header', 'stage':'attach', 'driver':driver, 'mix_rate':44100,
             'scope':'read_only_latest_playback_not_server_drain'}]
    identities = []
    for role, count in [('match_device',7), ('actor_shot',70), ('actor_hurt',70), ('reload_voice',280)]:
        for _ in range(count):
            identity = str(1000 + len(identities)); identities.append(identity)
            rows.append({'kind':'object', 'stage':'attach', 'id':identity, 'class':'AudioStreamPlayer3D'})
            rows.append({'kind':'player', 'stage':'attach', 'id':identity, 'event':'node_added', 'state':{
                'path':'/root/Match/Audio', 'owner':{'role':role,'id':'1','path':'/root/Match','script':'res://scripts/gameplay/match.gd'},
                'inside_tree':True, 'queued_for_deletion':False, 'playing':False, 'stream_paused':False,
                'has_stream_playback':False, 'stream_id':'', 'latest_playback_id':'', 'latest_playing':None}})
    for stage in ['before_hud_leave','after_hud_leave'] * 6 + ['before_final_leave','after_final_leave','final_pre_quit']:
        rows.extend({'kind':'weak','stage':stage,'id':identity,'alive':False} for identity in identities)
        rows.append({'kind':'checkpoint','stage':stage,'time_since_last_mix':0.01,'time_to_next_mix':0.01})
    for sequence, row in enumerate(rows):
        row.update(schema=1,sequence=sequence,process_frame=1,physics_frame=1,usec=sequence)
    raw = 'WorkerThreadPool: 3 threads, 1 max low-priority.\n' + analysis.ENGINE + ' - https://godotengine.org\n'
    raw += '\n'.join(analysis.PREFIX + json.dumps(row) for row in rows)
    raw += '\nINPUT_MODE_TEST checks=462 failures=0 graphical_pointer=false scope=simulated_capabilities_and_input_not_physical_hardware baseline=false\n'
    if leak: raw += 'WARNING: 2 ObjectDB instances were leaked at exit\nLeaked instance: AudioStreamWAV:99 - Reference count: 1\nLeaked instance: AudioStreamPlaybackWAV:98 - Reference count: 1\n'
    return raw


class AcquisitionControls(unittest.TestCase):
    def fixture(self, root, mode='leak'):
        source, output, engine = root/'source', root/'attempt', root/'fake-engine'
        source.mkdir(); engine.write_bytes(b'synthetic executable pin; never run')
        originals = {}
        files = {'game/project.godot':'config_version=5\n[application]\nconfig/name="SIGHTBREAK"\n',
                 'game/tests/audio_lifecycle_probe.gd':'extends RefCounted\n',
                 'game/tests/input_mode_test.gd':'extends SceneTree\n'}
        for name, raw in files.items():
            p=source/name; p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
            originals[name]={'sha256':acquisition.sha(p)}
        instances=[]
        class FakePhases:
            def __init__(self, out, binary, expected, deadline, env):
                self.output,self.receipts,self.env=out,[],env;instances.append(self)
            def execute(self,label,args,cap):
                receipt={'label':label,'command':[str(engine),*args],'exit':0,'clean_log':True,
                         'cleanup_complete':True,'timed_out':False,'cap':cap}
                self.receipts.append(receipt)
                log=self.output/(label+'.log');log.write_text('')
                project=self.output/'project'
                if label=='engine-version': log.write_text(acquisition.toolchain.ENGINE+'\n')
                if label=='private-import':
                    uid=project/'tests/audio_lifecycle_probe.gd.uid';uid.write_text('uid://synthetic123\n')
                    if mode=='bad-uid': uid.write_text('not a UID')
                    if mode=='tracked-drift': (project/'tests/input_mode_test.gd').write_text('changed')
                    if mode=='warning-import':
                        log.write_text('WARNING: 2 ObjectDB instances were leaked at exit\n');receipt['clean_log']=False
                    if mode=='import-timeout': raise TimeoutError('synthetic bounded import timeout')
                if label in ('before-input-mode','after-input-mode'):
                    custom=next(line.split('=',1)[1] for line in (project/'project.godot').read_text().splitlines() if line.startswith('config/custom_user_dir_name='))
                    custom=json.loads(custom);data=Path(self.env['XDG_DATA_HOME']);user=data/custom;user.mkdir(parents=True,exist_ok=True)
                    payload={'project_path':str(project),'data_dir':str(data),'user_data_dir':str(user),
                             'driver':'Dummy','uses_custom_user_dir':True,'custom_user_dir':custom,
                             'profile_exists':False,'diagnostics_exist':False}
                    if mode=='foreign-native': payload['user_data_dir']=str(root/'foreign')
                    if mode=='preexisting-state': payload['profile_exists']=True
                    destination=Path(args[-1].removeprefix('--receipt='));destination.write_text(json.dumps(payload))
                if label=='input-mode':
                    log.write_text(synthetic_suite(leak=mode!='clean',driver='CoreAudio' if mode=='wrong-driver' else 'Dummy'))
                    receipt['clean_log']=not acquisition.failed(log.read_text())
                    if mode=='survivor': receipt['cleanup_complete']=False;raise RuntimeError('synthetic survivor')
                    if mode=='suite-drift': (project/'tests/input_mode_test.gd').write_text('changed after suite')
                return receipt
        return source,output,engine,originals,instances,FakePhases

    def run_fake(self, root, mode='leak'):
        source,out,engine,originals,instances,fake=self.fixture(root,mode)
        with patch.object(acquisition.platform,'system',return_value='Linux'), patch.object(acquisition,'tracked',return_value=originals), patch.object(acquisition,'proc_table',return_value={}), patch.object(acquisition,'Phases',fake), patch.object(acquisition.subprocess,'Popen',side_effect=AssertionError('Native execution forbidden')):
            result=acquisition.acquire(source,'a'*40,engine,acquisition.sha(engine),out)
        return result,json.loads((out/'overall.json').read_text()),out,instances

    def test_complete_mocked_leak_attempt_retains_strict_failure_and_exact_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,report,out,instances=self.run_fake(Path(tmp))
            self.assertEqual(result,1);self.assertTrue(report['acquisition_integrity'])
            self.assertFalse(report['sample_strict_clean']);self.assertFalse(report['original_leak_blocker_resolved'])
            suite=next(row for row in instances[0].receipts if row['label']=='input-mode')
            self.assertEqual(suite['command'][3:],acquisition.SUITE)
            self.assertNotIn('--audio-driver',suite['command'])
            self.assertEqual(json.loads((out/'analysis.json').read_text())['driver'],'Dummy')
            self.assertTrue(report['private_project_removed']);self.assertTrue(report['private_state_removed'])
            self.assertTrue((out/'generated-uids/tests/audio_lifecycle_probe.gd.uid').is_file())

    def test_clean_mocked_sample_never_resolves_original_blocker(self):
        with tempfile.TemporaryDirectory() as tmp:
            result,report,_,_=self.run_fake(Path(tmp),'clean')
            self.assertEqual(result,0);self.assertTrue(report['sample_strict_clean'])
            self.assertFalse(report['original_leak_blocker_resolved'])

    def test_preparation_losses_skip_suite_and_retain_overall(self):
        for mode in ['warning-import','bad-uid','tracked-drift','import-timeout','foreign-native','preexisting-state']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,report,out,instances=self.run_fake(Path(tmp),mode)
                self.assertEqual(result,1);self.assertIn('error',report)
                self.assertNotIn('input-mode',[row['label'] for row in instances[0].receipts])
                self.assertTrue((out/'overall.json').is_file())

    def test_survivor_driver_and_suite_drift_cannot_pass(self):
        for mode in ['survivor','wrong-driver','suite-drift']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                result,report,_,_=self.run_fake(Path(tmp),mode)
                self.assertEqual(result,1);self.assertFalse(report['passed'])
                self.assertTrue(report.get('error') or report['finalization_errors'])

    def test_existing_output_source_and_engine_refusals_prevent_launch(self):
        for mode in ['existing-output','wrong-source','wrong-engine']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                source,out,engine,originals,_,_=self.fixture(Path(tmp))
                if mode=='existing-output': out.mkdir()
                with patch.object(acquisition.platform,'system',return_value='Linux'), patch.object(acquisition,'tracked',side_effect=RuntimeError('source mismatch') if mode=='wrong-source' else None,return_value=originals), patch.object(acquisition,'proc_table',return_value={}), patch.object(acquisition,'Phases') as phases:
                    if mode=='existing-output':
                        with self.assertRaises(FileExistsError): acquisition.acquire(source,'a'*40,engine,acquisition.sha(engine),out)
                    else:
                        self.assertEqual(acquisition.acquire(source,'a'*40,engine,'0'*64 if mode=='wrong-engine' else acquisition.sha(engine),out),1)
                        self.assertTrue((out/'overall.json').is_file())
                    phases.assert_not_called()

    def test_pid_reuse_refuses_signal_and_stable_identity_allows_only_exact_pid(self):
        old={'pid':10,'start_ticks':100}
        with patch.object(acquisition,'proc_table',return_value={10:{'pid':10,'start_ticks':101}}),patch.object(acquisition.os,'kill') as kill:
            self.assertFalse(acquisition.signal_identity(old,signal.SIGTERM));kill.assert_not_called()
        with patch.object(acquisition,'proc_table',return_value={10:old}),patch.object(acquisition.os,'kill') as kill:
            self.assertTrue(acquisition.signal_identity(old,signal.SIGTERM));kill.assert_called_once_with(10,signal.SIGTERM)

    def test_phase_deadline_reserves_cleanup_and_finalization_before_spawn(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);engine=out/'engine';engine.write_bytes(b'fake')
            phase=acquisition.Phases(out,engine,acquisition.sha(engine),100,{})
            with patch.object(acquisition.time,'monotonic',return_value=88),patch.object(acquisition.subprocess,'Popen') as spawn:
                with self.assertRaises(TimeoutError): phase.execute('suite',acquisition.SUITE,120)
                spawn.assert_not_called()

    def test_phase_spawn_failure_retains_attempt_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);engine=out/'engine';engine.write_bytes(b'fake')
            phase=acquisition.Phases(out,engine,acquisition.sha(engine),time.monotonic()+240,{})
            with patch.object(acquisition.subprocess,'Popen',side_effect=OSError('synthetic spawn failure')):
                with self.assertRaises(OSError): phase.execute('suite',acquisition.SUITE,120)
            self.assertTrue((out/'suite.receipt.json').is_file())
            self.assertTrue(json.loads((out/'suite.receipt.json').read_text())['cleanup_complete'])

    def phase_process_fixture(self, output, stubborn=False, wrong_group=False):
        engine=output/'engine';engine.write_bytes(b'fake')
        active={10:{'pid':10,'ppid':1,'pgid':99 if wrong_group else 10,'sid':10,'start_ticks':100,'state':'R','comm':'synthetic','exe':'fake'},
                11:{'pid':11,'ppid':10,'pgid':11,'sid':11,'start_ticks':101,'state':'R','comm':'synthetic-child','exe':'fake'}}
        clock=Mock();clock.value=0
        clock.monotonic=lambda:clock.value
        def sleep(seconds): clock.value+=seconds
        clock.sleep=sleep
        process=Mock();process.pid=10;process.returncode=None
        def poll():
            if 10 not in active: process.returncode=-15
            return process.returncode
        process.poll.side_effect=poll
        def kill(pid,_signum):
            if not stubborn: active.pop(pid,None)
        phase=acquisition.Phases(output,engine,acquisition.sha(engine),100,{})
        return phase,process,active,clock,kill

    def test_real_phase_timeout_branch_cleans_observed_escaped_child_within_reserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);phase,process,active,clock,kill=self.phase_process_fixture(output)
            with patch.object(acquisition.subprocess,'Popen',return_value=process),patch.object(acquisition,'proc_table',side_effect=lambda:dict(active)),patch.object(acquisition.os,'kill',side_effect=kill) as signals,patch.object(acquisition.time,'monotonic',side_effect=clock.monotonic),patch.object(acquisition.time,'sleep',side_effect=clock.sleep):
                with self.assertRaises(TimeoutError): phase.execute('suite',acquisition.SUITE,1)
            receipt=json.loads((output/'suite.receipt.json').read_text())
            self.assertTrue(receipt['timed_out']);self.assertTrue(receipt['cleanup_complete'])
            self.assertEqual({row['pid'] for row in receipt['observed']},{10,11})
            self.assertEqual({call.args[0] for call in signals.call_args_list},{10,11})
            self.assertLessEqual(receipt['cleanup_wall_seconds'],acquisition.CLEANUP)
            self.assertEqual(receipt['terminal_session'],[]);self.assertEqual(receipt['terminal_group'],[])

    def test_real_phase_stubborn_survivor_retains_term_kill_and_failed_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);phase,process,active,clock,kill=self.phase_process_fixture(output,stubborn=True)
            with patch.object(acquisition.subprocess,'Popen',return_value=process),patch.object(acquisition,'proc_table',side_effect=lambda:dict(active)),patch.object(acquisition.os,'kill',side_effect=kill),patch.object(acquisition.time,'monotonic',side_effect=clock.monotonic),patch.object(acquisition.time,'sleep',side_effect=clock.sleep):
                with self.assertRaises(TimeoutError): phase.execute('suite',acquisition.SUITE,1)
            receipt=json.loads((output/'suite.receipt.json').read_text())
            self.assertFalse(receipt['cleanup_complete'])
            self.assertEqual({row['signal'] for row in receipt['signals']},{'SIGTERM','SIGKILL'})
            self.assertEqual({row['pid'] for row in receipt['terminal_observed']},{10,11})
            self.assertLessEqual(receipt['cleanup_wall_seconds'],acquisition.CLEANUP)

    def test_unproven_root_group_is_never_signaled_and_receipt_survives(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);phase,process,active,clock,_=self.phase_process_fixture(output,wrong_group=True)
            with patch.object(acquisition.subprocess,'Popen',return_value=process),patch.object(acquisition,'proc_table',side_effect=lambda:dict(active)),patch.object(acquisition.os,'kill') as kill,patch.object(acquisition.time,'monotonic',side_effect=clock.monotonic),patch.object(acquisition.time,'sleep',side_effect=clock.sleep):
                with self.assertRaisesRegex(RuntimeError,'group/session'): phase.execute('suite',acquisition.SUITE,1)
            kill.assert_not_called()
            receipt=json.loads((output/'suite.receipt.json').read_text())
            self.assertFalse(receipt['cleanup_complete']);self.assertIn('cleanup_error',receipt)

    def test_real_phase_exit_zero_still_preserves_objectdb_warning_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp);phase,process,active,clock,_=self.phase_process_fixture(output)
            active.pop(11)
            def poll():
                active.pop(10,None);process.returncode=0;return 0
            process.poll.side_effect=poll
            def spawn(*_args,**kwargs):
                kwargs['stdout'].write(b'WARNING: 2 ObjectDB instances were leaked at exit\n');return process
            with patch.object(acquisition.subprocess,'Popen',side_effect=spawn),patch.object(acquisition,'proc_table',side_effect=lambda:dict(active)),patch.object(acquisition.time,'monotonic',side_effect=clock.monotonic):
                receipt=phase.execute('private-import',['--headless','--editor','--import','--quit'],120)
            self.assertEqual(receipt['exit'],0);self.assertTrue(receipt['cleanup_complete'])
            self.assertFalse(receipt['clean_log']);self.assertFalse(acquisition.qualified(receipt))

    def test_real_source_blob_guard_accepts_exact_bytes_and_rejects_drift_or_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,_,_,originals,_,_=self.fixture(Path(tmp))
            entries=[]
            for name in originals:
                raw=(source/name).read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
                entries.append('100644 blob '+blob+'\t'+name)
            def git(_source,_deadline,*args):
                return {'rev-parse':'a'*40 if args[1]=='HEAD' else 'sha1',
                        'status':'', 'ls-tree':'\0'.join(entries)+'\0'}[args[0]]
            with patch.object(acquisition,'git',side_effect=git):
                self.assertEqual(len(acquisition.tracked(source,'a'*40,time.monotonic()+10)),3)
                path=source/'game/tests/input_mode_test.gd';path.write_text('changed')
                with self.assertRaisesRegex(RuntimeError,'differ from Git'): acquisition.tracked(source,'a'*40,time.monotonic()+10)
                path.unlink()
                with self.assertRaisesRegex(RuntimeError,'Missing'): acquisition.tracked(source,'a'*40,time.monotonic()+10)


if __name__=='__main__': unittest.main()
