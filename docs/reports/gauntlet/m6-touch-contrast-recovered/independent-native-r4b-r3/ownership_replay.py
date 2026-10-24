#!/usr/bin/env python3
"""Independent native winner-map replay using source loop comparisons."""
import datetime
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
RAW = Path('/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3')
started = time.monotonic()
totals = {}
errors = []
for variant in ('baseline', 'candidate'):
    rows = []
    for metadata in sorted((RAW / variant).glob('*/scene.json')):
        info = json.loads(metadata.read_text())
        order = [action for action in info['action_order'] if action != 'move']
        assert len(order) == len(set(order)) == 11
        for component in order:
            path = metadata.parent / ('component_' + component + '-footprint.png')
            assert hashlib.sha256(path.read_bytes()).hexdigest() == info['images'][path.name]
            image = np.asarray(Image.open(path).convert('RGB'))
            ys, xs = np.where(image.max(axis=-1) >= 1)
            best = np.full(len(xs), np.inf)
            winners = np.full(len(xs), '', dtype='<U8')
            for action in order:
                data = info['geometry'][action]
                # Preserve the baseline's radius/1.25 rule and native order;
                # the candidate uses hit_radius/1 and lexicographic exact ties.
                denominator = data['radius'] if variant == 'baseline' else data['hit_radius']
                distance = np.sqrt((xs + .5 - data['point'][0]) ** 2 + (ys + .5 - data['point'][1]) ** 2) / denominator
                inside = distance <= (1.25 if variant == 'baseline' else 1.0)
                better = distance < best
                if variant == 'candidate':
                    better |= (distance == best) & (action < winners)
                choose = inside & better
                best[choose] = distance[choose]
                winners[choose] = action
            wrong = winners != component
            replay = {(int(x), int(y)): str(winner) for x, y, winner in zip(xs[wrong], ys[wrong], winners[wrong])}
            record = info['ownership'][component]
            native = {(x, y): winner for x, y, winner in record['wrong_owner_witnesses_xy_action']}
            native_unique = len(native) == len(record['wrong_owner_witnesses_xy_action'])
            unclaimed = int((winners == '').sum())
            support_valid = all(type(x) is int and type(y) is int and 0 <= y < image.shape[0] and 0 <= x < image.shape[1] and image[y, x].max() >= 1 and winner in (*order, '') and winner != component for (x, y), winner in native.items())
            matches = native_unique and support_valid and native == replay and record['support_pixels'] == len(xs) and record['wrong_owner_pixels'] == len(replay) and record['unclaimed_pixels'] == unclaimed
            row = {'scene': info['id'], 'action': component, 'complete_support_pixels': len(xs), 'wrong_owner_pixels': len(replay), 'unclaimed_pixels': unclaimed, 'native_map_matches_source_loop_replay': bool(matches)}
            rows.append(row)
            if not matches:
                errors.append({**row, 'missing_native_witnesses': [[x, y, replay[(x, y)]] for x, y in replay.keys() - native.keys()], 'extra_native_witnesses': [[x, y, native[(x, y)]] for x, y in native.keys() - replay.keys()], 'different_winners': [[x, y, native[(x, y)], replay[(x, y)]] for x, y in native.keys() & replay.keys() if native[(x, y)] != replay[(x, y)]]})
    totals[variant] = {'component_rows': len(rows), 'complete_support_pixels': sum(row['complete_support_pixels'] for row in rows), 'wrong_owner_pixels': sum(row['wrong_owner_pixels'] for row in rows), 'unclaimed_pixels': sum(row['unclaimed_pixels'] for row in rows), 'all_native_maps_match_source_loop_replay': all(row['native_map_matches_source_loop_replay'] for row in rows), 'rows': rows}
result = {'kind': 'INDEPENDENT_COMPLETE_NATIVE_SOURCE_LOOP_OWNERSHIP_REPLAY', 'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sources': totals, 'errors': errors, 'provenance_agreement_pass': not errors and all(value['component_rows'] == 352 and value['all_native_maps_match_source_loop_replay'] for value in totals.values()), 'bad_baseline_product_quality_is_not_provenance_failure': True, 'wall_seconds': time.monotonic() - started}
(OUT / 'ownership-replay.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'sources'}))
raise SystemExit(not result['provenance_agreement_pass'])
