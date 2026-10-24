#!/usr/bin/env python3
"""Pure source/target/controller falsifiers. No native calls or gameplay evidence."""
import copy
from dataclasses import FrozenInstanceError
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import macos_deploy_ocr as ocr
import macos_native_input as native
import macos_ordinary_input as ordinary
import macos_semantic_deploy as semantic
import verify_macos_ordinary as driver
from test_macos_ax_read_only import FakeBackend, observation
from test_macos_ordinary_controller import SyntheticController

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'scripts/fixtures/macos_semantic_deploy'


def original_ordinary_source(path, data):
    amendments = json.loads((FIXTURES/'source-amendments.json').read_text())[path]
    if hashlib.sha256(data).hexdigest() != amendments['candidate_sha256']:
        raise AssertionError('Ordinary semantic source differs from the declared exact delta')
    lines = data.decode().splitlines(keepends=True)
    for part in reversed(amendments['parts']):
        start, end = part['new_start'], part['new_end']
        if lines[start:end] != part['new']:
            raise AssertionError('Declared ordinary amendment does not match candidate bytes')
        lines[start:end] = part['old']
    original = ''.join(lines).encode()
    if (hashlib.sha256(original).hexdigest() != amendments['base_sha256']
            or original != (FIXTURES/(Path(path).name+'.txt')).read_bytes()):
        raise AssertionError('Original ordinary source fixture or undeclared source changed')
    return original


def semantic_receipt(pid, bounds, observer_pid, nonce, started):
    backend = FakeBackend()
    backend.pid, backend.bounds = pid, list(bounds)
    backend.objects[1]['frame'] = [100, 300, 350, 100]
    receipt = observation(backend)
    receipt.update(scope='Read-only exported AX semantic exposure; no input/gameplay acceptance',
        observer_pid=observer_pid, nonce=nonce, started_monotonic=started, finished_monotonic=started+.2,
        displays=[{'display_id': 1, 'bounds_points': [0, 0, 1024, 768], 'mode_dimensions': [1024, 768],
            'mode_pixel_dimensions': [1024, 768], 'mode_pixel_per_unit': [1, 1],
            'scale_scope': 'Raw public CGDisplayMode metadata; not an assumed AX coordinate multiplier'}])
    for snapshot in receipt['snapshots']:
        snapshot.update(started_monotonic=started, finished_monotonic=started+.1)
    return receipt


