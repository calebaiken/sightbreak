#!/usr/bin/env python3
"""Independent synthetic pack bytes and fake-process outer acquisition controls."""
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import linux_profile_acquire as acq
import linux_profile_payload as pack
import test_linux_profile_overhead as fixture_data


def descriptor(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def project_binary(changes=None, omitted=()):
    values = {'application/run/main_scene': 'res://diagnostics/linux_profile_overhead.tscn',
              'display/window/size/viewport_width': 1280, 'display/window/size/viewport_height': 720,
              'display/window/size/window_width_override': 1280, 'display/window/size/window_height_override': 720,
              'rendering/renderer/rendering_method': 'gl_compatibility',
              'rendering/renderer/rendering_method.mobile': 'gl_compatibility',
              'rendering/anti_aliasing/quality/msaa_3d': 1,
              'rendering/driver/threads/thread_model': 1, 'debug/settings/stdout/print_gpu_profile': False,
              'editor/export/convert_text_resources_to_binary': False}
    values.update(changes or {})
    for key in omitted:
        del values[key]
    result = b'ECFG' + struct.pack('<I', len(values))
    for key, value in values.items():
        key = key.encode()
        if type(value) is bool:
            encoded = struct.pack('<II', 1, int(value))
        elif type(value) is int:
            encoded = struct.pack('<Ii', 2, value)
        else:
            text = value.encode()
            encoded = struct.pack('<II', 4, len(text)) + text + bytes((-len(text)) % 4)
        result += struct.pack('<I', len(key)) + key + struct.pack('<I', len(encoded)) + encoded
    return result


def uid_binary(entries):
    data = struct.pack('<I', len(entries))
    for key, value in entries.items():
        raw = key.encode()
        data += struct.pack('<QI', value, len(raw)) + raw
    return data


def minimal_template():
    """Hand-built ELF64: null/string/pck sections and one bounded load segment."""
    data = bytearray(512)
    data[:16] = b'\x7fELF\x02\x01\x01' + bytes(9)
    struct.pack_into('<HHIQQQI6H', data, 16, 2, 62, 1, 0, 64, 128, 0, 64, 56, 1, 64, 3, 1)
    struct.pack_into('<II6Q', data, 64, 1, 5, 0, 0, 0, 512, 512, 8)
    names = b'\0.shstrtab\0pck\0'
    data[340:340 + len(names)] = names
    struct.pack_into('<II4Q2I2Q', data, 192, 1, 3, 0, 0, 340, len(names), 0, 0, 1, 0)
    struct.pack_into('<II4Q2I2Q', data, 256, 11, 1, 2, 0, 400, 8, 0, 0, 8, 0)
    return bytes(data)


def make_payload(template, resources):
    """Manual directory/data builder, independent of production pack inspector."""
    data, entries = bytearray(104), []
    for name, raw in sorted(resources.items()):
        data.extend(bytes((-len(data)) % 8))
        entries.append((name, len(data) - 104, raw))
        data.extend(raw)
    directory = len(data)
    data.extend(struct.pack('<I', len(entries)))
    for name, offset, raw in entries:
        name = name.encode()
        name += bytes((-len(name)) % 4)
        data.extend(struct.pack('<I', len(name)) + name + struct.pack('<QQ16sI', offset, len(raw), hashlib.md5(raw).digest(), 0))
    struct.pack_into('<6I2Q', data, 0, 0x43504447, 4, 4, 7, 2, 2, 104, directory)
    prefix = bytearray(template)
    struct.pack_into('<QQ', prefix, 256 + 24, len(template), len(data) + 12)
    return bytes(prefix + data + struct.pack('<QI', len(data), 0x43504447))


def manual_stage(root):
    stage = root / 'project'
    stage.mkdir()
    script = b'extends Node\n# synthetic fixed-view control, never executed\n'
    scene = b'[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://diagnostics/linux_profile_overhead.gd" id="1"]\n[node name="Synthetic" type="Node"]\nscript = ExtResource("1")\n'
    source = {'commit': 'c' * 40, 'fixture_sha256': descriptor(script)['sha256'], 'scene_sha256': descriptor(scene)['sha256']}
    base = {'assets/a.png': descriptor(b'original texture')['sha256']}
    ledger = (json.dumps({'source': source, 'content': base}) + '\n').encode()
    original_import = b'[remap]\nimporter="texture"\ntype="CompressedTexture2D"\nuid="uid://synthetic"\npath="res://.godot/imported/a.ctex"\nmetadata={\n"vram_texture": false\n}\n[deps]\nsource_file="res://assets/a.png"\ndest_files=["res://.godot/imported/a.ctex"]\n[params]\ncompress/mode=0\n'
    files = {'diagnostics/linux_profile_overhead.gd': script, 'diagnostics/linux_profile_overhead.tscn': scene,
             'diagnostics/source_ledger.json': ledger, 'assets/a.png': b'original texture', 'assets/a.png.import': original_import,
             'project.godot': b'''[application]
run/main_scene="res://diagnostics/linux_profile_overhead.tscn"
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/size/window_width_override=1280
window/size/window_height_override=720
[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
anti_aliasing/quality/msaa_3d=1
driver/threads/thread_model=1
[debug]
settings/stdout/print_gpu_profile=false
[editor]
export/convert_text_resources_to_binary=false
'''}
    record = {'source': source, 'base_files': base, 'files': {name: descriptor(raw) for name, raw in files.items()}}
    resources = {name: raw for name, raw in files.items() if name.startswith('diagnostics/')}
    resources.update({'assets/a.png.import': b'[remap]\nimporter="texture"\ntype="CompressedTexture2D"\nuid="uid://synthetic"\npath="res://.godot/imported/a.ctex"\nmetadata={\n"vram_texture": false\n}\n',
                      '.godot/imported/a.ctex': b'fresh imported cache bytes', 'project.binary': project_binary(),
                      '.godot/global_script_class_cache.cfg': b'list=[]\n',
                      '.godot/uid_cache.bin': uid_binary({'res://diagnostics/linux_profile_overhead.gd': 42})})
    for name, raw in {**files, **{name: value for name, value in resources.items() if name.startswith('.godot/')}}.items():
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    template = root / 'template'
    template.write_bytes(minimal_template())
    executable = root / 'export'
    executable.write_bytes(make_payload(template.read_bytes(), resources))
    return stage, record, resources, template, executable


class PayloadTests(unittest.TestCase):
    def test_handbuilt_text_payload_binds_every_source_cache_and_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = manual_stage(Path(temporary))
            result, raw = pack.inspect(executable, template, stage, record)
            self.assertEqual(result['PCK_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual({row['path'] for row in result['resources']}, set(resources))
            self.assertEqual(result['uid_cache'], {'res://diagnostics/linux_profile_overhead.gd': 42})
            self.assertEqual(result['project']['editor/export/convert_text_resources_to_binary'], False)

    def test_rebuilt_valid_md5_packs_with_wrong_source_ledger_cache_or_paths_reject(self):
        def mutate(resources, name):
            if name == 'fixture': resources['diagnostics/linux_profile_overhead.gd'] += b'changed'
            if name == 'scene': resources['diagnostics/linux_profile_overhead.tscn'] += b'changed'
            if name == 'ledger': resources['diagnostics/source_ledger.json'] = b'{}'
            if name == 'cache': resources['.godot/imported/a.ctex'] += b'changed'
            if name == 'remap': resources['assets/a.png.import'] = resources['assets/a.png.import'].replace(b'a.ctex', b'other.ctex')
            if name == 'UID': resources['.godot/uid_cache.bin'] = uid_binary({'res://diagnostics/linux_profile_overhead.gd': 43})
            if name == 'class': resources['.godot/global_script_class_cache.cfg'] = b'list=[{"path":"res://other.gd","class":"Other","language":"GDScript"}]'
            if name == 'settings': resources['project.binary'] = project_binary({'display/window/size/viewport_width': 640})
            if name == 'main': resources['project.binary'] = project_binary({'application/run/main_scene': 'res://main.tscn'})
            if name == 'bytecode': resources['diagnostics/linux_profile_overhead.gdc'] = resources.pop('diagnostics/linux_profile_overhead.gd')
            if name == 'missing': resources.pop('diagnostics/source_ledger.json')
            if name == 'tests': resources['tests/f.gd'] = b'extends Node'
            if name == 'escape': resources['../f.gd'] = b'extends Node'
            if name == 'extra': resources['unexpected.json'] = b'{}'
        for name in ('fixture', 'scene', 'ledger', 'cache', 'remap', 'UID', 'class', 'settings', 'main', 'bytecode', 'missing', 'tests', 'escape', 'extra'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = manual_stage(Path(temporary))
                mutate(resources, name)
                executable.write_bytes(make_payload(template.read_bytes(), resources))
                with self.assertRaises((acq.accepted.Invalid, KeyError)):
                    pack.inspect(executable, template, stage, record)

    def test_headers_prefix_directory_md5_trailer_and_overlap_reject(self):
        for name in ('ELF', 'machine', 'prefix', 'trailer', 'version', 'reserved', 'directory', 'MD5', 'overlap'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                stage, record, resources, template, executable = manual_stage(Path(temporary))
                data = bytearray(executable.read_bytes())
                if name == 'ELF': data[4] = 1
                if name == 'machine': struct.pack_into('<H', data, 18, 183)
                if name == 'prefix': data[420] = 1
                if name == 'trailer': data[-1] ^= 1
                if name == 'version': struct.pack_into('<I', data, 512 + 16, 3)
                if name == 'reserved': data[512 + 40] = 1
                if name == 'directory': struct.pack_into('<Q', data, 512 + 32, len(data) * 2)
                if name == 'MD5': data[512 + 104] ^= 1
                if name == 'overlap':
                    directory = struct.unpack_from('<Q', data, 512 + 32)[0] + 512
                    n = struct.unpack_from('<I', data, directory + 4)[0]
                    first = directory + 8 + n
                    second = first + 36
                    second_name = struct.unpack_from('<I', data, second)[0]
                    # Both entries have valid MD5s and in-range identical data;
                    # the independent overlap check must reject this alias.
                    data[second + 4 + second_name:second + 4 + second_name + 36] = data[first:first + 36]
                executable.write_bytes(data)
                with self.assertRaises((acq.accepted.Invalid, struct.error)):
                    pack.inspect(executable, template, stage, record)

    def test_stage_and_api_json_cannot_replace_frozen_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage, record, resources, template, executable = manual_stage(Path(temporary))
            resources['diagnostics/linux_profile_overhead.gd'] += b'mutated together'
            (stage / 'diagnostics/linux_profile_overhead.gd').write_bytes(resources['diagnostics/linux_profile_overhead.gd'])
            executable.write_bytes(make_payload(template.read_bytes(), resources))
            with self.assertRaisesRegex(acq.accepted.Invalid, 'frozen inventory'):
                pack.inspect(executable, template, stage, record)
        for text in ('NaN', 'Infinity', '-Infinity', '1e999'):
            with self.assertRaises(acq.accepted.Invalid):
                acq.accepted.strict_json('{"clock":' + text + '}')


class BudgetTests(unittest.TestCase):
    def run_phase(self, mode, value=14.999):
        clock = {'now': 0.0}
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary)
            stack.enter_context(patch.object(acq, 'OUTPUT', root))
            stack.enter_context(patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']))
            def timer(_kind, seconds):
                if seconds == 0 and mode == 'alarm_restore': clock['now'] = 15.001
            stack.enter_context(patch.object(acq.signal, 'setitimer', side_effect=timer))
            budget = acq.Budget({})
            original_write, original_read, original_digest = acq.write, acq.read_json, acq.digest
            def operation():
                clock['now'] = value
                return {'synthetic': True}
            def write(path, value):
                original_write(path, value)
                if mode == 'publication': clock['now'] = 15.001
            def read(path):
                value = original_read(path)
                if mode == 'reread': clock['now'] = 15.001
                return value
            def digest(path):
                value = original_digest(path)
                if mode == 'hash': clock['now'] = 15.001
                return value
            stack.enter_context(patch.object(acq, 'write', side_effect=write))
            stack.enter_context(patch.object(acq, 'read_json', side_effect=read))
            stack.enter_context(patch.object(acq, 'digest', side_effect=digest))
            if mode == 'valid':
                self.assertEqual(budget.phase('version', operation), {'synthetic': True})
                self.assertTrue(budget.receipt['phases'][0]['passed'])
            else:
                with self.assertRaises(TimeoutError): budget.phase('version', operation)
                self.assertFalse(budget.receipt['phases'][0]['passed'])

    def test_positive_original_phase_boundary_and_late_publication_read_hash(self):
        self.run_phase('valid')
        self.run_phase('complete', 15)
        self.run_phase('complete', 15.001)
        for mode in ('publication', 'reread', 'hash', 'alarm_restore'):
            with self.subTest(mode=mode): self.run_phase(mode)

    def test_whole_cap_is_not_restarted_and_original_active_alarm_rejects(self):
        clock = {'now': 0.0}
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)), \
                patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']), patch.object(acq.signal, 'setitimer') as timer:
            budget = acq.Budget({})
            clock['now'] = 1319
            def operation():
                self.assertEqual(budget.phase_until, 1320)
                clock['now'] = 1320
            with self.assertRaises(TimeoutError): budget.phase('version', operation)
            timer.assert_any_call(signal.ITIMER_REAL, 1)
        with patch.object(acq.signal, 'getitimer', return_value=(9, 0)), patch.object(acq.signal, 'setitimer') as timer:
            budget = acq.Budget({})
            with self.assertRaisesRegex(acq.accepted.Invalid, 'Existing'):
                with budget.armed(budget.until, 'collision'): pass
            timer.assert_not_called()


class OwnershipAndCommandTests(unittest.TestCase):
    def command(self, mode):
        clock, registry = {'now': 0.0}, {}
        class Process:
            pid, returncode = 44001, None
            def poll(self):
                if mode == 'timeout': return None
                self.returncode = 0
                registry.pop(self.pid, None)
                if mode == 'late_completed': clock['now'] = 15.001
                return self.returncode
            def wait(self, timeout):
                return self.returncode
        process = Process()
        def launch(argv, **kwargs):
            registry[44001] = {'pid': 44001, 'start_ticks': 100, 'ppid': 1, 'pgid': 44001, 'sid': 44001, 'state': 'S'}
            if mode == 'left_child':
                registry[44002] = {'pid': 44002, 'start_ticks': 101, 'ppid': 44001, 'pgid': 44001, 'sid': 44001, 'state': 'S'}
            kwargs['stdout'].write(b'4.7.2.stable.official.ed1daf0bf\n')
            kwargs['stderr'].write(b'WARNING: synthetic zero-exit warning\n' if mode == 'warning' else b'')
            return process
        def sleep(value):
            clock['now'] += value
            if mode == 'timeout': clock['now'] = max(clock['now'], 16)
        def send(row, signum):
            if mode != 'left_child':
                registry.pop(row['pid'], None)
                process.returncode = -int(signum)
            return True
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            stack.enter_context(patch.object(acq, 'OUTPUT', Path(temporary)))
            stack.enter_context(patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']))
            stack.enter_context(patch.object(acq.time, 'sleep', side_effect=sleep))
            stack.enter_context(patch.object(acq.signal, 'setitimer'))
            stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=launch))
            stack.enter_context(patch.object(acq, 'process_scan', side_effect=lambda: deepcopy(registry)))
            stack.enter_context(patch.object(acq, 'signal_identity', side_effect=send))
            controller = acq.Acquisition('c' * 40)
            try:
                controller.budget.phase('version', lambda: controller.command('version', ['/fake-engine', '--version'], temporary))
            except (acq.accepted.Invalid, TimeoutError) as error:
                controller.receipt['error'] = str(error)
            return controller.receipt

    def test_natural_completed_child_passes_and_zero_exit_warning_rejects(self):
        positive = self.command('valid')
        self.assertTrue(positive['phases'][0]['passed'])
        self.assertTrue(positive['commands'][0]['cleanup']['complete'])
        self.assertFalse(positive['commands'][0]['cleanup']['forced'])
        negative = self.command('warning')
        self.assertFalse(negative['phases'][0]['passed'])
        self.assertIn('Strict native log', negative['error'])
        self.assertEqual(negative['commands'][0]['exit_code'], 0)

    def test_deadline_completed_child_timeout_and_remaining_session_reject(self):
        for mode in ('late_completed', 'timeout', 'left_child'):
            with self.subTest(mode=mode):
                result = self.command(mode)
                self.assertFalse(result['phases'][0]['passed'])
                self.assertEqual(len(result['commands']), 1)
                if mode == 'left_child':
                    self.assertFalse(result['commands'][0]['cleanup']['complete'])
                else:
                    self.assertTrue(result['commands'][0]['cleanup']['complete'])

    def test_pidfd_revalidation_does_not_signal_reused_pid(self):
        row = {'pid': 44001, 'start_ticks': 100}
        for reused in (False, True):
            with patch.object(acq, 'process_scan', side_effect=[{44001: row}, {44001: {**row, 'start_ticks': 101 if reused else 100}}]), \
                    patch.object(acq.os, 'pidfd_open', return_value=77), patch.object(acq.os, 'close') as close, \
                    patch.object(acq.signal, 'pidfd_send_signal') as send:
                self.assertEqual(acq.signal_identity(row, signal.SIGTERM), not reused)
                self.assertEqual(send.call_count, 0 if reused else 1)
                close.assert_called_once_with(77)

    def test_observed_escaped_child_is_retained_but_unrelated_reused_identity_is_not_killed(self):
        for reuse in (False, True):
            registry = {10: {'pid': 10, 'start_ticks': 1, 'ppid': 1, 'pgid': 10, 'sid': 10, 'state': 'S'},
                        11: {'pid': 11, 'start_ticks': 2, 'ppid': 10, 'pgid': 10, 'sid': 10, 'state': 'S'}}
            class Process:
                pid, returncode = 10, 0
                def poll(self): registry.pop(10, None); return 0
            clock = {'now': 0}
            def send(row, _signal): registry.pop(row['pid'], None); return True
            with patch.object(acq, 'process_scan', side_effect=lambda: deepcopy(registry)), \
                    patch.object(acq, 'signal_identity', side_effect=send) as kill, \
                    patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']), \
                    patch.object(acq.time, 'sleep', side_effect=lambda value: clock.update(now=clock['now'] + value)):
                owner = acq.Ownership(Process(), {})
                registry[11].update(ppid=1, pgid=77, sid=77, start_ticks=99 if reuse else 2)
                result = owner.cleanup()
                self.assertTrue(result['complete'])
                self.assertEqual(kill.call_count, 0 if reuse else 1)


class FlowTests(unittest.TestCase):
    def flow(self, failure=None):
        calls = []
        class Flow(acq.Acquisition):
            def point(self, name, value=None):
                calls.append(name)
                if name == failure: raise acq.accepted.Invalid('synthetic ' + name)
                return value or {}
            def preflight(self):
                self.python_path, self.engine = '/fake-python', Path('/fake-editor')
                return self.point('preflight')
            def stage(self):
                self.project = acq.OUTPUT / 'project'; self.project.mkdir()
                return self.point('stage')
            def command(self, label, argv, cwd, environment=None):
                self.point(label)
                calls.append(list(argv))
                return acq.toolchain.ENGINE if label == 'version' else ''
            def inventory_stage(self, label): return self.point(label + '-inventory')
            def inspect_artifact(self): return self.point('artifact')
            def seal_payload(self): return self.point('seal')
            def run_block(self): return self.point('block')
            def finalize(self): return self.point('finalize')
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)), \
                patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('Pure policy test cannot spawn')):
            controller = Flow('c' * 40)
            try: controller.execute()
            except acq.accepted.Invalid as error: controller.receipt['error'] = str(error)
            return calls, controller.receipt

    def test_fixed_one_pass_order_and_each_failure_stops_before_later_phase(self):
        names = ['preflight', 'stage', 'version', 'import', 'import-inventory', 'export', 'export-inventory', 'artifact', 'seal', 'block', 'finalize']
        calls, receipt = self.flow()
        self.assertTrue(receipt['passed'])
        self.assertEqual([value for value in calls if isinstance(value, str)], names)
        commands = [value for value in calls if isinstance(value, list)]
        self.assertTrue(all(value[:3] == ['/usr/bin/taskset', '-c', '0,1'] for value in commands))
        self.assertEqual(commands[1][-2:], ['--import', '--quit'])
        self.assertIn('--export-debug', commands[2])
        for index, name in enumerate(names):
            with self.subTest(failure=name):
                calls, receipt = self.flow(name)
                self.assertFalse(receipt['passed'])
                self.assertEqual([value for value in calls if isinstance(value, str)], names[:index + 1])

    def test_strict_matcher_includes_warnings_leaks_indented_and_zero_exit_patterns(self):
        for line in ('WARNING: x', '  ERROR: x', 'SCRIPT ERROR: x', 'Parse Error: x', 'ObjectDB instances leaked at exit',
                     'Leaked instance: x', 'resources still in use at exit', 'orphaned node x'):
            self.assertTrue(acq.strict_log(line), line)
        self.assertFalse(acq.strict_log('Godot Engine v4.7.2\nGPU PROFILE (total 20ms):\n\t-Render Opaque Pass: 18ms'))

    def test_unexpected_uid_is_retained_before_inventory_rejection(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
            controller = acq.Acquisition('c' * 40)
            controller.project = Path(temporary) / 'project'; controller.project.mkdir()
            (controller.project / 'original.gd').write_text('extends Node')
            controller.stage_record = {'files': acq.accepted.inventory(controller.project)}
            (controller.project / 'unexpected.gd.uid').write_text('uid://synthetic')
            with self.assertRaisesRegex(acq.accepted.Invalid, 'source/UID changed'):
                controller.inventory_stage('import')
            self.assertEqual((Path(temporary) / 'import-generated-uids/unexpected.gd.uid').read_text(), 'uid://synthetic')
            self.assertIn('unexpected.gd.uid', acq.read_json(Path(temporary) / 'import-complete-stage.json'))

    def test_nested_cache_directory_cannot_hide_unexpected_stage_source(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
            controller = acq.Acquisition('c' * 40)
            controller.project = Path(temporary) / 'project'; controller.project.mkdir()
            controller.stage_record = {'files': {}}
            hidden = controller.project / 'unexpected/.godot/hidden.gd'; hidden.parent.mkdir(parents=True)
            hidden.write_text('extends Node')
            with self.assertRaisesRegex(acq.accepted.Invalid, 'source/UID changed'):
                controller.inventory_stage('import')


class SourceAndPreparationTests(unittest.TestCase):
    def test_stage_inputs_cannot_change_between_original_inventory_and_amendment(self):
        for target in ('world.gd', 'project.godot'):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
                controller = acq.Acquisition('c' * 40); controller.python_path = '/fake-python'
                inventory = acq.accepted.inventory
                def command(*_args):
                    project = Path(temporary) / 'project'; project.mkdir()
                    (project / 'world.gd').write_text('extends Node\n')
                    (project / 'project.godot').write_text('[application]\nrun/main_scene="res://diagnostics/linux_profile_overhead.tscn"\n')
                    (project / 'export_presets.cfg').write_text('script_export_mode=2\n' * 5)
                    acq.write(Path(temporary) / 'project-stage.json', {'files': inventory(project), 'source': {'commit': 'c' * 40}})
                def changed_after_read(project):
                    result = inventory(project)
                    path = project / target
                    path.write_text(path.read_text() + '\n; late source change\n')
                    return result
                with patch.object(controller, 'command', side_effect=command), \
                        patch.object(acq.accepted, 'inventory', side_effect=changed_after_read):
                    with self.assertRaisesRegex(acq.accepted.Invalid, 'accepted bytes|Packaging input changed'):
                        controller.stage()

    def test_original_uid_and_other_source_bytes_are_checked_against_git_blobs(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'ROOT', Path(temporary)), \
                patch.object(acq, 'ACCEPTED', {}), patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('No process permitted')):
            root = Path(temporary); (root / 'game').mkdir()
            files = {'game/f.gd': b'extends Node\n', 'game/f.gd.uid': b'uid://original\n'}
            index = ''
            for name, raw in files.items():
                (root / name).write_bytes(raw)
                blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
                index += '100644 ' + blob + ' 0\t' + name + '\0'
            controller = acq.Acquisition('c' * 40)
            def git(*args):
                return 'c' * 40 if args[0] == 'rev-parse' else index if args[0] == 'ls-files' else ''
            with patch.object(controller, 'git', side_effect=git):
                valid = controller.sources()
                self.assertEqual(len(valid), 2)
                (root / 'game/f.gd.uid').write_text('uid://changed')
                with self.assertRaisesRegex(acq.accepted.Invalid, 'Git blob'):
                    controller.sources()

    def test_real_stage_amendment_changes_only_external_packaging_and_retains_original(self):
        preset = (acq.ROOT / 'game/export_presets.cfg').read_text()
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
            controller = acq.Acquisition('c' * 40); controller.python_path = '/fake-python'
            def stage_command(label, argv, cwd):
                self.assertEqual(label, 'stage')
                project = Path(temporary) / 'project'; project.mkdir()
                (project / 'project.godot').write_text('[application]\nrun/main_scene="res://diagnostics/linux_profile_overhead.tscn"\n[rendering]\ndriver/threads/thread_model=1\n[debug]\nsettings/stdout/print_gpu_profile=false\n')
                (project / 'export_presets.cfg').write_text(preset)
                record = {'files': acq.accepted.inventory(project), 'source': {'commit': 'c' * 40}}
                acq.write(Path(temporary) / 'project-stage.json', record)
            with patch.object(controller, 'command', side_effect=stage_command):
                result = controller.stage()
            original = acq.read_json(Path(temporary) / 'project-stage.json')
            self.assertNotEqual(original['files'], result['files'])
            text = (controller.project / 'export_presets.cfg').read_text()
            self.assertEqual(text.count('script_export_mode=0'), 1)
            self.assertEqual(text.count('script_export_mode=2'), 4)
            self.assertIn('export/convert_text_resources_to_binary=false', (controller.project / 'project.godot').read_text())
            self.assertEqual(acq.read_json(Path(temporary) / 'diagnostic-packaging-amendment.json')['before']['export_presets.cfg'], preset)
        self.assertEqual((acq.ROOT / 'game/export_presets.cfg').read_text(), preset)

    def test_official_archive_members_are_compared_to_installed_bytes(self):
        for mode in ('valid', 'installed_mismatch', 'archive_mismatch'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
                root = Path(temporary); install = root / 'tools'; install.mkdir(); templates = root / 'templates'; templates.mkdir()
                editor = install / 'editor'; editor.write_bytes(b'synthetic editor, never executed')
                members = {'version.txt': b'4.7.2.stable\n', 'linux_debug.x86_64': b'synthetic debug', 'linux_release.x86_64': b'synthetic release'}
                for name, raw in members.items(): (templates / name).write_bytes(raw)
                with zipfile.ZipFile(install / 'godot.zip', 'w') as bundle: bundle.writestr('Godot_v4.7.2-stable_linux.x86_64', editor.read_bytes())
                with zipfile.ZipFile(install / 'templates.tpz', 'w') as bundle:
                    for name, raw in members.items(): bundle.writestr('templates/' + name, raw)
                editor_sha = hashlib.sha512((install / 'godot.zip').read_bytes()).hexdigest()
                template_sha = hashlib.sha512((install / 'templates.tpz').read_bytes()).hexdigest()
                if mode == 'installed_mismatch': editor.write_bytes(b'wrong installed editor')
                if mode == 'archive_mismatch':
                    with (install / 'templates.tpz').open('ab') as stream: stream.write(b'changed archive')
                controller = acq.Acquisition('c' * 40); controller.engine = editor; controller.templates = templates
                controller.pins = {'tools': [{'path': str(path), **descriptor(path.read_bytes())} for path in [editor, *install.glob('*.zip'), install / 'templates.tpz', *templates.iterdir()]]}
                stack.enter_context(patch.object(acq, 'INSTALL', install))
                stack.enter_context(patch.object(acq.toolchain, 'EDITORS', {'linux': ('linux', 'editor', editor_sha)}))
                stack.enter_context(patch.object(acq.toolchain, 'TEMPLATES_SHA512', template_sha))
                stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('No process permitted')))
                if mode == 'valid': self.assertEqual(len(controller.verify_tools()), 4)
                else:
                    with self.assertRaisesRegex(acq.accepted.Invalid, 'Installed member|SHA-512'):
                        controller.verify_tools()

    def test_real_seal_gate_does_not_substitute_for_independent_payload_binding(self):
        for bad in (False, True):
            with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)):
                controller = acq.Acquisition('c' * 40); controller.python_path = '/fake-python'; controller.executable = Path(temporary) / 'ELF'
                controller.stage_record = {'synthetic': True}
                acq.write(Path(temporary) / 'diagnostic-stage.json', controller.stage_record)
                controller.receipt['independent_payload'] = {'ELF_sha256': 'elf', 'ledger_sha256': 'ledger'}
                def command(*args): acq.write(Path(temporary) / 'seal.json', {
                    'payload_sha256': 'wrong' if bad else 'elf', 'source_ledger_sha256': 'ledger',
                    'stage_record': str(Path(temporary) / 'diagnostic-stage.json'),
                    'stage_sha256': acq.digest(Path(temporary) / 'diagnostic-stage.json')})
                with patch.object(controller, 'command', side_effect=command):
                    if bad:
                        with self.assertRaisesRegex(acq.accepted.Invalid, 'independent payload'): controller.seal_payload()
                    else: self.assertEqual(controller.seal_payload()['payload_sha256'], 'elf')


