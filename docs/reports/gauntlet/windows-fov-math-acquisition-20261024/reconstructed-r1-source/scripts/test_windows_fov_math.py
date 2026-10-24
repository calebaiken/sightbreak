"""Builder pure models only. No Windows API, process, helper or native execution."""
import copy
import io
import json
from pathlib import Path
import random
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import windows_fov_math as w
from test_fov_math_reference import declared_binary_records, encoded

PAYLOAD=json.loads((w.ROOT/w.PROJECT/w.reference.BINARY_CASES_NAME).read_bytes())
RAW=encoded(declared_binary_records())


class Clock:
    def __init__(self):self.now=100.
    def __call__(self):return self.now
    def sleep(self,seconds):self.now+=seconds


class Pipe(io.BytesIO):
    def __init__(self,fd):super().__init__();self.fd=fd
    def fileno(self):return self.fd


class Process:
    def __init__(self,clock,finish=.03,code=0):
        self.clock,self.finish,self.code=clock,clock()+finish,code
        self.pid=200;self._handle=999;self.stdout=Pipe(2);self.stderr=Pipe(3)
        self.killed=False;self.waited=False
    def poll(self):return self.code if self.clock()>=self.finish else None
    def wait(self,timeout):
        if self.poll() is None:raise TimeoutError('source model process still live')
        self.waited=True;return self.code
    def kill(self):self.killed=True;self.finish=self.clock();self.code=1


class Job:
    def __init__(self,clock,process=None):
        self.clock,self.process=clock,process;self.pid=100;self.handles={};self.extra=[];self.dead_extra=0
        self.birth=123456;self.reject_bind=False;self.fail_sample=False;self.calls=0;self.held=[];self.terminated=[];self.closed=False
        self.controller=dict(pid=100,birth=123)
        self.baseline=dict(total=1,active=1,terminated=0,page_faults=0,ids=[100])
    def sample(self):
        self.calls+=1
        if self.fail_sample:raise OSError('query ownership unavailable')
        ids=[100]+([200] if self.process is not None and self.process.poll() is None else [])+list(self.extra)
        return dict(total=2+self.dead_extra+len(self.extra),active=len(ids),terminated=0,page_faults=self.calls,ids=sorted(ids))
    def identity(self):
        exited=self.process.poll() is not None
        return dict(pid=200,birth=self.birth,exited=exited,exit_time=987 if exited else 0,exit_code=self.process.poll() if exited else 259)
    def bind(self,process):
        if self.reject_bind:raise ValueError('root held identity unavailable')
        self.handles[200]=(999,self.birth);return self.identity()
    def root(self,process):
        if 200 not in self.handles or self.handles[200][1]!=self.birth:raise ValueError('held root birth changed')
        return self.identity()
    def hold_unexpected(self,pid):self.held.append(pid);self.handles[pid]=(pid,555);return dict(pid=pid,birth=555,exited=False)
    def terminate(self,pid):
        if pid==100:raise AssertionError('baseline termination forbidden')
        self.terminated.append(pid)
        if pid==200:self.process.kill()
        elif pid in self.extra:self.extra.remove(pid);self.dead_extra+=1
    def close_held(self):self.closed=True


class Streams:
    def __init__(self,process,out,raw=RAW,stderr=b'',*,attach_error=False,no_eof=False,overflow=False):
        self.process=process;self.files={n:(Path(out)/(n+'.log')).open('wb') for n in w.LIMITS}
        self.files['stdout'].write(raw);self.files['stderr'].write(stderr)
        self.eof=dict.fromkeys(w.LIMITS,False);self.overflow=overflow;self.attach_error=attach_error;self.no_eof=no_eof;self.closed=False
    def attach(self,process):
        if self.attach_error:raise OSError('nonblocking attach unavailable')
    def poll(self,deadline,clock):
        if self.process.poll() is not None and not self.no_eof:self.eof=dict.fromkeys(w.LIMITS,True)
        return self.overflow
    def state(self):return dict(eof=self.eof,complete=all(self.eof.values()) and not self.overflow and not self.attach_error)
    def close(self):
        self.closed=True
        for f in self.files.values():f.close()
        self.process.stdout.close();self.process.stderr.close()


