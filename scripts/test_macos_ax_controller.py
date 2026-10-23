#!/usr/bin/env python3
"""Full synthetic controller and AppKit paths; no real processes/native calls."""
from contextlib import ExitStack
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import types
import unittest
from unittest.mock import patch

import macos_ax_appkit
import probe_macos_ax
import verify_macos_ax_read_only as driver
from macos_ax_contract import CAPS
from test_macos_ax_read_only import FakeBackend, observation, synthetic_capture


class SyntheticRun:
    def __init__(self, directory, fault=None):
        self.directory, self.fault = Path(directory), fault
        self.home = self.directory / 'home'
        self.home.mkdir()
        self.now, self.next_pid, self.client, self.ui = 1., 1000, None, None
        self.focused, self.focus_calls, self.ax_done, self.default_reads = False, 0, False, 0
        self.private, self.profile = None, False
        self.bounds = [40,60,960,568]
        self.identity = {'source_commit':'SYNTHETIC','source_game_tree':'SYNTHETIC',
                         'source_content_sha256':'SYNTHETIC','source_validation_sha256':'SYNTHETIC',
                         'source_dirty':False,'source_game_dirty':False}
        self.exe_bytes = b'SYNTHETIC NONEXECUTABLE ONLY'
        self.manifest = {'artifact':{'sha256':hashlib.sha256(self.exe_bytes).hexdigest()}}
        self.window_type = self.make_window()

    def clock(self): return self.now
    def sleep(self, seconds): self.now += seconds

    def rows(self, pid):
        rows=[{'owner_pid':pid,'window_id':34,'onscreen':True,'bounds_points_including_chrome':list(self.bounds)}]
        if self.ax_done:
            if self.fault=='late_window': rows.append(dict(rows[0],window_id=35))
            if self.fault=='late_geometry': rows[0]['bounds_points_including_chrome'][2]+=1
        return rows

    def default_inventory(self):
        self.default_reads+=1
        if self.fault=='default' and self.default_reads>2:
            return {'directory_exists':True,'directories':[],'files':{'unexpected':{}}}
        return {'directory_exists':False,'directories':[],'files':{}}

    def stage(self, original, destination, name):
        self.private=self.home/'Library/Application Support'/name
        destination=Path(destination)
        (destination/'Contents/MacOS').mkdir(parents=True)
        (destination/'Contents/MacOS/SIGHTBREAK').write_bytes(self.exe_bytes)
        return {'staged':str(destination),'executable_sha256':self.manifest['artifact']['sha256']}

    def make_window(self):
        harness=self
        class Window:
            require_window=macos_ax_appkit.AXWindow.require_window
            require_target=macos_ax_appkit.AXWindow.require_target
            focus=macos_ax_appkit.AXWindow.focus
            pin=macos_ax_appkit.AXWindow.pin
            state=macos_ax_appkit.AXWindow.state
            request_close=macos_ax_appkit.AXWindow.request_close
            close=macos_ax_appkit.AXWindow.close
            def __init__(self,pid,window,bounds,trace,private_guard):
                self.pid,self.window,self.bounds=pid,window,bounds
                self.trace,self.private_guard=trace,private_guard
                self.event_post_attempts,self.focus_requests,self.pinned,self.pool=0,0,False,1
                harness.ui=self
            def windows(self,pid):return harness.rows(pid)
            def controls(self):return {'lmb_down':False,'escape_down':False,'tab_down':False}
            def foreground_pid(self):return self.pid if harness.focused else 42
            def pump(self,seconds):harness.now+=seconds
            def application(self):return self.pid
            def message(self,_receiver,selector,*_arguments,**_keywords):
                if selector=='activateWithOptions:':
                    harness.focus_calls+=1
                    harness.focused=True
                    if harness.fault=='focus_late':harness.now+=5.001
                    return True
                if selector=='terminate':
                    if harness.fault=='close_refused':return False
                    harness.client.returncode=0
                    if harness.fault=='close_late':harness.now+=20.001
                    return True
                if selector=='drain':return None
                raise AssertionError('Unexpected synthetic AppKit message '+selector)
        return Window

    def popen(self,arguments,**keywords):
        self.next_pid+=1
        harness=self
        compile_command='-parse-as-library' in arguments
        capture_command='--png' in arguments
        ax_command=str(driver.AX_SOURCE) in arguments
        is_client=not(compile_command or capture_command or ax_command)
        class Process:
            pid=harness.next_pid
            returncode=None
            def poll(self):return self.returncode
            def wait(self,timeout):
                if is_client:
                    if harness.fault=='close_timeout':raise TimeoutError('synthetic close timeout')
                    return self.returncode
                if compile_command and harness.fault=='compile_late':harness.now+=60.001
                if capture_command and harness.fault=='capture_late':harness.now+=25.001
                if ax_command and harness.fault=='ax_late':harness.now+=5.001
                self.returncode=0
                return 0
        process=Process()
        if compile_command:
            Path(arguments[arguments.index('-o')+1]).write_bytes(b'SYNTHETIC NONEXECUTABLE CAPTURE ONLY')
        elif is_client:
            self.client=process
            self.private.mkdir(parents=True)
            (self.private/'mac-ordinary-engine.log').write_text('Godot Engine v4.7.2.stable SYNTHETIC\n')
            if self.fault=='menu_profile':
                (self.private/'offline_training.json').write_text('SYNTHETIC CONTENTS MUST NOT BE READ AS PROFILE DATA')
                self.profile=True
            if self.fault=='native_leak':keywords['stdout'].write('ObjectDB instances leaked at exit\n')
        elif capture_command:
            image=synthetic_capture()
            image.update(owner_pid=self.client.pid,window_id=34)
            name=Path(arguments[arguments.index('--report')+1])
            if self.fault=='menu_late' and name.stem.startswith('00-'):
                image['text']=[];self.now+=25
            if self.fault=='foreign_capture':image['owner_pid']+=1
            png=Path(arguments[arguments.index('--png')+1])
            png.write_bytes(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II',*image['image_dimensions'])+b'SYNTHETIC ONLY')
            name.write_text(json.dumps(image))
            self.now+=.02
        else:
            backend=FakeBackend();backend.pid=self.client.pid
            report=observation(backend)
            report.update(observer_pid=process.pid,nonce=arguments[arguments.index('--nonce')+1],
                          started_monotonic=self.now,finished_monotonic=self.now+.2)
            for snapshot in report['snapshots']:
                snapshot['started_monotonic']=self.now
                snapshot['finished_monotonic']=self.now+.1
            if self.fault=='stale':report['started_monotonic']=-5
            if self.fault=='nonce':report['nonce']='f'*32
            if self.fault=='untrusted':report['AXIsProcessTrusted']=False
            if self.fault=='duplicate':
                extra=dict(report['snapshots'][-1]['nodes'][1],node=100)
                report['snapshots'][-1]['nodes'].append(extra);report['examined_nodes']+=1
            if self.fault=='wrong_words':
                row=report['snapshots'][-1]['nodes'][1];row['title']=row['normalized_title']='DEPLOY · ONLINE 5V5'
            if self.fault=='receipt_bytes':report['oversized']='x'*(CAPS['receipt_bytes']+1)
            if self.fault=='raw_changed':
                (self.directory/'out/01-focused-menu.json').write_text('CHANGED SYNTHETIC FILE')
            if self.fault=='trace':
                (self.directory/'out/stock-offline-trace').mkdir()
            Path(arguments[arguments.index('--report')+1]).write_text(json.dumps(report))
            self.now+=.2
            self.ax_done=True
            if self.fault=='lost_focus':self.focused=False
        return process

    def execute(self):
        harness=self
        class API:
            def preflight(self):return {'CGPreflightScreenCaptureAccess':True,'AXIsProcessTrusted':True}
            def windows(self,pid):return harness.rows(pid)
        def verify_payload(_receipt):
            if self.fault=='payload':raise RuntimeError('synthetic payload mutation')
        def reap(process):
            return {'owned_group_gone':self.fault!='survivor','signals_sent':[15] if self.fault=='signal' else [],
                    'exit_code':process.returncode}
        def current_source():
            return dict(self.identity,source_commit='MUTATED') if self.fault=='source' and self.ax_done else self.identity
        patches=[patch.object(driver,'MacReadOnly',API),patch.object(driver,'AXWindow',self.window_type),
                 patch.object(driver,'source',current_source),patch.object(driver,'clean',lambda _:None),
                 patch.object(driver,'validate_record',lambda *_:self.manifest),
                 patch.object(driver.toolchain,'verify_engine',lambda:'SYNTHETIC NOT EXECUTED'),
                 patch.object(driver,'account_home',lambda:self.home),
                 patch.object(driver,'default_inventory',self.default_inventory),
                 patch.object(driver,'require_absent_profile',lambda:{}),patch.object(driver,'stage_app',self.stage),
                 patch.object(driver,'verify_staged_app',verify_payload),patch.object(driver,'reap',reap),
                 patch.object(driver.subprocess,'Popen',self.popen),
                 patch.object(driver.time,'monotonic',self.clock),patch.object(driver.time,'sleep',self.sleep)]
        with ExitStack() as stack:
            for item in patches:stack.enter_context(item)
            stack.enter_context(patch('sys.stdout',new=io.StringIO()))
            code=driver.run(self.directory/'out')
        return code,json.loads((self.directory/'out/results.json').read_text())


class ControllerControls(unittest.TestCase):
    def execute(self,fault=None):
        with tempfile.TemporaryDirectory() as directory:
            # Canonicalize only this test-owned temporary root, including macOS /var alias.
            harness=SyntheticRun(Path(directory).resolve(),fault)
            code,result=harness.execute()
            return code,result,harness.focus_calls

    def test_valid_full_synthetic_diagnostic_posts_no_event_and_ordinary_closes(self):
        code,result,focus=self.execute()
        self.assertEqual(code,0,result)
        self.assertEqual(result['status'],'PASS_READ_ONLY_AX_EXPOSURE_ONLY')
        self.assertFalse(result['gameplay_target_accepted'])
        self.assertTrue(result['original_native_ocr_unchanged'])
        self.assertEqual((result['cg_event_post_attempts'],focus,result['normal_exit_code']),(0,1,0))

    def test_private_menu_profile_creation_is_preserved_and_reported_without_parsing(self):
        code,result,_=self.execute('menu_profile')
        self.assertEqual(code,0,result)
        self.assertEqual(result['private_menu_profile_files_present'],['offline_training.json'])

    def test_late_compile_capture_focus_menu_ax_and_close_never_pass(self):
        for fault in ('compile_late','capture_late','focus_late','menu_late','ax_late','close_late'):
            with self.subTest(fault=fault):
                code,result,focus=self.execute(fault)
                self.assertNotEqual(code,0,result)
                self.assertFalse(result['passed'])
                self.assertLessEqual(focus,1)

    def test_binding_context_duplicate_byte_cap_and_unexpected_match_trace_fail(self):
        for fault in ('stale','nonce','untrusted','duplicate','wrong_words','receipt_bytes','foreign_capture','raw_changed','trace'):
            with self.subTest(fault=fault):
                code,result,focus=self.execute(fault)
                self.assertNotEqual(code,0,result)
                self.assertFalse(result['passed'])
                self.assertEqual(result['cg_event_post_attempts'],0)
                self.assertLessEqual(focus,1)

    def test_late_geometry_window_or_foreground_change_preserves_current_failure_rows(self):
        for fault in ('late_window','late_geometry','lost_focus'):
            with self.subTest(fault=fault):
                code,result,_=self.execute(fault)
                self.assertNotEqual(code,0,result)
                self.assertTrue(any(row['event']=='owned_window_guard' for row in result['actions']))

    def test_payload_default_source_native_leaks_cleanup_signals_survivors_close_refusal_fail(self):
        for fault in ('payload','default','source','native_leak','signal','survivor','close_refused'):
            with self.subTest(fault=fault):
                code,result,_=self.execute(fault)
                self.assertNotEqual(code,0,result)
                self.assertFalse(result['passed'])

    def test_actual_appkit_focus_and_pin_methods_refuse_repeat_and_late_extra_window(self):
        with tempfile.TemporaryDirectory() as directory:
            harness=SyntheticRun(Path(directory).resolve())
            harness.client=types.SimpleNamespace(pid=12,returncode=None)
            ui=harness.window_type(12,34,harness.bounds,lambda *_a,**_k:None,lambda:None)
            with patch.object(macos_ax_appkit.time,'monotonic',harness.clock):
                ui.focus(5)
                with self.assertRaises(RuntimeError):ui.focus(5)
                harness.ax_done=True;harness.fault='late_window'
                with self.assertRaises(RuntimeError):ui.pin(synthetic_capture())
            self.assertFalse(ui.pinned)
            self.assertEqual((ui.event_post_attempts,ui.focus_requests),(0,1))

    def test_non_native_refusal_precedes_all_compilation_launch_and_library_loads(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(driver.subprocess,'Popen') as popen:
            with patch('platform.system',return_value='Linux'),patch('sys.stdout',new=io.StringIO()):
                code=driver.run(Path(directory).resolve()/'out')
                result=probe_macos_ax.collect(12,34,[0,0,100,100],'a'*32,5)
            self.assertNotEqual(code,0)
            self.assertFalse(result['complete'])
            popen.assert_not_called()


if __name__=='__main__':unittest.main()
