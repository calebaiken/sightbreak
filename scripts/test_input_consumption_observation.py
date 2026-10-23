#!/usr/bin/env python3
"""Synthetic schema/counterexamples and exact source invariance; no native proof."""
import argparse
import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from analyze_input_consumption import analyze, analyze_role, parse_log, PREFIX

ROOT = Path(__file__).resolve().parents[1]
BASE_HASHES = {
    'game/scripts/gameplay/match.gd': '2db21ed6eb27d2095e899db836b417288c8a96e5e3239c8aa7affa6bb6a54173',
    'scripts/fixtures/export_integration.gd': 'b5621ad5e52d17b938e81a285b4e690dc2bf10ae5955c0ae43442c78e0c079e4',
    'scripts/verify_integration_export.py': '6de6b78597d5af681f3ee883886422b065ebe2c2f96a72f628ff52e502f698fe',
    'game/tests/movement_prediction_test.gd': 'aad242761fcd1541183fd29470530e6a883ed57b0b55134e418987691b0e344d',
    'scripts/validate.sh': 'd7c87f91a61caee769a37f1d5f97c3e1efa17015a85ba82823e7a153f4063d4f',
}


def without_observer(text):
    inside, output = False, []
    for line in text.splitlines(keepends=True):
        if '# BEGIN INPUT OBSERVATION' in line:
            if inside:
                raise ValueError('nested diagnostic block')
            inside = True
        elif '# END INPUT OBSERVATION' in line:
            if not inside:
                raise ValueError('unmatched diagnostic block end')
            inside = False
        elif not inside and '# INPUT_OBSERVATION_HOOK' not in line:
            output.append(line)
    if inside:
        raise ValueError('unterminated diagnostic block')
    return ''.join(output)


def control(sequence=-1, fire=False):
    return {'sequence': sequence, 'fire': fire, 'reload': False, 'move': [0.0, 0.0]}


def declared_rows(role):
    """Hand-authored parser fixtures, never acquired native observations."""
    stages = (['ready', 'client_attempt', 'client_connected', 'welcome_received', 'client_tick', 'input_send_called', 'client_tick']
              if role == 'client' else ['ready', 'peer_connected', 'peer_bound', 'input_received', 'input_accepted', 'input_consumed', 'authority_tick'])
    counters, rows = {}, []
    for index, reason in enumerate(stages, 1):
        now = index * 1000 + (4000 if role == 'authority' and index >= 4 else 0)
        counters[reason] = counters.get(reason, 0) + 1
        if role == 'client' and index >= 5:
            counters['snapshot_applied'] = 1
        snapshot = {'tick': 50, 'epoch': 1, 'own_ack': 1, 'wall_msec': 4000} if role == 'client' and index >= 5 else {}
        bound = role == 'authority' and index >= 3
        latest = {}
        packet = {'epoch': 1, 'count': 1, 'first': 1, 'last': 1, 'fire': 1, 'reload': 0, 'moving': 0, 'wall_msec': now}
        if reason in {'input_send_called', 'input_received', 'input_accepted'}:
            latest[reason] = packet
        if reason == 'input_consumed':
            latest[reason] = {**control(1, True), 'peer': 9, 'actor': 1, 'generation': 1, 'wall_msec': now}
        rows.append({
            'schema': 1, 'scope': 'debug_guest_loopback_input_observation', 'role': role, 'reason': reason,
            'index': index, 'wall_unix_msec': 100000 + now, 'wall_msec': now,
            'process_frames': index, 'physics_frames': index * 2, 'drawn_frames': index,
            'connection_state': 'connected' if role == 'client' else 'hosting', 'transport_status': 2,
            'transport_id': 9 if role == 'client' else 1,
            'local_id': 1 if role == 'client' else 0, 'local_attempt': 1 if role == 'client' and index >= 2 else 0,
            'peer': 9 if role == 'authority' and index >= 2 else 0,
            'bound_actor': 1 if bound else 0, 'last_bound_actor': 1 if bound else 0, 'peer_bound': bound,
            'generation': 1 if role == 'authority' and index >= 2 else -1, 'joined': bound,
            'input_age_msec': 0 if bound else -1, 'deadline_remaining_msec': 20000 if bound else -1,
            'simulation_tick': index if role == 'authority' else 0, 'authority_epoch': 1,
            'stream_ack': 1 if bound else -1, 'queue_count': 0, 'stream_rejected': 0, 'stream_skipped': 0,
            'prediction_epoch': 1 if role == 'client' else -1, 'prediction_sequence': 1 if role == 'client' else 0,
            'pending_count': 1 if reason == 'input_send_called' else 0, 'pending_oldest_sequence': 1 if reason == 'input_send_called' else -1, 'pending_newest_sequence': 1 if reason == 'input_send_called' else -1,
            'snapshot': snapshot, 'snapshot_age_msec': now - snapshot['wall_msec'] if snapshot else -1,
            'local_input': control(), 'physical': {'r': False, 'lmb': False, **({'physical_mouse_fire': False, 'application_focused': True, 'paused': False, 'waiting_for_input_release': False} if role == 'client' else {})},
            'counters': deepcopy(counters), 'latest': latest,
            'actor': {'id': 1, 'alive': True, 'ammo': 30, 'reserve': 90, 'reload': 0.0, 'input': control()} if bound or role == 'client' else {},
        })
    return rows