class PipeControls(unittest.TestCase):
    def build(self,root,events,*,bad_fd=None):
        process=Process(Clock())
        def nonblock(fd,value):
            self.assertFalse(value)
            if fd==bad_fd:raise OSError('synthetic pipe capability failure')
        def read(fd,size):
            self.assertEqual(size,65536)
            queue=events[fd]
            if not queue:raise BlockingIOError()
            item=queue.pop(0)
            if isinstance(item,BaseException):raise item
            return item
        streams=w.PipeRetention(root,read=read,set_blocking=nonblock)
        return process,streams

    def test_eagain_not_eof_and_eof_requires_empty_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            process,streams=self.build(d,{2:[BlockingIOError(),b'abc',b''],3:[b'']})
            streams.attach(process);streams.poll(101,Clock())
            self.assertFalse(streams.eof['stdout']);self.assertTrue(streams.eof['stderr'])
            streams.poll(101,Clock());self.assertTrue(streams.state()['complete']);self.assertEqual(streams.counts['stdout'],3);streams.close()
            self.assertEqual((Path(d)/'stdout.log').read_bytes(),b'abc')

    def test_generated_exact_cap_and_one_byte_overflow_never_complete(self):
        for cap in (1,17,65536):
            for excess in (0,1):
                with self.subTest(cap=cap,excess=excess),tempfile.TemporaryDirectory() as d,patch.dict(w.LIMITS,stdout=cap,stderr=cap):
                    process,streams=self.build(d,{2:[b'a'*(cap+excess),b''],3:[b'']})
                    streams.attach(process);overflow=streams.poll(101,Clock());state=streams.state();streams.close()
                    self.assertEqual(overflow,bool(excess));self.assertEqual(state['complete'],not excess)
                    self.assertEqual((Path(d)/'stdout.log').read_bytes(),b'a'*cap)
                    self.assertEqual(state['observed_bytes']['stdout'],cap+excess)

    def test_fair_bounded_reads_preserve_both_streams(self):
        with tempfile.TemporaryDirectory() as d:
            events={2:[b'a']*100,3:[b'b',b'']}
            process,streams=self.build(d,events);streams.attach(process);streams.poll(101,Clock())
            self.assertEqual(streams.counts,dict(stdout=4,stderr=1));self.assertEqual(len(events[2]),96);streams.close()

    def test_early_attachment_failure_keeps_sinks_and_unread_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            process,streams=self.build(d,{2:[b'retained',b''],3:[b'not-readable']},bad_fd=3)
            with self.assertRaises(OSError):streams.attach(process)
            streams.poll(101,Clock());state=streams.state();streams.close()
            self.assertEqual((Path(d)/'stdout.log').read_bytes(),b'retained');self.assertFalse(state['complete']);self.assertIn('stderr',state['attachment_errors'])

    def test_deadline_before_read_does_not_claim_eof(self):
        with tempfile.TemporaryDirectory() as d:
            process,streams=self.build(d,{2:[b''],3:[b'']});streams.attach(process)
            with self.assertRaises(ValueError):streams.poll(100,Clock())
            self.assertFalse(streams.state()['complete']);streams.close()


