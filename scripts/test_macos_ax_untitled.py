#!/usr/bin/env python3
"""Pure untitled-button API/traversal controls; never construct native libraries."""
import argparse
import copy
import ctypes as C
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


# An explicit clean old checkout is a falsifier; no Git history is needed.
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
options, remaining = parser.parse_known_args()
sys.path.insert(0, str(options.source_root.resolve() / 'scripts'))
import probe_macos_ax as observer
import macos_ax_contract as contract
from test_macos_ax_read_only import (FakeBackend, boundary_reader, observation,
                                     synthetic_capture, validate)


def native_reader(*, error=-25212, pointer=None, role='AXButton', elapsed=0.,
                  error_attribute='AXTitle', after_copy=None):
    """Real adapter and call guards with fake C functions and counted CFStrings."""
    reader, now = boundary_reader(), [10.]
    reader.key = lambda name: name
    reader.role_value, reader.title_reads = role, 0
    reader.decoded = []
    role_pointer, title_pointer = 0xA11, 0xA22

    def copied(_element, name, output):
        if name == error_attribute:
            if name == 'AXTitle':
                reader.title_reads += 1
            output._obj.value = pointer
            now[0] += elapsed
            if after_copy:
                after_copy(reader)
            return error
        if name != 'AXRole':
            raise AssertionError('Unexpected fake attribute ' + name)
        output._obj.value = role_pointer
        return 0

    def pid(_element, output):
        output._obj.value = reader.pid
        return 0

    def text(value):
        reader.decoded.append(value)
        if value == role_pointer:
            return reader.role_value
        if value == title_pointer:
            return contract.LABEL
        raise AssertionError('NULL/unknown CFString decoded')

    def converted(value, buffer, capacity, _encoding):
        raw = text(value).encode('utf-8')
        if len(raw) + 1 > capacity:
            return False
        C.memmove(buffer, raw + b'\0', len(raw) + 1)
        return True

    reader.cf.CFStringGetTypeID = lambda: 7
    reader.cf.CFStringGetLength = lambda value: len(text(value).encode('utf-16-le')) // 2
    reader.cf.CFStringGetCString = converted
    reader.ax = SimpleNamespace(AXUIElementGetTypeID=lambda: 7,
        AXUIElementSetMessagingTimeout=lambda *_: 0,
        AXUIElementGetPid=pid, AXUIElementCopyAttributeValue=copied)
    return reader, now


class NativeUntitledControls(unittest.TestCase):
    def test_no_value_null_button_title_is_empty_without_a_native_string_read(self):
        reader, now = native_reader()
        with patch.object(observer.time, 'monotonic', lambda: now[0]):
            self.assertEqual(reader.title(1), '')
        self.assertEqual(reader.title_reads, 1)
        self.assertNotIn(None, reader.decoded)
        self.assertNotIn(0xA22, reader.decoded)
        self.assertEqual(contract.normalized_title(''), '')
        self.assertNotEqual(contract.normalized_title(''), contract.LABEL)
        reader.close()
        self.assertEqual(reader.released.count(0xA11), 2)

    def test_other_errors_success_null_and_error_pointer_remain_failures(self):
        cases = [(code, pointer) for code in
                 (-25200, -25201, -25202, -25204, -25205, -25208, -25211, -25213, -25214)
                 for pointer in (None, 0xA22)] + [(0, None), (-25212, 0xA22)]
        for error, pointer in cases:
            with self.subTest(error=error, pointer=pointer):
                reader, now = native_reader(error=error, pointer=pointer)
                with patch.object(observer.time, 'monotonic', lambda: now[0]):
                    with self.assertRaises(RuntimeError):
                        reader.title(1)
                reader.close()
                self.assertEqual(reader.released.count(0xA22), int(pointer is not None))

    def test_window_secure_and_non_title_attributes_do_not_gain_no_value_handling(self):
        for role in ('AXWindow', 'AXGroup', 'AXTextField', 'AXSecureTextField',
                     'AXSearchField', 'AXTextArea', 'AXComboBox', 'AXStaticText'):
            with self.subTest(role=role):
                reader, now = native_reader(role=role)
                with patch.object(observer.time, 'monotonic', lambda: now[0]):
                    with self.assertRaises(RuntimeError):
                        reader.title(1)
                self.assertEqual(reader.title_reads, int(role == 'AXWindow'))
                reader.close()
        for name in ('AXRole', 'AXEnabled', 'AXWindow', 'AXPosition', 'AXSize'):
            with self.subTest(attribute=name):
                reader, now = native_reader(error_attribute=name)
                with patch.object(observer.time, 'monotonic', lambda: now[0]):
                    with self.assertRaises(RuntimeError):
                        reader.attribute(1, name)
                reader.close()

    def test_no_value_after_role_change_late_return_or_geometry_change_rejects(self):
        cases = [dict(elapsed=.25), dict(elapsed=.3), dict(elapsed=5.001),
                 dict(after_copy=lambda reader: setattr(reader, 'role_value', 'AXSecureTextField')),
                 dict(after_copy=lambda reader: reader.rows.append(dict(reader.rows[0], window_id=35)))]
        for fault in cases:
            with self.subTest(fault=fault):
                reader, now = native_reader(**fault)
                with patch.object(observer.time, 'monotonic', lambda: now[0]):
                    with self.assertRaises((RuntimeError, TimeoutError)):
                        reader.title(1)
                self.assertEqual(reader.deadline, 15.)
                reader.close()
        reader, now = native_reader(pointer=0xA22, elapsed=.25)
        with patch.object(observer.time, 'monotonic', lambda: now[0]):
            with self.assertRaises(TimeoutError):
                reader.title(1)
        reader.close()
        self.assertEqual(reader.released.count(0xA22), 1)


