#!/usr/bin/env python3
"""Pure JSON/arithmetic and fake-process controls. Never start a native/helper process."""
import copy
import io
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import acquire_fov_math_reference as acquisition
import fov_math_reference as reference

ROOT=Path(__file__).resolve().parents[1]
PAYLOAD=json.loads((ROOT/'tools/fov_math_reference/cases.json').read_text())
CASES_SHA=reference.sha((ROOT/'tools/fov_math_reference/cases.json').read_bytes())
PROGRAM_SHA=acquisition.digest(ROOT/'tools/fov_math_reference/reference.gd')


def declared_records():
    precision=dict(single=True,double=False,scalar64=16777217.,vector_component=16777216.,packed32=16777216.,packed64=16777217.,
                   scalar64_le=reference.bits64(16777217.),vector64_le=reference.bits64(16777216.),
                   packed32_le=struct.pack('<f',16777216.).hex(),packed64_le=reference.bits64(16777217.))
    rows=[dict(kind='header',schema=1,engine=dict(major=4,minor=7,patch=2,hash='ed1daf0bf'),
               cases_sha256=CASES_SHA,program_sha256=PROGRAM_SHA,precision=precision)]
    for case in PAYLOAD['cases']:
        values,predicates=reference.model(case,True)
        rows.append(dict(kind='case',id=case['id'],input_sha256=case['input_sha256'],values=values,
                         bits64=reference.bit_tree(values),predicates=predicates))
    rows.append(dict(kind='done',count=len(PAYLOAD['cases']),cases_sha256=CASES_SHA))
    return rows


def encoded(rows):
    return b'\n'.join((reference.PREFIX+json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False)).encode() for r in rows)+b'\n'


def declared_binary_records():
    payload=json.loads((ROOT/'tools/fov_math_reference'/reference.BINARY_CASES_NAME).read_text())
    digest=reference.sha((ROOT/'tools/fov_math_reference'/reference.BINARY_CASES_NAME).read_bytes())
    rows=declared_records();rows[0].update(schema=2,cases_sha256=digest,input_codec=reference.INPUT_CODEC,
                                        canonical_cases_sha256=reference.CANONICAL_CASES_SHA256)
    for row,case in zip(rows[1:-1],payload['cases']):
        row.update(ordinal=case['ordinal'],transport_sha256=case['transport_sha256'],decoded_input64_le=copy.deepcopy(case['input64_le']))
    rows[-1]['cases_sha256']=digest
    return rows


class CorpusAndSchemaControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=declared_records();cls.raw=encoded(cls.rows)

    def parse(self,rows):
        return reference.parse_output(encoded(rows),PAYLOAD,cases_sha256=CASES_SHA,program_sha256=PROGRAM_SHA)

    def test_corpus_rebuilds_exactly_and_preserves_original_fixture(self):
        self.assertEqual(reference.generate(ROOT),PAYLOAD)
        fixture=ROOT/'game/tests/fixtures/bot_objective_timeout.jsonl'
        self.assertEqual(reference.sha(fixture.read_bytes()),PAYLOAD['source_fixture_sha256'])
        self.assertEqual(len(PAYLOAD['cases']),588)
        self.assertEqual(len({r['id'] for r in PAYLOAD['cases']}),588)
        self.assertEqual(sum(r['group']=='captured' for r in PAYLOAD['cases']),151)
        self.assertEqual([r['enemy_id'] for r in PAYLOAD['cases'] if r['group']=='defuse'],[8,9,10])
        self.assertEqual(sum(r['group']=='cutoff32' for r in PAYLOAD['cases']),263)
        self.assertEqual(sum(r['group']=='seeded' for r in PAYLOAD['cases']),128)
        self.assertEqual(sum(r['group']=='recent' for r in PAYLOAD['cases']),14)

    def test_declared_output_schema_and_comparison_never_promote_native_parity(self):
        result=self.parse(self.rows)
        self.assertTrue(result['reference_capture_schema_valid'])
        self.assertEqual(result['broader_cutoff_parity'],'UNRESOLVED')
        self.assertFalse(result['visibility_gameplay_physical_acceptance'])
        self.assertTrue(all(r['transfer']=='UNRESOLVED_FOR_UNMEASURED_INPUTS' for r in result['comparisons']))

    def test_source_clear_cases_and_recent_boundary_are_separate(self):
        cases={r['id']:r for r in PAYLOAD['cases']}
        self.assertTrue(reference.model(cases['captured/122/6/2'])[1]['geometric'])
        self.assertFalse(reference.model(cases['captured/122/6/2/yaw-zero-synthetic'])[1]['geometric'])
        for eid in (8,9,10):self.assertFalse(reference.model(cases[f'defuse/6/{eid}'])[1]['geometric'])
        for case in PAYLOAD['cases']:
            if case['group']=='recent':
                pred=reference.model(case)[1]
                self.assertFalse(pred['geometric'])
                self.assertEqual(pred['recent_attacker'],case['elapsed']<1.2 and case['meta']['specific'])

    def test_input_mutations_reject(self):
        changes=[lambda p:p['cases'].append(copy.deepcopy(p['cases'][0])),
                 lambda p:p['cases'][0].update(input_sha256='0'*64),
                 lambda p:p['cases'][0]['actor_position'].__setitem__(0,float('nan')),
                 lambda p:p['cases'][0].update(yaw=True),lambda p:p.update(schema=True),
                 lambda p:p['cases'][0].update(id=[]),lambda p:p['cases'][0].update(enemy_id=0),
                 lambda p:p['cases'][0].update(extra='not source'),lambda p:p.update(engine='other'),
                 lambda p:p['cases'][0].update(elapsed=1e308,damaged_at=-1e308)]
        for change in changes:
            data=copy.deepcopy(PAYLOAD);change(data)
            with self.subTest(change=change),self.assertRaises(ValueError):reference.validate_cases(data)

    def test_output_identity_count_order_and_provenance_mutations_reject(self):
        changes=[lambda r:r.pop(),lambda r:r.pop(1),lambda r:r.insert(1,copy.deepcopy(r[1])),
                 lambda r:r.__setitem__(slice(1,3),[r[2],r[1]]),lambda r:r[1].update(input_sha256='0'*64),
                 lambda r:r[0].update(cases_sha256='0'*64),lambda r:r[0].update(program_sha256='0'*64),
                 lambda r:r[0]['engine'].update(patch=1),lambda r:r[0]['engine'].update(hash='ed1daf0bfINVALID'),
                 lambda r:r[-1].update(count=True),lambda r:r[1].update(extra=1)]
        for change in changes:
            rows=copy.deepcopy(self.rows);change(rows)
            with self.subTest(change=change),self.assertRaises(ValueError):self.parse(rows)

    def test_numeric_bits_shortening_and_boolean_mutations_reject(self):
        changes=[lambda r:r[1]['values'].update(dot=.1234),lambda r:r[1]['bits64'].update(dot='0'*16),
                 lambda r:r[1]['bits64'].update(toward=['0'*16]),lambda r:r[1]['predicates'].update(geometric=not r[1]['predicates']['geometric']),
                 lambda r:r[1]['predicates'].update(in_fov=1),lambda r:r[0]['precision'].update(vector_component=16777217.),
                 lambda r:r[0]['precision'].update(packed32_le='bad'),lambda r:r[1]['values'].update(distance=-1.)]
        for change in changes:
            rows=copy.deepcopy(self.rows);change(rows)
            with self.subTest(change=change),self.assertRaises(ValueError):self.parse(rows)
        with self.assertRaises(ValueError):reference.parse_output(self.raw.replace(b'"dot":',b'"dot":NaN,"duplicate":',1),PAYLOAD,cases_sha256=CASES_SHA,program_sha256=PROGRAM_SHA)

    def test_bad_framing_duplicate_keys_and_unknown_log_lines_reject(self):
        for raw in (self.raw+b'WARNING: retained native warning\n',b'\xff'+self.raw,
                    self.raw.replace(b'"schema":1',b'"schema":1,"schema":1',1)):
            with self.subTest(raw=raw[:20]),self.assertRaises((ValueError,UnicodeError)):
                reference.parse_output(raw,PAYLOAD,cases_sha256=CASES_SHA,program_sha256=PROGRAM_SHA)

    def test_coordinated_corruption_cannot_bypass_required_analytical_controls(self):
        for identity,field,value in [('axis/front','dot',-1.),('axis/zero','dot',1.),('axis/back','toward',[0.,0.,-1.]),('axis/comparison/2','dot',.1)]:
            rows=copy.deepcopy(self.rows);row=next(r for r in rows if r.get('id')==identity)
            row['values'][field]=value;row['bits64']=reference.bit_tree(row['values'])
            geometric=row['values']['dot']>row['values']['threshold'];row['predicates'].update(geometric=geometric,in_fov=geometric)
            row['predicates']['stage']='requires_visibility' if geometric else 'fov'
            with self.subTest(identity=identity,field=field),self.assertRaises(ValueError):self.parse(rows)

    def test_signed_zero_is_retained_in_binary_companion(self):
        rows=copy.deepcopy(self.rows)
        row=next(r for r in rows if r.get('id')=='angle/1')
        self.assertEqual(row['bits64']['yaw'],'0000000000000080')
        row['values']['yaw']=0.0 # Native JSON may erase negative zero; binary remains authoritative.
        self.parse(rows)

    def test_isolated_project_and_script_have_no_game_or_scene_loads(self):
        project=(ROOT/'tools/fov_math_reference/project.godot').read_text()
        script=(ROOT/'tools/fov_math_reference/reference.gd').read_text()
        self.assertNotIn('autoload',project);self.assertNotIn('run/main_scene',project)
        for forbidden in ('preload(', 'load(', 'res://scripts/', 'get_world_3d', 'can_see(', 'randomize('):self.assertNotIn(forbidden,script)
        self.assertTrue(script.startswith('extends SceneTree'))
        self.assertIn('JSON.stringify(value, "", true, true)',script)
        self.assertIn('delta.normalized()',script);self.assertIn('facing.dot(toward)',script)


