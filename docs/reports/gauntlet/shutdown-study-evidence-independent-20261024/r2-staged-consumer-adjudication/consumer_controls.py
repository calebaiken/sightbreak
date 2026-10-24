"""Frozen pure construction controls; never imports the R2 reader/collector."""
import ast
import copy
import ctypes
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
ROOT=REPORT.parents[4]
OUT=REPORT/'pure-r1'
RECORDS={};BASELINES={}
draft=(REPORT/'STAGED_CONSUMER_V2_PROPOSAL.py').read_bytes()
assert hashlib.sha256(draft).hexdigest()=='868e424f26950c1f248a7b7f93f7e974fa23bf1e56d2598de923c4848d430da9'
fixture=(ROOT/'scripts/shutdown_evidence_fixtures.py').read_bytes()
assert hashlib.sha256(fixture).hexdigest()=='c0d98d6d94cf9bc5875a919d56ebc734536fa88f1d82c9e8d1c5cef7f13a6f3b'
changes=[(b'reload_before = _snapshot(20500,',b'reload_before = _snapshot(20000,'),
         (b"'draw_calls_last_rendered_frame': 100,",b"'draw_calls_last_rendered_frame': 100.0,"),
         (b"'primitives_last_rendered_frame': 1000,",b"'primitives_last_rendered_frame': 1000.0,"),
         (b'def write_complete_trial(',b'def _write_format_trial_v1(')]
adapted=fixture
for before,after in changes:
    assert adapted.count(before)==1,before
    adapted=adapted.replace(before,after)
scope={'__file__':str(ROOT/'scripts/shutdown_evidence_fixtures.py')}
exec(compile(adapted,'<private recipe V1>','exec'),scope)
exec(compile(draft,'<frozen staged proposal>','exec'),scope)
clock_raw=(REPORT.parent/'r2-clock-seam-v2b-adjudication/CLOCK_SEAM_V2B_PROPOSAL.py').read_bytes()
assert hashlib.sha256(clock_raw).hexdigest()=='a3fa48aa56900e01ca85a5e12dcb9f6980c9c9764600ec9fc37875a7d39cc34c'
exec(compile(clock_raw,'<approved fixture clock>','exec'),scope)
Producer=scope['DeclaredProducer'];Clock=scope['DeclaredClock']
SOURCE_HASHES={}


def extract(path,names,cls=None):
    raw=(ROOT/path).read_bytes();SOURCE_HASHES[path]=hashlib.sha256(raw).hexdigest()
    tree=ast.parse(raw)
    body=tree.body if cls is None else next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls).body
    selected=[copy.deepcopy(next(n for n in body if isinstance(n,ast.FunctionDef) and n.name==name)) for name in names]
    return ast.Module(body=selected,type_ignores=[])


source_scope=dict(math=math,statistics=statistics,time=time,deepcopy=copy.deepcopy,C=ctypes)
exec(compile(extract('scripts/verify_offline_export.py',['require_living_capture_phase']),'<source named predicates>','exec'),source_scope)
exec(compile(extract('scripts/native_approach.py',['approach_floor']),'<source approach>','exec'),source_scope)
exec(compile(extract('scripts/native_settings_route.py',['relocate_settings_actor']),'<source route>','exec'),source_scope)
exec(compile(extract('scripts/verify_integration_export.py',['key_pulse'],cls='WinUI'),'<source pulse>','exec'),source_scope)


