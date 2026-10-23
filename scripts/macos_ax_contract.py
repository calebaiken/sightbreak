"""Pure read-only AX receipt checks. No semantic observation authorizes input."""
import math
import unicodedata

from macos_native_input import same_bounds
from macos_ordinary_input import capture_geometry, owned_visible_windows
from verify_macos_menu import require_screen


SCHEMA = 'macos-owned-window-ax-read-only-v1'
LABEL = 'DEPLOY · OFFLINE 5V5'
MAPPING = 'AXPosition/AXSize desktop points; identity validated against exact CG window'
CAPS = {'seconds': 5, 'snapshots': 3, 'spacing_seconds': .1, 'call_seconds': .25,
        'depth': 16, 'nodes': 256, 'receipt_bytes': 512 * 1024, 'title_bytes': 512}
ATTRIBUTES = ('AXRole', 'AXChildren', 'AXWindows', 'AXTitle', 'AXPosition',
              'AXSize', 'AXEnabled', 'AXWindow')
READ_APIS = ('AXUIElementCreateApplication', 'AXUIElementGetPid', 'AXUIElementSetMessagingTimeout',
             'AXUIElementCopyAttributeValue', 'AXUIElementGetAttributeValueCount', 'AXUIElementCopyAttributeValues')
PRUNED_ROLES = ('AXTextField', 'AXSecureTextField', 'AXSearchField', 'AXTextArea', 'AXComboBox')
NODE_KEYS = {'node', 'parent', 'depth', 'pid', 'role', 'pruned', 'title',
             'normalized_title', 'enabled', 'frame_points', 'window_frame_points'}


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def rectangle(value):
    if (not isinstance(value, (list, tuple)) or len(value) != 4
            or not all(number(item) for item in value) or min(value[2:]) <= 0):
        raise RuntimeError('Finite positive rectangle required')
    return value


def inside(inner, outer, tolerance=0):
    rectangle(inner); rectangle(outer)
    return (inner[0] >= outer[0] - tolerance and inner[1] >= outer[1] - tolerance
            and inner[0] + inner[2] <= outer[0] + outer[2] + tolerance
            and inner[1] + inner[3] <= outer[1] + outer[3] + tolerance)


def normalized_title(value):
    if not isinstance(value, str):
        raise RuntimeError('Allowed title is malformed or exceeds its finite byte cap')
    try:
        size = len(value.encode('utf-8', errors='strict'))
    except UnicodeError:
        raise RuntimeError('Allowed title is not strict Unicode') from None
    if size > CAPS['title_bytes'] or any(unicodedata.category(char) == 'Cc' for char in value):
        raise RuntimeError('Allowed title contains controls or exceeds its finite byte cap')
    return ' '.join(value.replace('•', '·').split())


def require_owned(rows, pid, window=None, bounds=None):
    if not isinstance(rows, list) or len(rows) > CAPS['nodes']:
        raise RuntimeError('Malformed or oversized owned-window inventory')
    owned = owned_visible_windows(rows, pid)
    if len(owned) != 1:
        raise RuntimeError('Exactly one owned visible layer-zero window required')
    selected = owned[0]
    rectangle(selected.get('bounds_points_including_chrome'))
    if (not isinstance(selected.get('window_id'), int) or isinstance(selected['window_id'], bool)
            or selected['window_id'] <= 0 or (window is not None and selected['window_id'] != window)
            or (bounds is not None and not same_bounds(selected['bounds_points_including_chrome'], bounds))):
        raise RuntimeError('Owned window ID or pinned geometry changed')
    return selected


def require_capture(capture, pid, window, bounds):
    capture_geometry(capture)
    require_screen(capture, 'menu')  # Existing 0.8 menu anchors stay unchanged.
    if (capture.get('owner_pid') != pid or capture.get('window_id') != window
            or not same_bounds(capture.get('bounds_points_including_chrome'), bounds)
            or capture.get('input_events_posted') != 0 or capture.get('permission_requests_made') != 0):
        raise RuntimeError('Original native menu capture is not bound to the pinned owner/window')


