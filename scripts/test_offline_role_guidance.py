#!/usr/bin/env python3
"""Declared observation controls only; no exported gameplay or life injection."""
from copy import deepcopy
import unittest

from verify_offline_match import require_planted_guidance_context


class PlantedGuidanceContextTests(unittest.TestCase):
    def setUp(self):
        self.observation = {
            'simulation_tick': 1520, 'phase': 'live', 'round_number': 1,
            'objective_state': 'planted',
            'local_actor': {'id': 1, 'team': 0, 'alive': True, 'health': 100},
            'ui': {'status_text': 'DEFEND THE DEVICE'},
        }

    def require(self, observation):
        require_planted_guidance_context(observation, 1, 1)

    def test_living_original_attacker_context_is_accepted(self):
        self.require(self.observation)
        # Guidance text remains a separate exact predicate at the call site.
        self.observation['ui']['status_text'] = 'Sable  ›  Echo'
        self.require(self.observation)

    def test_death_reports_actual_context_even_with_stale_attacker_text(self):
        for changes in ({'alive': False, 'health': 0}, {'alive': False}, {'health': 0}):
            with self.subTest(changes=changes):
                item = deepcopy(self.observation)
                item['simulation_tick'] = 1833
                item['local_actor'].update(changes)
                with self.assertRaisesRegex(RuntimeError, 'Player died.*1833'):
                    self.require(item)

    def test_replacement_role_round_or_objective_cannot_be_accepted(self):
        for section, field, value in (
                ('local_actor', 'id', 2), ('local_actor', 'team', 1),
                ('', 'round_number', 2), ('', 'phase', 'post'),
                ('', 'objective_state', 'defused')):
            with self.subTest(field=field, value=value):
                item = deepcopy(self.observation)
                (item[section] if section else item)[field] = value
                with self.assertRaisesRegex(RuntimeError, 'lost its actual attacker context'):
                    self.require(item)

    def test_missing_or_invalid_life_is_context_failure(self):
        for field, value in (('alive', None), ('alive', 1), ('health', None),
                             ('health', True), ('health', float('nan')), ('health', 101)):
            with self.subTest(field=field, value=value):
                item = deepcopy(self.observation)
                item['local_actor'][field] = value
                with self.assertRaisesRegex(RuntimeError, 'lost its actual attacker context'):
                    self.require(item)


if __name__ == '__main__':
    unittest.main()