class FakeClock:
    def __init__(self):self.now=100.
    def __call__(self):return self.now
    def sleep(self,seconds):self.now+=seconds


class FakeKernel:
    supervisor=50
    def __init__(self,*,survivor=False,observer_error=False):
        self.supervisor_birth=1
        self.table={100:dict(pid=100,state='R',ppid=50,pgrp=100,session=100,start_ticks=123)}
        if survivor:self.table[101]=dict(pid=101,state='R',ppid=50,pgrp=777,session=777,start_ticks=124)
        self.survivor=survivor;self.observer_error=observer_error;self.sent=[];self.closed=[];self.enabled=False
    def enable_subreaper(self):self.enabled=True
    def identity(self,pid):
        if pid==self.supervisor:
            return dict(pid=pid,state='R',ppid=49,pgrp=50,session=50,start_ticks=self.supervisor_birth)
        return copy.deepcopy(self.table.get(pid))
    def children(self,pid):
        if self.observer_error:raise OSError('declared observer error')
        return [p for p,r in self.table.items() if r['ppid']==pid]
    def open_pid(self,pid):return pid
    def close_pid(self,fd):self.closed.append(fd)
    def send(self,fd,signum):
        self.sent.append((fd,signum))
        if not(self.survivor and fd==101):self.table.pop(fd,None)
    def reap(self,pid):self.table.pop(pid,None);return(pid,0)
    def affinity(self,pid):return[0,1]
    def executable(self,pid):return str(acquisition.ENGINE.resolve())


class FakeProcess:
    pid=100
    def __init__(self,clock,kernel,finish=.1,code=0):
        self.clock,self.kernel,self.finish,self.code=clock,kernel,clock()+finish,code
        self.returncode=None;self.stdout=io.BytesIO();self.stderr=io.BytesIO();self.killed=False
    def poll(self):
        if 100 not in self.kernel.table:
            if self.returncode is None:self.returncode=-9
        elif self.clock()>=self.finish:
            self.kernel.table.pop(100);self.returncode=self.code
        return self.returncode
    def kill(self):self.killed=True;self.kernel.table.pop(100,None);self.returncode=-9
    def wait(self,timeout):return self.poll()


class FakeStreams:
    def __init__(self,clock,out,raw,*,overflow=False,stderr=b''):
        self.clock,self.overflow=clock,overflow;self.counts={'stdout':len(raw),'stderr':len(stderr)};self.retained=dict(self.counts)
        (out/'stdout.log').write_bytes(raw);(out/'stderr.log').write_bytes(stderr);self.done=False;self.closed=False;self.eof={'stdout':False,'stderr':False}
    def read(self,seconds):self.clock.sleep(min(seconds,.01));self.done=True;self.eof=dict.fromkeys(self.eof,True);return self.overflow
    def pending(self):return not self.done
    def close(self):self.closed=True


class SupervisorControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.raw=encoded(declared_binary_records())

    def trial(self,*,finish=.1,code=0,survivor=False,overflow=False,stderr=b'',observer_error=False,bad_affinity=False,preflight_error=False):
        clock=FakeClock();kernel=FakeKernel(survivor=survivor,observer_error=observer_error);calls=[]
        temporary=tempfile.TemporaryDirectory();out=Path(temporary.name)/'owned'
        process=FakeProcess(clock,kernel,finish,code)
        if bad_affinity:kernel.affinity=lambda pid:[4]
        if preflight_error:
            def unavailable():raise RuntimeError('owned process child-list interface unavailable for existing task')
            kernel.enable_subreaper=unavailable
        def spawn(command,**options):calls.append((command,options));return process
        binding=dict(commit='a'*40,files={p:acquisition.digest(ROOT/p) for p in acquisition.COMPONENT})
        original=acquisition.digest
        def digest(path):return acquisition.ENGINE_SHA256 if Path(path)==acquisition.ENGINE else original(path)
        with patch.object(acquisition,'source_binding',return_value=binding),patch.object(acquisition,'digest',side_effect=digest),patch.object(acquisition.os,'sched_getaffinity',return_value={4}):
            report=acquisition.acquire(out,'a'*40,clock=clock,sleep=clock.sleep,process_factory=spawn,kernel=kernel,
                 stream_factory=lambda proc,path:FakeStreams(clock,path,self.raw,overflow=overflow,stderr=stderr))
        return temporary,out,report,calls,kernel,process,clock

    def test_one_isolated_pinned_invocation_and_complete_success(self):
        tmp,out,report,calls,kernel,process,clock=self.trial()
        try:
            self.assertTrue(report['passed']);self.assertEqual(report['native_invocations'],1);self.assertEqual(len(calls),1)
            command,options=calls[0];self.assertEqual(command[0],str(acquisition.ENGINE));self.assertIn('--headless',command)
            self.assertEqual(command[command.index('--path')+1],str(out/'project'));self.assertTrue(options['start_new_session'])
            self.assertEqual(options['env'].get('HOME'),__import__('os').environ.get('HOME'))
            self.assertTrue(all(str(out) in v for v in report['isolated_user_paths'].values()))
            self.assertEqual(report['whole_seconds'],60);self.assertEqual(report['cleanup_seconds'],5)
            self.assertEqual(report['cleanup']['survivors'],[]);self.assertFalse(report['cleanup']['signals'])
            self.assertTrue(kernel.enabled);self.assertTrue(process.stdout.closed and process.stderr.closed)
        finally:tmp.cleanup()

    def test_late_observation_and_timeout_fail_then_cleanup_owned_root(self):
        for finish in (60.,61.):
            tmp,out,report,calls,kernel,process,clock=self.trial(finish=finish)
            try:
                self.assertFalse(report['passed']);self.assertEqual(len(calls),1);self.assertFalse(kernel.table)
                self.assertLessEqual(clock(),165.000001)
            finally:tmp.cleanup()

    def test_stream_cap_stderr_and_nonzero_exit_fail_without_retry(self):
        for settings in (dict(overflow=True),dict(stderr=b'ERROR: retained\n'),dict(code=2)):
            tmp,out,report,calls,kernel,process,clock=self.trial(**settings)
            try:self.assertFalse(report['passed']);self.assertEqual(len(calls),1);self.assertFalse(kernel.table)
            finally:tmp.cleanup()

    def test_surviving_escaped_owned_child_fails_within_cleanup_budget(self):
        tmp,out,report,calls,kernel,process,clock=self.trial(survivor=True)
        try:
            self.assertFalse(report['passed']);self.assertTrue(report['cleanup']['survivors'])
            self.assertTrue(any(signal==9 for _,signal in kernel.sent));self.assertLessEqual(clock(),105.2)
        finally:tmp.cleanup()

    def test_observer_error_never_passes_and_still_stops_owned_popen_root(self):
        tmp,out,report,calls,kernel,process,clock=self.trial(observer_error=True)
        try:
            self.assertFalse(report['passed']);self.assertTrue(process.killed);self.assertFalse(kernel.table)
            self.assertIn('cleanup_error',report);self.assertTrue(report['failure_log_coverage_complete'])
        finally:tmp.cleanup()

    def test_output_reuse_relative_path_and_wrong_supervisor_cpu_do_not_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            for path in (Path(tmp),Path('relative-output')):
                with patch.object(acquisition.os,'sched_getaffinity',return_value={4}),self.assertRaises(RuntimeError):
                    acquisition.acquire(path,'a'*40,process_factory=lambda *a,**k:self.fail('unexpected process'))
            with patch.object(acquisition.os,'sched_getaffinity',return_value={0}),self.assertRaises(RuntimeError):
                acquisition.acquire(Path(tmp)/'absent','a'*40,process_factory=lambda *a,**k:self.fail('unexpected process'))

    def test_tree_does_not_signal_unrelated_process_and_reaps_owned_zombie(self):
        kernel=FakeKernel();kernel.table[999]=dict(pid=999,state='R',ppid=999,pgrp=999,session=999,start_ticks=999)
        kernel.table[101]=dict(pid=101,state='Z',ppid=50,pgrp=777,session=777,start_ticks=124)
        tree=acquisition.OwnedTree(kernel,100);tree.observe();tree.reap_descendants();tree.signal_all(15)
        self.assertIn(999,kernel.table);self.assertNotIn(101,kernel.table);self.assertTrue(all(pid!=999 for pid,_ in kernel.sent));tree.close()

    def test_early_root_readback_failure_still_retains_and_drains_native_pipes(self):
        tmp,out,report,calls,kernel,process,clock=self.trial(bad_affinity=True)
        try:
            self.assertFalse(report['passed']);self.assertEqual(len(calls),1);self.assertNotIn('math',report)
            self.assertEqual((out/'stdout.log').read_bytes(),self.raw)
            self.assertTrue(report['failure_log_coverage_complete']);self.assertTrue(all(report['stream_eof'].values()))
            self.assertFalse(kernel.table);self.assertTrue(process.stdout.closed and process.stderr.closed)
        finally:tmp.cleanup()

    def test_cleanup_drains_pending_failure_tail_in_same_original_five_seconds(self):
        clock=FakeClock();kernel=FakeKernel();process=FakeProcess(clock,kernel)
        tree=acquisition.OwnedTree(kernel,100);tree.observe()
        class Tail:
            def __init__(self):self.calls=0;self.output=b'';self.eof=False
            def pending(self):return not self.eof
            def read(self,seconds):
                clock.sleep(min(seconds,.01));self.calls+=1
                self.output+=b'prefix' if self.calls==1 else b'tail'
                self.eof=self.calls==2
                return False
        streams=Tail();deadline=clock()+5
        result=acquisition.cleanup(process,tree,deadline,streams=streams,clock=clock,sleep=clock.sleep)
        self.assertTrue(result['passed']);self.assertEqual(streams.output,b'prefixtail');self.assertTrue(streams.eof)
        self.assertLessEqual(clock(),deadline);self.assertFalse(kernel.table);tree.close()

    def test_source_git_children_receive_only_remaining_whole_deadline(self):
        clock=FakeClock();timeouts=[]
        def output(command,**options):
            timeouts.append(options['timeout']);clock.sleep(.1)
            return 'a'*40 if options.get('text') else b''
        def run(command,**options):
            timeouts.append(options['timeout']);clock.sleep(.1);return SimpleNamespace(returncode=0)
        with patch.object(acquisition.subprocess,'check_output',side_effect=output),patch.object(acquisition.subprocess,'run',side_effect=run),patch.object(acquisition,'digest',return_value='b'*64):
            binding=acquisition.source_binding('a'*40,deadline=101.,clock=clock)
        self.assertEqual(binding['commit'],'a'*40);self.assertEqual(len(timeouts),4)
        self.assertTrue(all(0<t<=1 for t in timeouts));self.assertEqual(timeouts,sorted(timeouts,reverse=True))
        clock.now=101.
        with patch.object(acquisition.subprocess,'check_output',side_effect=AssertionError('must not spawn late')),self.assertRaises(RuntimeError):
            acquisition.source_binding('a'*40,deadline=101.,clock=clock)

    def test_real_stream_collector_caps_retained_bytes_and_closes_all_streams(self):
        class Pipe(io.BytesIO):
            def fileno(self):return 10 if self.name=='stdout' else 11
        class Selector:
            def __init__(self):self.items={};self.closed=False
            def register(self,obj,events,name):self.items[obj]=SimpleNamespace(fileobj=obj,data=name)
            def select(self,timeout):return [(key,1) for key in self.items.values()]
            def unregister(self,obj):self.items.pop(obj)
            def get_map(self):return self.items
            def close(self):self.closed=True
        process=SimpleNamespace(stdout=Pipe(),stderr=Pipe());process.stdout.name='stdout';process.stderr.name='stderr'
        selector=Selector();chunks={10:[b'0123456789abcdef',b''],11:[b'error!',b'']}
        with tempfile.TemporaryDirectory() as tmp,patch.object(acquisition.selectors,'DefaultSelector',return_value=selector),patch.object(acquisition.os,'set_blocking'),patch.object(acquisition.os,'read',side_effect=lambda fd,size:chunks[fd].pop(0)),patch.object(acquisition,'STREAM_LIMITS',{'stdout':8,'stderr':4}):
            streams=acquisition.Streams(process,Path(tmp));self.assertTrue(streams.read(0));self.assertEqual(streams.counts,{'stdout':16,'stderr':6})
            self.assertEqual(streams.retained,{'stdout':8,'stderr':4});self.assertFalse(streams.read(0));self.assertFalse(streams.pending())
            streams.close();self.assertEqual((Path(tmp)/'stdout.log').read_bytes(),b'01234567');self.assertEqual((Path(tmp)/'stderr.log').read_bytes(),b'erro')
            self.assertTrue(process.stdout.closed and process.stderr.closed and selector.closed)

    def test_birth_identity_change_fails_without_signaling_reused_pid(self):
        kernel=FakeKernel();original=kernel.open_pid
        def changed(pid):
            result=original(pid);kernel.table[pid]['start_ticks']+=1;return result
        kernel.open_pid=changed;tree=acquisition.OwnedTree(kernel,100)
        with self.assertRaisesRegex(RuntimeError,'birth identity'):tree.observe()
        self.assertFalse(tree.seen);self.assertFalse(kernel.sent)

    def test_unavailable_prelaunch_observer_does_not_create_native_process(self):
        tmp,out,report,calls,kernel,process,clock=self.trial(preflight_error=True)
        try:
            self.assertFalse(report['passed']);self.assertEqual(calls,[])
            self.assertEqual(report['native_invocations'],0);self.assertNotIn('cleanup',report)
            self.assertIn('child-list interface unavailable',report['error'])
            self.assertNotIn('spawned_pid',report);self.assertFalse(process.killed)
        finally:tmp.cleanup()

    def test_intended_root_pid_is_retained_but_does_not_replace_failed_readback(self):
        tmp,out,report,calls,kernel,process,clock=self.trial(bad_affinity=True)
        try:
            self.assertEqual(report['spawned_pid'],100);self.assertFalse(report['passed'])
            self.assertNotIn('math',report);self.assertTrue(report['failure_log_coverage_complete'])
        finally:tmp.cleanup()

    def test_direct_root_binding_checks_parent_and_birth_before_ownership(self):
        for changed in ('parent','birth'):
            kernel=FakeKernel();tree=acquisition.OwnedTree(kernel,100)
            if changed=='parent':kernel.table[100]['ppid']=999
            else:
                def reused(pid):kernel.table[pid]['start_ticks']+=1;return pid
                kernel.open_pid=reused
            with self.assertRaisesRegex(RuntimeError,'parent|birth'):tree.bind_root()
            self.assertFalse(tree.seen);self.assertFalse(kernel.sent)
            if changed=='birth':self.assertEqual(kernel.closed,[100])

    def test_live_popen_root_cannot_vanish_with_empty_discovery(self):
        clock=FakeClock();kernel=FakeKernel();kernel.children=lambda pid:[]
        process=FakeProcess(clock,kernel);tree=acquisition.OwnedTree(kernel,100)
        result=acquisition.cleanup(process,tree,clock()+5,clock=clock,sleep=clock.sleep)
        self.assertFalse(result['passed']);self.assertTrue(process.killed)
        self.assertTrue(result['root_popen_waited']);self.assertFalse(result['root_birth_bound'])
        self.assertEqual(result['root_exit_code'],-9);self.assertTrue(result['signals'])

    def test_bound_exited_popen_root_has_explicit_wait_status(self):
        clock=FakeClock();kernel=FakeKernel();process=FakeProcess(clock,kernel)
        tree=acquisition.OwnedTree(kernel,100);tree.bind_root();clock.sleep(.2)
        result=acquisition.cleanup(process,tree,clock()+5,clock=clock,sleep=clock.sleep)
        self.assertTrue(result['passed']);self.assertTrue(result['root_birth_bound'])
        self.assertTrue(result['root_popen_waited']);self.assertEqual(result['root_exit_code'],0)
        self.assertFalse(result['signals']);tree.close()


