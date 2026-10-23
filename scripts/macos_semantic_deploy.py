"""Explicit ordinary Deploy binding from fresh owned read-only AX evidence."""
import copy
from dataclasses import dataclass, field
import hashlib
import json
import os
import stat
import struct
from pathlib import Path
import sys
import time
import uuid

from macos_ax_contract import (CAPS, LABEL, PRUNED_ROLES, normalized_title, number, rectangle,
                               validate_observation)
from probe_macos_input import digest
from macos_ordinary_input import no_symlinks

AX_SOURCE = Path(__file__).with_name('probe_macos_ax.py')
SOURCES = (Path(__file__), AX_SOURCE, Path(__file__).with_name('macos_ax_contract.py'))
RECEIPT_KEYS = {'schema', 'scope', 'owner_pid', 'window_id', 'observer_pid', 'nonce',
                'started_monotonic', 'finished_monotonic', 'caps', 'snapshots', 'examined_nodes',
                'complete', 'input_events_posted', 'permission_requests_made', 'coordinate_mapping',
                'AXIsProcessTrusted', 'displays', 'api_call_counts', 'last_owned_layer_zero_rows'}
SNAPSHOT_KEYS = {'started_monotonic', 'finished_monotonic', 'cg_before', 'cg_after',
                 'windows', 'nodes', 'complete'}
DISPLAY_KEYS = {'display_id', 'bounds_points', 'mode_dimensions', 'mode_pixel_dimensions',
                'mode_pixel_per_unit', 'scale_scope'}
WINDOW_KEYS = {'owner_pid', 'window_id', 'onscreen', 'bounds_points_including_chrome'}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class FileSeal:
    path: str
    sha256: str
    identity: tuple
    directories: tuple
    limit: int

    def metadata(self):
        return {'path': self.path, 'sha256': self.sha256, 'identity': list(self.identity),
                'directories': [list(row) for row in self.directories], 'limit': self.limit}

    @classmethod
    def from_metadata(cls, value):
        if set(value) != {'path', 'sha256', 'identity', 'directories', 'limit'}:
            raise RuntimeError('Malformed original native file seal')
        return cls(value['path'], value['sha256'], tuple(value['identity']),
                   tuple(tuple(row) for row in value['directories']), value['limit'])


