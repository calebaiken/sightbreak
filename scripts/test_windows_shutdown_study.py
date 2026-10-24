"""Generated pure controls only: no Windows API/process/engine is invoked."""
import copy
import ast
import ctypes as C
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import shutdown_study_retention as retention
import windows_shutdown_study as study

BASE='8ee93ac725d519c9f6d7f1ffbb3f7c9ee960baf8'


class Owner:
    def __init__(self,fail=None,survivor=None):self.baseline=99;self.queries=[];self.fail=fail;self.survivor=survivor;self.cleaned=0
    def query(self,label):
        row=dict(label=label,verified=True,active_processes=1,process_ids=[99]);self.queries.append(row)
        if self.fail and self.fail in label:row.update(verified=False,error='query failed');raise RuntimeError('query failed')
        if self.survivor and self.survivor in label:row.update(active_processes=2,process_ids=[99,100])
        return row
    def baseline_only(self,row):return row.get('verified') and row.get('active_processes')==1 and row.get('process_ids')==[99]
    def safety_cleanup(self):self.cleaned+=1;return dict(passed=True,failure_only=True,never_normal_close=True)


class StudyTests(unittest.TestCase):
    def run_generated(self,*,failures=(),owner=None,identity_reader=None,observe=False,evidence=True):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)/'study';calls=[]
        owner=owner or Owner();identity={'source':'exact','exe':'same','pck':'same','host':'same'}
        def driver(args,callback,directory):
            index=len(calls)+1;calls.append((args,directory))
            directory.mkdir();(directory/'original-failure.bin').write_bytes(bytes([index])*7)
            if observe:callback('native_launch',pid=100+index)
            if index in failures:raise RuntimeError('preserved failure '+str(index))
        result=study.collect_trials(root,identity,owner,driver,identity_reader=identity_reader or (lambda:identity),
                                    load_evidence=lambda _:dict(strict_passed=evidence))
        return result,calls,owner,root

    def test_all_four_exact_balanced_order_and_distinct_profiles(self):
        result,calls,owner,_=self.run_generated(observe=True)
        self.assertTrue(result['passed']);self.assertEqual(result['attempts'],4)
        self.assertEqual([('--reopened-verbose' in args) for args,_ in calls],[False,True,True,False])
        self.assertEqual(len({str(p) for _,p in calls}),4)
        for args,_ in calls:
            self.assertEqual(args[args.index('--timeout')+1],'300')
            self.assertNotIn('--quit-after',args);self.assertFalse(any('seed' in arg for arg in args))
        self.assertEqual(owner.cleaned,0)

    def test_every_failure_subset_consumes_fixed_arm_no_replacement(self):
        for mask in range(16):
            failures=[i+1 for i in range(4) if mask&(1<<i)]
            with self.subTest(failures=failures):
                result,calls,owner,root=self.run_generated(failures=failures)
                self.assertEqual(len(calls),4);self.assertEqual(result['attempts'],4)
                self.assertEqual(result['passed'],not failures)
                for i in range(1,5):
                    self.assertTrue(any(q['label']==f'trial{i}/after' for q in owner.queries))
                    self.assertEqual((Path(result['trials'][i-1]['output'])/'original-failure.bin').read_bytes(),bytes([i])*7)
                self.assertEqual(owner.cleaned,0)

    def test_unreached_close_counts_as_failed_attempt_not_replacement(self):
        result,calls,_,_=self.run_generated(failures=(1,2,3,4),evidence=False)
        self.assertFalse(result['passed']);self.assertEqual(len(calls),4)
        self.assertTrue(all(t['attempted'] and 'driver_error' in t for t in result['trials']))

    def test_missing_results_preserves_originals_and_attempt(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);out=Path(temp.name)/'out';owner=Owner()
        def driver(args,callback,directory):directory.mkdir();(directory/'partial.tmp').write_bytes(b'original')
        result=study.collect_trials(out,{},owner,driver,identity_reader=lambda:{})
        self.assertEqual(result['attempts'],4);self.assertFalse(result['passed'])
        self.assertTrue(all('evidence_error' in t for t in result['trials']))
        self.assertEqual(len(list(out.rglob('partial.tmp'))),4)

    def test_query_failure_before_and_after_flow_stops_and_audits(self):
        for phase,attempts in [('trial2/before',1),('trial2/after',2),('trial2/native_launch',2)]:
            with self.subTest(phase=phase):
                result,calls,owner,_=self.run_generated(owner=Owner(fail=phase),observe=True)
                self.assertEqual(len(calls),attempts);self.assertFalse(result['passed']);self.assertTrue(result['stopped'])
                self.assertEqual(owner.cleaned,1);self.assertEqual(owner.queries[-1]['label'],'study/final')

    def test_owned_survivor_forces_safety_then_stops(self):
        for phase,count in [('trial1/before',0),('trial3/after',3)]:
            result,calls,owner,_=self.run_generated(owner=Owner(survivor=phase))
            self.assertEqual(len(calls),count);self.assertEqual(owner.cleaned,1)
            self.assertTrue(result['trials'][-1]['failure_safety_cleanup']['never_normal_close'])
            self.assertFalse(result['passed'])

    def test_identity_changes_stop_source_exe_pck_or_host(self):
        for field in ('source','exe','pck','host'):
            for changed_at in (1,2,3,8):
                calls=0;base={'source':'exact','exe':'same','pck':'same','host':'same'}
                def read():
                    nonlocal calls
                    calls+=1;value=base.copy()
                    if calls>=changed_at:value[field]='changed'
                    return value
                result,_,owner,_=self.run_generated(identity_reader=read)
                self.assertFalse(result['passed']);self.assertTrue(result.get('stopped'));self.assertEqual(owner.cleaned,1)

    def test_final_audit_failure_cannot_pass(self):
        result,calls,_,_=self.run_generated(owner=Owner(fail='study/final'))
        self.assertEqual(len(calls),4);self.assertFalse(result['passed']);self.assertIn('final_ownership_error',result)

    def test_failure_safety_budget_is_single_use_even_with_final_unknown(self):
        class AlwaysUnknown(Owner):
            def query(self,label):
                self.queries.append(dict(label=label,verified=False,error='unknown'))
                raise RuntimeError('unknown')
        result,calls,owner,_=self.run_generated(owner=AlwaysUnknown())
        self.assertFalse(result['passed']);self.assertFalse(calls)
        self.assertEqual(owner.cleaned,1,'one failure-only5s budget for collection, never renewed')

    def test_current_preflight_blocks_before_owner_or_driver(self):
        check=dict(status='BLOCKED',execution_authorized=False)
        with patch.object(retention,'preflight',return_value=check),patch.object(study,'WindowsOwner') as owner,patch.object(study,'real_driver') as driver,patch.object(sys,'argv',['study','collect','--expected-source','a'*40,'--output','/unreached']):
            with self.assertRaisesRegex(RuntimeError,'BLOCKED'):study.main()
            owner.assert_not_called();driver.assert_not_called()

    def test_exact_pck_range_and_corrupt_trailers(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);p=Path(temp.name)/'synthetic.exe'
        pack=struct.pack('<6IQ',0x43504447,4,4,7,2,0,0)+b'PACK-DATA'
        blob=b'PE-prefix'+pack+struct.pack('<QI',len(pack),0x43504447);p.write_bytes(blob)
        value=study.embedded_pck_identity(p)
        self.assertEqual(value['sha256'],retention.sha(pack));self.assertEqual(value['offset'],9)
        for bad in (b'',blob[:-1],blob[:-12]+struct.pack('<QI',len(blob)+1,0x43504447),blob.replace(pack[:4],b'xxxx')):
            p.write_bytes(bad)
            with self.assertRaises((RuntimeError,struct.error)):study.embedded_pck_identity(p)

    def test_typed_instances_separate_resource_cache_never_infer_owner(self):
        raw=b'WARNING: 3 ObjectDB instances leaked at exit\nLeaked instance: RefCounted:9223372036854775808 - Reference count: 2\nLeaked instance: Node:123\nLeaked instance: Resource:124 - Resource path: res://thing.tres\nResource still in use: res://different.tres\nLeaked instance: nonsense\n'
        value=study.typed_leak_rows(raw)
        self.assertEqual(len(value['instances']),3);self.assertEqual(value['instances'][0]['decimal_id'],'9223372036854775808')
        self.assertEqual(value['instances'][0]['reference_count'],2);self.assertEqual(len(value['resource_cache_rows']),1)
        self.assertEqual(value['unparsed_instance_rows'],['Leaked instance: nonsense'])
        self.assertEqual(value['retaining_owner'],'UNRESOLVED');self.assertEqual(value['old_failure_identity'],'NOT_ATTRIBUTED')

    def test_optional_hook_exact_default_byte_erasure(self):
        path=Path(__file__).with_name('verify_offline_export.py');text=path.read_text()
        text=text.replace('def main(*, study_observer=None):','def main():')
        text=re.sub(r'    # BEGIN SHUTDOWN STUDY OBSERVATIONS\n.*?    # END SHUTDOWN STUDY OBSERVATIONS\n','',text,flags=re.S)
        text=re.sub(r'        # BEGIN SHUTDOWN STUDY LAUNCH\n.*?        # END SHUTDOWN STUDY LAUNCH\n','',text,flags=re.S)
        for label in ('INITIAL','REOPENED'):
            text=re.sub(r'        # BEGIN SHUTDOWN STUDY '+label+r' CLOSE\n.*?        # END SHUTDOWN STUDY '+label+r' CLOSE\n((?:            [^\n]*\n){2})',lambda m:''.join(line[4:]+'\n' for line in m[1].splitlines()),text,count=1,flags=re.S)
        old=subprocess.check_output(['git','show',BASE+':scripts/verify_offline_export.py'],cwd=path.parents[1]).decode()
        self.assertEqual(text,old)

    def test_actual_close_helper_original_limits_and_observation_order(self):
        tree=ast.parse(Path(__file__).with_name('verify_offline_export.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        helper=next(n for n in main.body if isinstance(n,ast.FunctionDef) and n.name=='study_close')
        for budget in (3.,19.5,20.,100.):
            for failure in (None,'request','wait'):
                with self.subTest(budget=budget,failure=failure):
                    calls=[];result={'shutdown_study_observations':[]}
                    class Clock:
                        def monotonic(self):return 123.
                        def time_ns(self):return 456
                    class UI:
                        def request_close(self):
                            calls.append('request')
                            if failure=='request':raise RuntimeError('original request failure')
                    class Process:
                        pid=101
                        def wait(self,timeout):
                            calls.append(('wait',timeout))
                            if failure=='wait':raise RuntimeError('original wait failure')
                        def poll(self):return None if failure else 0
                    def observed(event,**row):calls.append('observe')
                    scope=dict(ui=UI(),time=Clock(),result=result,remaining=lambda:budget,study_observer=observed)
                    exec(compile(ast.Module(body=[helper],type_ignores=[]),'<production close helper>','exec'),scope)
                    if failure:
                        with self.assertRaisesRegex(RuntimeError,'original'):scope['study_close'](Process(),'reopened')
                    else:scope['study_close'](Process(),'reopened')
                    self.assertEqual(calls[-1],'observe');self.assertEqual(calls[0],'request')
                    if failure!='request':self.assertEqual(calls[1],('wait',min(20,budget)))
                    row=result['shutdown_study_observations'][0]
                    self.assertEqual(row['close_limit_seconds'],20)
                    self.assertEqual('original_close_error' in row,failure is not None)

    def test_dedicated_workflow_no_other_qualification_and_preflight_first(self):
        text=(Path(__file__).resolve().parents[1]/'.github/workflows/windows-shutdown-study.yml').read_text()
        self.assertNotIn('  push:',text);self.assertEqual(text.count('actions/upload-artifact@'),2)
        self.assertEqual(text.count('scripts/export.py'),1)
        for forbidden in ('run_native_regressions','verify_offline_match','verify_integration_export.py','--smoke','& $ocr --version','macos','linux','matrix:','continue-on-error','workflow_run:'):
            self.assertNotIn(forbidden,text)
        self.assertLess(text.index('id: retention'),text.index('scripts/toolchain.py'))
        self.assertIn("if: github.run_attempt == 1",text)


class RetentionTests(unittest.TestCase):
    def test_actual_fixed_model_is_blocked_not_a_compression_assumption(self):
        model=retention.fixed_model();result=retention.assess(model)
        self.assertEqual(result['status'],'BLOCKED');self.assertFalse(result['execution_authorized'])
        self.assertEqual(result['ocr_prefix_capacity_per_trial'],32*1024*1024)
        self.assertGreaterEqual(len(result['reasons']),8)

    def test_archive_count_and_ceiling_cannot_be_relaxed(self):
        for count,size in [(1,32*1024*1024),(3,32*1024*1024),(2,33*1024*1024)]:
            with self.assertRaises(ValueError):retention.assess(retention.fixed_model(),archive_count=count,archive_bytes=size)

    def test_unknown_maximum_and_single_member_oversize_controls(self):
        model=retention.fixed_model()
        for key,value in list(model.items()):
            if key.endswith('_bytes') and value is None:model[key]=0
        model.update(complete_ocr_stdout_on_overflow=True,all_zip_headers_indexes_bytes=100,largest_member_with_headers_bytes=100)
        # Existing OCR prefix maxima exceed total capacity even if everything
        # else were unrealistically zero; this is a possible cap, not raw minimum.
        self.assertIn('exceeds original total capacity',' '.join(retention.assess(model)['reasons']))
        model['ocr_stdout_prefix_bytes']=1
        finite=retention.assess(model)
        self.assertEqual(finite['status'],'RETENTION_MODEL_ONLY')
        self.assertEqual(finite['conservative_all_trials_bytes'],4*16+100)
        model['largest_member_with_headers_bytes']=33*1024*1024
        self.assertIn('indivisible',' '.join(retention.assess(model)['reasons']))

    def test_lossless_two_archives_every_unknown_partial_file_and_original_bytes(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);source=root/'raw';source.mkdir()
        data={'raw.png':b'PNG'+bytes(range(256))*6,'unknown.tmp':b'partial\x00failure','trace/events.jsonl':b'{"original":true}\n','unicode-\u03b1.bin':b'bytes'}
        for name,value in data.items():p=source/name;p.parent.mkdir(exist_ok=True);p.write_bytes(value)
        before=retention.inventory(source);reports=retention.complete_archives(source,root/'archives')
        self.assertEqual(len(reports),2);actual={}
        for report in reports:
            with zipfile.ZipFile(report['path']) as z:
                for name in z.namelist():
                    if name.startswith('evidence/'):self.assertNotIn(name[9:],actual);actual[name[9:]]=z.read(name)
                index=json.loads(z.read('index.json'));self.assertEqual(index['all_files'],before)
            self.assertLessEqual(report['bytes'],retention.ARCHIVE_BYTES)
        self.assertEqual(actual,data);self.assertEqual(before,retention.inventory(source))

    def test_oversize_data_or_index_publishes_nothing_and_preserves_source(self):
        for cap,files in [(200,{'large':b'x'*1000}),(900,{'a':b'a','b':b'b','c':b'c'})]:
            temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);source=root/'raw';source.mkdir()
            for name,data in files.items():(source/name).write_bytes(data)
            before=retention.inventory(source)
            with self.assertRaises(ValueError):retention.complete_archives(source,root/'archives',archive_bytes=cap)
            self.assertFalse((root/'archives').exists());self.assertEqual(before,retention.inventory(source))

    def test_modified_evidence_during_packaging_is_not_published(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);source=root/'raw';source.mkdir();(source/'a').write_bytes(b'a')
        original=retention.inventory;calls=0
        def changed(path):
            nonlocal calls
            calls+=1
            if calls==2:(source/'a').write_bytes(b'changed')
            return original(path)
        with patch.object(retention,'inventory',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'changed'):retention.complete_archives(source,root/'archives')
        self.assertFalse((root/'archives').exists())

    def test_symlink_existing_output_and_raised_cap_rejected(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name);source=root/'raw';source.mkdir();(source/'a').write_bytes(b'a')
        (root/'existing').mkdir()
        with self.assertRaises(ValueError):retention.complete_archives(source,root/'existing')
        with self.assertRaises(ValueError):retention.complete_archives(source,root/'new',archive_bytes=retention.ARCHIVE_BYTES+1)
        (source/'link').symlink_to(source/'a')
        with self.assertRaisesRegex(ValueError,'symlink'):retention.complete_archives(source,root/'new')


class WindowsAdapterTests(unittest.TestCase):
    def test_capture_birth_handles_membership_id_and_pid_reuse(self):
        class Kernel:
            def __init__(self):self.next_handle=100;self.birth=2**63+17;self.member=1;self.pid=99;self.closed=[]
            def OpenProcess(self,access,inherit,pid):self.next_handle+=1;return self.next_handle
            def GetProcessId(self,h):return self.pid
            def IsProcessInJob(self,h,job,member):C.cast(member,C.POINTER(C.c_int))[0]=self.member;return 1
            def GetProcessTimes(self,h,creation,*rest):C.cast(creation,C.POINTER(C.c_uint64))[0]=self.birth;return 1
            def CloseHandle(self,h):self.closed.append(h);return 1
        owner=study.WindowsOwner.__new__(study.WindowsOwner);owner.kernel=Kernel();owner.job=7;owner.handles={}
        first=owner.capture(99);again=owner.capture(99)
        self.assertEqual(first,again);self.assertEqual(first['creation_filetime'],2**63+17)
        owner.kernel.birth+=1;second=owner.capture(99);self.assertNotEqual(first['handle_value'],second['handle_value'])
        self.assertEqual(len(owner.handles),2)
        owner.kernel.member=0
        with self.assertRaisesRegex(RuntimeError,'outside'):owner.capture(99)
        owner.kernel.member=1;owner.kernel.pid=100
        with self.assertRaisesRegex(RuntimeError,'mismatch'):owner.capture(99)
        self.assertEqual(len(owner.handles),2);self.assertEqual(len(owner.kernel.closed),3)

    def test_basic_accounting_and_nested_list_offsets_and_partial_query_reject(self):
        class Kernel:
            mismatch=False
            def QueryInformationJobObject(self,job,kind,data,size,returned):
                if kind==1:
                    C.c_uint32.from_buffer(data,32).value=999 # PageFaults, not TotalProcesses.
                    for offset,value in [(36,7),(40,1),(44,6)]:C.c_uint32.from_buffer(data,offset).value=value
                else:
                    C.c_uint32.from_buffer(data,0).value=2 if self.mismatch else 1
                    C.c_uint32.from_buffer(data,4).value=1;C.c_uint64.from_buffer(data,8).value=99
                return 1
        owner=study.WindowsOwner.__new__(study.WindowsOwner);owner.kernel=Kernel();owner.job=7;owner.baseline=99;owner.queries=[]
        owner.baseline_identity=dict(pid=99,creation_filetime=123,handle_value=456,member_of_outer_job=True)
        owner.capture=lambda pid:owner.baseline_identity.copy();owner.completion_records=lambda:[]
        row=owner.query('actual buffers');self.assertEqual(row['total_processes'],7);self.assertEqual(row['terminated_processes'],6)
        self.assertTrue(owner.baseline_only(row));owner.kernel.mismatch=True
        with self.assertRaisesRegex(RuntimeError,'disagreement'):owner.query('incomplete')
        self.assertFalse(owner.queries[-1]['verified'])

    def test_wrong_baseline_birth_or_missing_controller_rejected(self):
        owner=study.WindowsOwner.__new__(study.WindowsOwner);owner.baseline=99
        for row in [dict(verified=True,active_processes=0,process_ids=[]),dict(verified=True,active_processes=1,process_ids=[100]),dict(verified=False,active_processes=1,process_ids=[99])]:
            self.assertFalse(owner.baseline_only(row))

    def test_safety_cleanup_handles_only_owned_births_and_never_controller(self):
        class Kernel:
            def __init__(self):self.alive={10,20};self.killed=[]
            def WaitForSingleObject(self,h,msec):return 258 if h in self.alive else 0
            def TerminateProcess(self,h,code):self.killed.append(h);self.alive.remove(h);return 1
        owner=study.WindowsOwner.__new__(study.WindowsOwner);owner.kernel=Kernel();owner.baseline=99;owner.handles={(99,1):10,(100,2):20}
        owner.query=lambda _:dict(verified=True,active_processes=1,process_ids=[99])
        times=iter([0.,.1,.2,.3]);result=owner.safety_cleanup(clock=lambda:next(times))
        self.assertTrue(result['passed']);self.assertEqual(owner.kernel.killed,[20]);self.assertEqual(result['terminated'][0]['creation_filetime'],2)

    def test_late_or_unknown_safety_cleanup_never_qualifies(self):
        owner=study.WindowsOwner.__new__(study.WindowsOwner);owner.baseline=99;owner.handles={}
        owner.query=lambda _:dict(verified=True,active_processes=1,process_ids=[99])
        times=iter([0.,6.,6.]);self.assertFalse(owner.safety_cleanup(clock=lambda:next(times))['passed'])
        def unknown(_):raise RuntimeError('ownership unknown')
        owner.query=unknown;self.assertFalse(owner.safety_cleanup(clock=lambda:0.)['passed'])


if __name__=='__main__':unittest.main()
