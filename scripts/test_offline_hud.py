#!/usr/bin/env python3
"""Negative controls for the exported-client living-player evidence gate."""
import unittest
from offline_hud import parse_hud_text, require_paused_training


class LivingHUDTests(unittest.TestCase):
    def test_offline_pause_requires_both_rendered_labels(self):
        text = 'FIELD MENU\nTraining is paused.\nRESUME\n'
        self.assertEqual(require_paused_training(text), text)

    def test_network_menu_and_missing_pause_proof_fail_closed(self):
        for text in ('', 'FIELD MENU', 'Training is paused.',
                     'FIELD MENU\nThe match continues while this menu is open.',
                     'FIELD MENU\nTraining is paused.\nThe match continues.'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                require_paused_training(text)

    def test_actual_v2_ocr_is_recognized(self):
        record = parse_hud_text('800 - FUNDS\n100 - HEALTH .\n', 'SIDEARM 14/60\nFRAG x1 SMOKE <1\n')
        self.assertEqual((record['health'], record['ammo'], record['reserve']), (100, 14, 60))

    def test_positive_damaged_player_is_recognized(self):
        self.assertEqual(parse_hud_text('025 · HEALTH', '12 / 60')['health'], 25)

    def test_blank_zero_unreadable_and_ambiguous_health_fail_closed(self):
        for status in ('', '000 HEALTH', 'HEALTH', 'l00 HEALTH', '101 HEALTH', '-1 HEALTH',
                       '100 HEALTH\n000 HEALTH', '100 HEALTH\nELIMINATED', '100 HEALTH\nSPECTATING'):
            with self.subTest(status=status), self.assertRaises(ValueError):
                parse_hud_text(status, '12 / 60')

    def test_unreadable_or_ambiguous_ammunition_rejected(self):
        for text in ('', 'SIDEARM l2/6O', '-12/60', '12/60\n15/59'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_hud_text('100 HEALTH', text)


if __name__ == '__main__':
    unittest.main()
