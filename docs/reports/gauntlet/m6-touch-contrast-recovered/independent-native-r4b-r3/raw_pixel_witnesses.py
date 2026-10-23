#!/usr/bin/env python3
"""Read exact failed native pixels; keep every registered failure unchanged."""
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from PIL import Image

RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
OUT = Path(__file__).resolve().parent
original = json.loads((RAW / 'recomputed.json').read_text())
read = lambda p: np.asarray(Image.open(p).convert('RGB'), dtype=np.int16)
started = time.monotonic()
failed = []
for row in original['candidate']['rows']:
    if row['gate'] == 'retained_intermediate_stroke_diagnostic' or row['pass']:
        continue
    scene = RAW / 'candidate' / row['scene']
    images = {'normal': read(scene / 'normal.png')}
    for part in ('underlay', 'black', 'white', 'footprint'):
        images[part] = read(scene / (row['group'] + '-' + part + '.png'))
    delta = images['white'] - images['black']
    bad = np.argwhere(delta.max(axis=-1) - delta.min(axis=-1) > 1)
    pixels = []
    for y, x in bad:
        pixels.append({'yx': [int(y), int(x)], 'rgb': {key: value[y, x].tolist() for key, value in images.items()}, 'diagnostic_delta_rgb': delta[y, x].tolist(), 'diagnostic_channel_spread': int(delta[y, x].max() - delta[y, x].min()), 'complete_footprint_supported': bool(images['footprint'][y, x].max() >= 1)})
    assert len(pixels) == row['nonneutral_coverage_pixels'] == 1
    assert not any(row.get(key, 0) for key in ('outside_changed', 'unexpected_support_pixels', 'underlay_compositing_errors', 'missing_footprint_pixels', 'negative_diagnostic_pixels', 'unqualified_contours'))
    failed.append({'scene': row['scene'], 'group': row['group'], 'original_required': row['required'], 'original_contrast_lower_bound': row['contrast_lower_bound'], 'original_resolved': row['resolved'], 'original_pass': row['pass'], 'actual_nonneutral_witnesses': pixels, 'interpretation': 'The unchanged diagnostic-neutrality predicate fails on a two-code channel spread. No threshold or registered result is changed.'})

glyphs = []
for variant in ('baseline', 'candidate'):
    for layout in ('mobile-min', 'mobile-max'):
        scene = RAW / variant / (layout + '-white-idle')
        info = json.loads((scene / 'scene.json').read_text())
        footprint = read(scene / 'active_label-footprint.png')
        components = {action: read(scene / ('component_' + action + '-footprint.png')) for action in info['paint_geometry']}
        yy, xx = np.where(footprint.max(axis=-1) >= 1)
        assignments = np.zeros(len(xx), dtype=np.int16)
        memberships = {}
        for action, data in info['paint_geometry'].items():
            if info['counts'].get(action, 1) <= 0:
                continue
            ox, oy = data['label_origin']
            in_bounds = (xx + .5 >= ox - 1) & (xx + .5 <= ox + data['label_width'] + 1) & (yy + .5 >= oy - data['font_ascent'] - 1) & (yy + .5 <= oy + data['font_descent'] + 1)
            in_component = components[action][yy, xx].max(axis=-1) >= 1
            memberships[action] = (in_bounds, in_component)
            assignments += in_bounds & in_component
        witnesses = []
        for index in np.flatnonzero(assignments != 1):
            y, x = int(yy[index]), int(xx[index])
            distances = {action: float(np.hypot(x + .5 - data['point'][0], y + .5 - data['point'][1]) / data['hit_radius']) for action, data in info['paint_geometry'].items()}
            nearest = min(distances, key=distances.get)
            witnesses.append({'yx': [y, x], 'assignments': int(assignments[index]), 'footprint_rgb': footprint[y, x].tolist(), 'source_bounds_containing': [action for action, (bounds, component) in memberships.items() if bounds[index]], 'complete_components_containing': [action for action, image in components.items() if image[y, x].max() >= 1], 'nearest_normalized_hit_action': nearest, 'nearest_normalized_hit_distance': distances[nearest], 'nearest_label_metadata': info['paint_geometry'][nearest]})
        glyphs.append({'variant': variant, 'scene': scene.name, 'active_label_support': len(xx), 'unassigned_or_multiple_pixels': witnesses, 'assignment_zero_count': int((assignments == 0).sum()), 'assignment_multiple_count': int((assignments > 1).sum())})

result = {'kind': 'INDEPENDENT_ORIGINAL_RAW_PIXEL_WITNESSES', 'original_analyzer_sha256': hashlib.sha256((RAW / 'recomputed.json').read_bytes()).hexdigest(), 'candidate_failed_gated_rows': failed, 'mobile_active_label_witnesses': glyphs, 'original_gates_unchanged': True, 'wall_seconds': time.monotonic() - started}
(OUT / 'raw-pixel-witnesses.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