def corroborating_text(capture):
    matches = []
    for row in capture.get('text', []):
        if normalized_title(row.get('text')) != LABEL:
            continue
        confidence, box = row.get('confidence'), row.get('box_normalized_bottom_left')
        rectangle(box)
        if (not number(confidence) or not 0 <= confidence <= 1 or min(box[:2]) < 0
                or box[0] + box[2] > 1 or box[1] + box[3] > 1):
            raise RuntimeError('Malformed original Deploy corroboration')
        matches.append(row)
    if len(matches) != 1:
        raise RuntimeError('Exactly one original complete Deploy word sequence required')
    return matches[0]


def validate_request(receipt, *, pid, window, bounds, nonce, observer_pid, started, finished, budget):
    """Bind trust/method/time separately from traversal and semantic readiness."""
    rectangle(bounds)
    if (receipt.get('schema') != SCHEMA or receipt.get('nonce') != nonce
            or receipt.get('owner_pid') != pid or receipt.get('window_id') != window
            or receipt.get('observer_pid') != observer_pid
            or receipt.get('AXIsProcessTrusted') is not True
            or receipt.get('caps') != CAPS or receipt.get('input_events_posted') != 0
            or receipt.get('permission_requests_made') != 0
            or receipt.get('coordinate_mapping') != MAPPING):
        raise RuntimeError('AX receipt prerequisite, source-request or method binding failed')
    first, last = receipt.get('started_monotonic'), receipt.get('finished_monotonic')
    if (not all(number(value) for value in (started, finished, budget, first, last))
            or not 0 < budget <= CAPS['seconds'] or not started <= first <= last <= finished
            or last - first >= budget or finished - started >= budget):
        raise RuntimeError('AX receipt is stale or exceeds its original deadline')
    calls = receipt.get('api_call_counts')
    if (not isinstance(calls, dict) or set(calls) - set(READ_APIS)
            or any(not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 32768
                   for value in calls.values()) or sum(calls.values()) > 32768):
        raise RuntimeError('AX API receipt violates read-only call allowlist/bound')
    return first, last