class SupervisorControls(unittest.TestCase):
    def simulate(self,*,finish=.03,code=0,mutate=None,no_eof=False,overflow=False,deadline=101):
        clock=Clock();process=Process(clock,finish,code);job=Job(clock,process)
        if mutate:mutate(job,process)
        with tempfile.TemporaryDirectory() as d:
            streams=Streams(process,d,no_eof=no_eof,overflow=overflow)
            try:return w.supervise(process,job,streams,deadline,clock=clock,sleep=clock.sleep),job,process,clock
            finally:streams.close()

    def test_root_completed_before_first_sample_uses_retained_handle(self):
        result,job,process,clock=self.simulate(finish=-1)
        self.assertEqual(result['exit_code'],0);self.assertEqual(result['audit']['last']['ids'],[100]);self.assertTrue(result['audit']['root']['exited']);self.assertTrue(process.waited)

    def test_generated_normal_completion_has_only_controller_plus_exact_root(self):
        for finish in (0,.001,.02,.1,.5):
            result,job,process,clock=self.simulate(finish=finish)
            self.assertLess(clock(),101);self.assertEqual(result['audit']['last']['total'],2);self.assertTrue(process.waited)
            self.assertTrue(all(set(row['ids'])<={100,200} for row in result['audit']['transitions']))

    def test_page_fault_variations_do_not_exhaust_transition_retention(self):
        result,job,process,clock=self.simulate(finish=.75)
        self.assertGreater(result['audit']['samples'],50);self.assertLessEqual(len(result['audit']['transitions']),2)

    def test_already_exited_unexpected_descendant_detected_from_total(self):
        with self.assertRaisesRegex(ValueError,'unexpected owned'):self.simulate(finish=-1,mutate=lambda j,p:setattr(j,'dead_extra',1))

    def test_active_unexpected_descendant_is_held_before_failure(self):
        clock=Clock();process=Process(clock);job=Job(clock,process);job.extra=[300]
        with tempfile.TemporaryDirectory() as d:
            streams=Streams(process,d)
            with self.assertRaisesRegex(ValueError,'unexpected owned'):w.supervise(process,job,streams,101,clock=clock,sleep=clock.sleep)
            self.assertEqual(job.held,[300]);streams.close()

    def test_root_birth_cannot_change_after_bind(self):
        clock=Clock();process=Process(clock);job=Job(clock,process);job.bind(process);job.birth+=1
        with self.assertRaisesRegex(ValueError,'birth'):job.root(process)

    def test_no_eof_after_exit_and_genuine_live_timeout_fail(self):
        for kwargs in ({'finish':-1,'no_eof':True},{'finish':10}):
            with self.subTest(kwargs=kwargs),self.assertRaisesRegex(ValueError,'deadline'):self.simulate(**kwargs,deadline=100.05)

    def test_stream_overflow_or_ownership_error_never_normal_success(self):
        for kwargs in ({'overflow':True},{'mutate':lambda j,p:setattr(j,'fail_sample',True)},{'mutate':lambda j,p:setattr(j,'reject_bind',True)}):
            with self.subTest(kwargs=kwargs),self.assertRaises((OSError,ValueError)):self.simulate(**kwargs)

    def test_failure_cleanup_reaps_owned_root_and_never_signals_controller(self):
        clock=Clock();process=Process(clock,10);job=Job(clock,process);job.bind(process);job.extra=[300]
        with tempfile.TemporaryDirectory() as d:
            streams=Streams(process,d);streams.attach(process)
            result=w.safety_cleanup(process,job,streams,105,clock=clock,sleep=clock.sleep);streams.close()
        self.assertTrue(result['passed']);self.assertEqual(result['final']['ids'],[100]);self.assertNotIn(100,job.terminated);self.assertIn(300,job.held);self.assertTrue(process.waited)

    def test_failure_cleanup_query_error_preserves_popen_safety_handle_and_fails(self):
        clock=Clock();process=Process(clock,10);job=Job(clock,process);job.fail_sample=True
        with tempfile.TemporaryDirectory() as d:
            streams=Streams(process,d);streams.attach(process)
            result=w.safety_cleanup(process,job,streams,100.05,clock=clock,sleep=clock.sleep);streams.close()
        self.assertFalse(result['passed']);self.assertTrue(process.killed);self.assertTrue(result['errors']);self.assertLessEqual(clock(),100.05)

    def test_cleanup_timeout_does_not_claim_accounted_completion(self):
        clock=Clock();process=Process(clock,10);job=Job(clock,process);job.bind(process)
        job.terminate=lambda pid:None;process.kill=lambda:None
        result=w.safety_cleanup(process,job,None,100.05,clock=clock,sleep=clock.sleep)
        self.assertFalse(result['passed']);self.assertFalse(result['root']['exited'])