class SemanticController(SyntheticController):
    def __init__(self, directory, fault=None):
        self.native_posts, self.pointer, self.mouse_down = [], [280, 344.4], False
        self.ax_calls, self.semantic_guard_calls, self.live_calls = 0, 0, []
        super().__init__(directory, fault)

    def native_capture(self, name):
        image = super().native_capture(name)
        if name == '01-focused-menu':
            image['text'][3].update(text='DEPLOY • OFFLINE 5V5', confidence=.5)
        return image

    def popen(self, arguments, **keywords):
        if str(semantic.AX_SOURCE) not in arguments:
            process = super().popen(arguments, **keywords)
            if '--png' in arguments:
                data = json.loads(Path(arguments[arguments.index('--report')+1]).read_text())
                Path(arguments[arguments.index('--png')+1]).write_bytes(
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'+struct.pack('>II', *data['image_dimensions'])+b'SYNTHETIC ONLY')
            return process
        self.ax_calls += 1
        self.next_pid += 1
        pid, started = self.next_pid, self.now
        receipt = semantic_receipt(self.client.pid, self.active_ui.bounds, pid,
                                   arguments[arguments.index('--nonce')+1], started)
        node = receipt['snapshots'][-1]['nodes'][1]
        if self.fault == 'duplicate':
            receipt['snapshots'][-1]['nodes'].append(dict(node, node=100));receipt['examined_nodes'] += 1
        elif self.fault == 'disabled': node['enabled'] = False
        elif self.fault == 'title': node['title'] = 'DEPLOY · ONLINE 5V5'
        elif self.fault == 'foreign_pid': receipt['owner_pid'] += 1
        elif self.fault == 'foreign_window': receipt['window_id'] += 1
        elif self.fault == 'wrong_frame': node['frame_points'][0] = 500
        elif self.fault == 'stale_ax': receipt['started_monotonic'] -= 1
        elif self.fault == 'nonce': receipt['nonce'] = '0'*32
        elif self.fault == 'untrusted': receipt['AXIsProcessTrusted'] = False
        elif self.fault == 'incomplete': receipt['complete'] = False
        elif self.fault == 'privacy_top': receipt['account_text'] = 'PRIVATE SYNTHETIC ONLY'
        elif self.fault == 'privacy_node': node['AXValue'] = 'PRIVATE SYNTHETIC ONLY'
        elif self.fault == 'privacy_structural': receipt['snapshots'][-1]['nodes'][3]['frame_points'] = ['PRIVATE']
        elif self.fault == 'bool_cap': receipt['caps']['snapshots'] = 3.0
        elif self.fault == 'float_window_pid': receipt['snapshots'][-1]['windows'][0]['pid'] = float(self.client.pid)
        elif self.fault == 'float_cg_pid': receipt['snapshots'][-1]['cg_after'][0]['owner_pid'] = float(self.client.pid)
        elif self.fault == 'float_count': receipt['examined_nodes'] = float(receipt['examined_nodes'])
        elif self.fault == 'bool_events': receipt['input_events_posted'] = False
        elif self.fault == 'bool_prompts': receipt['permission_requests_made'] = False
        elif self.fault == 'privacy_display': receipt['displays'][0]['mode_dimensions'] = ['PRIVATE', 768]
        elif self.fault == 'privacy_window': receipt['last_owned_layer_zero_rows'][0]['title'] = 'PRIVATE'
        elif self.fault == 'oversize': receipt['unexpected'] = 'x'*(semantic.CAPS['receipt_bytes']+1)
        elif self.fault == 'raw_changed': (self.directory/'01-focused-menu.json').write_text('MUTATED')
        Path(arguments[arguments.index('--report')+1]).write_text(json.dumps(receipt))
        harness = self
        class Process:
            returncode = None
            def poll(self): return self.returncode
            def wait(self, timeout):
                harness.now += 5.001 if harness.fault == 'ax_late' else .2
                self.returncode = 1 if harness.fault == 'ax_exit' else 0
                return self.returncode
        process = Process();process.pid = pid
        return process

    def make_ui(self):
        base, harness = super().make_ui(), self
        class UI(base, ordinary.MacOrdinaryUI):
            click_label = ordinary.MacOrdinaryUI.click_label
            _click_label = ordinary.MacOrdinaryUI._click_label
            post = ordinary.MacOrdinaryUI.post
            release_owned = ordinary.MacOrdinaryUI.release_owned
            button = native.MacMenuUI.button
            def observed_state(self, control, down, **keywords):
                if control == 'lmb':
                    return native.MacMenuUI.observed_state(self, control, down, **keywords)
                return super().observed_state(control, down, **keywords)
            def fire_button(self, down):
                harness.mouse_down = down
                return super().fire_button(down)
            confirm_release = native.MacMenuUI.confirm_release
            def __init__(self, pid, window, bounds, trace):
                super().__init__(pid, window, bounds, trace)
                self.held = set()
                def delayed_trace(event, **details):
                    trace(event, **details)
                    if event == 'cg_event_post_attempt' and ((harness.fault == 'trace_move_late' and details['event_kind'] == 'pointer_move')
                            or (harness.fault == 'trace_down_late' and details['event_kind'] == 'lmb_down')):
                        harness.now += 5.001
                self.trace = delayed_trace
                self.cf = SimpleNamespace(CFRelease=lambda _: None)
                def posted(_, event):
                    kind, x, y = event
                    harness.native_posts.append(kind)
                    if kind == 5:
                        harness.pointer = [x, y]
                        if harness.fault == 'stale_before_down': harness.now += 4.8
                        if harness.fault == 'geometry_before_down': harness.window_id += 1
                        if harness.fault == 'bytes_before_down': (harness.directory/'semantic-deploy-ax.json').write_text('MUTATED')
                        for fault, name in [('replace_png', '01-focused-menu.png'), ('replace_native', '01-focused-menu.json'),
                                            ('replace_ax', 'semantic-deploy-ax.json'), ('replace_live', 'semantic-live-1.json')]:
                            if harness.fault == fault:
                                path = harness.directory/name
                                previous = path.stat()
                                replacement = path.with_suffix('.replacement')
                                replacement.write_bytes(path.read_bytes())
                                os.utime(replacement, ns=(previous.st_atime_ns, previous.st_mtime_ns))
                                replacement.replace(path)
                        if harness.fault == 'symlink_before_down':
                            original = harness.directory/'semantic-deploy-ax.json'
                            retained = original.with_suffix('.retained')
                            original.rename(retained);original.symlink_to(retained)
                    if kind in (1, 2):
                        harness.mouse_down = kind == 1
                        if kind == 1 and not harness.deployed: harness.deployed = True
                self.cg = SimpleNamespace(CGEventCreateMouseEvent=lambda _, kind, point, button: (kind, point.x, point.y),
                    CGEventSetFlags=lambda *_: None, CGEventPost=posted,
                    CGEventSourceButtonState=lambda *_: harness.mouse_down)
            def pin_for_input(self, image):
                super().pin_for_input(image)
                if harness.fault == 'png_before_acquire':
                    path = harness.directory/'01-focused-menu.png'
                    path.write_bytes(path.read_bytes()+b'SUBSTITUTED AFTER ACCEPTED CAPTURE')
                if harness.fault == 'receipt_before_acquire':
                    image['text'][3]['confidence'] = .6
                    (harness.directory/'01-focused-menu.json').write_text(json.dumps(image))
            def require_target(self):
                super().require_target()
                if getattr(self, 'semantic_deploy_target', None) is not None:
                    harness.target = self.semantic_deploy_target
                    harness.semantic_guard_calls += 1
                    if harness.fault == 'stale_before_move': harness.now += 5.001
            def diagnostics(self):
                return {'foreground_pid': self.pid, 'lmb_down': harness.mouse_down,
                        'escape_down': False, 'reload_down': False, 'pointer_points': list(harness.pointer)}
        return UI

    def execute(self):
        run = driver.run
        def semantic_run(output, preflight):
            # Actual file hashes for this pure target-binding harness; absent
            # synthetic executable/helper paths retain their non-native marker.
            from test_macos_ordinary_controller import SYNTHETIC_DIGEST
            from macos_ax_live import LIVE_SCHEMA, encode, GUARD_BYTES
            harness = self
            def file_digest(path):
                return semantic.digest(path) if Path(path).is_file() else SYNTHETIC_DIGEST
            def start_live(pid, window, bounds, nonce, budget, expires, report, log, processes):
                process = harness.popen([str(semantic.AX_SOURCE), '--pid', str(pid), '--window', str(window),
                    '--nonce', nonce, '--report', str(report)], stdout=io.StringIO())
                process.wait(timeout=budget)
                if process.returncode == 0: process.returncode = None
                processes.append(('semantic-deploy-live', process))
                receipt = json.loads(Path(report).read_text())
                class Channel:
                    sequence, closed = 0, False
                    def query(channel, kind):
                        channel.sequence += 1; harness.live_calls.append(kind)
                        first = harness.now;harness.now += .01
                        node = copy.deepcopy(receipt['snapshots'][-1]['nodes'][1])
                        button = {key:value for key,value in node.items() if key not in ('node','parent','depth')}
                        if kind == 'lmb_down':
                            if harness.fault == 'live_disabled': button['enabled'] = False
                            if harness.fault == 'live_title': button['title'] = 'CHANGED'
                            if harness.fault == 'live_frame': button['frame_points'][0] += 10
                            if harness.fault == 'live_window': button['window_frame_points'][0] += 10
                            if harness.fault == 'live_pid': button['pid'] += 1
                            if harness.fault == 'live_late': harness.now += 5.001
                        response = {'schema': LIVE_SCHEMA, 'nonce': nonce, 'sequence': channel.sequence, 'kind': kind,
                            'owner_pid':pid,'window_id':window,'observer_pid':process.pid,'original_node':node['node'],
                            'started_monotonic':first,'finished_monotonic':harness.now,'button':button,
                            'owned_rows':copy.deepcopy(receipt['last_owned_layer_zero_rows']),
                            'api_call_counts':{'AXUIElementGetPid':4+channel.sequence},
                            'input_events_posted':0,'permission_requests_made':0}
                        if kind == 'lmb_down':
                            if harness.fault == 'live_nonce': response['nonce']='f'*32
                            if harness.fault == 'live_sequence': response['sequence']=True
                            if harness.fault == 'live_private': response['private_account']='SYNTHETIC PRIVATE'
                            if harness.fault == 'live_zero': response['input_events_posted']=False
                            if harness.fault == 'live_count': response['api_call_counts']={'AXUIElementPerformAction':1}
                        return encode(response, GUARD_BYTES)
                    def close(channel):
                        channel.closed = True
                        if process.returncode is None: process.returncode = 0
                channel = Channel();channel.process = process
                raw = Path(report).read_bytes()
                Path(report).unlink()  # Success is retained by the parent's writing descriptor.
                return channel, raw
            with patch.object(driver, 'digest', file_digest), patch.object(semantic, 'start_live', start_live):
                return run(output, preflight, deploy_target='owned-ax')
        with patch.object(driver, 'run', semantic_run):
            return super().execute()


class SemanticControls(unittest.TestCase):
    def execute(self, fault=None):
        with tempfile.TemporaryDirectory() as temporary:
            harness = SemanticController(Path(temporary).resolve()/'synthetic', fault)
            code, result = harness.execute()
            return code, result, harness

    def test_explicit_semantic_target_runs_existing_os_input_sequence_with_original_point_five_ocr(self):
        code, result, harness = self.execute()
        self.assertEqual(code, 0, result.get('failure'))
        self.assertEqual(harness.ax_calls, 1)
        self.assertEqual(harness.live_calls, ['pointer_move', 'lmb_down'])
        self.assertEqual(harness.native_posts[:3], [5, 1, 2])
        self.assertTrue(result['native_reload'])
        self.assertFalse(result['semantic_deploy_target']['input_delivery_or_gameplay_accepted'])
        self.assertEqual(result['semantic_deploy_target']['original_native_row']['confidence'], .5)
        self.assertEqual(result['semantic_deploy_target']['target_points'], [280, 344.4])
        self.assertIsNone(harness.active_ui.semantic_deploy_target)
        launch = result['client_command']
        self.assertEqual(launch[launch.index('--accessibility'):launch.index('--accessibility')+2], ['--accessibility', 'always'])
        self.assertFalse(any('--analysis-mode' in row['command'] for row in result['actions'] if row['event'] == 'helper_command'))
        self.assertTrue(all(row['owned_group_gone'] and not row['signals_sent'] for row in result['cleanup']))

    def test_original_c838_both_point_five_receipt_still_rejects_original_ocr_gate(self):
        raw = (FIXTURES/'original-focused-39920948579.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'ce9a6c0905e2cc880d1b2956eaeaedaedea42e45bbffb91328bf8ff1bd7c433b')
        image = json.loads(raw)
        self.assertEqual(next(row['confidence'] for row in image['text'] if row['text'].startswith('DEPLOY')), .5)
        self.assertEqual(next(row['confidence'] for row in image['derived_deploy_analysis']['text'] if row['text'].startswith('DEPLOY')), .5)
        before = copy.deepcopy(image)
        with self.assertRaises(RuntimeError): ordinary.label_point(image, ocr.LABEL)
        ocr.bind_analysis(image, image['derived_deploy_analysis']['source_png_sha256'],
            image['derived_deploy_analysis']['analysis_png_sha256'], image['image_dimensions'],
            image['derived_deploy_analysis']['analysis_image_dimensions'])
        with self.assertRaises(RuntimeError): ordinary.label_point(image, ocr.LABEL)
        image.pop(ocr.BINDING)
        self.assertEqual(image, before)

    def test_collection_identity_geometry_duplicate_disabled_privacy_and_late_fail_before_any_move(self):
        for fault in ('duplicate', 'disabled', 'title', 'foreign_pid', 'foreign_window', 'wrong_frame', 'stale_ax',
                      'nonce', 'untrusted', 'incomplete', 'privacy_top', 'privacy_node', 'privacy_display',
                      'privacy_window', 'privacy_structural', 'bool_cap', 'float_window_pid', 'float_cg_pid',
                      'float_count', 'bool_events', 'bool_prompts', 'oversize', 'raw_changed', 'ax_late', 'ax_exit', 'stale_before_move'):
            with self.subTest(fault=fault):
                code, result, harness = self.execute(fault)
                self.assertEqual(code, 1, result)
                self.assertFalse(result['passed'])
                self.assertEqual(harness.native_posts, [])
                self.assertFalse(harness.deployed)
                self.assertEqual(result['cg_event_post_attempts'], 0)

    def test_original_capture_hashes_cannot_be_renewed_after_pre_acquisition_substitution(self):
        for fault in ('png_before_acquire', 'receipt_before_acquire'):
            with self.subTest(fault=fault):
                code, result, harness = self.execute(fault)
                self.assertEqual(code, 1, result.get('failure'))
                self.assertEqual(harness.native_posts, [])
                self.assertEqual(harness.ax_calls, 0)
                self.assertFalse(harness.deployed)

    def test_stale_or_mutated_after_move_never_posts_button_down(self):
        for fault in ('stale_before_down', 'geometry_before_down', 'bytes_before_down', 'symlink_before_down',
                      'replace_png', 'replace_native', 'replace_ax', 'replace_live'):
            with self.subTest(fault=fault):
                code, result, harness = self.execute(fault)
                self.assertEqual(code, 2 if fault == 'symlink_before_down' else 1, result.get('failure', result.get('blocker')))
                self.assertEqual(harness.native_posts, [5])
                self.assertFalse(harness.deployed)
                self.assertEqual(harness.active_ui.held, set())
                self.assertEqual(result['cg_event_post_attempts'], 1)

    def test_same_retained_target_current_changes_after_move_reject_before_down(self):
        for fault in ('live_disabled', 'live_title', 'live_frame', 'live_window', 'live_pid', 'live_late',
                      'live_nonce', 'live_sequence', 'live_private', 'live_zero', 'live_count'):
            with self.subTest(fault=fault):
                code, result, harness = self.execute(fault)
                self.assertEqual(code, 1, result.get('failure'))
                self.assertEqual(harness.native_posts, [5])
                self.assertEqual(harness.live_calls, ['pointer_move','lmb_down'])
                self.assertFalse(harness.deployed)
                self.assertTrue(harness.target.live.closed)
                self.assertEqual(harness.active_ui.held, set())

    def test_trace_io_delay_cannot_deliver_stale_move_or_down(self):
        for fault, posts, attempts in [('trace_move_late', [], 1), ('trace_down_late', [5], 2)]:
            with self.subTest(fault=fault):
                code, result, harness = self.execute(fault)
                self.assertEqual(code, 1, result.get('failure'))
                self.assertEqual(harness.native_posts, posts)
                self.assertEqual(result['cg_event_post_attempts'], attempts)
                self.assertFalse(harness.deployed)
                self.assertEqual(harness.active_ui.held, set())

    def test_descriptor_reader_rejects_fifo_and_bounds_file_growth_without_path_read_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            fifo = root/'fifo';os.mkfifo(fifo)
            with patch.object(Path, 'read_text', side_effect=AssertionError('Unbounded path read')):
                with self.assertRaises(RuntimeError): semantic.read_public_json(fifo)
            path = root/'growing.json';path.write_text('{}')
            native_read, lengths, grown = os.read, [], [False]
            def grow(descriptor, count):
                if not grown[0]:
                    with path.open('ab') as stream: stream.write(b' '*(semantic.CAPS['receipt_bytes']+1))
                    grown[0] = True
                result = native_read(descriptor, count);lengths.append(len(result));return result
            with patch.object(semantic.os, 'read', grow):
                with self.assertRaises(RuntimeError): semantic.read_public_json(path)
            self.assertLessEqual(sum(lengths), semantic.CAPS['receipt_bytes']+1)

    def test_initial_and_live_response_descriptor_identity_cannot_be_replaced_before_sealing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            seed = root/'seed'; seed.write_bytes(b'{}\n')
            _, original = semantic.read_regular(seed, semantic.GUARD_BYTES)
            read = semantic.read_regular
            for name in ('semantic-deploy-ax.json','semantic-live-1.json'):
                path = root/name
                def substituted(current, *arguments):
                    current = Path(current)
                    current.rename(current.with_suffix('.retained'))
                    current.write_bytes(b'{}\n')
                    return read(current,*arguments)
                with patch.object(semantic,'read_regular',substituted):
                    with self.assertRaisesRegex(RuntimeError,'changed before sealing'):
                        semantic.retain_response(path,b'{}\n',semantic.GUARD_BYTES,original.directories)
            # A regular-file copy in a different ancestor is also rejected.
            child = root/'replacement'; child.mkdir()
            with self.assertRaisesRegex(RuntimeError,'changed before sealing'):
                semantic.retain_response(child/'ax.json',b'{}\n',semantic.GUARD_BYTES,original.directories)

    def test_target_replay_or_foreign_capture_controller_and_json_spoof_fail(self):
        code, _, harness = self.execute()
        self.assertEqual(code, 0)
        ui = harness.active_ui
        target = harness.target
        self.assertTrue(target.used)
        with self.assertRaises(RuntimeError): target.point(target.capture, ui)
        with self.assertRaises(FrozenInstanceError): target.expires = 99999
        object.__setattr__(target, 'used', False)  # Test-only reset for the remaining independent gates.
        with patch.object(semantic.time, 'monotonic', lambda: target.binding['finished']):
            with self.assertRaises(RuntimeError): target.point(copy.deepcopy(target.capture), ui)
            with self.assertRaises(RuntimeError): target.point(target.capture, object())
            target.receipt['snapshots'][-1]['nodes'][1]['enabled'] = False
            with self.assertRaises(RuntimeError): target.point(target.capture, ui)
        # A JSON object can never enter the in-memory semantic target type.
        ui.semantic_deploy_target = {'point': [280, 344.4]}
        with self.assertRaises(RuntimeError): ui.click_label({}, ocr.LABEL)

    def test_strict_public_json_rejects_duplicate_keys_nonfinite_and_oversized_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve()/'synthetic.json'
            for raw in ('{"owner_pid": 12, "owner_pid": 99}', '{"secret": NaN}',
                        '{"secret": Infinity}', '"'+'x'*semantic.CAPS['receipt_bytes']+'"'):
                path.write_text(raw)
                with self.subTest(raw=raw[:30]), self.assertRaises(RuntimeError): semantic.read_public_json(path)

    def test_declared_ordinary_source_delta_reconstructs_exact_original_and_rejects_other_changes(self):
        for path in ('scripts/macos_ordinary_input.py', 'scripts/verify_macos_ordinary.py'):
            current = (ROOT/path).read_bytes()
            original_ordinary_source(path, current)
            with self.assertRaises(AssertionError): original_ordinary_source(path, current+b'\n')
        original = (FIXTURES/'macos_ordinary_input.py.txt').read_text()
        current = (ROOT/'scripts/macos_ordinary_input.py').read_text()
        import ast
        def function(source, name):
            return ast.dump(next(node for node in ast.walk(ast.parse(source))
                                 if isinstance(node, ast.FunctionDef) and node.name == name))
        for name in ('label_point', 'capture_geometry', 'require_private_userdir', 'living_context',
                     'require_initial', 'hud_values', 'pin_for_input', 'require_window', 'reload_key', 'fire_button'):
            self.assertEqual(function(current,name), function(original,name))

    def test_manual_qualification_recipe_pins_source_and_explicit_mode_without_changing_default_workflow(self):
        recipe = (ROOT/'.github/workflows/macos-semantic-qualification.yml').read_text()
        self.assertIn('  workflow_dispatch:', recipe)
        self.assertNotIn('  push:', recipe)
        self.assertIn("re.fullmatch('[0-9a-f]{40}', expected)", recipe)
        self.assertIn("os.environ['GITHUB_SHA'] != expected", recipe)
        self.assertIn('runs-on: macos-15', recipe)
        self.assertEqual(recipe.count('--deploy-target owned-ax'),1)
        for action in ('actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683',
                       'actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065',
                       'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02'):
            self.assertIn(action,recipe)

    def test_default_cli_and_workflow_remain_original_and_no_new_native_api_exists(self):
        self.assertEqual((ROOT/'.github/workflows/desktop-alpha.yml').read_bytes(),
                         (FIXTURES/'desktop-alpha-base.yml.txt').read_bytes())
        source = (ROOT/'scripts/macos_semantic_deploy.py').read_text()
        for forbidden in ('AXUIElementPerformAction', 'AXUIElementSetAttributeValue', 'AXIsProcessTrustedWithOptions',
                          'CGEventCreate', 'CGEventPost', 'C.CDLL'):
            self.assertNotIn(forbidden, source)
        self.assertEqual(driver.BUDGETS, {'total': 300, 'compile': 60, 'window': 30, 'focus': 5, 'menu': 60,
            'deploy': 30, 'live': 60, 'fire': 5, 'reload_start': 5, 'reload_complete': 15, 'reload_frames': 5,
            'field_menu': 10, 'return_menu': 30, 'close': 20, 'capture': 25})


if __name__ == '__main__': unittest.main()
