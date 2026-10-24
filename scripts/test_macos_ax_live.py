#!/usr/bin/env python3
"""Pure retained-reference and bounded pipe protocol controls; no native APIs."""
import copy
from contextlib import redirect_stderr
import io
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import macos_ax_live as live
from test_macos_ax_read_only import FakeBackend


class Backend(FakeBackend):
    instances = []
    def __init__(self, pid, window, bounds, deadline):
        super().__init__()
        self.pid, self.window, self.bounds, self.deadline = pid, window, list(bounds), deadline
        self.calls, self.candidates, self.containers, self.collecting = {}, [], {}, True
        self.latest_rows, self.closed = [], 0
        type(self).instances.append(self)
    def preflight(self): return {'AXIsProcessTrusted': True}
    def displays(self): return []
    def guard(self):
        live.remaining(self.deadline)
        self.latest_rows = super().guard()
        return self.latest_rows
    def check_element(self, element):
        self.calls['AXUIElementGetPid'] = self.calls.get('AXUIElementGetPid',0)+1
        if self.objects[element].get('pid', self.pid) != self.pid: raise RuntimeError('Wrong retained PID')
    def elements(self, element, name, limit):
        values = self.objects[element]['children']
        if len(values) > limit: raise RuntimeError('Structural cap')
        self.calls['AXUIElementCopyAttributeValues'] = self.calls.get('AXUIElementCopyAttributeValues',0)+1
        return values
    def title(self, element):
        if self.role(element) not in ('AXButton','AXWindow'): raise AssertionError('Private title read')
        title = self.objects[element]['title']
        if self.collecting and live.normalized_title(title) == live.LABEL: self.candidates.append(element)
        self.calls['AXUIElementCopyAttributeValue'] = self.calls.get('AXUIElementCopyAttributeValue',0)+1
        return title
    def containing_window(self, element):
        window = self.objects[element].get('window',0)
        if self.collecting: self.containers[element] = window
        return window
    def close(self): self.closed += 1


