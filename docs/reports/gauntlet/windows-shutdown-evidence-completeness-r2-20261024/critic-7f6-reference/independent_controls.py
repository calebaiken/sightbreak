"""Source-derived receipt falsifiers; only synthetic files/fake main/owner data."""
import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE=DATA=OUTPUT=study=evidence=old_models=None
CASES=[];CAPTURES=[];REQUIRED=[]


def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(value):return json.dumps(value,indent=2,allow_nan=False)+'\n'


class ReceiptControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=old_models.StudyTests();cls.addClassCleanup(cls.model.doCleanups)
        report,_,_,_=cls.model.run_generated(observe=True)
        (OUTPUT/'BOOTSTRAP_REPORT.json').write_text(dump(report))
        if not report['passed']:raise AssertionError('source-shaped positive construction failed: '+str([r.get('evidence_error') for r in report['trials']]))
        cls.root=Path(report['trials'][0]['output'])
        cls.base={p.relative_to(cls.root).as_posix():p.read_bytes() for p in cls.root.rglob('*') if p.is_file()}
        cls.good=dict(identity=copy.deepcopy(report['identity']),trial=copy.deepcopy({k:v for k,v in report['trials'][0].items() if k not in ('evidence','evidence_error','strict_passed')}))
        cls.verbose=copy.deepcopy(report['trials'][1]);cls.identity=copy.deepcopy(report['identity'])
        baseline=OUTPUT/'baseline';baseline.mkdir()
        for name,raw in cls.base.items():p=baseline/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        (OUTPUT/'BASELINE_CONTEXT.json').write_text(dump(cls.good))

    def setUp(self):self.restore()

    def restore(self):
        for p in self.root.rglob('*'):
            if p.is_file() or p.is_symlink():p.unlink()
        for name,raw in self.base.items():p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        self.context=copy.deepcopy(self.good)

    def row(self):return json.loads((self.root/'results.json').read_bytes())

    def put(self,row):
        (self.root/'results.json').write_text(dump(row))
        (self.root/'controller-stdout.log').write_text('\n'.join(CAPTURES)+'\n'+dump(row))

    def record(self,label,expected,*,root=None,context=None,cwd=None,explicit=None):
        directory=self.root if root is None else root;ctx=self.context if context is None else context
        before=Path.cwd();error=None;result=None
        try:
            if cwd is not None:os.chdir(cwd)
            result=study.trial_evidence(directory,context=ctx)
        except Exception as caught:error=type(caught).__name__+': '+str(caught)
        finally:os.chdir(before)
        ordinal=len(CASES)+1;dest=OUTPUT/'cases'/('%03d-'%ordinal+label);dest.mkdir(parents=True)
        actual={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        changed=[]
        for name,raw in actual.items():
            if self.base.get(name)!=raw:
                p=dest/'delta'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);changed.append(name)
        (dest/'CONTEXT.json').write_text(dump(ctx))
        metadata=dict(label=label,expected_strict_passed=expected,actual_strict_passed=None if result is None else result.get('strict_passed'),
                      candidate_exception=error,original_root=str(self.root),call_root=str(directory),cwd=None if cwd is None else str(cwd),
                      changed_files=changed,removed_files=sorted(set(self.base)-set(actual)),
                      file_bindings={name:dict(bytes=len(raw),sha256=sha(raw)) for name,raw in actual.items()},extra=explicit)
        (dest/'INPUT.json').write_text(dump(metadata));(dest/'RESULT.json').write_text(dump(result))
        CASES.append(metadata)
        with self.subTest(case=label):
            self.assertIsNone(error,'candidate threw instead of returning explicit completeness errors')
            self.assertIsNotNone(result)
            self.assertIs(result['strict_passed'],expected)
        return result

    def test_01_coherent_positive_variants_and_relative_caller_path(self):
        self.record('ordinary-positive',True)
        trial=copy.deepcopy(self.verbose)
        verbose=study.trial_evidence(Path(trial['output']),context=dict(identity=self.identity,trial=trial))
        (OUTPUT/'VERBOSE_POSITIVE.json').write_text(dump(verbose));self.assertTrue(verbose['strict_passed'])
        self.restore();(self.root/'unknown.partial').write_bytes(b'complete unknown extra\x00\xff')
        result=self.record('unknown-extra-positive',True);self.assertIn('unknown.partial',result['extra_files'])
        self.restore();row=self.row();row['elapsed_seconds']=301
        self.context['trial']['finished_monotonic']=self.context['trial']['started_monotonic']+302
        self.context['trial']['job_queries'][-1]['monotonic']=self.context['trial']['finished_monotonic']+.01
        self.put(row);self.record('coherent-cleanup301-positive',True)
        self.restore();row=self.row();path=self.root/'restart-profile-trace/events.jsonl';lines=path.read_bytes().splitlines();initial=json.loads(lines[0])
        initial['match_seed']='-315159265';initial['actor_spread_seeds']={key:str(-abs(int(value))) for key,value in initial['actor_spread_seeds'].items()}
        lines[0]=json.dumps(initial).encode();path.write_bytes(b'\n'.join(lines)+b'\n')
        for key in ('expected_binding','binding_before_capture','binding_after_capture'):row['phase_capture_fences']['10-reopened-loaded-settings'][key]['loaded_initial_event']=copy.deepcopy(initial)
        self.put(row);self.record('signed-seed-positive',True)
        self.restore();row=self.row();cwd=self.root.parent.parent;relative=Path(self.root.parent.name)/self.root.name
        self.context['trial']['output']=str(relative)
        argv=self.context['trial']['driver_arguments'];argv[argv.index('--output')+1]=str(relative)
        row['controller_command']=[sys.executable,*argv];self.put(row)
        self.record('source-permitted-relative-output-positive',True,root=relative,cwd=cwd)

    def test_02_all_independently_derived53_required_omissions(self):
        self.record('omission-baseline',True)
        for index,name in enumerate(REQUIRED):
            self.restore();(self.root/name).unlink()
            result=self.record('missing-%02d'%index,False,explicit=dict(missing=name))
            self.assertIn('missing required file: '+name,result['evidence_errors'])

    def test_03_named_capture_context_and_two_frame_relationships(self):
        self.record('capture-baseline',True)
        for kind in ('wrong-phase','wrong-actor','missing-two-frames','dead-after-capture'):
            self.restore();row=self.row();fence=row['phase_capture_fences']['06c-next-round'];state=fence['after_capture']
            if kind=='wrong-phase':state.update(phase='live',time_left=99.)
            elif kind=='wrong-actor':state['local_actor']=copy.deepcopy(state['actors'][1])
            elif kind=='missing-two-frames':
                ready=fence['ready'];ready['drawn_frames']=fence['acknowledged']['drawn_frames'];ready['frame_diagnostics']['drawn_frames']=ready['drawn_frames']
            else:
                state['local_actor'].update(alive=False,health=0.)
                next(actor for actor in state['actors'] if actor['id']==state['local_actor']['id']).update(alive=False,health=0.)
            self.put(row);self.record('capture-'+kind,False)

    def test_04_pause_and_source_constant_receipts(self):
        self.record('subreceipt-baseline',True)
        for kind in ('pause-not-paused','paused-time-advanced','reload-deadline-false','reload-watchdog-bool','settings-living-false'):
            self.restore();row=self.row()
            if kind=='pause-not-paused':row['hud_analysis_pauses'][0]['paused']['ui']['paused']=False
            elif kind=='paused-time-advanced':row['hud_analysis_pauses'][0]['after_analysis']['elapsed']=row['hud_analysis_pauses'][0]['paused']['elapsed']+1.
            elif kind=='reload-deadline-false':row['native_reload']['whole_flow_deadline_unchanged']=False
            elif kind=='reload-watchdog-bool':row['native_reload']['completion_watchdog_seconds']=True
            else:row['native_settings_resume']['same_living_player_required']=False
            self.put(row);self.record(kind,False)

    def test_05_callback_job_relationships_and_x64_boundaries(self):
        self.record('job-baseline',True)
        for kind in ('wrong-callback-job-label','job-before-callback-clock','missing-active-identities','controller-birth-u65','controller-handle-u65'):
            self.restore();trial=self.context['trial'];launch=trial['observations'][0]
            if kind=='wrong-callback-job-label':launch['job']['label']='trial4/native_launch'
            elif kind=='job-before-callback-clock':launch['job']['monotonic']=0.
            elif kind=='missing-active-identities':launch['job'].pop('processes')
            else:
                key='creation_filetime' if kind=='controller-birth-u65' else 'handle_value'
                for query in [trial['job_queries'][0],*[o['job'] for o in trial['observations']],trial['job_queries'][1]]:
                    for row in [*query.get('held_processes',[]),*query.get('processes',[])]:
                        if row['pid']==99:row[key]=2**64+1
            self.record(kind,False)

    def test_06_actual_byte_formats_and_synchronized_close_types(self):
        self.record('format-baseline',True)
        for kind in ('png-crc','duplicate-json','close-limit21','close-exit-bool'):
            self.restore()
            if kind=='png-crc':
                p=self.root/'01-menu.png';raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
            elif kind=='duplicate-json':
                p=self.root/'results.json';raw=p.read_bytes().replace(b'"passed": true',b'"passed": true, "passed": true',1);p.write_bytes(raw)
                (self.root/'controller-stdout.log').write_bytes(('\n'.join(CAPTURES)+'\n').encode()+raw)
            else:
                row=self.row();key='close_limit_seconds' if kind=='close-limit21' else 'exit_code';value=21 if key=='close_limit_seconds' else False
                row['shutdown_study_observations'][0][key]=value;self.context['trial']['observations'][1][key]=value;self.put(row)
            self.record(kind,False)

    def test_07_missing_close_propagates_with_complete_files_and_optimistic_loader(self):
        original=study.collect_trials
        def bridge(output,identity,owner,driver,**options):
            def driving(arguments,callback,directory):
                def observed(event,**details):
                    if directory.name.startswith('01-') and event=='close_wait_finished' and details.get('process')=='client':return None
                    return callback(event,**details)
                return driver(arguments,observed,directory)
            return original(output,identity,owner,driving,**options)
        model=old_models.StudyTests()
        try:
            with patch.object(study,'collect_trials',bridge):report,_,owner,_=model.run_generated(observe=True,evidence=True)
            (OUTPUT/'WHOLE_COLLECTION_MISSING_CLOSE.json').write_text(dump(report))
            self.assertEqual(report['attempts'],4);self.assertFalse(report['passed']);self.assertEqual(owner.cleaned,0)
            self.assertFalse(report['trials'][0]['strict_passed']);self.assertEqual(report['trials'][0]['evidence']['availability']['present_required_files'],53)
            self.assertTrue(all(row['strict_passed'] for row in report['trials'][1:]))
            self.assertIn('two launches/two closes missing',';'.join(report['trials'][0]['evidence']['evidence_errors']))
        finally:model.doCleanups()

    def test_08_wrapper_originals_and_publication_receipt_collision(self):
        records=[]
        for scenario in ('success','invocation-error','receipt-collision'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp);out=root/'trial';capture=root/'trial.controller-capture';marker=b'preexisting unique publication bytes\x00\xff';calls=[]
                def fake_main(*,study_observer):
                    calls.append(True);self.assertFalse(any(out.iterdir()),'exact default empty-output guard')
                    print('full raw controller line');sys.stderr.write('raw stderr line\n')
                    if scenario=='receipt-collision':(capture/'publication.json').write_bytes(marker)
                    if scenario=='invocation-error':print('partial tail');raise RuntimeError('original pure invocation error')
                error=None
                try:
                    with patch.dict(sys.modules,{'verify_offline_export':types.SimpleNamespace(main=fake_main)}):study.real_driver(['scripts/verify_offline_export.py','--output',str(out)],lambda *a,**k:None,out)
                except Exception as caught:error=type(caught).__name__+': '+str(caught)
                dest=OUTPUT/'wrapper-cases'/scenario;dest.mkdir(parents=True)
                for file in root.rglob('*'):
                    if file.is_file():p=dest/file.relative_to(root);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(file.read_bytes())
                records.append(dict(scenario=scenario,error=error,calls=len(calls),original_marker_hex=marker.hex()))
                with self.subTest(scenario=scenario):
                    self.assertEqual(len(calls),1)
                    self.assertEqual((out/'controller-stdout.log').read_bytes(),(capture/'controller-stdout.log').read_bytes())
                    self.assertEqual((out/'controller-stderr.log').read_bytes(),b'raw stderr line\n')
                    if scenario=='success':self.assertIsNone(error)
                    elif scenario=='invocation-error':self.assertIn('original pure invocation error',error)
                    else:
                        with self.subTest(postcondition='collision-is-error'):self.assertIsNotNone(error,'receipt collision silently succeeded')
                        with self.subTest(postcondition='original-receipt-bytes-retained'):self.assertEqual((capture/'publication.json').read_bytes(),marker)
        (OUTPUT/'WRAPPER_RESULTS.json').write_text(dump(records))

    def test_09_actual_fixed_model_blocks_public_main_before_effects(self):
        retention=study.retention;model=retention.assess(retention.fixed_model());self.assertEqual(model['status'],'BLOCKED');self.assertFalse(model['execution_authorized'])
        out=OUTPUT/'unreached-public-output'
        with patch.object(retention,'preflight',return_value=model),patch.object(study,'WindowsOwner') as owner,patch.object(study,'runtime_identity') as identity,patch.object(study,'real_driver') as driver,patch.object(sys,'argv',['study','collect','--expected-source','0f478a078277fdb0d711837bef67cf14262d9d8f','--output',str(out)]):
            with self.assertRaisesRegex(RuntimeError,'BLOCKED'):study.main()
            owner.assert_not_called();identity.assert_not_called();driver.assert_not_called()
        self.assertFalse(out.exists());(OUTPUT/'PURE_PUBLIC_GATE.json').write_text(dump(dict(model=model,owner_calls=0,identity_calls=0,driver_calls=0,actual_physical_preflight_rerun=False)))