def text(rows):
    return 'SYNTHETIC PURE PARSER FIXTURE ONLY\n' + '\n'.join(PREFIX + json.dumps(row) for row in rows)


class InputConsumptionControls(unittest.TestCase):
    def report(self, client=None, authority=None):
        return analyze(text(declared_rows('client') if client is None else client),
                       text(declared_rows('authority') if authority is None else authority))

    def test_complete_declared_pipeline_keeps_acceptance_separate_from_consumption(self):
        report = self.report()
        self.assertTrue(report['diagnostic_complete'], report['errors'])
        authority = report['roles']['authority']
        self.assertEqual(len(authority['accepted_events']), 1)
        self.assertEqual(len(authority['consumed_events']), 1)
        self.assertNotEqual(authority['accepted_events'][0]['index'], authority['consumed_events'][0]['index'])
        self.assertTrue(report['cause_status'].startswith('UNRESOLVED'))

    def test_empty_original_style_logs_cannot_be_retroactively_qualified(self):
        report = analyze('MATCH: Server disconnected. Attempting to reconnect\n', 'SERVER_NOTICE Operator disconnected; bot taking over\n')
        self.assertFalse(report['diagnostic_complete'])
        self.assertEqual(len(report['errors']), 2)

    def test_packet_accepted_without_consumed_event_is_insufficient(self):
        rows = declared_rows('authority')
        rows[5]['reason'] = 'authority_tick'
        for row in rows:
            row['counters'].pop('input_consumed', None)
            row['counters']['authority_tick'] = 1
        report = self.report(authority=rows)
        self.assertFalse(report['diagnostic_complete'])
        self.assertIn('missing pipeline stages', str(report['errors']))

    def test_missing_direct_event_cannot_be_replaced_by_counter_claim(self):
        rows = declared_rows('authority')
        rows[3]['reason'] = 'authority_tick'
        rows[3]['counters']['authority_tick'] = 1
        for row in rows[4:]:
            row['counters']['authority_tick'] = 1
        report = self.report(authority=rows)
        self.assertFalse(report['diagnostic_complete'])
        self.assertIn('direct pipeline', str(report['errors']))

    def test_old_generation_or_actor_alias_cannot_qualify_current_consumption(self):
        for field, value in [('generation', 2), ('peer', 10), ('bound_actor', 2)]:
            rows = declared_rows('authority')
            rows[5][field] = value
            with self.subTest(field=field):
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])
        rows = declared_rows('authority')
        rows[5]['latest']['input_consumed']['generation'] = 0
        self.assertIn('consumed identity', str(self.report(authority=rows)['errors']))

    def test_welcome_links_transport_identity_to_authority_generation_without_actor_guessing(self):
        report = self.report()
        self.assertTrue(report['diagnostic_complete'], report['errors'])
        self.assertEqual(report['attempt_generation_links'], [{'client_local_attempt': 1, 'peer': 9, 'generation': 1, 'bound_actor': 1, 'wall_unix_msec': 103000}])
        rows = declared_rows('client')
        rows[3]['transport_id'] = 10
        self.assertIn('welcome cannot bind', str(self.report(client=rows)['errors']))

    def test_stale_send_call_metadata_or_impossible_pending_history_is_rejected(self):
        for change in ('metadata', 'history'):
            rows = declared_rows('client')
            if change == 'metadata':
                rows[5]['latest']['input_send_called']['wall_msec'] = 1
            else:
                rows[5]['pending_oldest_sequence'] = 2
            with self.subTest(change=change):
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_retired_generation_cannot_consume_even_when_actor_id_is_reused(self):
        rows = declared_rows('authority')
        expired = deepcopy(rows[4])
        expired['reason'] = 'peer_disconnected'
        rows.insert(5, expired)
        for index, row in enumerate(rows, 1):
            row['index'] = index
            if index >= 6:
                row['counters']['peer_disconnected'] = 1
        self.assertIn('current observed peer-generation', str(self.report(authority=rows)['errors']))

    def test_reordered_indices_wall_frames_and_regressed_counters_are_rejected(self):
        for field, value in [('index', 1), ('wall_msec', 0), ('wall_unix_msec', 0), ('physics_frames', 0)]:
            rows = declared_rows('authority')
            rows[5][field] = value
            with self.subTest(field=field):
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])
        rows = declared_rows('client')
        rows[-1]['counters']['client_attempt'] = 0
        self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_stale_epoch_or_stale_latest_metadata_never_qualifies_an_input_stage(self):
        for reason, field, value in [('input_accepted', 'epoch', 0), ('input_consumed', 'wall_msec', 1000), ('input_consumed', 'sequence', 0)]:
            rows = declared_rows('authority')
            row = next(r for r in rows if r['reason'] == reason)
            row['latest'][reason][field] = value
            with self.subTest(field=field):
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_pending_saturation_and_large_gap_remain_observations_without_cause(self):
        rows = declared_rows('client')
        row = rows[-1]
        row.update(wall_msec=50000, wall_unix_msec=150000, snapshot_age_msec=46000,
                   pending_count=120, prediction_sequence=502, pending_oldest_sequence=383, pending_newest_sequence=502)
        row['physical']['lmb'] = row['physical']['physical_mouse_fire'] = row['local_input']['fire'] = True
        report = self.report(client=rows)
        self.assertTrue(report['diagnostic_complete'], report['errors'])
        self.assertEqual(report['roles']['client']['pending_saturation_indices'], [7])
        self.assertEqual(report['roles']['client']['max_snapshot_age_msec'], 46000)
        self.assertEqual(report['roles']['client']['max_observation_gap_msec'], 44000)
        self.assertTrue(report['cause_status'].startswith('UNRESOLVED'))

    def test_truncation_and_mixed_roles_are_rejected(self):
        for field, value in [('reason', 'observation_limit'), ('role', 'authority'), ('index', 1025)]:
            rows = declared_rows('client')
            rows[-1][field] = value
            with self.subTest(field=field):
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_unexpected_private_payload_or_other_actor_fields_are_rejected(self):
        for section, field, value in [('', 'ticket', 'fictional'), ('actor', 'position', [1, 2, 3]), ('physical', 'profile', {}), ('actor', 'id', 2)]:
            rows = declared_rows('client')
            (rows[-1][section] if section else rows[-1])[field] = value
            with self.subTest(field=field):
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_bool_counters_nan_move_and_impossible_packet_counts_are_rejected(self):
        rows = declared_rows('client')
        rows[-1]['prediction_sequence'] = True
        self.assertFalse(self.report(client=rows)['diagnostic_complete'])
        rows = declared_rows('client')
        rows[-1]['local_input']['move'][0] = float('nan')
        self.assertFalse(self.report(client=rows)['diagnostic_complete'])
        rows = declared_rows('authority')
        rows[4]['latest']['input_accepted']['fire'] = 13
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_malformed_or_embedded_prefix_is_not_a_record(self):
        for raw in [PREFIX + '{', 'notice ' + PREFIX + '{}', PREFIX + '{"role":"client","role":"client"}']:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_log(raw)

    def test_stripping_only_marked_additions_recovers_exact_original_sources(self):
        for name, expected in BASE_HASHES.items():
            with self.subTest(path=name):
                original = without_observer((ROOT / name).read_text()).encode()
                self.assertEqual(hashlib.sha256(original).hexdigest(), expected)

    def test_unbalanced_source_markers_are_rejected(self):
        for source in ['# BEGIN INPUT OBSERVATION X\n', '# END INPUT OBSERVATION X\n', '# BEGIN INPUT OBSERVATION X\n# BEGIN INPUT OBSERVATION Y\n']:
            with self.assertRaises(ValueError):
                without_observer(source)

    def test_observer_additions_do_not_call_gameplay_transport_or_input_mutators(self):
        source = (ROOT / 'game/scripts/gameplay/match.gd').read_text()
        methods = source.split('# BEGIN INPUT OBSERVATION METHODS\n')[1].split('# END INPUT OBSERVATION METHODS')[0]
        forbidden = [r'@rpc', r'\.rpc(?:_id)?\(', r'_input_stream\.(?:accept|pop|forget|reset_epoch)\(',
                     r'_prediction\.(?:predict|packet|reconcile|reset)\(', r'_peer_lifecycle\.(?:active|allow_input|admitted|forget|reject|connected)\(',
                     r'\b(?:set_local_input|start_reload|_connect_client|_apply_snapshot)\(',
                     r'Input\.(?:parse_input_event|action_press|action_release|flush_buffered_events)\(',
                     r'^\s*(?:actor\.|options\[|_local_input\s*=|_peer_actors\[|_last_input_sequence\[|connection_state\s*=)']
        for pattern in forbidden:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, methods, flags=re.M))
        self.assertIn('if _native_input_observation.is_empty(): return', methods)
        self.assertIn('if int(diagnostic.count) >= 1024: return', methods)
        self.assertIn('"observation_limit" if int(diagnostic.count) == 1023', methods)
        self.assertIn('now - int(diagnostic.last_emit) < 1000', methods)

    def test_actual_controller_flag_is_opt_in_and_adds_only_debug_user_arguments(self):
        tree = ast.parse((ROOT / 'scripts/verify_integration_export.py').read_text())
        declaration = next(node for node in ast.walk(tree) if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and any(isinstance(arg, ast.Constant) and arg.value == '--observe-input-consumption' for arg in node.value.args))
        additions = sorted((node for node in ast.walk(tree) if isinstance(node, ast.If) and isinstance(node.test, ast.Attribute) and node.test.attr == 'observe_input_consumption'), key=lambda node: node.lineno)
        self.assertEqual(len(additions), 3)
        for enabled in (False, True):
            parser = argparse.ArgumentParser()
            exec(compile(ast.Module(body=[declaration], type_ignores=[]), 'actual-observer-argument', 'exec'), {'parser': parser})
            args = parser.parse_args(['--observe-input-consumption'] if enabled else [])
            env = {'args': args, 'result': {}, 'client_command': ['game', '--quit-after', '10'], 'server_command': ['godot', '--', '--output=fresh']}
            exec(compile(ast.Module(body=additions, type_ignores=[]), 'actual-observer-commands', 'exec'), env)
            self.assertEqual(env['client_command'], ['game', '--quit-after', '10'] + (['--', '--native-input-observation'] if enabled else []))
            self.assertEqual(env['server_command'], ['godot', '--', '--output=fresh'] + (['--native-input-observation'] if enabled else []))
            self.assertEqual(bool(env['result']), enabled)


if __name__ == '__main__':
    unittest.main()
