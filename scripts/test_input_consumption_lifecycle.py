#!/usr/bin/env python3
"""Pure source-bound lifecycle/header regressions; never native qualification."""
from copy import deepcopy
import unittest

from analyze_input_consumption import analyze, analyze_role
from test_input_consumption_observation import declared_rows, text


def restamp(rows):
    """Retain declared data while making inserted/reordered events coherent."""
    counters, latest = {}, {}
    for index, row in enumerate(rows, 1):
        reason = row['reason']
        now = index * 1000 + (4000 if row['role'] == 'authority' and index >= 4 else 0)
        row.update(index=index, process_frames=index, physics_frames=index * 2,
                   drawn_frames=index, wall_msec=now, wall_unix_msec=100000 + now)
        counters[reason] = counters.get(reason, 0) + 1
        if row['snapshot']:
            counters['snapshot_applied'] = 1
            snapshot = deepcopy(latest.get('snapshot_applied', row['snapshot']))
            if 'snapshot_applied' not in latest:
                snapshot['wall_msec'] = rows[index - 2]['wall_msec'] if index > 1 else now
            row['snapshot'] = snapshot
            row['snapshot_age_msec'] = now - row['snapshot']['wall_msec']
        row['counters'] = deepcopy(counters)
        if reason in row['latest']:
            latest[reason] = deepcopy(row['latest'][reason])
            latest[reason]['wall_msec'] = now
        if row['snapshot']:
            latest['snapshot_applied'] = deepcopy(row['snapshot'])
        row['latest'] = deepcopy(latest)
    return rows


class InputObservationLifecycleControls(unittest.TestCase):
    def report(self, client=None, authority=None):
        return analyze(text(declared_rows('client') if client is None else client),
                       text(declared_rows('authority') if authority is None else authority))

    def test_binding_requires_its_preceding_connected_peer_and_generation(self):
        for mutation in ('generation', 'peer', 'before_connection'):
            with self.subTest(mutation=mutation):
                rows = declared_rows('authority')
                if mutation == 'before_connection':
                    rows[1], rows[2] = rows[2], rows[1]
                    restamp(rows)
                else:
                    value = 2 if mutation == 'generation' else 10
                    for row in rows[2:]:
                        row[mutation] = value
                        if 'input_consumed' in row['latest']:
                            row['latest']['input_consumed'][mutation] = value
                client = declared_rows('client')
                if mutation == 'peer':
                    for row in client[2:]:
                        row['transport_id'] = 10
                self.assertFalse(self.report(client=client, authority=rows)['diagnostic_complete'])

    def test_one_live_identity_cannot_emit_a_second_binding(self):
        for actor in (1, 2):
            with self.subTest(actor=actor):
                rows = declared_rows('authority')
                rows.insert(3, deepcopy(rows[2]))
                for row in rows[3:]:
                    row.update(bound_actor=actor, last_bound_actor=actor)
                    row['actor']['id'] = actor
                    if 'input_consumed' in row['latest']:
                        row['latest']['input_consumed']['actor'] = actor
                self.assertFalse(self.report(authority=restamp(rows))['diagnostic_complete'])

    def test_fresh_generation_after_retirement_can_reuse_peer_and_actor(self):
        rows = declared_rows('authority')
        disconnected = deepcopy(rows[-1])
        disconnected['reason'] = 'peer_disconnected'
        rows.append(disconnected)
        for original in declared_rows('authority')[1:]:
            row = deepcopy(original)
            row['generation'] = 2
            if 'input_consumed' in row['latest']:
                row['latest']['input_consumed']['generation'] = 2
            rows.append(row)
        report = analyze_role(restamp(rows), 'authority')
        self.assertEqual([row['generation'] for row in report['binding_events']], [1, 2])
        self.assertEqual([row['generation'] for row in report['consumed_events']], [1, 2])

    def test_first_acceptance_cannot_precede_first_direct_receive(self):
        rows = declared_rows('authority')
        rows[3], rows[4] = rows[4], rows[3]
        self.assertFalse(self.report(authority=restamp(rows))['diagnostic_complete'])

    def test_attempt_number_and_counter_match_actual_attempt_events(self):
        for mutation in ('number', 'counter', 'before_first_attempt'):
            with self.subTest(mutation=mutation):
                rows = declared_rows('client')
                if mutation == 'number':
                    for row in rows[3:]:
                        row['local_attempt'] = 2
                elif mutation == 'counter':
                    for row in rows[3:]:
                        row['counters']['client_attempt'] = 2
                else:
                    rows[0]['local_attempt'] = 1
                self.assertFalse(self.report(client=rows)['diagnostic_complete'])
        # A real failed first attempt followed by a second attempt is permitted.
        rows = declared_rows('client')
        failed = deepcopy(rows[1])
        failed['reason'] = 'client_connection_failed'
        rows[2:2] = [failed, deepcopy(rows[1])]
        for row in rows[3:]:
            row['local_attempt'] = 2
        report = self.report(client=restamp(rows))
        self.assertTrue(report['diagnostic_complete'], report['errors'])

    def test_accepted_header_permits_unordered_or_duplicate_batch_endpoints(self):
        # Source accept stages a dictionary, without sorting/requiring unique
        # incoming sequences. Header endpoints retain the original array order.
        for first, last in ((2, 1), (1, 1)):
            with self.subTest(first=first, last=last):
                rows = declared_rows('authority')
                for row in rows:
                    popped = row['reason'] in {'input_consumed', 'authority_tick'}
                    row['stream_ack'] = 1 if popped else -1
                    row['queue_count'] = (2 if first != last else 1) if row['reason'] == 'input_accepted' else int(popped and first != last)
                    for stage in ('input_received', 'input_accepted'):
                        if stage in row['latest']:
                            row['latest'][stage].update(count=2, first=first, last=last, fire=2)
                    if popped:
                        row['actor']['input'].update(sequence=1, fire=True)
                report = self.report(authority=rows)
                self.assertTrue(report['diagnostic_complete'], report['errors'])

    def test_single_command_accepted_header_requires_equal_positive_endpoints(self):
        for first, last in ((0, 0), (1, 2), (2, 1)):
            with self.subTest(first=first, last=last):
                rows = declared_rows('authority')
                rows[4]['latest']['input_accepted'].update(first=first, last=last)
                self.assertFalse(self.report(authority=rows)['diagnostic_complete'])


if __name__ == '__main__':
    unittest.main()