def save(name,value):
    (OUT/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run_case(name,*,verbose=False,observer=None):
    root=OUT/name;root.mkdir();(root/'original-failure.bin').write_bytes(b'unchanged original artifact\x00\xff')
    clock=Clock()
    result=scope['write_declared_trial'](root,scope['fixture_identity'](),clock=clock,
        format_writer=scope['_write_format_trial_v1'],snapshot=scope['_snapshot'],verbose=verbose,observer=observer)
    return root,result,clock


class MarkerError(RuntimeError):pass


class FakeUI:
    def __init__(self,clock):self.clock=clock;self.window=1001;self.pid=101;self.user=self;self.down=set()
    def IsWindowVisible(self,window):self.clock.advance(.0001);return True
    def GetWindowThreadProcessId(self,window,pointer):self.clock.advance(.0001);pointer._obj.value=self.pid;return 77
    def GetForegroundWindow(self):self.clock.advance(.0001);return self.window
    def GetAsyncKeyState(self,key):
        self.clock.advance(.0001);return 0x8000 if key in {ord(k.upper()) for k in self.down} else 0
    def key(self,key,down):
        self.clock.advance(.0001);(self.down.add if down else self.down.discard)(key)


class ConsumerControls(unittest.TestCase):
    def test_01_declared_format_runs_and_persistent_held_keys(self):
        rows=[]
        for arm in ('ordinary','verbose'):
            callbacks=[]
            root,result,clock=run_case('baseline-'+arm,verbose=arm=='verbose',observer=lambda event,**details:callbacks.append(dict(event=event,**details)))
            BASELINES[arm]=(root,result,clock)
            self.assertEqual(len(result['captures']),22);self.assertEqual(len(result['ocr_commands']),16);self.assertEqual(len(callbacks),4)
            self.assertTrue(result['passed']);self.assertLess(result['elapsed_seconds'],300)
            self.assertNotIn('--verbose',result['commands'][0]['command'])
            self.assertEqual('--verbose' in result['commands'][1]['command'],arm=='verbose')
            self.assertIs(type(result['native_reload']['before']['frame_diagnostics']['draw_calls_last_rendered_frame']),float)
            actions=json.loads((root/'actions.json').read_text());held=set();lmb=False
            for row in actions:
                if row['event']=='key_after':
                    (held.add if row['down'] else held.discard)(row['key'])
                self.assertEqual(row['held_keys'],sorted(held),(arm,row['event'],row.get('label')))
                self.assertEqual(row['native_state']['lmb_down'],lmb)
                if row['event']=='button':lmb=row['down']
            self.assertFalse(held);self.assertFalse(lmb)
            rows.append(dict(arm=arm,callbacks=callbacks,captures=22,OCR=16,elapsed=result['elapsed_seconds'],format_only=True))
        save('DECLARED_FORMAT_RUNS.json',rows)
    def test_02_source_wait_conditions_exist_before_completed_trace(self):
        checkpoints=[];original=Producer.trace
        def trace(producer,event,**fields):
            if event=='wait_completed':
                label=fields.get('label');text=(producer.root/'client.log').read_text() if (producer.root/'client.log').exists() else ''
                if label=='Actual offline live phase':valid='MATCH: Round live. Secure Relay Yard.' in text
                elif label=='Natural exported round completion':valid='MATCH: Round 2' in text
                elif label=='Second active round for weapon switching':valid=text.count('MATCH: Round live.')>=2
                elif label=='Reopened process loaded profile into ordinary offline match':valid=(producer.root/'restart-profile-trace/events.jsonl').is_file()
                else:return original(producer,event,**fields)
                checkpoints.append(dict(label=label,condition_true=valid,seconds=producer.clock.monotonic()-producer.started,client_log_bytes=len(text.encode()),reopened_events_exists=(producer.root/'restart-profile-trace/events.jsonl').exists()))
            return original(producer,event,**fields)
        with patch.object(Producer,'trace',trace):run_case('wait-gates')
        save('GATE_CHECKPOINTS.json',checkpoints)
        self.assertEqual(len(checkpoints),4)
        self.assertEqual([r['label'] for r in checkpoints if not r['condition_true']],[],'A successful source wait requires its predicate true before completion')
    def test_03_local_source_predicates_and_typed_receipt_boundaries(self):
        root,result,clock=BASELINES['ordinary']
        for name,fence in result['phase_capture_fences'].items():
            previous=None
            for field in ('acknowledged','ready','before_capture','after_capture_barrier','after_capture'):
                state=fence[field];source_scope['require_living_capture_phase'](state,fence['expected_actor_id'],fence['expected_round'])
                if previous is not None:self.assertGreater(state['wall_msec'],previous['wall_msec'])
                previous=state
            self.assertGreaterEqual(fence['ready']['drawn_frames'],fence['acknowledged']['drawn_frames']+2)
            self.assertGreater(fence['remaining_original_budget_seconds'],0)
        for row in result['hud_analysis_pauses']:
            self.assertTrue(row['paused']['ui']['paused']);self.assertTrue(row['after_analysis']['ui']['paused'])
            self.assertEqual(row['paused']['elapsed'],row['after_analysis']['elapsed'])
            self.assertEqual(row['paused']['local_actor']['health'],row['after_analysis']['local_actor']['health'])
        reload=result['native_reload'];self.assertIs(type(reload['completion_watchdog_seconds']),int);self.assertEqual(reload['completion_watchdog_seconds'],15)
        self.assertIs(reload['whole_flow_deadline_unchanged'],True)
        self.assertGreaterEqual(reload['observed_simulation_seconds'],reload['started']['local_actor']['reload']-1/60)
        self.assertIs(result['native_settings_resume']['same_living_player_required'],True)
    def test_04_callback_failures_stop_future_target_stages(self):
        rows=[]
        for index in range(4):
            root=OUT/('callback-failure-'+str(index));root.mkdir();marker=b'unchanged original artifact\x00\xff';(root/'original-failure.bin').write_bytes(marker)
            seen=[];error=MarkerError('original callback '+str(index))
            def observer(event,**details):
                seen.append(dict(event=event,**details))
                if len(seen)==index+1:raise error
            caught=None
            try:scope['write_declared_trial'](root,scope['fixture_identity'](),clock=Clock(),format_writer=scope['_write_format_trial_v1'],snapshot=scope['_snapshot'],observer=observer)
            except MarkerError as actual:caught=actual
            self.assertIs(caught,error);self.assertEqual(len(seen),index+1);self.assertEqual((root/'original-failure.bin').read_bytes(),marker)
            result=json.loads((root/'results.json').read_text());self.assertIs(result['passed'],False)
            if index==0:
                self.assertFalse(list(root.glob('*.png')));self.assertFalse((root/'initial-offline-trace').exists());self.assertFalse((root/'state').exists())
            if index<=2:
                self.assertFalse((root/'09-reopened-menu.png').exists());self.assertFalse((root/'restart-profile-trace').exists())
            self.assertNotIn(b'"passed": true',(root/'controller-stdout.log').read_bytes())
            rows.append(dict(index=index,events=seen,files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()),same_original_exception=True))
        save('CALLBACK_FAILURES.json',rows)
    def test_05_initial_collisions_preserve_original_bytes(self):
        rows=[]
        for index,name in enumerate(('results.json','client.log','01-menu.png')):
            root=OUT/('initial-collision-'+str(index));root.mkdir();marker=b'preexisting producer bytes\x00\xff';(root/name).write_bytes(marker);calls=[]
            with self.assertRaisesRegex(ValueError,'existing producer output'):
                scope['write_declared_trial'](root,scope['fixture_identity'](),clock=Clock(),format_writer=scope['_write_format_trial_v1'],snapshot=scope['_snapshot'],observer=lambda *a,**k:calls.append((a,k)))
            self.assertEqual((root/name).read_bytes(),marker);self.assertEqual(calls,[]);rows.append(name)
        self.assertEqual((BASELINES['ordinary'][0]/'original-failure.bin').read_bytes(),b'unchanged original artifact\x00\xff')
        save('INITIAL_COLLISIONS.json',rows)
    def test_06_replaced_owned_metadata_is_not_overwritten(self):
        original=Producer.trace;marker=b'unique replacement metadata\x00\xff';injected=[]
        def trace(producer,event,**fields):
            if event=='capture_end' and fields.get('capture')=='01-menu' and not injected:
                (producer.root/'actions.json').rename(producer.root/'retained-original-actions.bin')
                (producer.root/'actions.json').write_bytes(marker);injected.append(str(producer.root))
            return original(producer,event,**fields)
        error=None
        try:
            with patch.object(Producer,'trace',trace):root,result,clock=run_case('owned-replacement')
        except (ValueError,OSError) as caught:error=type(caught).__name__+': '+str(caught)
        root=OUT/'owned-replacement';after=(root/'actions.json').read_bytes()
        save('OWNED_REPLACEMENT.json',dict(marker_hex=marker.hex(),retained_original_exists=(root/'retained-original-actions.bin').exists(),error=error,after_bytes=len(after),after_sha256=hashlib.sha256(after).hexdigest(),marker_preserved=after==marker))
        self.assertEqual(after,marker,'Name membership cannot authorize truncating a replaced metadata file')
    def test_07_one_shot_capture_publication_error_retains_partial(self):
        original=Producer.put;error=OSError('original one-shot capture publication error');raised=[]
        def put(producer,name,raw):
            if name=='05-after-fire.png' and not raised:raised.append(True);raise error
            return original(producer,name,raw)
        caught=None
        try:
            with patch.object(Producer,'put',put):run_case('capture-publication-error')
        except OSError as actual:caught=actual
        root=OUT/'capture-publication-error';self.assertIs(caught,error)
        self.assertTrue((root/'04-move-aim.png').is_file());self.assertFalse((root/'05-after-fire.png').exists());self.assertFalse((root/'06-after-reload.png').exists())
        self.assertIs(json.loads((root/'results.json').read_text())['passed'],False)
        save('CAPTURE_PUBLICATION_FAILURE.json',dict(error=str(caught),same_original_exception=True,files=sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())))
    def test_08_declared_route_and_pulse_match_pure_source_branch(self):
        root,result,_=BASELINES['ordinary'];declared=result['settings_cover_route'];feedback=copy.deepcopy(declared['observations']);index=0
        clock=Clock();records=[];pulses=[];keys=[];ui=FakeUI(clock)
        def observe():
            nonlocal index
            if index:clock.advance(.01)
            value=feedback[index];index+=1;return copy.deepcopy(value)
        def pulse(names,seconds,deadline):
            receipt={};source_scope['key_pulse'](ui,names,seconds,deadline=deadline,receipt=receipt,clock=clock.monotonic,sleep=clock.advance,elapsed_clock=clock.perf_counter)
            pulses.append(receipt);return receipt
        receipt={}
        source_scope['relocate_settings_actor'](copy.deepcopy(feedback[0]),actor_id=1,round_number=2,observe=observe,
            key=lambda name,down:keys.append((name,down)),pause=clock.advance,record=lambda event,**fields:records.append(dict(event=event,**fields)),deadline=clock.monotonic()+35,receipt=receipt,clock=clock.monotonic,pulse=pulse)
        self.assertEqual(index,15);self.assertEqual(len(pulses),6);self.assertEqual(len(receipt['observations']),15)
        self.assertEqual(receipt['status'],'FIXED_ROUTE_REACHED');self.assertEqual(receipt['endpoint'],declared['endpoint'])
        self.assertEqual(len(keys),8);self.assertTrue(all(not down for name,down in keys))
        actions=json.loads((root/'actions.json').read_text());controls=[r for r in actions if r['event']=='settings_route_movement_control']
        actual=[r for r in records if r['event']=='movement_control'];self.assertEqual(len(controls),len(actual))
        for a,b in zip(controls,actual):
            for field in ('mode','distance','simulation_per_wall','pulse_wall_seconds'):self.assertEqual(a[field],b[field])
        for a,b in zip(declared['native_pulses'],pulses):
            self.assertEqual(set(a),set(b));self.assertEqual(a['status'],b['status'])
            self.assertEqual(a['keys'],b['keys']);self.assertEqual(a['requested_seconds'],b['requested_seconds'])
            self.assertEqual([r['label'] for r in a['os_states']],[r['label'] for r in b['os_states']])
            self.assertEqual(a['sleep_calls'],b['sleep_calls']);self.assertIs(a['release_complete'],True)
        save('ROUTE_SOURCE_REPLAY.json',dict(source_hashes=SOURCE_HASHES,source_route=receipt,source_pulses=pulses,source_records=records,feedback_reads=index,declared_algorithmic_only=True,physical_or_OS_truth=False))


