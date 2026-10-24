"""Bounded retained-element AX properties and private child-pipe protocol only."""
import copy
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time

from macos_ax_contract import (CAPS, LABEL, MAPPING, SCHEMA, normalized_title, require_owned, inside)
from macos_native_input import same_bounds
from probe_macos_ax import BoundedObserver, NativeAX

LIVE_SCHEMA = 'macos-retained-deploy-live-v1'
COMMAND_BYTES = 256
GUARD_BYTES = 8192
LIVE_SOURCE = Path(__file__).with_name('probe_macos_ax_live.py')


def remaining(deadline):
    value = deadline - time.monotonic()
    if value <= 0:
        raise TimeoutError('Original AX request deadline exceeded; no renewal')
    return value


def encode(value, limit):
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()+b'\n'
    if len(data) > limit:
        raise RuntimeError('AX private protocol message exceeds its fixed byte cap')
    return data


def decode(data):
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result: raise RuntimeError('Duplicate AX private protocol key')
            result[name] = value
        return result
    def nonfinite(_value): raise RuntimeError('Nonfinite AX private protocol value')
    return json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=nonfinite)


def write_frame(descriptor, data, deadline):
    sent = 0
    while sent < len(data):
        if not select.select([], [descriptor], [], remaining(deadline))[1]:
            raise TimeoutError('AX private pipe write exceeded original deadline')
        count = os.write(descriptor, data[sent:])
        if count <= 0: raise RuntimeError('AX private pipe write made no progress')
        sent += count
    remaining(deadline)


def read_frame(descriptor, limit, deadline):
    data = bytearray()
    while len(data) <= limit:
        if not select.select([descriptor], [], [], remaining(deadline))[0]:
            raise TimeoutError('AX private pipe read exceeded original deadline')
        chunk = os.read(descriptor, min(4096, limit+1-len(data)))
        if not chunk: raise RuntimeError('AX private pipe ended before a complete bounded message')
        data.extend(chunk)
        if len(data) > limit: raise RuntimeError('AX private pipe response exceeds fixed byte cap')
        if b'\n' in data:
            if data.count(b'\n') != 1 or not data.endswith(b'\n'):
                raise RuntimeError('AX private pipe contains extra or reordered messages')
            remaining(deadline)
            return bytes(data)
    raise RuntimeError('AX private pipe response exceeds fixed byte cap')


class RetainedAX(NativeAX):
    """Remember only references already owned by the accepted initial traversal."""
    def __init__(self, *arguments):
        super().__init__(*arguments)
        self.collecting, self.candidates, self.containers = True, [], {}

    def title(self, element):
        value = super().title(element)
        if self.collecting and normalized_title(value) == LABEL and self.role(element) == 'AXButton':
            if not any(self.same(element, old) for old in self.candidates):
                self.candidates.append(element)
        return value

    def containing_window(self, element):
        value = super().containing_window(element)
        if self.collecting: self.containers[element] = value
        return value


def current_properties(backend, element, original_window, expected_frame):
    """Recheck the SAME retained object; never search for a replacement."""
    backend.guard()
    backend.check_element(element)
    role, title = backend.role(element), backend.title(element)
    enabled, frame = backend.enabled(element), backend.frame(element)
    window = backend.containing_window(element)
    backend.check_element(window)
    window_role, window_frame = backend.role(window), backend.frame(window)
    rows = backend.guard()
    if (role != 'AXButton' or normalized_title(title) != LABEL or enabled is not True
            or not same_bounds(frame, expected_frame) or not inside(frame, backend.bounds)
            or not backend.same(window, original_window)
            or window_role != 'AXWindow' or not same_bounds(window_frame, backend.bounds)
            or sum(backend.calls.values()) > 32768):
        raise RuntimeError('Original retained AX Deploy element changed current identity or properties')
    return {'pid': backend.pid, 'role': role, 'title': title, 'normalized_title': normalized_title(title),
            'enabled': enabled, 'frame_points': frame, 'window_frame_points': window_frame}, rows


