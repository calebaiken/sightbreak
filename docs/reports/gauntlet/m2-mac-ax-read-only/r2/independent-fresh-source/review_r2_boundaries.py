#!/usr/bin/env python3
"""Independent R2 pure boundary controls; never construct native libraries."""
import ctypes as C
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(SOURCE / 'scripts'))
import probe_macos_ax as observer
import macos_ax_contract as contract
from test_macos_ax_read_only import FakeBackend, observation, validate


def reader():
    value = observer.NativeAX.__new__(observer.NativeAX)
    value.pid, value.window, value.bounds = 12, 34, [40, 60, 960, 568]
    value.calls, value.refs, value.keys, value.latest_rows = {}, [], {}, []
    value.deadline, value.now = 15.0, 10.0
    value.released, value.retained = [], []
    value.rows = [{'owner_pid': 12, 'window_id': 34, 'onscreen': True,
        'bounds_points_including_chrome': [40, 60, 960, 568]}]
    value.windows = lambda _pid: value.rows
    def retain(pointer):
        value.retained.append(pointer)
        return pointer
    value.cf = SimpleNamespace(CFRelease=value.released.append, CFRetain=retain)
    return value


def string_reader(raw, units, *, terminated=True):
    value = reader()
    value.role, value.attribute = lambda _: 'AXButton', lambda *_: 1
    def converted(_pointer, buffer, capacity, _encoding):
        contents = raw + (b'\0' if terminated else b'')
        if len(contents) > capacity:
            return False
        C.memmove(buffer, contents, len(contents))
        return True
    value.cf = SimpleNamespace(CFGetTypeID=lambda _: 7, CFStringGetTypeID=lambda: 7,
        CFStringGetLength=lambda _: units, CFStringGetCString=converted)
    return value