class MainPublicationTests(unittest.TestCase):
    def execute(self, mode):
        clock, called = {'now': 0.0}, []
        original_write, original_read = acq.write, acq.read_json
        original_class = acq.Acquisition
        class Controller(original_class):
            def execute(self):
                called.append('execute')
                if mode == 'preparation_failure':
                    self.project = acq.OUTPUT / 'project'; self.project.mkdir()
                    (self.project / 'fixture.gd.uid').write_text('uid://retained')
                    raise acq.accepted.Invalid('synthetic preparation failure')
                self.final_accept_until = 61
                self.receipt['phases'] = [{'name': 'finalize', 'deadline_monotonic': 61, 'passed': True}]
                self.receipt['passed'] = True
                clock['now'] = 60.999
        def write(path, value):
            original_write(path, value)
            if Path(path).name == 'overall.json' and value['passed'] and mode == 'late_overall_write': clock['now'] = 61.001
            if Path(path).name == 'outputs.json' and mode == 'late_manifest_write': clock['now'] = 61.001
        def read(path):
            value = original_read(path)
            if Path(path).name == 'overall.json' and value['passed'] and mode == 'late_overall_read': clock['now'] = 61.001
            return value
        def printed(*_args, **_kwargs):
            if mode == 'late_stdout': clock['now'] = 61.001
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            root = Path(temporary); output = root / 'builds/attempt'
            if mode == 'existing_claim': output.mkdir(parents=True); (output / 'sentinel').write_text('preserve')
            for key, value in [('ROOT', root), ('OUTPUT', output), ('LANE_LOCK', root / 'lane.lock'), ('ACQUISITION_LOCK', root / 'acquisition.lock'), ('Acquisition', Controller)]:
                stack.enter_context(patch.object(acq, key, value))
            stack.enter_context(patch.object(acq.time, 'monotonic', side_effect=lambda: clock['now']))
            def timer(_kind, seconds):
                if seconds == 0 and called and mode == 'late_alarm_restore': clock['now'] = 61.001
            stack.enter_context(patch.object(acq.signal, 'setitimer', side_effect=timer))
            stack.enter_context(patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')))
            stack.enter_context(patch.object(acq, 'write', side_effect=write))
            stack.enter_context(patch.object(acq, 'read_json', side_effect=read))
            stack.enter_context(patch('sys.argv', ['linux_profile_acquire.py', '--execute-frozen-source', 'c' * 40]))
            stack.enter_context(patch('builtins.print', side_effect=printed))
            old_signals = {number: signal.getsignal(number) for number in (signal.SIGTERM, signal.SIGINT)}
            try: code = acq.main()
            finally:
                for number, handler in old_signals.items(): signal.signal(number, handler)
            if mode == 'existing_claim':
                self.assertEqual(called, []); self.assertEqual((output / 'sentinel').read_text(), 'preserve')
                self.assertEqual(list(output.iterdir()), [output / 'sentinel'])
                return code, None
            receipt = original_read(output / 'overall.json')
            if mode == 'preparation_failure':
                self.assertEqual((output / 'failed-preparation-generated-uids/fixture.gd.uid').read_text(), 'uid://retained')
            if mode.startswith('late_') and mode != 'late_manifest_write':
                self.assertEqual(code, 1, 'A late finalization must not return success')
                self.assertTrue((output / 'rejected-overall-publication.json').is_file())
            return code, receipt

    def test_main_positive_final_boundary_and_all_late_finalization_paths_reject(self):
        code, receipt = self.execute('valid')
        self.assertEqual(code, 0); self.assertTrue(receipt['passed'])
        for mode in ('late_manifest_write', 'late_overall_write', 'late_overall_read', 'late_stdout', 'late_alarm_restore', 'preparation_failure', 'existing_claim'):
            with self.subTest(mode=mode):
                code, receipt = self.execute(mode)
                self.assertEqual(code, 1)
                if receipt: self.assertFalse(receipt['passed'])


class BlockBindingTests(unittest.TestCase):
    def execute(self, mode):
        with tempfile.TemporaryDirectory() as temporary, patch.object(acq, 'OUTPUT', Path(temporary)), \
                patch.object(acq.subprocess, 'Popen', side_effect=AssertionError('No native process permitted')):
            root = Path(temporary)
            controller = acq.Acquisition('c' * 40)
            controller.python_path, controller.xvfb, controller.display = '/fake-python', '/fake-xvfb', ':99127'
            controller.executable = root / 'ELF'; controller.executable.write_bytes(b'placeholder, never executed')
            controller.seal = {'source': {'commit': 'c' * 40}, 'payload_sha256': acq.digest(controller.executable)}
            acq.write(root / 'seal.json', controller.seal)
            controller.receipt['seal_sha256'] = acq.digest(root / 'seal.json')
            expected = fixture_data.manual_expected(controller.seal['payload_sha256'], str(controller.executable))
            expected.update(source=controller.seal['source'], display=':99127', cpus=[0, 1],
                            seal_sha256='wrong' if mode == 'seal' else controller.receipt['seal_sha256'])
            block_root = root / 'native-block'; block_root.mkdir()
            proof = b'identical synthetic PNG stand-in, never rendered'
            rows = []
            for index in range(4):
                row = fixture_data.manual_record(index, controller.seal['payload_sha256'])
                directory = block_root / f'{index + 1:02d}-' / ('on' if index in (1, 2) else 'off')
                if mode == 'escaped' and index == 0: directory = root / 'outside-registered-condition'
                directory.mkdir(parents=True)
                paths = {key: str(directory / 'state' / key) for key in ('data', 'config', 'cache', 'mesa')}
                row.update(output=str(directory), engine_argv=acq.accepted.engine_argv(controller.executable, row['profile'], directory, row['token']),
                           seal_sha256=expected['seal_sha256'], cache_initial={'paths': paths, 'empty': True})
                row['process_argv'] = ['taskset', '-c', '0,1', *row['engine_argv']]
                row['actual_cmdline'] = deepcopy(row['engine_argv'])
                row['selected_environment'].update(DISPLAY=':99127', XDG_DATA_HOME=paths['data'], XDG_CONFIG_HOME=paths['config'],
                                                    XDG_CACHE_HOME=paths['cache'], MESA_SHADER_CACHE_DIR=paths['mesa'])
                row['actual_environment'] = deepcopy(row['selected_environment'])
                for name in ('host_begin', 'host_end'): row[name]['affinity'] = [0, 1]
                row['fixture']['png_sha256'] = hashlib.sha256(proof).hexdigest()
                if mode == 'warning' and index == 0: row['stdout'] += 'WARNING: zero-exit native warning\n'
                acq.write(directory / 'condition.json', row)
                row['publication_sha256'] = acq.digest(directory / 'condition.json')
                (directory / 'client.log').write_text(row['stdout'])
                (directory / 'proof.png').write_bytes(proof + (b'changed' if mode == 'PNG' and index == 0 else b''))
                metrics = deepcopy(row['fixture'])
                if mode == 'metrics' and index == 0: metrics['token'] = 'changed'
                acq.write(directory / 'metrics.json', metrics)
                if mode == 'condition' and index == 0:
                    (directory / 'condition.json').write_text('{}')
                rows.append(row)
            # These controls remain valid to the accepted evaluator. The new
            # outer raw-file/binding gate must independently detect the change.
            self.assertTrue(acq.accepted.evaluate(rows, expected)['comparable'])
            (block_root / 'xvfb.log').write_text('WARNING: zero-exit display warning\n' if mode == 'Xvfb' else '')
            block = {'passed': mode != 'failed', 'expected': expected, 'records': rows,
                     'xvfb_cleanup': {'pid_absent': True, 'group_absent': True}}
            acq.write(block_root / 'block.json', block)
            with patch.object(controller, 'command') as command:
                if mode == 'valid':
                    value = controller.run_block()
                    self.assertTrue(value['passed'])
                    argv = command.call_args.args[1]
                    self.assertEqual(argv[:3], ['/usr/bin/taskset', '-c', '0,1'])
                    self.assertEqual(argv[-2:], ['--cpus', '0,1'])
                else:
                    with self.assertRaises(acq.accepted.Invalid): controller.run_block()

    def test_real_outer_block_gate_accepts_bound_data_and_rejects_otherwise_valid_mutations(self):
        for mode in ('valid', 'warning', 'Xvfb', 'PNG', 'metrics', 'condition', 'escaped', 'seal', 'failed'):
            with self.subTest(mode=mode): self.execute(mode)


if __name__ == '__main__':
    unittest.main()