def file_identity(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid,
            value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def read_regular(path, limit, expected=None):
    """One bounded descriptor read, no-follow ancestors, stable regular-file identity."""
    path = Path(path).absolute()
    no_symlinks(path)
    if type(limit) is not int or limit <= 0 or any(part == '..' for part in path.parts):
        raise RuntimeError('Invalid bounded native evidence file request')
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    parent, descriptor, directories = None, None, []
    try:
        parent = os.open(path.anchor, directory_flags)
        for part in path.parts[1:-1]:
            row = os.fstat(parent)
            directories.append((row.st_dev, row.st_ino, row.st_mode, row.st_uid, row.st_gid))
            child = os.open(part, directory_flags, dir_fd=parent)
            os.close(parent); parent = child
        row = os.fstat(parent)
        directories.append((row.st_dev, row.st_ino, row.st_mode, row.st_uid, row.st_gid))
        descriptor = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= limit:
            raise RuntimeError('Native evidence must be a bounded regular file')
        if expected is not None and (type(expected) is not FileSeal or expected.path != str(path)
                or expected.limit != limit or expected.identity != file_identity(before)
                or expected.directories != tuple(directories)):
            raise RuntimeError('Original native evidence file or ancestor identity changed')
        chunks, size = [], 0
        while size <= limit:
            chunk = os.read(descriptor, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk); size += len(chunk)
        after = os.fstat(descriptor)
        named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        if (size > limit or size != before.st_size or file_identity(before) != file_identity(after)
                or file_identity(after) != file_identity(named)):
            raise RuntimeError('Native evidence grew, changed or was replaced during its bounded read')
        data = b''.join(chunks)
        seal = FileSeal(str(path), hashlib.sha256(data).hexdigest(), file_identity(after), tuple(directories), limit)
        if expected is not None and seal != expected:
            raise RuntimeError('Original native evidence bytes or identity changed')
        return data, seal
    finally:
        if descriptor is not None: os.close(descriptor)
        if parent is not None: os.close(parent)


def decode_public_json(data):
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise RuntimeError('Duplicate key in semantic source receipt')
            result[name] = value
        return result
    def nonfinite(_value):
        raise RuntimeError('Nonfinite semantic source receipt')
    return json.loads(data.decode('utf-8', errors='strict'), object_pairs_hook=pairs, parse_constant=nonfinite)


def read_public_json(path):
    data, _seal = read_regular(path, CAPS['receipt_bytes'])
    return decode_public_json(data)


def seal_native_capture(png, native, capture):
    # Finite original full-window PNG bound; the AX/JSON512KiB cap is unchanged.
    image, png_seal = read_regular(png, 32 * 1024 * 1024)
    raw, native_seal = read_regular(native, CAPS['receipt_bytes'])
    if (len(image) < 24 or image[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            or list(struct.unpack('>II', image[16:24])) != capture['image_dimensions']
            or decode_public_json(raw) != capture or 'derived_deploy_analysis' in capture):
        raise RuntimeError('Original semantic native PNG/receipt binding failed')
    return png_seal, native_seal


def private_shape(receipt):
    """A semantic input target accepts only the reader's public fixed schema."""
    if (set(receipt) != RECEIPT_KEYS
            or receipt.get('scope') != 'Read-only exported AX semantic exposure; no input/gameplay acceptance'):
        raise RuntimeError('Semantic receipt contains unexpected or missing public fields')
    if fingerprint(receipt['caps']) != fingerprint(CAPS):
        raise RuntimeError('Semantic caps must retain their exact public types and values')
    for key in ('owner_pid', 'window_id', 'observer_pid'):
        if type(receipt[key]) is not int or receipt[key] <= 0:
            raise RuntimeError('Semantic receipt identity must be a positive native integer')
    if type(receipt['examined_nodes']) is not int or receipt['examined_nodes'] <= 0:
        raise RuntimeError('Semantic examined-node count must retain its native integer type')
    for key in ('input_events_posted', 'permission_requests_made'):
        if type(receipt[key]) is not int or receipt[key] != 0:
            raise RuntimeError('Semantic zero-event counters must be native integer zero')
    displays = receipt['displays']
    if not isinstance(displays, list) or not 1 <= len(displays) < 16:
        raise RuntimeError('Malformed bounded public display metadata')
    for display in displays:
        if (not isinstance(display, dict) or set(display) != DISPLAY_KEYS
                or display['scale_scope'] != 'Raw public CGDisplayMode metadata; not an assumed AX coordinate multiplier'):
            raise RuntimeError('Unexpected public display metadata fields')
        rectangle(display['bounds_points'])
        if (type(display['display_id']) is not int or display['display_id'] <= 0
                or any(not isinstance(display[key], list) or len(display[key]) != 2
                       or any(type(value) is not int or not 0 < value <= 131072 for value in display[key])
                       for key in ('mode_dimensions', 'mode_pixel_dimensions'))
                or not isinstance(display['mode_pixel_per_unit'], list) or len(display['mode_pixel_per_unit']) != 2
                or any(not number(value) or value <= 0 for value in display['mode_pixel_per_unit'])):
            raise RuntimeError('Malformed bounded public display geometry')
    inventories = [receipt['last_owned_layer_zero_rows']]
    for snapshot in receipt['snapshots']:
        if set(snapshot) != SNAPSHOT_KEYS:
            raise RuntimeError('Semantic snapshot contains unexpected public fields')
        inventories.extend((snapshot['cg_before'], snapshot['cg_after']))
        for window in snapshot['windows']:
            if type(window.get('pid')) is not int:
                raise RuntimeError('AX window PID must retain its native integer type')
        for node in snapshot['nodes']:
            role = node.get('role')
            keys = {'node', 'parent', 'depth', 'pid', 'role'}
            if role in ('AXButton', 'AXWindow'):
                keys |= {'title', 'normalized_title'}
            if role == 'AXButton':
                keys |= {'enabled', 'frame_points', 'window_frame_points'}
                rectangle(node['frame_points']); rectangle(node['window_frame_points'])
                if type(node['enabled']) is not bool:
                    raise RuntimeError('Malformed public semantic enabled flag')
            elif role in PRUNED_ROLES:
                keys |= {'pruned'}
            if set(node) != keys or type(node['pid']) is not int:
                raise RuntimeError('Semantic node contains missing or private fields')
    for rows in inventories:
        if (not isinstance(rows, list) or any(set(row) != WINDOW_KEYS
                or type(row['owner_pid']) is not int or type(row['window_id']) is not int
                or type(row['onscreen']) is not bool for row in rows)):
            raise RuntimeError('Unexpected or mistyped public owned-window metadata fields')


@dataclass(frozen=True)
class SemanticDeployTarget:
    capture: dict
    receipt: dict
    binding: dict
    files: tuple
    expires: float
    owner: object
    proof: str
    used: bool = field(default=False, init=False)

    def point(self, capture, ui):
        if type(self) is not SemanticDeployTarget or self.used or ui is not self.owner or capture is not self.capture:
            raise RuntimeError('Semantic Deploy target is unbound, replayed or belongs to another controller')
        if fingerprint([capture, self.receipt, self.binding]) != self.proof:
            raise RuntimeError('Semantic Deploy evidence changed after binding')
        private_shape(self.receipt)
        exposure = validate_observation(self.receipt, capture, **self.binding)
        button = exposure['button']
        if (set(button) != {'node', 'parent', 'depth', 'pid', 'role', 'title', 'normalized_title',
                           'enabled', 'frame_points', 'window_frame_points'}
                or normalized_title(button['title']) != LABEL):
            raise RuntimeError('Complete exact semantic Deploy title/frame provenance required')
        if (ui.pid != self.binding['pid'] or ui.window != self.binding['window']
                or list(ui.bounds) != list(self.binding['bounds']) or not ui.input_geometry_pinned):
            raise RuntimeError('Semantic Deploy target does not bind the pinned input owner')
        for seal in self.files:
            read_regular(seal.path, seal.limit, seal)
        ui.require_target()  # Original private/profile, permissions, unique window and foreground guards.
        if not self.binding['finished'] <= time.monotonic() < self.expires:
            raise TimeoutError('Semantic Deploy target exceeded its original nonrenewable AX deadline')
        # Use the center of the corroborated native text region. It is inside
        # the unique enabled AX button; no assumed layout coordinate is used.
        x, y, width, height = exposure['original_text_frame_points']
        return (x + width / 2, y + height / 2)

    def consume(self):
        object.__setattr__(self, 'used', True)


def acquire_target(ui, capture, output, command, remaining, menu_deadline, result):
    """One bounded subprocess, owned guards and immutable original-byte binding."""
    if ui.event_post_attempts or ui.held or not ui.input_geometry_pinned:
        raise RuntimeError('Semantic Deploy acquisition requires a fresh pre-input pinned owner')
    output = Path(output)
    png, native = output / '01-focused-menu.png', output / '01-focused-menu.json'
    accepted = [row for row in result['captures'] if row.get('name') == '01-focused-menu']
    if len(accepted) != 1 or accepted[0].get('window_id') != ui.window:
        raise RuntimeError('One original focused native capture acceptance required')
    record = accepted[0]
    native_files = tuple(FileSeal.from_metadata(value) for value in record['semantic_original_files'])
    if (len(native_files) != 2 or [seal.path for seal in native_files] != [str(png), str(native)]
            or [seal.sha256 for seal in native_files] != [record['png_sha256'], record['receipt_sha256']]):
        raise RuntimeError('Original native capture seal provenance mismatch')
    for seal in native_files:
        read_regular(seal.path, seal.limit, seal)
    if tuple(seal_native_capture(png, native, capture)) != native_files:
        raise RuntimeError('Original focused native capture was substituted before acquisition')
    ui.require_target()
    nonce = uuid.uuid4().hex
    budget = min(CAPS['seconds'], remaining(menu_deadline))
    started = time.monotonic()
    expires = min(menu_deadline, started + budget)
    ax_file = output / 'semantic-deploy-ax.json'
    child = command('semantic-deploy-ax', [sys.executable, str(AX_SOURCE), '--pid', str(ui.pid),
                    '--window', str(ui.window), '--bounds', *map(str, ui.bounds), '--nonce', nonce,
                    '--budget', str(budget), '--report', str(ax_file)], budget, allow_failure=True,
                    return_process=True)
    ui.require_target()
    finished = time.monotonic()
    remaining(expires)
    raw_ax, ax_seal = read_regular(ax_file, CAPS['receipt_bytes'])
    receipt = decode_public_json(raw_ax)
    binding = dict(pid=ui.pid, window=ui.window, bounds=list(ui.bounds), nonce=nonce,
                   observer_pid=child.pid, started=started, finished=finished, budget=budget)
    result['semantic_deploy_observation'] = {'receipt_sha256': ax_seal.sha256, **copy.deepcopy(binding),
                                            'expires_monotonic': expires}
    if child.returncode:
        raise RuntimeError('Semantic Deploy observer failed; original evidence retained')
    private_shape(receipt)
    exposure = validate_observation(receipt, capture, **binding)
    files = (*native_files, ax_seal)
    target = SemanticDeployTarget(capture, receipt, binding, files, expires, ui,
                                  fingerprint([capture, receipt, binding]))
    point = target.point(capture, ui)
    result['semantic_deploy_target'] = {'method': 'fresh-owned-ax-and-original-native-text',
        'button': copy.deepcopy(exposure['button']), 'original_native_row': copy.deepcopy(exposure['original_native_row']),
        'target_points': list(point), 'ocr_confidence_threshold_changed': False,
        'input_delivery_or_gameplay_accepted': False}
    return target
