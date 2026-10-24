#!/usr/bin/env python3
"""Independent synthetic C ABI fixtures; no libraries, engine or native process."""
import argparse
import copy
import ctypes as C
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
options, remaining = parser.parse_known_args()
sys.path.insert(0, str(options.root.resolve() / 'scripts'))
import probe_macos_ax as observer
import macos_ax_contract as contract
from test_macos_ax_read_only import synthetic_capture


class ABI:
    """Public AX outputs with explicit types, ownership and a controlled clock."""
    def __init__(self):
        self.now, self.counter = 10., 1000
        self.values, self.attrs, self.released, self.copies = {}, {}, [], []
        self.element_pids = {1: 12, 10: 12, 11: 12, 12: 12, 13: 12}
        self.roles = {1: 'AXApplication', 10: 'AXWindow', 11: 'AXGroup',
                      12: 'AXButton', 13: 'AXButton'}
        self.children = {1: [10], 10: [11, 12], 11: [13], 12: [], 13: []}
        self.elapsed, self.after_copy = 0., None
        self.rows = [{'owner_pid': 12, 'window_id': 34, 'onscreen': True,
                     'bounds_points_including_chrome': [40, 60, 960, 568]}]
        self.reader = observer.NativeAX.__new__(observer.NativeAX)
        reader = self.reader
        reader.pid, reader.window, reader.bounds, reader.deadline = 12, 34, [40, 60, 960, 568], 15.
        reader.refs, reader.keys, reader.calls, reader.latest_rows = [], {}, {}, []
        reader.windows = lambda _pid: copy.deepcopy(self.rows)
        reader.key = lambda name: name
        reader.cf = SimpleNamespace(
            CFGetTypeID=self.type_id, CFStringGetTypeID=lambda: 21,
            CFBooleanGetTypeID=lambda: 22, CFArrayGetTypeID=lambda: 23,
            CFStringGetLength=lambda ptr: len(self.values[ptr][1].encode('utf-16-le')) // 2,
            CFStringGetCString=self.convert, CFBooleanGetValue=lambda ptr: self.values[ptr][1],
            CFArrayGetCount=lambda ptr: len(self.values[ptr][1]),
            CFArrayGetValueAtIndex=lambda ptr, idx: self.values[ptr][1][idx],
            CFRetain=lambda ptr: ptr, CFRelease=self.released.append,
            CFEqual=lambda left, right: left == right)
        reader.ax = SimpleNamespace(
            AXUIElementGetTypeID=lambda: 7, AXUIElementSetMessagingTimeout=lambda *_: 0,
            AXUIElementGetPid=self.pid, AXUIElementCopyAttributeValue=self.copied,
            AXUIElementCreateApplication=lambda _pid: 1,
            AXUIElementGetAttributeValueCount=self.count,
            AXUIElementCopyAttributeValues=self.array,
            AXValueGetTypeID=lambda: 24, AXValueGetType=lambda ptr: self.values[ptr][1][0],
            AXValueGetValue=self.geometry)
        for element, title in ((10, 'SIGHTBREAK (SYNTHETIC)'), (13, contract.LABEL)):
            self.set(element, 'AXTitle', 'str', title)
        self.attrs[12, 'AXTitle'] = (-25212, None)
        for element in (10, 12, 13):
            self.set(element, 'AXPosition', 'geo', (1, (40, 60) if element == 10 else (100, 320)))
            self.set(element, 'AXSize', 'geo', (2, (960, 568) if element == 10 else (350, 100)))
        for element in (12, 13):
            self.set(element, 'AXEnabled', 'bool', True)
            self.attrs[element, 'AXWindow'] = (0, 10)

    def alloc(self, kind, value):
        self.counter += 1
        self.values[self.counter] = (kind, value)
        return self.counter

    def set(self, element, name, kind, value):
        ptr = self.alloc(kind, value)
        self.attrs[element, name] = (0, ptr)
        return ptr

    def type_id(self, ptr):
        return 7 if ptr in self.element_pids else {'str': 21, 'bool': 22, 'array': 23, 'geo': 24}[self.values[ptr][0]]

    def pid(self, element, output):
        output._obj.value = self.element_pids[element]
        return 0

    def copied(self, element, name, output):
        if name == 'AXRole' and (element, name) not in self.attrs:
            error, ptr = 0, self.alloc('str', self.roles[element])
        else:
            error, ptr = self.attrs[element, name]
        output._obj.value = ptr
        self.copies.append((element, name, error, ptr))
        if name == 'AXTitle':
            self.now += self.elapsed
            if self.after_copy:
                self.after_copy(self)
        return error

    def convert(self, ptr, output, capacity, _encoding):
        data = self.values[ptr][1].encode('utf-8') + b'\0'
        if len(data) > capacity:
            return False
        C.memmove(output, data, len(data))
        return True

    def count(self, element, _name, output):
        output._obj.value = len(self.children[element])
        return 0

    def array(self, element, _name, start, count, output):
        output._obj.value = self.alloc('array', self.children[element][start:start + count])
        return 0

    def geometry(self, ptr, kind, output):
        recorded, values = self.values[ptr][1]
        if kind != recorded:
            return False
        names = ('x', 'y') if kind == 1 else ('width', 'height')
        for name, value in zip(names, values):
            setattr(output._obj, name, value)
        return True

    def run(self, function):
        try:
            with patch.object(observer.time, 'monotonic', lambda: self.now):
                return function()
        finally:
            self.reader.close()

    def observation(self):
        result = dict(schema=contract.SCHEMA, nonce='a' * 32, owner_pid=12, window_id=34,
            observer_pid=999, AXIsProcessTrusted=True, complete=False, caps=copy.deepcopy(contract.CAPS),
            snapshots=[], examined_nodes=0, input_events_posted=0, permission_requests_made=0,
            coordinate_mapping=contract.MAPPING, started_monotonic=10.)
        observer.BoundedObserver(self.reader, result, clock=lambda: self.now,
            sleep=lambda elapsed: setattr(self, 'now', self.now + elapsed)).observe()
        result.update(finished_monotonic=self.now, last_owned_layer_zero_rows=self.reader.guard(),
                      api_call_counts=dict(self.reader.calls))
        return contract.validate_observation(result, synthetic_capture(), pid=12, window=34,
            bounds=self.reader.bounds, nonce='a' * 32, observer_pid=999, started=9.99,
            finished=10.3, budget=5.)