class ProcInterfaceControls(unittest.TestCase):
    def fixture(self):
        tmp=tempfile.TemporaryDirectory();root=Path(tmp.name);parent=root/'50';task=parent/'task'/'50'
        task.mkdir(parents=True)
        def mapped(value):
            p=Path(value)
            return root.joinpath(*p.parts[2:]) if p.is_absolute() and p.parts[1:2]==('proc',) else p
        return tmp,parent,task,mapped

    def test_existing_task_missing_interface_and_existing_parent_missing_tasks_fail(self):
        tmp,parent,task,mapped=self.fixture()
        try:
            with patch.object(acquisition,'Path',side_effect=mapped):
                with self.assertRaisesRegex(RuntimeError,'existing task'):acquisition.LinuxKernel().children(50)
                task.rmdir()
                with self.assertRaisesRegex(RuntimeError,'empty for existing parent'):acquisition.LinuxKernel().children(50)
                (parent/'task').rmdir()
                with self.assertRaisesRegex(RuntimeError,'existing parent'):acquisition.LinuxKernel().children(50)
                parent.rmdir();self.assertEqual(acquisition.LinuxKernel().children(50),[])
        finally:tmp.cleanup()

    def test_multiple_thread_lists_deduplicate_and_invalid_pid_tokens_fail(self):
        tmp,parent,task,mapped=self.fixture();other=parent/'task'/'51';other.mkdir()
        try:
            (task/'children').write_text('100 101\n');(other/'children').write_text('101 102')
            with patch.object(acquisition,'Path',side_effect=mapped):
                self.assertEqual(acquisition.LinuxKernel().children(50),[100,101,102])
                for token in ('0','-1','abc','1.5','１２３'):
                    (task/'children').write_text(token)
                    with self.subTest(token=token),self.assertRaisesRegex(RuntimeError,'malformed'):acquisition.LinuxKernel().children(50)
                (task/'children').write_text('')
                with patch.object(Path,'read_text',side_effect=PermissionError('denied')):
                    with self.assertRaises(PermissionError):acquisition.LinuxKernel().children(50)
        finally:tmp.cleanup()

    def test_departed_thread_is_distinct_from_missing_children_on_live_thread(self):
        tmp,parent,task,mapped=self.fixture();original=Path.read_text
        def departed(path,*args,**kwargs):
            if path==task/'children':task.rmdir();raise FileNotFoundError('declared thread departure')
            return original(path,*args,**kwargs)
        try:
            with patch.object(acquisition,'Path',side_effect=mapped),patch.object(Path,'read_text',departed):
                self.assertEqual(acquisition.LinuxKernel().children(50),[])
        finally:tmp.cleanup()

    def test_supervisor_preflight_checks_interface_before_subreaper_mutation(self):
        kernel=acquisition.LinuxKernel();kernel.identity=lambda pid:dict(pid=pid)
        kernel.children=lambda pid:(_ for _ in ()).throw(RuntimeError('interface absent'))
        with patch.object(acquisition.ctypes,'CDLL') as libc,self.assertRaisesRegex(RuntimeError,'interface absent'):
            kernel.enable_subreaper()
        libc.assert_not_called()


if __name__=='__main__':unittest.main()