class TraversalUntitledControls(unittest.TestCase):
    @staticmethod
    def backend():
        backend = FakeBackend()
        backend.objects[0]['children'] = [10, 11]
        backend.objects[10] = {'role': 'AXGroup', 'children': [1]}
        backend.objects[11] = {'role': 'AXButton', 'enabled': True, 'children': [12]}
        backend.objects[12] = {'role': 'AXGroup', 'children': []}
        original_title = backend.title

        def title(node):
            if node != 11:
                return original_title(node)
            backend.calls.append(('title', node))
            reader, now = native_reader()
            try:
                with patch.object(observer.time, 'monotonic', lambda: now[0]):
                    return reader.title(1)
            finally:
                reader.close()

        backend.title = title
        return backend

    def test_untitled_sibling_does_not_hide_group_deploy_or_its_own_children(self):
        backend = self.backend()
        receipt = observation(backend)
        nodes = receipt['snapshots'][0]['nodes']
        self.assertEqual([row['role'] for row in nodes[:3]], ['AXWindow', 'AXGroup', 'AXButton'])
        self.assertEqual(nodes[2]['title'], '')
        self.assertEqual(nodes[2]['normalized_title'], '')
        self.assertTrue(receipt['complete'])
        self.assertIn(('AXChildren', 11), backend.calls)
        self.assertIn(('pid', 12), backend.calls)
        result = validate(receipt)
        self.assertTrue(result['unique_semantic_candidate'])
        self.assertEqual(result['button']['title'], 'DEPLOY   ·   OFFLINE 5V5')
        self.assertFalse(result['gameplay_target_accepted'])

    def test_untitled_tree_keeps_unique_exact_enabled_and_frame_selection(self):
        for fault in ('missing', 'wrong', 'duplicate', 'disabled', 'outside'):
            with self.subTest(fault=fault):
                backend = self.backend()
                if fault == 'missing':
                    backend.objects[10]['children'] = []
                elif fault == 'wrong':
                    backend.objects[1]['title'] = 'DEPLOY · ONLINE 5V5'
                elif fault == 'duplicate':
                    backend.objects[13] = copy.deepcopy(backend.objects[1])
                    backend.objects[10]['children'].append(13)
                elif fault == 'disabled':
                    backend.objects[1]['enabled'] = False
                else:
                    backend.objects[1]['frame'] = [-100, -100, 10, 10]
                with self.assertRaises(RuntimeError):
                    validate(observation(backend))
        image = synthetic_capture()
        with self.assertRaises(RuntimeError):
            from macos_ordinary_input import label_point
            label_point(image, contract.LABEL)

    def test_later_error_preserves_partial_untitled_tree_and_rejects_collection(self):
        backend = self.backend()
        backend.objects[12]['pid'] = 13
        result = {'snapshots': [], 'examined_nodes': 0, 'complete': False}
        with self.assertRaises(RuntimeError):
            observer.BoundedObserver(backend, result, clock=backend.clock, sleep=backend.sleep).observe()
        self.assertFalse(result['complete'])
        nodes = result['snapshots'][0]['nodes']
        self.assertFalse(result['snapshots'][0]['complete'])
        self.assertEqual(nodes[2]['title'], '')
        self.assertTrue(any(row.get('normalized_title') == contract.LABEL for row in nodes))


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining])