def serve(pid, window, bounds, nonce, budget, deadline, report, *, backend_type=RetainedAX,
          input_fd=0, output_fd=1):
    started, backend, complete = time.monotonic(), None, False
    result = {'schema': SCHEMA, 'scope': 'Read-only exported AX semantic exposure; no input/gameplay acceptance',
        'owner_pid': pid, 'window_id': window, 'observer_pid': os.getpid(), 'nonce': nonce,
        'started_monotonic': started, 'caps': copy.deepcopy(CAPS), 'snapshots': [], 'examined_nodes': 0,
        'complete': False, 'input_events_posted': 0, 'permission_requests_made': 0, 'coordinate_mapping': MAPPING}
    try:
        if (type(pid) is not int or pid <= 0 or type(window) is not int or window <= 0
                or not isinstance(nonce, str) or len(nonce) != 32 or any(c not in '0123456789abcdef' for c in nonce)
                or not 0 < budget <= CAPS['seconds'] or not started < deadline <= started+budget):
            raise RuntimeError('Malformed original-deadline live AX request')
        remaining(deadline)
        backend = backend_type(pid, window, bounds, deadline)
        result['AXIsProcessTrusted'] = backend.preflight()['AXIsProcessTrusted']
        if result['AXIsProcessTrusted'] is not True:
            raise RuntimeError('Current AX helper is untrusted; no request made')
        result['displays'] = backend.displays()
        BoundedObserver(backend, result).observe()
        backend.guard()
        latest = result['snapshots'][-1]
        matches = [node for node in latest['nodes'] if node.get('normalized_title') == LABEL and node.get('role') == 'AXButton']
        if not result['complete'] or len(matches) != 1 or len(backend.candidates) != 1:
            raise RuntimeError('Initial complete tree lacks one unique original Deploy reference')
        target, row = backend.candidates[0], matches[0]
        original_window = backend.containers[target]
        original_frame = tuple(row['frame_points'])
        backend.collecting = False
        result.update(finished_monotonic=time.monotonic(), api_call_counts=dict(backend.calls),
                      last_owned_layer_zero_rows=backend.latest_rows)
        remaining(deadline)
        data = encode(result, CAPS['receipt_bytes'])
        with Path(report).open('xb') as stream: stream.write(data)
        write_frame(output_fd, data, deadline)
        for sequence, kind in ((1, 'pointer_move'), (2, 'lmb_down')):
            command = decode(read_frame(input_fd, COMMAND_BYTES, deadline))
            if command == {'kind': 'stop', 'nonce': nonce}:
                complete = True
                return 0
            if type(command.get('sequence')) is not int or command != {'kind': kind, 'nonce': nonce, 'sequence': sequence}:
                raise RuntimeError('AX private command identity, order or fixed schema failed')
            first = time.monotonic()
            button, rows = current_properties(backend, target, original_window, original_frame)
            response = {'schema': LIVE_SCHEMA, 'nonce': nonce, 'sequence': sequence, 'kind': kind,
                'owner_pid': pid, 'window_id': window, 'observer_pid': os.getpid(), 'original_node': row['node'],
                'started_monotonic': first, 'finished_monotonic': time.monotonic(), 'button': button,
                'owned_rows': rows, 'api_call_counts': dict(backend.calls),
                'input_events_posted': 0, 'permission_requests_made': 0}
            remaining(deadline)
            write_frame(output_fd, encode(response, GUARD_BYTES), deadline)
        command = decode(read_frame(input_fd, COMMAND_BYTES, deadline))
        if command != {'kind': 'stop', 'nonce': nonce}:
            raise RuntimeError('Only ordinary stop is allowed after two retained-target checks')
        complete = True
        return 0
    except BaseException as error:
        # Native pointers/private text never enter diagnostics. Original partial
        # traversal remains retained if the first fixed-schema receipt exists.
        result.update(complete=False, finished_monotonic=time.monotonic(),
                      failure={'type': type(error).__name__, 'message': str(error)})
        if backend is not None:
            result.update(api_call_counts=dict(backend.calls), last_owned_layer_zero_rows=backend.latest_rows)
        if not os.path.lexists(report):
            try:
                with Path(report).open('xb') as stream: stream.write(encode(result, CAPS['receipt_bytes']))
            except BaseException:
                pass  # Never replace an existing/oversized partial receipt.
        print(type(error).__name__+': '+str(error), file=sys.stderr)
        return 1
    finally:
        if backend is not None: backend.close()


class LiveChannel:
    def __init__(self, process, nonce, expires):
        self.process, self.nonce, self.expires = process, nonce, expires
        self.sequence, self.closed = 0, False
        for stream in (process.stdin, process.stdout): os.set_blocking(stream.fileno(), False)

    def initial(self):
        return read_frame(self.process.stdout.fileno(), CAPS['receipt_bytes'], self.expires)

    def query(self, kind):
        if self.closed or self.sequence >= 2 or kind != ('pointer_move', 'lmb_down')[self.sequence]:
            raise RuntimeError('Retained AX channel cannot renew, reorder or reacquire a target')
        if self.process.poll() is not None: raise RuntimeError('Retained AX helper exited before live validation')
        self.sequence += 1
        write_frame(self.process.stdin.fileno(), encode({'kind': kind, 'nonce': self.nonce,
                    'sequence': self.sequence}, COMMAND_BYTES), self.expires)
        return read_frame(self.process.stdout.fileno(), GUARD_BYTES, self.expires)

    def close(self):
        if self.closed: return
        self.closed = True
        failure = None
        try:
            if self.process.poll() is None and time.monotonic() < self.expires:
                write_frame(self.process.stdin.fileno(), encode({'kind': 'stop', 'nonce': self.nonce}, COMMAND_BYTES), self.expires)
        except BaseException as error:
            failure = error
        finally:
            try:
                self.process.stdin.close()
            finally:
                self.process.stdout.close()
        # Lifecycle-only wait, never another AX read or renewed action deadline.
        self.process.wait(timeout=1)
        if failure is not None: raise failure
        if self.process.returncode: raise RuntimeError('Retained AX helper did not ordinarily exit cleanly')


def start_live(pid, window, bounds, nonce, budget, expires, report, log, processes):
    arguments = [sys.executable, str(LIVE_SOURCE), '--pid', str(pid), '--window', str(window),
        '--bounds', *map(str, bounds), '--nonce', nonce, '--budget', str(budget),
        '--deadline', str(expires), '--report', str(report)]
    with Path(log).open('x') as stderr:
        child = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr,
                                 start_new_session=True, close_fds=True, bufsize=0)
    processes.append(('semantic-deploy-live', child))
    channel = None
    try:
        channel = LiveChannel(child, nonce, expires)
        raw = channel.initial()
        return channel, raw
    except BaseException:
        if channel is not None:
            channel.close()
        else:
            child.stdin.close(); child.stdout.close()
            child.wait(timeout=1)
        raise