class IndependentR2Boundaries(unittest.TestCase):
    def test_actual_elapsed_cap_applies_to_success_and_error_returns(self):
        for elapsed in (0.0, 0.249, 0.25, 0.300):
            for error in (0, -25205):
                with self.subTest(elapsed=elapsed, error=error):
                    value = reader()
                    def native(*_):
                        value.now += elapsed
                        return error
                    value.ax = SimpleNamespace(AXUIElementGetPid=native)
                    with patch.object(observer.time, 'monotonic', lambda: value.now):
                        if elapsed < 0.25:
                            self.assertEqual(value.call('AXUIElementGetPid', 1, None), error)
                        else:
                            with self.assertRaises(TimeoutError):
                                value.call('AXUIElementGetPid', 1, None)
                    self.assertEqual(value.deadline, 15.0)
                    self.assertEqual(value.calls, {'AXUIElementGetPid': 1})

    def test_copy_out_parameter_survives_baseexception_and_close_is_idempotent(self):
        class BoundaryAbort(BaseException):
            pass
        for api in ('AXUIElementCopyAttributeValue', 'AXUIElementCopyAttributeValues'):
            with self.subTest(api=api):
                value, pointer = reader(), C.c_void_p()
                def native(output):
                    output._obj.value = 9001
                    raise BoundaryAbort('Synthetic failure after native out-parameter write')
                value.ax = SimpleNamespace(**{api: native})
                with patch.object(observer.time, 'monotonic', lambda: value.now):
                    with self.assertRaises(BoundaryAbort):
                        value.call(api, C.byref(pointer), owned_out=pointer)
                self.assertEqual(value.refs, [9001])
                value.close()
                value.close()
                self.assertEqual(value.released, [9001])

    def test_pre_call_window_rejection_never_calls_or_owns_native_result(self):
        value = reader()
        value.rows.append(dict(value.rows[0], window_id=35))
        reached = []
        value.ax = SimpleNamespace(AXUIElementCreateApplication=lambda _: reached.append(True) or 9001)
        with patch.object(observer.time, 'monotonic', lambda: value.now):
            with self.assertRaises(RuntimeError):
                value.application()
        value.close()
        self.assertEqual((reached, value.refs, value.released, value.calls), ([], [], [], {}))

    def test_full_registry_releases_copied_pointer_even_before_late_check(self):
        value, pointer = reader(), C.c_void_p()
        value.refs = list(range(1, 2049))
        def native(output):
            output._obj.value = 9001
            value.now += 0.300
            return 0
        value.ax = SimpleNamespace(AXUIElementCopyAttributeValue=native)
        with patch.object(observer.time, 'monotonic', lambda: value.now):
            with self.assertRaises(RuntimeError):
                value.call('AXUIElementCopyAttributeValue', C.byref(pointer), owned_out=pointer)
        self.assertEqual(value.released, [9001])
        value.close()
        self.assertEqual(value.released.count(9001), 1)
        self.assertEqual(len(value.released), 2049)

    def test_borrowed_array_child_is_retained_before_foreign_pid_rejection(self):
        value = reader()
        value.key = lambda name: name
        value.cf.CFGetTypeID = lambda _: 7
        value.cf.CFArrayGetTypeID = lambda: 7
        value.cf.CFArrayGetCount = lambda _: 1
        value.cf.CFArrayGetValueAtIndex = lambda *_: 9002
        def pid(element, output):
            output._obj.value = 13 if element == 9002 else 12
            return 0
        def count(_element, _key, output):
            output._obj.value = 1
            return 0
        def copied(_element, _key, _start, _count, output):
            output._obj.value = 9001
            return 0
        value.ax = SimpleNamespace(AXUIElementGetTypeID=lambda: 7,
            AXUIElementSetMessagingTimeout=lambda *_: 0, AXUIElementGetPid=pid,
            AXUIElementGetAttributeValueCount=count, AXUIElementCopyAttributeValues=copied)
        with patch.object(observer.time, 'monotonic', lambda: value.now):
            with self.assertRaisesRegex(RuntimeError, 'another or unavailable PID'):
                value.elements(1, 'AXChildren', 4)
        self.assertEqual(value.retained, [9002])
        value.close()
        self.assertEqual(value.released, [9002, 9001])

    def test_valid_utf16_counts_and_role_byte_boundary_preserve_exact_text(self):
        for text in ('', 'DEPLOY · OFFLINE 5V5', 'é'*256, '🙂'*128, 'e\u0301'*170):
            with self.subTest(text=text[:20]):
                value = string_reader(text.encode(), len(text.encode('utf-16-le'))//2)
                self.assertEqual(value.title(1), text)
        for text in ('A'*64, 'é'*32, '🙂'*16):
            value = string_reader(text.encode(), len(text.encode('utf-16-le'))//2)
            self.assertEqual(value.string(1, 'AXRole', 64), text)
        for text in ('A'*65, 'é'*33, '🙂'*17):
            value = string_reader(text.encode(), len(text.encode('utf-16-le'))//2)
            with self.assertRaises(RuntimeError):
                value.string(1, 'AXRole', 64)

    def test_nul_controls_bad_utf8_and_full_buffer_cannot_pass_as_prefix(self):
        label = contract.LABEL
        invalid = [(b'\xff', 1), (b'\xed\xa0\x80', 1), ('🙂'.encode(), 1)]
        for text in (label+'\0TAIL', label+'\0', '\0'+label,
                     label+'\x7f', label+'\x85', label+'\n', label+'\t'):
            invalid.append((text.encode(), len(text.encode('utf-16-le'))//2))
        for raw, units in invalid:
            with self.subTest(raw=raw):
                with self.assertRaises(RuntimeError):
                    string_reader(raw, units).title(1)
        with self.assertRaises(RuntimeError):
            string_reader(b'A'*513, 512, terminated=False).title(1)

    def test_complete_native_label_survives_full_validator_without_mutating_ocr(self):
        for text in ('DEPLOY · OFFLINE 5V5', 'DEPLOY   •   OFFLINE 5V5'):
            value = string_reader(text.encode(), len(text.encode('utf-16-le'))//2)
            backend = FakeBackend()
            backend.objects[1]['title'] = value.title(1)
            result = validate(observation(backend))
            self.assertTrue(result['unique_semantic_candidate'])
            self.assertFalse(result['gameplay_target_accepted'])
            self.assertEqual(result['original_native_row']['confidence'], 0.5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
