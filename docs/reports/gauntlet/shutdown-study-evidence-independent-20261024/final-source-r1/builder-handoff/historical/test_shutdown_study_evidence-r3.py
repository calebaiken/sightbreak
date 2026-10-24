"""Pure evidence-envelope and wrapper controls; no actual native main is invoked."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zlib

import shutdown_study_evidence as evidence
import shutdown_evidence_fixtures as fixtures
import windows_shutdown_study as study
from test_windows_shutdown_study import StudyTests


class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=StudyTests();cls.addClassCleanup(cls.model.doCleanups)
        report,_,_,_=cls.model.run_generated(observe=True)
        if not report['passed']:raise AssertionError([t.get('evidence_error') for t in report['trials']])
        trial=report['trials'][0];cls.root=Path(trial['output'])
        cls.original={p.relative_to(cls.root).as_posix():p.read_bytes() for p in cls.root.rglob('*') if p.is_file()}
        cls.original_context=dict(identity=copy.deepcopy(report['identity']),trial=copy.deepcopy({k:v for k,v in trial.items() if k not in ('evidence','evidence_error','strict_passed')}))
    def setUp(self):
        for p in self.root.rglob('*'):
            if p.is_file() or p.is_symlink():p.unlink()
        for name,data in self.original.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        self.context=copy.deepcopy(self.original_context)
    def load(self):return study.trial_evidence(self.root,context=self.context)
    def result(self):return json.loads((self.root/'results.json').read_text())
    def put_result(self,row):
        (self.root/'results.json').write_text(json.dumps(row,indent=2)+'\n')
        (self.root/'controller-stdout.log').write_text('\n'.join(evidence.CAPTURES)+'\n'+json.dumps(row,indent=2)+'\n')
    def reject(self):
        result=self.load();self.assertFalse(result['strict_passed']);return result
    def test_ordinary_complete_envelope_is_unreviewed_not_native_approval(self):
        result=self.load();self.assertTrue(result['evidence_complete']);self.assertTrue(result['strict_passed'])
        self.assertEqual(result['independent_qualification'],'UNREVIEWED')
        self.assertEqual(result['availability']['present_required_files'],53)
        self.assertIn('original-failure.bin',result['extra_files'])
    def test_every_required_file_omission_rejects_without_changing_others(self):
        for name in evidence.REQUIRED:
            with self.subTest(name=name):
                p=self.root/name;original=p.read_bytes();p.unlink()
                result=self.reject();self.assertIn('missing required file: '+name,result['evidence_errors'])
                p.write_bytes(original)
        self.assertEqual({p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()},self.original)
    def test_passed_only_result_with_valid_context_still_fails(self):
        for p in self.root.rglob('*'):
            if p.is_file():p.unlink()
        (self.root/'results.json').write_text('{"passed":true}\n')
        result=self.reject();self.assertFalse(result['evidence_complete']);self.assertEqual(result['availability']['present_required_files'],1)
    def test_missing_results_with_valid_process_context_is_explicit(self):
        (self.root/'results.json').unlink();result=self.reject()
        self.assertTrue(any('results.json' in error for error in result['evidence_errors']))
    def test_strict_json_duplicate_nonfinite_wrongtype_and_empty_reject(self):
        original=(self.root/'results.json').read_bytes()
        for raw in (b'{"passed":true,"passed":true}',b'{"passed":NaN}',b'{"passed":1e999}',b'[]',b'',b'\xff'):
            with self.subTest(raw=raw):
                (self.root/'results.json').write_bytes(raw);self.reject()
        (self.root/'results.json').write_bytes(original)
    def test_png_crc_raster_filter_truncation_and_dimensions_reject(self):
        p=self.root/'01-menu.png';raw=p.read_bytes()
        bad=bytearray(raw);bad[-1]^=1
        def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
        header=chunk(b'IHDR',struct.pack('>IIBBBBB',640,360,8,2,0,0,0))
        wrong_filter=b'\x89PNG\r\n\x1a\n'+header+chunk(b'IDAT',zlib.compress((b'\x05'+b'\0'*(640*3))*360))+chunk(b'IEND',b'')
        for data in (bytes(bad),raw[:-5],raw+b'x',wrong_filter,fixtures.png_bytes(641,360)):
            with self.subTest(bytes=len(data)):
                p.write_bytes(data);self.reject()
        p.write_bytes(raw)
    def test_unknown_partial_extras_are_retained_and_hashed(self):
        p=self.root/'unknown-extension.partial';p.write_bytes(b'\0full unknown original\xff')
        result=self.load();self.assertTrue(result['strict_passed']);self.assertIn(p.name,result['extra_files'])
        row=next(x for x in result['all_files'] if x['path']==p.name);self.assertEqual(row['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
    def test_ocr_empty_list_count_and_mirrors_do_not_authorize(self):
        row=self.result();row['ocr_commands']=[];(self.root/'ocr-commands.json').write_text('[]');self.put_result(row)
        self.reject()
    def test_ocr_count_hash_path_exit_and_complete_mutations_reject(self):
        base=json.loads((self.root/'ocr-commands.json').read_text());result=self.result()
        for key,value in (('stdout_total_bytes',0),('stdout_sha256','0'*64),('stdout_path','ocr-stdout/../../elsewhere'),('exit_code',1),('stdout_complete',False),('stdout_truncated',True),('timed_out',True),('started_seconds',False)):
            with self.subTest(key=key):
                ocr=copy.deepcopy(base);ocr[0][key]=value
                (self.root/'ocr-commands.json').write_text(json.dumps(ocr));row=copy.deepcopy(result);row['ocr_commands']=ocr;self.put_result(row);self.reject()
        (self.root/'ocr-commands.json').write_text(json.dumps(base));self.put_result(result)
    def test_empty_successful_ui_ocr_and_bad_hud_cannot_pass_hash_coherence(self):
        original=self.result();base=json.loads((self.root/'ocr-commands.json').read_text())
        for index,payload in ((5,b''),(6,b'ELIMINATED\n')):
            row=copy.deepcopy(original);ocr=copy.deepcopy(base);name='ocr-stdout/%03d.log'%index
            (self.root/name).write_bytes(payload);ocr[index-1].update(stdout_total_bytes=len(payload),stdout_retained_bytes=len(payload),stdout_sha256=hashlib.sha256(payload).hexdigest())
            row['ocr_commands']=ocr;(self.root/'ocr-commands.json').write_text(json.dumps(ocr));self.put_result(row);self.reject()
            (self.root/name).write_bytes(self.original[name])
    def test_source_artifact_host_pid_and_profile_ties_reject(self):
        base=self.result()
        for change in ('source','artifact','host','pid','profile'):
            row=copy.deepcopy(base)
            if change=='source':row['source']['source_commit']='f'*40
            elif change=='artifact':row['executable_sha256']='f'*64
            elif change=='host':row['host']='unrelated host'
            elif change=='pid':
                row['commands'][0]['pid']+=1000;(self.root/'commands.json').write_text(json.dumps(row['commands']))
            else:row['phase_capture_fences']['10-reopened-loaded-settings']['binding_before_capture']['stored_profile']={}
            self.put_result(row);self.reject()
            (self.root/'commands.json').write_bytes(self.original['commands.json'])
    def test_empty_missing_or_stale_trace_fields_reject(self):
        p=self.root/'restart-profile-trace/events.jsonl';lines=p.read_bytes().splitlines()
        for change in ('empty','seed','index','scope','drop','profile'):
            initial=json.loads(lines[0]);rows=list(lines)
            if change=='empty':p.write_bytes(b'')
            else:
                if change=='seed':initial['actor_spread_seeds']={}
                elif change=='index':initial['event_index']=True
                elif change=='scope':initial['scope']='online_private'
                elif change=='drop':initial['events_dropped']=1
                else:initial['initial_profile']={}
                rows[0]=json.dumps(initial).encode();p.write_bytes(b'\n'.join(rows)+b'\n')
            self.reject()
        p.write_bytes(self.original[p.relative_to(self.root).as_posix()])
    def test_missing_empty_mismatched_process_and_close_context_reject(self):
        original=copy.deepcopy(self.context)
        for change in ('no_context','no_callbacks','no_birth','no_held_exit','close_pid','close_copy','close_error','close_budget'):
            self.context=copy.deepcopy(original);row=self.result()
            if change=='no_context':self.context=None
            elif change=='no_callbacks':self.context['trial']['observations']=[]
            elif change=='no_birth':self.context['trial']['observations'][0]['native_root_identity']={}
            elif change=='no_held_exit':self.context['trial']['job_queries'][-1]['held_processes']=[]
            elif change=='close_pid':row['shutdown_study_observations'][0]['pid']+=1
            elif change=='close_copy':self.context['trial']['observations'][1]['exit_code']=1
            elif change=='close_error':row['shutdown_study_observations'][0]['original_close_error']='timeout'
            else:row['shutdown_study_observations'][0]['wait_finished_monotonic']=row['shutdown_study_observations'][0]['request_before_monotonic']+21
            self.put_result(row);self.reject();self.put_result(json.loads(self.original['results.json']))
        self.context=original
    def test_warning_and_native_error_fail_without_filtering_bytes(self):
        p=self.root/'reopened.log';base=p.read_bytes()
        for text in (b'WARNING: ANGLE software renderer\n',b'ERROR: bad native state\n',b'ObjectDB instances leaked at exit\n'):
            p.write_bytes(base+text);result=self.reject();self.assertTrue(result['strict_errors']);self.assertEqual(p.read_bytes(),base+text)
    def test_cleanup_elapsed_and_wall_clock_step_are_not_invented_deadlines(self):
        row=self.result();row['elapsed_seconds']=301
        self.context['trial']['finished_monotonic']=self.context['trial']['started_monotonic']+302
        close=row['shutdown_study_observations'][0];close['wait_finished_wall_unix_ns']=close['request_before_wall_unix_ns']-1000
        self.context['trial']['observations'][1]['wait_finished_wall_unix_ns']=close['wait_finished_wall_unix_ns']
        self.put_result(row);self.assertTrue(self.load()['strict_passed'])
    def test_capture_sizes_follow_each_record_not_request_or_all_other_captures(self):
        row=self.result();name=evidence.CAPTURES[0];dimensions=[800,450]
        (self.root/(name+'.png')).write_bytes(fixtures.png_bytes(*dimensions));row['captures'][0]['dimensions']=dimensions
        actions=json.loads((self.root/'actions.json').read_text())
        for action in actions:
            if action.get('event')=='capture_end' and action.get('capture')==name:action['dimensions']=dimensions
        (self.root/'actions.json').write_text(json.dumps(actions));self.put_result(row);self.assertTrue(self.load()['strict_passed'])
    def test_exact_windows_controller_crlf_form_is_retained(self):
        p=self.root/'controller-stdout.log';p.write_bytes(p.read_bytes().replace(b'\n',b'\r\n'));self.assertTrue(self.load()['strict_passed'])


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.parent=Path(self.temp.name);self.out=self.parent/'trial';self.calls=[]
    def invoke(self,behavior=None):
        out=self.out
        def fake_main(*,study_observer):
            self.calls.append(True)
            if out.exists() and any(out.iterdir()):raise AssertionError('unchanged required-empty-output guard')
            print('full controller output')
            if behavior is not None:behavior(out)
            (out/'results.json').write_text('{"fake":true}\n')
        with patch.dict(sys.modules,{'verify_offline_export':types.SimpleNamespace(main=fake_main)}):
            study.real_driver(['scripts/verify_offline_export.py','--output',str(out)],lambda *a,**k:None,out)
    def test_real_wrapper_fake_success_passes_empty_guard_and_keeps_full_capture(self):
        self.invoke();capture=self.out.with_name('trial.controller-capture')
        self.assertEqual((self.out/'controller-stdout.log').read_bytes(),(capture/'controller-stdout.log').read_bytes())
        self.assertEqual((self.out/'controller-stderr.log').read_bytes(),b'');self.assertEqual(len(self.calls),1)
    def test_invocation_failure_retains_both_full_streams_and_original_error(self):
        def fail(out):print('partial failure output');raise RuntimeError('original fake invocation failure')
        with self.assertRaisesRegex(RuntimeError,'original fake invocation failure'):self.invoke(fail)
        self.assertIn(b'partial failure output',(self.out/'controller-stdout.log').read_bytes())
        self.assertIsNotNone(json.loads((self.out.with_name('trial.controller-capture')/'publication.json').read_text())['invocation_error'])
    def test_fresh_capture_collision_never_calls_main_or_overwrites(self):
        p=self.out.with_name('trial.controller-capture');p.mkdir();(p/'original').write_bytes(b'original')
        with self.assertRaises(FileExistsError):self.invoke()
        self.assertFalse(self.calls);self.assertEqual((p/'original').read_bytes(),b'original')
    def test_publication_collision_keeps_original_and_both_capture_streams(self):
        with self.assertRaisesRegex(RuntimeError,'publication failed'):self.invoke(lambda out:(out/'controller-stdout.log').write_bytes(b'collision original'))
        self.assertEqual((self.out/'controller-stdout.log').read_bytes(),b'collision original')
        self.assertTrue((self.out/'controller-stderr.log').is_file());self.assertIn(b'full controller output',(self.out.with_name('trial.controller-capture')/'controller-stdout.log').read_bytes())
    def test_partial_copy_error_retains_partial_and_full_originals(self):
        original=shutil.copyfileobj;calls=0
        def copy(reader,writer,*args):
            nonlocal calls
            calls+=1
            if calls==1:writer.write(reader.read(3));raise OSError('fake partial copy')
            return original(reader,writer,*args)
        with patch.object(shutil,'copyfileobj',copy),self.assertRaisesRegex(RuntimeError,'publication failed'):self.invoke()
        self.assertEqual((self.out/'controller-stdout.log').read_bytes(),b'ful')
        self.assertEqual((self.out.with_name('trial.controller-capture')/'controller-stdout.log').read_bytes(),b'full controller output\n')
        self.assertTrue((self.out/'controller-stderr.log').is_file())


if __name__=='__main__':unittest.main()
