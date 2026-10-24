"""Pure controlled finalization/audit models; never Windows API/native/SDK."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import windows_fov_math as w
from test_windows_fov_math import Clock,Process,Job,RAW,PAYLOAD


class Sink:
    def __init__(self,wrapped,name,events,fail_close=False,fail_flush=False):
        self.wrapped,self.name,self.events=wrapped,name,events
        self.fail_close,self.fail_flush=fail_close,fail_flush
    @property
    def closed(self):return self.wrapped.closed
    def write(self,data):return self.wrapped.write(data)
    def flush(self):
        if self.fail_flush:raise OSError('controlled flush failure '+self.name)
        return self.wrapped.flush()
    def close(self):
        self.events.append('sink/'+self.name)
        if self.fail_close:raise OSError('controlled sink close failure '+self.name)
        self.wrapped.close()


class Pipe(io.BytesIO):
    def __init__(self,fd,name,events,fail=False):
        super().__init__();self.fd,self.name,self.events,self.fail=fd,name,events,fail
    def fileno(self):return self.fd
    def close(self):
        self.events.append('pipe/'+self.name)
        if self.fail:raise OSError('controlled pipe close failure '+self.name)
        super().close()


class JobWithActualClosure(Job):
    """Actual production close_held body with pure modeled kernel callbacks."""
    def __init__(self,clock,events,fail_handle=None):
        super().__init__(clock);self.owned_handles=[];self.events=events;self.fail_handle=fail_handle
        outer=self
        class Kernel:
            def CloseHandle(self,handle):
                outer.events.append('handle/'+str(handle))
                if handle==outer.fail_handle:raise OSError('controlled owned handle close failure')
                return 1
        self.k=Kernel()
    @staticmethod
    def ok(value,label):
        if not value:raise OSError(label)
        return value
    def hold_unexpected(self,pid):
        known=pid in self.handles;value=super().hold_unexpected(pid)
        if not known:self.owned_handles.append(pid+1000)
        return value
    def close_held(self):
        self.events.append('job.close_held')
        try:return w.WindowsJob.close_held(self)
        finally:self.closed=True


def run_case(*,sink_fail=(),pipe_fail=(),state_fail=(),query_fail=False,read_fail=False,
             no_eof=False,overflow=False,extra=(),fail_handle=None,flush_fail=False,audit_snapshot_fail=False):
    clock=Clock();events=[];process=Process(clock,.03)
    process.stdout=Pipe(2,'stdout',events,'stdout' in pipe_fail)
    process.stderr=Pipe(3,'stderr',events,'stderr' in pipe_fail)
    job=JobWithActualClosure(clock,events,fail_handle);job.extra=list(extra)
    if query_fail:
        original=job.sample
        def sample():
            if job.calls>=1:raise OSError('controlled query failed after coherent sample')
            return original()
        job.sample=sample
    with tempfile.TemporaryDirectory() as d:
        out=Path(d);target=out/'project';target.mkdir()
        for name in ('reference.gd',w.reference.BINARY_CASES_NAME):(target/name).write_bytes((w.ROOT/w.PROJECT/name).read_bytes())
        remaining={2:bytearray(RAW),3:bytearray()};read_failed=False
        def read(fd,size):
            nonlocal read_failed
            if read_fail and clock()>100 and not read_failed:
                read_failed=True;raise OSError('controlled read failure after first audit')
            if process.poll() is None:raise BlockingIOError()
            if remaining[fd]:
                chunk=bytes(remaining[fd][:size]);del remaining[fd][:size];return chunk
            if no_eof:raise BlockingIOError()
            return b''
        streams=w.PipeRetention(out,read=read,set_blocking=lambda fd,blocking:None)
        for name,file in list(streams.files.items()):streams.files[name]=Sink(file,name,events,name in sink_fail,flush_fail and name=='stdout')
        state_original=streams.state;state_calls=0
        def state():
            nonlocal state_calls
            state_calls+=1
            if state_calls in state_fail:raise OSError('controlled stream state failure '+str(state_calls))
            return state_original()
        streams.state=state
        def spawn(*args,**kwargs):job.process=process;return process
        audit_original=w.Audit
        class SnapshotFailure(audit_original):
            calls=0
            def receipt(self):
                self.calls+=1
                if self.calls==2:raise ValueError('controlled terminal audit snapshot failure')
                return super().receipt()
        try:
            with patch.dict(w.LIMITS,stdout=16 if overflow else 8*w.MIB),patch.object(w,'Audit',SnapshotFailure if audit_snapshot_fail else audit_original):
                result=w.execute_prepared(out/w.MEMBER,target,out,PAYLOAD,101,clock=clock,sleep=clock.sleep,
                    process_factory=spawn,job_factory=lambda:job,stream_factory=lambda output:streams)
            resource_state={name:resource.closed for name,resource in streams.files.items()}
            resource_state.update({name+'_pipe':getattr(process,name).closed for name in w.LIMITS})
            summary=dict(events=list(events),closed=resource_state,job_close_attempted=job.closed,
                         remaining_owned_handles=list(job.owned_handles),final_clock=clock())
            json.dumps(result,allow_nan=False)  # Structured failure must serialize.
            return result,summary
        finally:
            # Pure test hygiene after recorded candidate state; no native handle.
            for resource in streams.files.values():resource.wrapped.close()
            io.BytesIO.close(process.stdout);io.BytesIO.close(process.stderr)


class FinalizationControls(unittest.TestCase):
    def assert_all_attempted(self,summary):
        for operation in ('sink/stdout','sink/stderr','pipe/stdout','pipe/stderr','job.close_held'):
            self.assertIn(operation,summary['events'])
        self.assertTrue(summary['job_close_attempted'])

    def test_ordinary_source_positive_retains_old_result_and_all_close_attempts(self):
        result,summary=run_case()
        self.assertTrue(result['passed'],result);self.assertTrue(result['finalization']['complete']);self.assert_all_attempted(summary)
        self.assertTrue(all(summary['closed'].values()));self.assertIn('finished',result)

    def test_each_sink_failure_cannot_skip_other_sink_pipes_handles_or_structured_return(self):
        for names in (('stdout',),('stderr',),('stdout','stderr')):
            with self.subTest(names=names):
                result,summary=run_case(sink_fail=names)
                self.assertFalse(result['passed']);self.assert_all_attempted(summary);self.assertIn('finished',result);self.assertFalse(result['finalization']['complete'])
                self.assertEqual(len(result['finalization']['stream_resources']['errors']),len(names))
                self.assertTrue(summary['closed']['stdout_pipe']);self.assertTrue(summary['closed']['stderr_pipe'])

    def test_each_pipe_failure_cannot_skip_its_sibling_or_job_finalization(self):
        for names in (('stdout',),('stderr',),('stdout','stderr')):
            with self.subTest(names=names):
                result,summary=run_case(pipe_fail=names)
                self.assertFalse(result['passed']);self.assert_all_attempted(summary);self.assertIn('elapsed',result)
                self.assertTrue(summary['closed']['stdout']);self.assertTrue(summary['closed']['stderr'])

    def test_state_before_after_and_all_failures_still_attempt_all_resources(self):
        for calls in ((2,),(3,),(1,2,3)):
            with self.subTest(calls=calls):
                result,summary=run_case(state_fail=calls)
                self.assertFalse(result['passed']);self.assert_all_attempted(summary);self.assertIn('finished',result)
                self.assertTrue(all(summary['closed'].values()))
                self.assertTrue(any(e['operation'].startswith('stream state/') for e in result['finalization']['errors']))

    def test_actual_owned_handle_closure_attempts_every_handle_and_retains_failed_ones(self):
        for failure in (11,22,33):
            job=w.WindowsJob.__new__(w.WindowsJob);job.owned_handles=[11,22,33];calls=[]
            class Kernel:
                def CloseHandle(self,handle):
                    calls.append(handle)
                    if handle==failure:raise OSError('controlled per-handle failure')
                    return 1
            job.k=Kernel();job.ok=lambda value,label:value
            with self.subTest(failure=failure),self.assertRaises(w.ResourceFinalizationError) as caught:job.close_held()
            self.assertEqual(calls,[11,22,33]);self.assertEqual(job.owned_handles,[failure]);self.assertEqual(len(caught.exception.report['attempts']),3)

    def test_unexpected_child_handle_failure_keeps_audit_and_attempts_distinct_sibling(self):
        result,summary=run_case(extra=(300,301),fail_handle=1300)
        self.assertFalse(result['passed']);self.assert_all_attempted(summary)
        self.assertIn('handle/1300',summary['events']);self.assertIn('handle/1301',summary['events'])
        self.assertEqual(summary['remaining_owned_handles'],[1300]);self.assertFalse(result['finalization']['job_handles']['call_completed'])
        self.assertEqual(result['audit']['last']['ids'],[100,200,300,301])

    def test_actual_retainer_direct_close_is_best_effort_not_first_failure_only(self):
        with tempfile.TemporaryDirectory() as d:
            events=[];retainer=w.PipeRetention(d,read=lambda fd,n:b'',set_blocking=lambda fd,b:None)
            for name,file in list(retainer.files.items()):retainer.files[name]=Sink(file,name,events,True)
            retainer.pipes={name:Pipe(index,name,events) for index,name in enumerate(w.LIMITS,2)}
            try:
                with self.assertRaises(w.ResourceFinalizationError) as caught:retainer.close()
                self.assertEqual(events,['sink/stdout','sink/stderr','pipe/stdout','pipe/stderr']);self.assertEqual(len(caught.exception.report['errors']),2)
            finally:
                for resource in retainer.files.values():resource.wrapped.close()
                for resource in retainer.pipes.values():io.BytesIO.close(resource)

    def test_combined_core_cleanup_state_and_close_failures_remain_structured_fail(self):
        result,summary=run_case(query_fail=True,state_fail=(1,2),sink_fail=('stdout',),pipe_fail=('stderr',))
        self.assertFalse(result['passed']);self.assert_all_attempted(summary);self.assertIn('finished',result)
        self.assertFalse(result['failure_cleanup']['passed']);self.assertGreaterEqual(len(result['finalization']['errors']),4)


class TerminalAuditControls(unittest.TestCase):
    def test_read_and_query_failures_retain_original_coherent_monitor_prefix(self):
        for kwargs in (dict(read_fail=True),dict(query_fail=True)):
            with self.subTest(kwargs=kwargs):
                result,summary=run_case(**kwargs)
                self.assertFalse(result['passed']);self.assertGreaterEqual(result['audit']['samples'],1)
                self.assertEqual(result['audit']['last']['ids'],[100,200]);self.assertEqual(result['audit']['transitions'][0]['total'],2)
                self.assertIn('failure_cleanup',result);self.assertIn('finished',result)

    def test_overflow_and_noeof_late_failure_keep_terminal_monitor_observation(self):
        for kwargs in (dict(overflow=True),dict(no_eof=True)):
            with self.subTest(kwargs=kwargs):
                result,summary=run_case(**kwargs)
                self.assertFalse(result['passed']);self.assertGreater(result['audit']['samples'],1)
                self.assertEqual(result['audit']['last']['ids'],[100]);self.assertTrue(result['audit']['root']['exited'])
                self.assertIn('failure_cleanup',result)

    def test_flush_and_terminal_snapshot_failures_cannot_skip_resource_attempts(self):
        for kwargs in (dict(flush_fail=True),dict(audit_snapshot_fail=True)):
            with self.subTest(kwargs=kwargs):
                result,summary=run_case(**kwargs)
                self.assertFalse(result['passed']);self.assertTrue(summary['job_close_attempted']);self.assertIn('finished',result)
                self.assertTrue(all(summary['closed'].values()))

    def test_audit_receipt_is_primitive_snapshot_not_live_mutable_history(self):
        clock=Clock();process=Process(clock);job=Job(clock,process);job.bind(process);audit=w.Audit(job,process);audit.observe()
        receipt=audit.receipt();audit.events[0]['ids'].append(999);audit.last['bracket_injected']=True
        self.assertEqual(receipt['last']['ids'],[100,200]);self.assertNotIn('bracket_injected',receipt['last'])


class ConservativeCoverageControls(unittest.TestCase):
    def test_stable_no_child_source_positive_remains_complete(self):
        clock=Clock();job=Job(clock,None);result=w.cleanup_unreturned(job,None,105,clock=clock,sleep=clock.sleep)
        self.assertTrue(result['passed']);self.assertTrue(result['identity_coverage_complete']);self.assertEqual(result['cumulative_total_max'],1)

    def test_query_failure_then_clean_sample_cannot_recover_identity_coverage(self):
        clock=Clock();job=Job(clock,None);original=job.sample;calls=0
        def sample():
            nonlocal calls
            calls+=1
            if calls==1:raise OSError('controlled initial query failure')
            return original()
        job.sample=sample;result=w.cleanup_unreturned(job,None,105,clock=clock,sleep=clock.sleep)
        self.assertTrue(result['passed']);self.assertFalse(result['identity_coverage_complete']);self.assertTrue(result['errors'])

    def test_defensive_inconsistent_cumulative_api_return_is_not_source_feasible_claim(self):
        # API robustness only. No source witness or actual1-to2 race is asserted.
        clock=Clock();job=Job(clock,None);original=job.sample;calls=0
        def sample():
            nonlocal calls
            calls+=1;value=original();value['total']=1 if calls==1 else 2;return value
        job.sample=sample;result=w.cleanup_unreturned(job,None,105,clock=clock,sleep=clock.sleep)
        self.assertFalse(result['identity_coverage_complete']);self.assertEqual(result['final']['total'],2);self.assertEqual(result['cumulative_total_max'],2)

    def test_public_gate_and_all_original_workflow_corpus_limits_remain_blocked(self):
        self.assertFalse(w.ARTIFACT_PROOF);self.assertFalse(w.artifact_preflight(0)['execution_admitted'])
        self.assertEqual((w.WHOLE,w.FAILURE_CLEANUP,w.MAX_ARCHIVES,w.DELIVERED_LIMIT),(60.,5.,2,32*w.MIB))


if __name__=='__main__':unittest.main()
