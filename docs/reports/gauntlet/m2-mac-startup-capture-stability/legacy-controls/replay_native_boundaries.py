#!/usr/bin/env python3
"""Independent pure ctypes-boundary falsifiers; loads no native libraries."""
import ctypes as C
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(SOURCE / 'scripts'))
import probe_macos_ax as observer
from test_macos_ax_read_only import FakeBackend, observation, validate


def reader():
    value = observer.NativeAX.__new__(observer.NativeAX)
    value.pid, value.window, value.bounds = 12, 34, [40, 60, 960, 568]
    value.calls, value.refs, value.keys, value.latest_rows = {}, [], {}, []
    value.deadline = 15.0
    value.released = []
    value.cf = SimpleNamespace(CFRelease=value.released.append)
    value.windows = lambda _pid: [{'owner_pid': 12, 'window_id': 34, 'onscreen': True,
        'bounds_points_including_chrome': [40, 60, 960, 568]}]
    return value


def late_guard(value, failure_call):
    calls = []
    def guard():
        calls.append(1)
        if len(calls) == failure_call:
            raise TimeoutError('Synthetic post-call deadline/window rejection')
        return value.latest_rows
    value.guard = guard


class NativeBoundaryFalsifiers(unittest.TestCase):
    def test_positive_native_call_below_point_two_five_and_owned_attribute_cleanup(self):
        value, now = reader(), [10.0]
        def timely(*_arguments):
            now[0] += 0.249
            return 0
        value.ax = SimpleNamespace(AXUIElementGetPid=timely)
        with patch.object(observer.time, 'monotonic', lambda: now[0]):
            self.assertEqual(value.call('AXUIElementGetPid', 1, None), 0)
        value.check_element, value.key = lambda _element: None, lambda name: name
        value.guard = lambda: []
        def copied(_element, _key, output):
            output._obj.value = 0xA22
            return 0
        value.ax = SimpleNamespace(AXUIElementCopyAttributeValue=copied)
        self.assertEqual(value.attribute(1, 'AXRole'), 0xA22)
        value.close()
        self.assertEqual(value.released, [0xA22])

    def test_native_call_over_point_two_five_seconds_must_reject_under_whole_cap(self):
        value, now = reader(), [10.0]
        def slow(*_arguments):
            now[0] += 0.300
            return 0
        value.ax = SimpleNamespace(AXUIElementGetPid=slow)
        with patch.object(observer.time, 'monotonic', lambda: now[0]):
            with self.assertRaises(TimeoutError):
                value.call('AXUIElementGetPid', 1, None)

    def test_created_application_released_when_post_call_guard_rejects(self):
        value = reader()
        value.ax = SimpleNamespace(AXUIElementCreateApplication=lambda _pid: 0xA11)
        late_guard(value, 2)
        with self.assertRaises(TimeoutError):
            value.application()
        value.close()
        self.assertEqual(value.released, [0xA11], 'Create-owned reference escaped both hold and CFRelease')

    def test_copied_attribute_released_when_post_call_guard_rejects(self):
        value = reader()
        value.check_element, value.key = lambda _element: None, lambda name: name
        def copied(_element, _key, output):
            output._obj.value = 0xA22
            return 0
        value.ax = SimpleNamespace(AXUIElementCopyAttributeValue=copied)
        late_guard(value, 2)
        with self.assertRaises(TimeoutError):
            value.attribute(1, 'AXRole')
        value.close()
        self.assertEqual(value.released, [0xA22], 'Copy-owned attribute escaped error cleanup')

    def test_copied_array_released_when_post_call_guard_rejects(self):
        value = reader()
        value.check_element, value.key = lambda _element: None, lambda name: name
        def count(_element, _key, output):
            output._obj.value = 1
            return 0
        def copied(_element, _key, _start, _count, output):
            output._obj.value = 0xA33
            return 0
        value.ax = SimpleNamespace(AXUIElementGetAttributeValueCount=count,
                                  AXUIElementCopyAttributeValues=copied)
        late_guard(value, 4)
        with self.assertRaises(TimeoutError):
            value.elements(1, 'AXChildren', 4)
        value.close()
        self.assertEqual(value.released, [0xA33], 'Copy-owned array escaped error cleanup')

    def test_embedded_nul_native_title_must_not_become_exact_deploy(self):
        value = reader()
        title = 'DEPLOY · OFFLINE 5V5\x00DIFFERENT TITLE'
        raw = title.encode('utf-8') + b'\x00'
        value.role, value.attribute = lambda _element: 'AXButton', lambda *_args: 1
        def encode(_pointer, buffer, _capacity, _encoding):
            C.memmove(buffer, raw, len(raw))
            return True
        value.cf = SimpleNamespace(CFGetTypeID=lambda _p: 7, CFStringGetTypeID=lambda: 7,
            CFStringGetLength=lambda _p: len(title), CFStringGetCString=encode)
        with self.assertRaises(RuntimeError):
            observed = value.title(1)
            backend = FakeBackend()
            backend.objects[1]['title'] = observed
            exposure = validate(observation(backend))
            print('NUL COUNTEREXAMPLE:', repr(title), 'became', repr(observed),
                  'unique_semantic_candidate=', exposure['unique_semantic_candidate'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