class IntegrationControls(unittest.TestCase):
    def trial(self,**kwargs):
        clock=Clock();process=Process(clock,kwargs.pop('finish',.03),kwargs.pop('code',0));job=Job(clock,process)
        mutation=kwargs.pop('mutation',None)
        if mutation:mutation(job,process)
        with tempfile.TemporaryDirectory() as d:
            out=Path(d);target=out/'project';target.mkdir()
            for name in ('reference.gd',w.reference.BINARY_CASES_NAME):
                (target/name).write_bytes((w.ROOT/w.PROJECT/name).read_bytes())
            args=[]
            def spawn(command,**options):
                args.append((command,options))
                if kwargs.get('spawn_error'):raise OSError('CreateProcess synthetic failure')
                return process
            streams=Streams(process,out,raw=kwargs.pop('raw',RAW),stderr=kwargs.pop('stderr',b''),
                            attach_error=kwargs.pop('attach_error',False),no_eof=kwargs.pop('no_eof',False),overflow=kwargs.pop('overflow',False))
            result=w.execute_prepared(out/w.MEMBER,target,out,PAYLOAD,101,clock=clock,sleep=clock.sleep,
                         process_factory=spawn,job_factory=lambda:job,stream_factory=lambda out:streams)
            return result,job,process,args,clock

    def test_source_faithful_generated_positive_integration_and_early_exit(self):
        for finish in (-1,.03):
            result,job,process,args,clock=self.trial(finish=finish)
            self.assertTrue(result['passed'],result);self.assertEqual(result['spawn_attempts'],1);self.assertEqual(len(args),1);self.assertTrue(job.closed)
            command,options=args[0];self.assertEqual(Path(command[0]).name,w.MEMBER);self.assertEqual(options['executable'],command[0]);self.assertEqual(options['bufsize'],0);self.assertEqual(options['creationflags'],0)
            self.assertNotIn('--version',command);self.assertEqual(options['env'].get('HOME'),w.os.environ.get('HOME'));self.assertFalse(result['math']['visibility_gameplay_physical_acceptance'])

    def test_startup_failure_and_setup_error_never_retry_or_lose_failure(self):
        for kwargs in ({'spawn_error':True},{'mutation':lambda j,p:setattr(j,'reject_bind',True)},{'attach_error':True}):
            result,job,process,args,clock=self.trial(**kwargs)
            self.assertFalse(result['passed']);self.assertEqual(len(args),1);self.assertTrue(job.closed)
            if kwargs.get('spawn_error'):self.assertIsNone(result['native_invocations']);self.assertFalse(result['popen_returned'])
            else:self.assertIn('failure_cleanup',result)

    def test_strict_logs_parser_exit_overflow_and_timeout_fail_after_cleanup(self):
        cases=[dict(stderr=b'WARNING x'),dict(raw=RAW+b'WARNING x\n'),dict(raw=RAW[:-32]),dict(code=1),dict(overflow=True),dict(no_eof=True)]
        for kwargs in cases:
            result,job,process,args,clock=self.trial(**kwargs)
            self.assertFalse(result['passed']);self.assertIn('failure_cleanup',result);self.assertTrue(job.closed);self.assertTrue(process.waited)

    def test_final_audit_failure_still_takes_failure_only_cleanup(self):
        def mutation(job,process):
            original=job.sample
            def sample():
                if job.calls>=6:raise OSError('late accounting lost')
                return original()
            job.sample=sample
        result,job,process,args,clock=self.trial(mutation=mutation)
        self.assertFalse(result['passed']);self.assertTrue('failure_cleanup' in result or 'cleanup_error' in result)


