"""Explicit ordinary Deploy binding from fresh owned read-only AX evidence."""
import copy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import sys
import time
import uuid

from macos_ax_contract import (CAPS, LABEL, PRUNED_ROLES, normalized_title, number, rectangle,
                               validate_observation)
from macos_deploy_ocr import png_dimensions
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


def read_public_json(path):
    no_symlinks(path)
    if Path(path).stat().st_size > CAPS['receipt_bytes']:
        raise RuntimeError('Semantic source receipt exceeds the original byte cap')
    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise RuntimeError('Duplicate key in semantic source receipt')
            result[name] = value
        return result
    def nonfinite(_value):
        raise RuntimeError('Nonfinite semantic source receipt')
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=nonfinite)


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
        if not isinstance(rows, list) or any(set(row) != WINDOW_KEYS for row in rows):
            raise RuntimeError('Unexpected public owned-window metadata fields')


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
        for path, expected in self.files:
            no_symlinks(path)
            if digest(path) != expected:
                raise RuntimeError('Original native capture or AX receipt changed before input')
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
    no_symlinks(png)
    if png_dimensions(png) != capture['image_dimensions']:
        raise RuntimeError('Original semantic corroboration PNG dimensions disagree')
    if read_public_json(native) != capture or 'derived_deploy_analysis' in capture:
        raise RuntimeError('Semantic route requires unchanged original focused native receipt')
    native_files = tuple((path, digest(path)) for path in (png, native))
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
    if ax_file.stat().st_size > CAPS['receipt_bytes']:
        raise RuntimeError('Semantic receipt exceeds the original byte cap')
    receipt = read_public_json(ax_file)
    binding = dict(pid=ui.pid, window=ui.window, bounds=list(ui.bounds), nonce=nonce,
                   observer_pid=child.pid, started=started, finished=finished, budget=budget)
    result['semantic_deploy_observation'] = {'receipt_sha256': digest(ax_file), **copy.deepcopy(binding),
                                            'expires_monotonic': expires}
    if child.returncode:
        raise RuntimeError('Semantic Deploy observer failed; original evidence retained')
    private_shape(receipt)
    exposure = validate_observation(receipt, capture, **binding)
    files = (*native_files, (ax_file, digest(ax_file)))
    target = SemanticDeployTarget(capture, receipt, binding, files, expires, ui,
                                  fingerprint([capture, receipt, binding]))
    point = target.point(capture, ui)
    result['semantic_deploy_target'] = {'method': 'fresh-owned-ax-and-original-native-text',
        'button': copy.deepcopy(exposure['button']), 'original_native_row': copy.deepcopy(exposure['original_native_row']),
        'target_points': list(point), 'ocr_confidence_threshold_changed': False,
        'input_delivery_or_gameplay_accepted': False}
    return target
