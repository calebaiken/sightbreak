"""Authority projection/source contradictions; no native or full-client claim."""
from copy import deepcopy
import unittest

from analyze_input_consumption import (analyze, authority_lifecycle_foundation,
                                       UnknownTransition)
from input_consumption_foundation_model import (AuthorityProjectionEmitter,
                                                declared_histories)
from test_input_consumption_foundation_model import source_negative_proposals
from test_input_consumption_observation import declared_rows, text


def projected_rows(rows):
    """Supply only observer counters to concrete model projection witnesses."""
    result = deepcopy(rows)
    counters = {}
    for row in result:
        counters[row['reason']] = counters.get(row['reason'], 0) + 1
        row['counters'] = deepcopy(counters)
    return result


class AuthorityFoundationEnforcement(unittest.TestCase):
    def test_all_eight_preserved_source_contradictions_are_invalid(self):
        for case in source_negative_proposals():
            before = deepcopy(case['rows'])
            with self.subTest(case=case['id']):
                report = analyze(text(declared_rows('client')), text(case['rows']))
                self.assertFalse(report['diagnostic_complete'], report)
                self.assertEqual(report['transition_status'], 'INVALID', report)
                self.assertEqual(case['rows'], before)

    def test_adjudicated_authority_positive_keeps_stage_results_distinct(self):
        report = analyze(text(declared_rows('client')), text(declared_rows('authority')))
        self.assertTrue(report['diagnostic_complete'], report)
        self.assertNotEqual(report['roles']['authority']['accepted_events'][0]['index'],
                            report['roles']['authority']['consumed_events'][0]['index'])

    def test_every_concrete_model_timer_witness_remains_possible(self):
        for case in declared_histories():
            rows = projected_rows(case['rows'])
            before = deepcopy(rows)
            with self.subTest(case=case['id']):
                authority_lifecycle_foundation(rows)
                self.assertEqual(rows, before)

    def test_selected_peer_sticky_actor_disconnect_and_new_generation(self):
        model = AuthorityProjectionEmitter()
        model.capture('ready', 0)
        model.connect(9, 1)
        model.bind(9, 1, 2)
        model.connect(10, 3)
        model.bind(10, 2, 4)
        model.disconnect(10, 5)
        model.capture('authority_tick', 6)
        model.connect(10, 7)
        model.bind(10, 2, 8)
        authority_lifecycle_foundation(projected_rows(model.rows))

    def test_unsupported_failed_duplicate_connection_is_unknown(self):
        model = AuthorityProjectionEmitter()
        model.capture('ready', 0)
        model.connect(9, 1)
        model.bind(9, 1, 2)
        model.connect(9, 3)
        with self.assertRaises(UnknownTransition):
            authority_lifecycle_foundation(projected_rows(model.rows))

    def test_unsupported_capacity_callback_is_unknown(self):
        model = AuthorityProjectionEmitter()
        model.capture('ready', 0)
        for peer in range(1, 11):
            model.connect(peer, 0)
        model.connect(11, 1)
        with self.assertRaises(UnknownTransition):
            authority_lifecycle_foundation(projected_rows(model.rows))

    def test_no_connect_absence_and_ready_cannot_invent_live_fields(self):
        base = declared_rows('authority')[:1]
        for field, value in [('generation', 1), ('joined', True), ('input_age_msec', 0),
                             ('deadline_remaining_msec', 20000), ('bound_actor', 1),
                             ('peer_bound', True), ('last_bound_actor', 1), ('peer', 9)]:
            rows = deepcopy(base)
            rows[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                authority_lifecycle_foundation(rows)

    def test_tick_cannot_switch_selected_peer_or_sticky_actor(self):
        for field, value in [('peer', 10), ('last_bound_actor', 2)]:
            rows = declared_rows('authority')
            rows[-1][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                authority_lifecycle_foundation(rows)

    def test_timer_contradiction_precedes_packet_origin_unknown(self):
        rows = declared_rows('authority')
        rows[3]['latest']['input_received']['count'] = 0
        rows[-1]['deadline_remaining_msec'] = 30000
        report = analyze(text(declared_rows('client')), text(rows))
        self.assertEqual(report['transition_status'], 'INVALID', report)
        self.assertTrue(any('lifecycle history' in error for error in report['errors']), report)

    def test_anonymous_global_activity_cannot_certify_this_peer(self):
        rows = declared_rows('authority')[:3]
        later = deepcopy(rows[-1])
        later.update(reason='authority_tick', wall_msec=6000,
                     input_age_msec=1000, deadline_remaining_msec=16000)
        later['counters']['input_accepted'] = 1
        later['counters']['authority_tick'] = 1
        rows.append(later)
        with self.assertRaises(UnknownTransition):
            authority_lifecycle_foundation(rows)


if __name__ == '__main__':
    unittest.main()
