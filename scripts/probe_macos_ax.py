#!/usr/bin/env python3
"""Bounded own-PID/window public AX reader. No inputs, actions or text values."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import re
import time

from macos_ax_contract import (ATTRIBUTES, CAPS, MAPPING, PRUNED_ROLES, READ_APIS,
                               SCHEMA, normalized_title, rectangle, require_owned)
from macos_native_input import same_bounds
from probe_macos_input import MacReadOnly, Point, Size


class NativeAX(MacReadOnly):
    """Only this backend touches native libraries; traversal below is pure-testable."""
    def __init__(self, pid, window, bounds, deadline):
        super().__init__()  # Refuse non-ARM/non-macOS before loading libraries.
        self.pid, self.window, self.bounds, self.deadline = pid, window, bounds, deadline
        self.refs, self.keys, self.calls, self.latest_rows = [], {}, {}, []
        for name, args, returns in (
            ('CFGetTypeID', [C.c_void_p], C.c_ulong),
            ('CFRetain', [C.c_void_p], C.c_void_p),
            ('CFEqual', [C.c_void_p, C.c_void_p], C.c_bool),
            ('CFArrayGetTypeID', [], C.c_ulong),
            ('CFArrayGetCount', [C.c_void_p], C.c_long),
            ('CFArrayGetValueAtIndex', [C.c_void_p, C.c_long], C.c_void_p),
            ('CFStringGetTypeID', [], C.c_ulong),
            ('CFStringGetLength', [C.c_void_p], C.c_long),
            ('CFStringGetCString', [C.c_void_p, C.c_void_p, C.c_long, C.c_uint32], C.c_bool),
            ('CFStringCreateWithCString', [C.c_void_p, C.c_char_p, C.c_uint32], C.c_void_p),
            ('CFBooleanGetTypeID', [], C.c_ulong),
            ('CFBooleanGetValue', [C.c_void_p], C.c_bool)):
            self.bind(self.cf, name, args, returns)
        for name, args, returns in (
            ('AXUIElementCreateApplication', [C.c_int32], C.c_void_p),
            ('AXUIElementGetTypeID', [], C.c_ulong),
            ('AXUIElementGetPid', [C.c_void_p, C.POINTER(C.c_int32)], C.c_int32),
            ('AXUIElementSetMessagingTimeout', [C.c_void_p, C.c_float], C.c_int32),
            ('AXUIElementCopyAttributeValue', [C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)], C.c_int32),
            ('AXUIElementGetAttributeValueCount', [C.c_void_p, C.c_void_p, C.POINTER(C.c_long)], C.c_int32),
            ('AXUIElementCopyAttributeValues', [C.c_void_p, C.c_void_p, C.c_long, C.c_long,
                                               C.POINTER(C.c_void_p)], C.c_int32),
            ('AXValueGetTypeID', [], C.c_ulong),
            ('AXValueGetType', [C.c_void_p], C.c_uint32),
            ('AXValueGetValue', [C.c_void_p, C.c_uint32, C.c_void_p], C.c_bool)):
            self.bind(self.ax, name, args, returns)

    def guard(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError('Original AX observation deadline exceeded')
        self.latest_rows = self.windows(self.pid)
        require_owned(self.latest_rows, self.pid, self.window, self.bounds)
        if time.monotonic() >= self.deadline:
            raise TimeoutError('Owned-window query returned after AX deadline')
        return self.latest_rows

    def call(self, name, *arguments):
        if name not in READ_APIS:
            raise RuntimeError('Native AX call outside read-only allowlist')
        self.guard()
        self.calls[name] = self.calls.get(name, 0) + 1
        result = getattr(self.ax, name)(*arguments)
        self.guard()  # Successful late returns and geometry changes still fail.
        return result

    def hold(self, pointer, *, retained=False):
        if not pointer or len(self.refs) >= 2048:
            raise RuntimeError('Null or excessive retained native reference')
        if not retained:
            pointer = self.cf.CFRetain(pointer)
        self.refs.append(pointer)
        return pointer

    def key(self, name):
        if name not in ATTRIBUTES:
            raise RuntimeError('AX attribute is outside the structural/button allowlist')
        if name not in self.keys:
            self.keys[name] = self.hold(self.cf.CFStringCreateWithCString(None, name.encode(), 0x08000100), retained=True)
        return self.keys[name]

    def application(self):
        value = self.hold(self.call('AXUIElementCreateApplication', self.pid), retained=True)
        self.check_element(value)
        return value

    def check_element(self, element):
        if not element or self.cf.CFGetTypeID(element) != self.ax.AXUIElementGetTypeID():
            raise RuntimeError('Malformed AX element reference')
        error = self.call('AXUIElementSetMessagingTimeout', element, CAPS['call_seconds'])
        if error:
            raise RuntimeError('AX messaging timeout setup failed code=' + str(error))
        pid = C.c_int32()
        error = self.call('AXUIElementGetPid', element, C.byref(pid))
        if error or pid.value != self.pid:
            raise RuntimeError('AX element belongs to another or unavailable PID')

    def attribute(self, element, name):
        self.check_element(element)
        value = C.c_void_p()
        error = self.call('AXUIElementCopyAttributeValue', element, self.key(name), C.byref(value))
        if error or not value.value:
            if value.value:
                self.cf.CFRelease(value)
            raise RuntimeError('Required AX attribute unavailable: ' + name + ' code=' + str(error))
        return self.hold(value.value, retained=True)

    def string(self, element, name, limit=512):
        if name not in ('AXRole', 'AXTitle'):
            raise RuntimeError('String reads restricted to role and allowed title')
        value = self.attribute(element, name)
        if self.cf.CFGetTypeID(value) != self.cf.CFStringGetTypeID():
            raise RuntimeError('Malformed AX string type')
        if not 0 <= self.cf.CFStringGetLength(value) <= limit:
            raise RuntimeError('AX string exceeds finite title/role cap')
        buffer = C.create_string_buffer(limit + 1)
        if not self.cf.CFStringGetCString(value, buffer, len(buffer), 0x08000100):
            raise RuntimeError('AX UTF-8 string exceeds finite byte cap')
        return buffer.value.decode('utf-8', errors='strict')

    def role(self, element):
        return self.string(element, 'AXRole', 64)

    def title(self, element):
        if self.role(element) not in ('AXButton', 'AXWindow'):
            raise RuntimeError('Title reads require semantic button or owned window role')
        return self.string(element, 'AXTitle', CAPS['title_bytes'])

    def frame(self, element):
        values = []
        # AXValue here is Apple's typed CGPoint/CGSize decoder, never AXValue attribute data.
        for name, kind, structure in (('AXPosition', 1, Point), ('AXSize', 2, Size)):
            value = self.attribute(element, name)
            if (self.cf.CFGetTypeID(value) != self.ax.AXValueGetTypeID()
                    or self.ax.AXValueGetType(value) != kind):
                raise RuntimeError('AX position/size is not the required public geometry type')
            result = structure()
            if not self.ax.AXValueGetValue(value, kind, C.byref(result)):
                raise RuntimeError('Public AX geometry decoder failed')
            values.extend([result.x, result.y] if kind == 1 else [result.width, result.height])
        return list(rectangle(values))

    def enabled(self, element):
        value = self.attribute(element, 'AXEnabled')
        if self.cf.CFGetTypeID(value) != self.cf.CFBooleanGetTypeID():
            raise RuntimeError('Malformed AX enabled flag')
        return bool(self.cf.CFBooleanGetValue(value))

    def containing_window(self, element):
        value = self.attribute(element, 'AXWindow')
        self.check_element(value)
        return value

    def elements(self, element, name, limit):
        if name not in ('AXWindows', 'AXChildren') or not 0 <= limit <= CAPS['nodes']:
            raise RuntimeError('Bounded structural child/window read required')
        self.check_element(element)
        count = C.c_long()
        error = self.call('AXUIElementGetAttributeValueCount', element, self.key(name), C.byref(count))
        if error or not 0 <= count.value <= limit:
            raise RuntimeError('Unsupported or oversized AX structural collection: ' + name + ' code=' + str(error))
        if not count.value:
            return []
        array = C.c_void_p()
        error = self.call('AXUIElementCopyAttributeValues', element, self.key(name), 0, count.value, C.byref(array))
        if error or not array.value:
            if array.value:
                self.cf.CFRelease(array)
            raise RuntimeError('Bounded AX structural read failed: ' + name + ' code=' + str(error))
        array = self.hold(array.value, retained=True)
        if (self.cf.CFGetTypeID(array) != self.cf.CFArrayGetTypeID()
                or self.cf.CFArrayGetCount(array) != count.value):
            raise RuntimeError('AX child collection type/count changed')
        values = [self.hold(self.cf.CFArrayGetValueAtIndex(array, index)) for index in range(count.value)]
        for value in values:
            self.check_element(value)
        return values

    def same(self, left, right):
        return bool(self.cf.CFEqual(left, right))

    def close(self):
        for pointer in reversed(self.refs):
            self.cf.CFRelease(pointer)
        self.refs.clear()


class BoundedObserver:
    """One traversal implementation for native reads and pure fake backends."""
    def __init__(self, backend, result, *, clock=time.monotonic, sleep=time.sleep):
        self.backend, self.result, self.clock, self.sleep = backend, result, clock, sleep
        self.examined = 0

    def snapshot(self, application):
        api = self.backend
        snapshot = {'started_monotonic': self.clock(), 'cg_before': api.guard(),
                    'windows': [], 'nodes': [], 'complete': False}
        self.result['snapshots'].append(snapshot)  # Preserve partial failures too.
        windows = api.elements(application, 'AXWindows', min(16, CAPS['nodes'] - self.examined))
        if not windows:
            snapshot['cg_after'] = api.guard()
            snapshot['finished_monotonic'] = self.clock()
            return snapshot
        # An extra AX window is ambiguous even if one frame appears to match.
        for window in windows:
            api.check_element(window)
            role, frame = api.role(window), api.frame(window)
            row = {'pid': api.pid, 'role': role, 'frame_points': frame,
                   'title': api.title(window)}
            snapshot['windows'].append(row)
        if (len(windows) != 1 or snapshot['windows'][0]['role'] != 'AXWindow'
                or not same_bounds(snapshot['windows'][0]['frame_points'], api.bounds)):
            raise RuntimeError('AX windows do not uniquely agree with the owned CG frame')
        seen, queue = [], [(windows[0], None, 0)]
        while queue:
            api.guard()
            element, parent, depth = queue.pop(0)
            if self.examined >= CAPS['nodes'] or depth > CAPS['depth']:
                raise RuntimeError('Cumulative node/depth cap exceeded')
            if any(api.same(element, old) for old in seen):
                raise RuntimeError('Cyclic/duplicate AX structural reference')
            seen.append(element)
            api.check_element(element)
            role = api.role(element)
            if not isinstance(role, str) or len(role.encode('utf-8')) > 64:
                raise RuntimeError('Malformed AX role')
            self.examined += 1
            self.result['examined_nodes'] = self.examined
            row = {'node': len(seen) - 1, 'parent': parent, 'depth': depth, 'pid': api.pid, 'role': role}
            snapshot['nodes'].append(row)
            if role in PRUNED_ROLES:
                row['pruned'] = True
                continue
            if role in ('AXWindow', 'AXButton'):
                row['title'] = api.title(element)
                row['normalized_title'] = normalized_title(row['title'])
            if role == 'AXButton':
                containing = api.containing_window(element)
                if not api.same(containing, windows[0]):
                    raise RuntimeError('AX button names another containing window')
                row.update(enabled=api.enabled(element), frame_points=api.frame(element),
                           window_frame_points=api.frame(containing))
            children = api.elements(element, 'AXChildren', CAPS['nodes'] - self.examined - len(queue))
            queue.extend((child, row['node'], depth + 1) for child in children)
        snapshot['complete'] = any(row['role'] == 'AXButton' for row in snapshot['nodes'])
        snapshot['cg_after'] = api.guard()
        snapshot['finished_monotonic'] = self.clock()
        return snapshot

    def observe(self):
        application = self.backend.application()
        for index in range(CAPS['snapshots']):
            if self.snapshot(application)['complete']:
                self.result['complete'] = True
                return
            if index + 1 < CAPS['snapshots']:
                self.backend.guard()
                self.sleep(CAPS['spacing_seconds'])
                self.backend.guard()


def collect(pid, window, bounds, nonce, budget, *, backend_type=NativeAX):
    started = time.monotonic()
    result = {'schema': SCHEMA, 'scope': 'Read-only exported AX semantic exposure; no input/gameplay acceptance',
              'owner_pid': pid, 'window_id': window, 'observer_pid': os.getpid(), 'nonce': nonce,
              'started_monotonic': started, 'caps': CAPS, 'snapshots': [], 'examined_nodes': 0,
              'complete': False, 'input_events_posted': 0, 'permission_requests_made': 0,
              'coordinate_mapping': MAPPING}
    backend = None
    try:
        if (not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0
                or not isinstance(window, int) or isinstance(window, bool) or window <= 0
                or not re.fullmatch('[0-9a-f]{32}', nonce) or not 0 < budget <= CAPS['seconds']):
            raise ValueError('Malformed bounded AX request')
        rectangle(bounds)
        backend = backend_type(pid, window, bounds, started + budget)
        result['AXIsProcessTrusted'] = backend.preflight()['AXIsProcessTrusted']
        if result['AXIsProcessTrusted'] is not True:
            raise RuntimeError('Current AX observer is untrusted; no permission request made')
        result['displays'] = backend.displays()
        BoundedObserver(backend, result).observe()
        backend.guard()
    except BaseException as error:
        result['complete'] = False
        result['failure'] = {'type': type(error).__name__, 'message': str(error)}
    finally:
        result['finished_monotonic'] = time.monotonic()
        if backend is not None:
            result['api_call_counts'] = dict(backend.calls)
            result['last_owned_layer_zero_rows'] = backend.latest_rows
            backend.close()
        if result['finished_monotonic'] - started >= budget:
            result['complete'] = False
            result['failure'] = {'type': 'TimeoutError', 'message': 'AX helper returned beyond original budget'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--window', type=int, required=True)
    parser.add_argument('--bounds', type=float, nargs=4, required=True)
    parser.add_argument('--nonce', required=True)
    parser.add_argument('--budget', type=float, required=True)
    parser.add_argument('--report', type=Path, required=True)
    arguments = parser.parse_args()
    if os.path.lexists(arguments.report):
        parser.error('Preserve existing AX receipt; choose a fresh output')
    result = collect(arguments.pid, arguments.window, arguments.bounds, arguments.nonce, arguments.budget)
    data = (json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()
    if len(data) > CAPS['receipt_bytes']:
        # Do not truncate or pass partial evidence. Bounded structure/title caps
        # normally keep this below the cap; retain only the explicit failure.
        data = (json.dumps({'schema': SCHEMA, 'complete': False, 'nonce': arguments.nonce,
                            'failure': {'type': 'RuntimeError', 'message': 'AX receipt byte cap exceeded'},
                            'input_events_posted': 0, 'permission_requests_made': 0}) + '\n').encode()
        result['complete'] = False
    with arguments.report.open('xb') as stream:
        stream.write(data)
    print(data.decode(), end='')
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
