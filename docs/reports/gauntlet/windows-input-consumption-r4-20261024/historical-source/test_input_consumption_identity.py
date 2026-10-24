#!/usr/bin/env python3
"""Reader regressions from independent malformed traces; no native proof."""
from copy import deepcopy
import unittest

from analyze_input_consumption import analyze
from test_input_consumption_observation import declared_rows, text


class InputObservationIdentityControls(unittest.TestCase):
    def report(self, client=None, authority=None):
        return analyze(text(declared_rows('client') if client is None else client),
                       text(declared_rows('authority') if authority is None else authority))

    def test_direct_receive_requires_fresh_metadata_and_current_binding(self):
        for mutation in ('missing', 'stale', 'unbound'):
            with self.subTest(mutation=mutation):
                rows = declared_rows('authority')
                if mutation == 'missing':
                    rows[3]['latest'].clear()
                elif mutation == 'stale':
                    rows[3]['latest']['input_received']['wall_msec'] -= 1
                else:
                    rows[3].update(peer=10, generation=2, bound_actor=0,
                                   peer_bound=False, joined=False)
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])

    def test_receive_keeps_malformed_prevalidation_payload_as_observation(self):
        rows = declared_rows('authority')
        rows[3]['latest']['input_received'].update(epoch=-1, first=-1, last=-9)
        self.assertTrue(self.report(authority=rows)['diagnostic_complete'])

    def test_accepted_interval_and_send_pending_range_are_required(self):
        rows = declared_rows('authority')
        rows[4]['latest']['input_accepted'].update(first=2, last=1)
        self.assertFalse(self.report(authority=rows)['diagnostic_complete'])
        rows = declared_rows('client')
        rows[5].update(prediction_sequence=2, pending_oldest_sequence=2,
                       pending_newest_sequence=2)
        self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_send_cannot_change_any_welcome_identity_field(self):
        for key, value in (('transport_id', 10), ('local_attempt', 2), ('local_id', 2)):
            with self.subTest(key=key):
                rows = declared_rows('client')
                rows[5][key] = value
                if key == 'local_id':
                    rows[5]['actor']['id'] = value
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])

    def test_disconnection_retires_welcome_until_new_welcome(self):
        # Reuse the same transport/actor after a disconnect. Equality alone
        # must not resurrect the retired welcome.
        for new_welcome in (False, True):
            with self.subTest(new_welcome=new_welcome):
                original = declared_rows('client')
                rows = original[:4]
                for reason in (['client_disconnected', 'welcome_received']
                               if new_welcome else ['client_disconnected']):
                    row = deepcopy(original[4])
                    row['reason'] = reason
                    rows.append(row)
                rows.extend(original[5:])
                counters = {}
                for index, row in enumerate(rows, 1):
                    row['index'] = row['process_frames'] = row['drawn_frames'] = index
                    row['physics_frames'] = index * 2
                    row['wall_msec'] = index * 1000
                    row['wall_unix_msec'] = 100000 + row['wall_msec']
                    counters[row['reason']] = counters.get(row['reason'], 0) + 1
                    if row['snapshot']:
                        counters['snapshot_applied'] = 1
                        row['snapshot_age_msec'] = row['wall_msec'] - row['snapshot']['wall_msec']
                    row['counters'] = deepcopy(counters)
                    if row['reason'] == 'input_send_called':
                        row['latest']['input_send_called']['wall_msec'] = row['wall_msec']
                self.assertEqual(self.report(client=rows)['diagnostic_complete'], new_welcome)

    def test_each_role_rejects_foreign_events_counters_and_latest(self):
        for role, foreign in (('client', 'peer_expired'), ('authority', 'client_disconnected')):
            for location in ('reason', 'counters', 'latest'):
                with self.subTest(role=role, location=location):
                    rows = declared_rows(role)
                    if location == 'reason':
                        rows[-1]['reason'] = foreign
                        rows[-1]['counters'][foreign] = 1
                    elif location == 'counters':
                        rows[-1]['counters'][foreign] = 1
                    else:
                        stage = 'input_accepted' if role == 'client' else 'input_send_called'
                        rows[-1]['latest'][stage] = {
                            'epoch': 1, 'count': 1, 'first': 1, 'last': 1,
                            'fire': 0, 'reload': 0, 'moving': 0, 'wall_msec': 1}
                    kwargs = {role if role == 'client' else 'authority': rows}
                    self.assertFalse(self.report(**kwargs)['diagnostic_complete'])


if __name__ == '__main__':
    unittest.main()