class LiveControls(unittest.TestCase):
    def exchange(self, fault=None):
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary).resolve()/'initial.json'
            request_read, request_write = os.pipe()
            response_read, response_write = os.pipe()
            for descriptor in (request_read, request_write, response_read, response_write): os.set_blocking(descriptor,False)
            deadline, nonce, result, captured = time.monotonic()+5, 'a'*32, [], io.StringIO()
            def server():
                try:
                    result.append(live.serve(12,34,[40,60,960,568],nonce,5,deadline,report,
                        backend_type=Backend,input_fd=request_read,output_fd=response_write))
                finally:
                    os.close(request_read);os.close(response_write)
            thread = threading.Thread(target=server)
            with redirect_stderr(captured):
                thread.start()
                initial = live.decode(live.read_frame(response_read, live.CAPS['receipt_bytes'], deadline))
                backend = Backend.instances[-1]
                self.assertTrue(initial['complete'])
                self.assertEqual(initial['examined_nodes'],4)
                self.assertEqual(backend.candidates,[1])
                responses=[]
                try:
                    for sequence,kind in ((1,'pointer_move'),(2,'lmb_down')):
                        if sequence==2:
                            if fault=='disabled':backend.objects[1]['enabled']=False
                            elif fault=='title':backend.objects[1]['title']='WRONG'
                            elif fault=='role':backend.objects[1]['role']='AXTextField'
                            elif fault=='frame':backend.objects[1]['frame'][0]+=1
                            elif fault=='window':backend.objects[1]['window']=3
                            elif fault=='pid':backend.objects[1]['pid']=99
                            elif fault=='expired':backend.deadline=time.monotonic()-1
                            elif fault=='cap':backend.calls['AXUIElementGetPid']=live.CALL_CAP
                            elif fault=='replacement':
                                backend.objects[1]['title']='OLD'
                                backend.objects[99]={'role':'AXButton','title':live.LABEL,'enabled':True,
                                                    'frame':[100,320,350,100],'window':0,'children':[]}
                        command={'kind':kind,'nonce':nonce,'sequence':sequence}
                        if fault=='nonce' and sequence==2:command['nonce']='b'*32
                        if fault=='order' and sequence==2:command['sequence']=1
                        if fault=='bool_sequence' and sequence==1:command['sequence']=True
                        live.write_frame(request_write,live.encode(command,live.COMMAND_BYTES),deadline)
                        responses.append(live.decode(live.read_frame(response_read,live.GUARD_BYTES,deadline)))
                    live.write_frame(request_write,live.encode({'kind':'stop','nonce':nonce},live.COMMAND_BYTES),deadline)
                except (RuntimeError,TimeoutError):
                    if fault is None: raise
                finally:
                    os.close(request_write);os.close(response_read)
                    thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
            self.assertEqual(backend.closed,1)
            if result == [0]:
                self.assertFalse(report.exists())  # Parent owns the original success receipt.
            else:
                self.assertFalse(live.decode(report.read_bytes())['complete'])
            return result,responses,backend

    def test_two_live_checks_use_same_retained_reference_then_close_exactly_once(self):
        result,responses,backend=self.exchange()
        self.assertEqual(result,[0])
        self.assertEqual([row['sequence'] for row in responses],[1,2])
        self.assertEqual([row['original_node'] for row in responses],[1,1])
        self.assertEqual(backend.candidates,[1])
        self.assertTrue(all(row['button']['enabled'] for row in responses))
        self.assertTrue(all(row['input_events_posted']==0 and row['permission_requests_made']==0 for row in responses))

    def test_current_change_foreign_identity_and_replacement_never_reacquire(self):
        for fault in ('disabled','title','role','frame','window','pid','replacement','nonce','order','bool_sequence','expired','cap'):
            with self.subTest(fault=fault):
                result,responses,backend=self.exchange(fault)
                self.assertEqual(result,[1])
                self.assertLessEqual(len(responses),1)
                self.assertEqual(backend.candidates,[1])

    def test_frame_caps_duplicate_json_extra_messages_and_expired_deadline_fail(self):
        for data,limit in [(b'x'*257,live.COMMAND_BYTES),(b'x'*8193,live.GUARD_BYTES),
                           (b'{}\n{}\n',live.GUARD_BYTES)]:
            read,write=os.pipe()
            try:
                os.write(write,data);os.close(write);write=None
                with self.assertRaises(RuntimeError):live.read_frame(read,limit,time.monotonic()+1)
            finally:
                os.close(read)
                if write is not None:os.close(write)
        with self.assertRaises(RuntimeError):live.decode(b'{"sequence":1,"sequence":2}')
        with self.assertRaises(RuntimeError):live.encode({'oversized':'x'*257},live.COMMAND_BYTES)
        with self.assertRaises(TimeoutError):live.read_frame(0,256,time.monotonic()-1)

    def test_channel_failure_closes_pipes_and_waits_for_owned_helper(self):
        read,write=os.pipe()
        stream_in,stream_out=os.fdopen(write,'wb',buffering=0),os.fdopen(read,'rb',buffering=0)
        class Process:
            stdin,stdout=stream_in,stream_out
            returncode=None
            waited=0
            def poll(self):return self.returncode
            def wait(self,timeout):self.waited+=1;self.returncode=0;return 0
        process=Process();channel=live.LiveChannel(process,'a'*32,time.monotonic()+1)
        with patch.object(live,'write_frame',side_effect=RuntimeError('synthetic pipe failure')):
            with self.assertRaises(RuntimeError):channel.close()
        self.assertTrue(stream_in.closed and stream_out.closed)
        self.assertEqual(process.waited,1)
        channel.close();self.assertEqual(process.waited,1)

    def test_cumulative_native_call_cap_rejects_before_one_more_native_call(self):
        backend = live.RetainedAX.__new__(live.RetainedAX)
        backend.calls = {'AXUIElementGetPid':live.CALL_CAP-1}
        def called(_backend, name):
            _backend.calls[name] = _backend.calls.get(name,0)+1
            return 17
        with patch.object(live.NativeAX,'call',called):
            self.assertEqual(backend.call('AXUIElementGetPid'),17)
            with self.assertRaisesRegex(RuntimeError,'shared AX API call cap'):
                backend.call('AXUIElementGetPid')
        self.assertEqual(sum(backend.calls.values()),live.CALL_CAP)

    def test_channel_shares_one_absolute_deadline_and_cannot_run_third_query(self):
        read,write=os.pipe()
        stream_in,stream_out=os.fdopen(write,'wb',buffering=0),os.fdopen(read,'rb',buffering=0)
        class Process:
            stdin,stdout=stream_in,stream_out
            returncode=None
            def poll(self):return self.returncode
            def wait(self,timeout):self.returncode=0;return 0
        process=Process();deadline=time.monotonic()+5
        channel=live.LiveChannel(process,'a'*32,deadline)
        with patch.object(live,'write_frame') as writer, patch.object(live,'read_frame',return_value=b'{}\n') as reader:
            channel.initial()
            with self.assertRaises(RuntimeError):channel.query('lmb_down')
            channel.query('pointer_move');channel.query('lmb_down')
            with self.assertRaises(RuntimeError):channel.query('pointer_move')
            channel.close()
            self.assertTrue(all(call.args[-1]==deadline for call in reader.call_args_list+writer.call_args_list))
            self.assertEqual([call.args[1] for call in reader.call_args_list],
                             [live.CAPS['receipt_bytes'],live.GUARD_BYTES,live.GUARD_BYTES])
        self.assertTrue(stream_in.closed and stream_out.closed)

    def test_retained_cf_references_release_once_on_repeated_close(self):
        backend=live.RetainedAX.__new__(live.RetainedAX)
        released=[]
        class CF:
            def CFRelease(self,pointer):released.append(pointer)
        backend.cf,backend.refs=CF(),[101,102,101]
        backend.close();backend.close()
        self.assertEqual(released,[101,102,101])  # Each original ownership is released once.

    def test_early_pipe_eof_never_returns_partial_response(self):
        read,write=os.pipe()
        try:
            os.write(write,b'{"schema":');os.close(write);write=None
            with self.assertRaisesRegex(RuntimeError,'ended before'):
                live.read_frame(read,live.GUARD_BYTES,time.monotonic()+1)
        finally:
            os.close(read)
            if write is not None:os.close(write)


if __name__=='__main__':unittest.main()