def validate_collection(receipt, **binding):
    first, last = validate_request(receipt, **binding)
    pid, window, bounds = binding['pid'], binding['window'], binding['bounds']
    if receipt.get('complete') is not True:
        raise RuntimeError('AX traversal did not complete')
    require_owned(receipt.get('last_owned_layer_zero_rows'), pid, window, bounds)
    snapshots = receipt.get('snapshots')
    if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= CAPS['snapshots']:
        raise RuntimeError('Invalid bounded AX snapshot sequence')
    total, previous_snapshot_end = 0, first
    for snapshot in snapshots:
        snap_first, snap_last = snapshot.get('started_monotonic'), snapshot.get('finished_monotonic')
        if (not number(snap_first) or not number(snap_last)
                or not previous_snapshot_end <= snap_first <= snap_last <= last):
            raise RuntimeError('Stale or reordered AX snapshot timestamps')
        previous_snapshot_end = snap_last
        require_owned(snapshot.get('cg_before'), pid, window, bounds)
        require_owned(snapshot.get('cg_after'), pid, window, bounds)
        nodes = snapshot.get('nodes')
        if not isinstance(nodes, list):
            raise RuntimeError('Malformed AX node collection')
        total += len(nodes)
        seen, depths, pruned = set(), {}, set()
        for node in nodes:
            if (set(node) - NODE_KEYS or not isinstance(node.get('node'), int)
                    or isinstance(node['node'], bool) or node['node'] < 0 or node['node'] in seen or node.get('pid') != pid
                    or not isinstance(node.get('depth'), int) or isinstance(node['depth'], bool)
                    or not 0 <= node['depth'] <= CAPS['depth']
                    or not isinstance(node.get('role'), str) or len(node['role']) > 64):
                raise RuntimeError('AX traversal identity/privacy/structure invariant failed')
            parent = node.get('parent')
            if ((node['depth'] == 0 and (seen or parent is not None))
                    or (node['depth'] > 0 and (not isinstance(parent, int) or isinstance(parent, bool)
                        or parent not in seen or parent in pruned or node['depth'] != depths[parent] + 1))):
                raise RuntimeError('AX parent/depth or pruned-subtree provenance failed')
            seen.add(node['node'])
            depths[node['node']] = node['depth']
            role = node['role']
            if role in PRUNED_ROLES and node.get('pruned') is not True:
                raise RuntimeError('Text-entry subtree was not pruned')
            if role in PRUNED_ROLES:
                pruned.add(node['node'])
            if role not in ('AXButton', 'AXWindow') and set(node) & {'title', 'normalized_title'}:
                raise RuntimeError('Unexpected non-button/window title read')
            if 'title' in node and normalized_title(node['title']) != node.get('normalized_title'):
                raise RuntimeError('AX title normalization provenance failed')
        windows = snapshot.get('windows')
        if not isinstance(windows, list) or len(windows) > 1:
            raise RuntimeError('Ambiguous or malformed AX window collection')
        for entry in windows:
            if (set(entry) != {'pid', 'role', 'frame_points', 'title'} or entry['pid'] != pid
                    or entry['role'] != 'AXWindow' or not same_bounds(entry['frame_points'], bounds)):
                raise RuntimeError('AX owned-window structural/frame binding failed')
            normalized_title(entry['title'])
        if nodes and (not windows or nodes[0]['role'] != 'AXWindow'):
            raise RuntimeError('AX nodes lack their unique native window root')
        if snapshot.get('complete') is not any(node['role'] == 'AXButton' for node in nodes):
            raise RuntimeError('AX snapshot completeness does not match observed structure')
    if not 1 <= total <= CAPS['nodes'] or receipt.get('examined_nodes') != total:
        raise RuntimeError('Cumulative AX node cap or receipt count failed')
    latest = snapshots[-1]
    if latest.get('complete') is not True:
        raise RuntimeError('AX tree remained busy/empty/incomplete')
    windows = latest.get('windows', [])
    if len(windows) != 1 or not same_bounds(windows[0].get('frame_points'), bounds):
        raise RuntimeError('Unique AX window/native frame agreement missing')
    return latest


def validate_observation(receipt, capture, **binding):
    """Validate exposure only; never return a click point or alter raw OCR rows."""
    pid, window, bounds = binding['pid'], binding['window'], binding['bounds']
    require_capture(capture, pid, window, bounds)
    latest = validate_collection(receipt, **binding)
    matches = [node for node in latest['nodes'] if node.get('role') == 'AXButton'
               and node.get('normalized_title') == LABEL]
    if len(matches) != 1:
        raise RuntimeError('Unique exact semantic Deploy button missing')
    button = matches[0]
    if (button.get('enabled') is not True or not inside(button.get('frame_points'), bounds)
            or not same_bounds(button.get('window_frame_points'), bounds)):
        raise RuntimeError('Semantic button is disabled or outside the owned native window')
    raw = corroborating_text(capture)
    x, y, width, height = raw['box_normalized_bottom_left']
    text_frame = [bounds[0] + x * bounds[2], bounds[1] + (1-y-height) * bounds[3],
                  width * bounds[2], height * bounds[3]]
    if not inside(text_frame, button['frame_points'], tolerance=.5):
        raise RuntimeError('Original Deploy text region and AX button frame disagree')
    return {'semantic_exposure_only': True, 'unique_semantic_candidate': True,
            'native_pixel_frame_agreement': True, 'button': button, 'original_native_row': raw,
            'original_text_frame_points': text_frame, 'gameplay_target_accepted': False,
            'ocr_confidence_threshold_changed': False}