def forbidden(*args,**kwargs):raise AssertionError('Real effect forbidden in staged consumer controls')


def main():
    assert os.sched_getaffinity(0)=={4};assert not OUT.exists();OUT.mkdir()
    (OUT/'PRIVATE_RECIPE_V1.py').write_bytes(adapted)
    save('RECIPE_BINDING.json',dict(original_fixture_sha256=hashlib.sha256(fixture).hexdigest(),private_recipe_sha256=hashlib.sha256(adapted).hexdigest(),literal_changes=[dict(before=a.decode(),after=b.decode()) for a,b in changes],source_hashes=SOURCE_HASHES))
    stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((subprocess,'Popen'),(subprocess,'run'),(os,'kill'),(os,'killpg'),(ctypes,'CDLL'),(time,'sleep')):
            guard.enter_context(patch.object(obj,name,forbidden))
        if hasattr(ctypes,'WinDLL'):guard.enter_context(patch.object(ctypes,'WinDLL',forbidden))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsumerControls))
    (OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),failure_names=[test.id() for test,_ in result.failures],error_names=[test.id() for test,_ in result.errors],source_hashes=SOURCE_HASHES,R2_reader_or_actual_collector_executed=False,native_API_helper_process_or_study_trials=0)
    save('RESULTS.json',report)
    size=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file());assert size<25*1024*1024,size
    print(json.dumps(dict(**report,total_retained_bytes=size)))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