class SourceSdkPackageControls(unittest.TestCase):
    def source(self,root):
        (root/'.git').mkdir();(root/'.git/HEAD').write_text('a'*40+'\n')
        files={}
        for name in w.SOURCE_FILES:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(name.encode())
            files[name]=dict(bytes=path.stat().st_size,sha256=w.digest(path))
        manifest=root/'manifest.json';w.write_json(manifest,dict(schema=1,source_commit='a'*40,files=files))
        return manifest,w.digest(manifest)

    def test_materialized_source_binding_and_mutations_ignore_git_status_shortcuts(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);manifest,sha=self.source(root);clock=Clock()
            self.assertEqual(len(w.source_binding(root,manifest,sha,'a'*40,deadline=101,clock=clock)['files']),len(w.SOURCE_FILES))
            path=root/w.SOURCE_FILES[0];path.write_bytes(b'changed actual bytes')
            with self.assertRaisesRegex(ValueError,'materialized'):w.source_binding(root,manifest,sha,'a'*40,deadline=101,clock=clock)

    def test_source_manifest_head_coverage_digest_and_deadline_reject(self):
        for mode in ('head','manifest','coverage','deadline','redirect'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d);manifest,sha=self.source(root);deadline=101
                if mode=='head':(root/'.git/HEAD').write_text('ref: refs/heads/unbound')
                if mode=='manifest':sha='0'*64
                if mode=='coverage':
                    data=json.loads(manifest.read_bytes());data['files'].pop(w.SOURCE_FILES[0]);w.write_json(manifest,data);sha=w.digest(manifest)
                if mode=='deadline':deadline=100
                if mode=='redirect':
                    path=root/w.SOURCE_FILES[0];path.unlink();path.symlink_to(manifest)
                with self.assertRaises(ValueError):w.source_binding(root,manifest,sha,'a'*40,deadline=deadline,clock=Clock())

    def test_public_preflight_blocks_before_sdk_api_or_engine_and_retains_complete_generated_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'checkout';root.mkdir();manifest,sha=self.source(root);out=Path(d)/'failed'
            with patch.object(w,'WindowsJob',side_effect=AssertionError('must not load API')),patch.object(w,'sdk_member',side_effect=AssertionError('must not extract SDK')):
                result=w.collect(out,Path(d)/'absent-sdk.zip',manifest,sha,'a'*40,root=root,clock=Clock())
            self.assertFalse(result['passed']);self.assertEqual(result['native_invocations'],0);self.assertFalse(result['preflight']['execution_admitted']);self.assertTrue(result['evidence_complete'])
            package=w.package(out,Path(d)/'archives');self.assertEqual(len(package['archives']),2)
            self.assertTrue(all(a['bytes']<w.INNER_LIMIT for a in package['archives']))

    def test_pe_gui_source_fixture_and_subsystem_machine_header_negatives(self):
        raw=bytearray(256);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,64);raw[64:68]=b'PE\0\0'
        struct.pack_into('<H',raw,68,0x8664);struct.pack_into('<H',raw,88,0x20b);struct.pack_into('<H',raw,156,2)
        w.pe_gui(raw)
        for offset,value in ((0,0),(64,0),(68,0),(88,0),(156,3)):
            bad=raw[:];bad[offset]=value
            with self.subTest(offset=offset),self.assertRaises(ValueError):w.pe_gui(bad)

    def test_authenticated_generated_sdk_fixture_extracts_only_gui_and_records_measured_member(self):
        raw=bytearray(256);raw[:2]=b'MZ';struct.pack_into('<I',raw,60,64);raw[64:68]=b'PE\0\0'
        struct.pack_into('<H',raw,68,0x8664);struct.pack_into('<H',raw,88,0x20b);struct.pack_into('<H',raw,156,2)
        with tempfile.TemporaryDirectory() as d:
            archive=Path(d)/'sdk.zip'
            with zipfile.ZipFile(archive,'w') as bundle:
                bundle.writestr(w.MEMBER,raw);bundle.writestr('Godot.console.exe',b'never extract')
            with patch.object(w,'SDK_BYTES',archive.stat().st_size),patch.object(w,'SDK_SHA512',w.digest(archive,'sha512')),patch.object(w,'SDK_SHA256',w.digest(archive)):
                path,receipt=w.sdk_member(archive,Path(d)/'runtime',deadline=101,clock=Clock())
            self.assertEqual(path.read_bytes(),raw);self.assertEqual(list(path.parent.iterdir()),[path]);self.assertEqual(receipt['member_sha256'],w.reference.sha(raw))
            with self.assertRaisesRegex(ValueError,'size mismatch'):w.sdk_member(archive,Path(d)/'another',deadline=101,clock=Clock())

    def package_tree(self,root):
        (root/'user').mkdir();(root/'user/godot.log').write_bytes(b'original user log')
        (root/'stdout.log').write_bytes(b'original stream')
        files={p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=w.digest(p)) for p in root.rglob('*') if p.is_file()}
        w.write_json(root/'receipt.json',dict(evidence_complete=True,evidence_files=files,passed=False))

    def test_package_preserves_failed_originals_losslessly_exact_two_and_fixed_partition(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'raw';root.mkdir();self.package_tree(root)
            result=w.package(root,Path(d)/'archives');self.assertTrue(result['complete']);self.assertEqual(len(result['archives']),2)
            self.assertEqual(result['archives'][1]['members'],['user/godot.log'])
            with zipfile.ZipFile(Path(d)/'archives/math-1.zip') as bundle:
                self.assertIn('receipt.json',bundle.namelist());self.assertEqual(bundle.read('stdout.log'),b'original stream')

    def test_incomplete_missing_extra_corrupt_oversize_and_symlink_packages_reject(self):
        for mode in ('incomplete','missing','extra','corrupt','oversize','symlink'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                root=Path(d)/'raw';root.mkdir();self.package_tree(root)
                if mode=='incomplete':
                    receipt=json.loads((root/'receipt.json').read_bytes());receipt['evidence_complete']=False;w.write_json(root/'receipt.json',receipt)
                if mode=='missing':(root/'stdout.log').unlink()
                if mode=='extra':(root/'unexpected.bin').write_bytes(b'x')
                if mode=='corrupt':(root/'stdout.log').write_bytes(b'changed')
                if mode=='oversize':
                    receipt=json.loads((root/'receipt.json').read_bytes());(root/'stdout.log').write_bytes(b'x'*(w.INNER_LIMIT+1));receipt['evidence_files']['stdout.log']=dict(bytes=(root/'stdout.log').stat().st_size,sha256=w.digest(root/'stdout.log'));w.write_json(root/'receipt.json',receipt)
                if mode=='symlink':
                    (root/'stdout.log').unlink();(root/'stdout.log').symlink_to(root/'user/godot.log')
                with self.assertRaises(ValueError):w.package(root,Path(d)/'archives')

    def test_artifact_model_never_turns_finite_prefixes_into_complete_original_admission(self):
        for source_bytes in (0,1,2*w.MIB,20*w.MIB):
            model=w.artifact_preflight(source_bytes)
            self.assertFalse(model['execution_admitted']);self.assertFalse(model['complete_original_proof']);self.assertEqual(model['maximum_archives'],2)
            self.assertEqual(model['retained_prefix_upper_bounds'][0],sum(w.LIMITS.values())+source_bytes+3*w.MIB)

    def test_workflow_is_dedicated_one_attempt_windows_exact_python_no_game_sdk_helper(self):
        source=(w.ROOT/'.github/workflows/windows-fov-math.yml').read_text()
        for wanted in ("python-version: '3.12.10'",'runs-on: windows-2025','github.run_attempt == 1','compression-level: 0'):self.assertIn(wanted,source)
        self.assertEqual(source.count('uses: actions/upload-artifact@'),2)
        for forbidden in ('scripts/toolchain.py','scripts/export.py','--version','gh api','windows-latest','macos-','ubuntu-'):self.assertNotIn(forbidden,source)


if __name__=='__main__':unittest.main()