def main():
    global SOURCE,DATA,OUTPUT,study,evidence,old_models,CAPTURES,REQUIRED
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--data',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert os.sched_getaffinity(0)=={4};SOURCE=a.source.resolve();DATA=a.data.resolve();OUTPUT=a.output.resolve();OUTPUT.mkdir(parents=True,exist_ok=False)
    oracle=json.loads((DATA.parent/'phase-a-fixture-adjudication/SOURCE_AND_PROPOSAL_BINDING.json').read_text());CAPTURES=oracle['capture_order'];REQUIRED=oracle['required_baseline_paths']+oracle['controller_additions']
    assert len(REQUIRED)==53;sys.path.insert(0,str(SOURCE/'scripts'))
    with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('subprocess.check_output',side_effect=AssertionError('historical Git forbidden in fresh controls')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
        study=importlib.import_module('windows_shutdown_study');evidence=importlib.import_module('shutdown_study_evidence');old_models=importlib.import_module('test_windows_shutdown_study')
        assert tuple(CAPTURES)==evidence.CAPTURES and set(REQUIRED)==set(evidence.REQUIRED)
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReceiptControls)
        with (OUTPUT/'original.stderr').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    failed={getattr(test,'test_case',test).id() for test,_ in result.failures}
    summary=dict(source=str(SOURCE),methods=result.testsRun,failure_events=len(result.failures),failed_methods=len(failed),errors=len(result.errors),skips=len(result.skipped),
                 loader_cases=len(CASES),false_accepts=[row['label'] for row in CASES if row['expected_strict_passed'] is False and row['actual_strict_passed'] is True],
                 false_rejects=[row['label'] for row in CASES if row['expected_strict_passed'] is True and row['actual_strict_passed'] is False],candidate_exceptions=[row for row in CASES if row['candidate_exception']],native_invocations=0)
    (OUTPUT/'INDEPENDENT.json').write_text(dump(summary));print(json.dumps(summary));raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