class IndependentChallenges(unittest.TestCase):
    def test_public_no_value_null_button_has_no_native_string_pointer(self):
        abi = ABI()
        self.assertEqual(abi.run(lambda: abi.reader.title(12)), '')
        self.assertEqual([row for row in abi.copies if row[1] == 'AXTitle'], [(12, 'AXTitle', -25212, None)])
        self.assertNotIn(None, abi.released)

    def test_complete_native_adapter_tree_crosses_untitled_sibling(self):
        abi = ABI()
        result = abi.run(abi.observation)
        self.assertTrue(result['unique_semantic_candidate'])
        self.assertEqual(result['button']['title'], contract.LABEL)
        self.assertFalse(result['gameplay_target_accepted'])
        self.assertEqual(sorted(abi.released), sorted(abi.reader.refs +
            [row[3] for row in abi.copies if row[3]] +
            [ptr for ptr, (kind, _) in abi.values.items() if kind == 'array'] + [1, 10, 11, 12, 13]))

    def test_error_matrix_and_contradictory_outputs_reject_and_release(self):
        for code in (-25200, -25201, -25202, -25204, -25205, -25208, -25211, -25212, -25213, -25214, 0):
            for pointer in (False, True):
                if code == -25212 and not pointer:
                    continue
                with self.subTest(error=code, pointer=pointer):
                    abi = ABI()
                    ptr = abi.alloc('str', contract.LABEL) if pointer else None
                    abi.attrs[12, 'AXTitle'] = (code, ptr)
                    if code == 0 and pointer:
                        self.assertEqual(abi.run(lambda: abi.reader.title(12)), contract.LABEL)
                    else:
                        with self.assertRaises(RuntimeError):
                            abi.run(lambda: abi.reader.title(12))
                    self.assertEqual(abi.released.count(ptr), int(bool(ptr)))

    def test_wrong_cf_type_empty_whitespace_and_counted_unicode(self):
        for kind, title, accepted in (('bool', True, False), ('str', '', True),
            ('str', '   ', True), ('str', 'DEPLOY · OFFLINE 5V5\0other', False),
            ('str', 'DEPLOY · OFFLINE 5V5\0', False), ('str', '🛰️', True)):
            with self.subTest(kind=kind, title=repr(title)):
                abi = ABI()
                abi.set(12, 'AXTitle', kind, title)
                if accepted:
                    self.assertEqual(abi.run(lambda: abi.reader.title(12)), title)
                else:
                    with self.assertRaises(RuntimeError):
                        abi.run(lambda: abi.reader.title(12))

    def test_required_titles_roles_and_non_title_values_stay_required(self):
        for element, name in ((10, 'AXTitle'), (12, 'AXRole'), (12, 'AXEnabled'),
                              (12, 'AXWindow'), (12, 'AXPosition'), (12, 'AXSize')):
            with self.subTest(element=element, name=name):
                abi = ABI()
                abi.attrs[element, name] = (-25212, None)
                with self.assertRaises(RuntimeError):
                    abi.run(lambda: abi.reader.title(element) if name == 'AXTitle'
                            else abi.reader.attribute(element, name))

    def test_sensitive_roles_never_read_titles(self):
        for role in (*contract.PRUNED_ROLES, 'AXStaticText', 'AXGroup'):
            with self.subTest(role=role):
                abi = ABI()
                abi.roles[12] = role
                with self.assertRaises(RuntimeError):
                    abi.run(lambda: abi.reader.title(12))
                self.assertFalse(any(name == 'AXTitle' for _, name, _, _ in abi.copies))

    def test_late_geometry_pid_and_changed_role_reject(self):
        changes = [lambda abi: setattr(abi, 'elapsed', .25),
            lambda abi: setattr(abi, 'elapsed', 5.001),
            lambda abi: setattr(abi, 'after_copy', lambda current: current.rows[0].update(window_id=35)),
            lambda abi: setattr(abi, 'after_copy', lambda current: current.element_pids.update({12: 13})),
            lambda abi: setattr(abi, 'after_copy', lambda current: current.roles.update({12: 'AXSecureTextField'}))]
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                abi = ABI()
                change(abi)
                with self.assertRaises((RuntimeError, TimeoutError)):
                    abi.run(lambda: abi.reader.title(12))

    def test_exact_deploy_controls_survive_untitled_auxiliary(self):
        for fault in ('missing', 'wrong_text', 'disabled', 'duplicate', 'outside', 'foreign_pid'):
            with self.subTest(fault=fault):
                abi = ABI()
                if fault == 'missing':
                    abi.attrs[13, 'AXTitle'] = (-25212, None)
                elif fault == 'wrong_text':
                    abi.set(13, 'AXTitle', 'str', 'DEPLOY · ONLINE 5V5')
                elif fault == 'disabled':
                    abi.set(13, 'AXEnabled', 'bool', False)
                elif fault == 'duplicate':
                    abi.set(12, 'AXTitle', 'str', contract.LABEL)
                elif fault == 'outside':
                    abi.set(13, 'AXPosition', 'geo', (1, (-100, -100)))
                else:
                    abi.element_pids[13] = 99
                with self.assertRaises(RuntimeError):
                    abi.run(abi.observation)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0], *remaining], verbosity=2)
