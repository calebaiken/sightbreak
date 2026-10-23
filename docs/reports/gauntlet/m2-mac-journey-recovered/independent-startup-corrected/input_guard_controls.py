#!/usr/bin/env python3
"""Pure actual-method checks for ambiguity before input allocation."""
import copy
import types
import unittest
from unittest.mock import patch

from independent_controls import base, capture, controller, ordinary, owned


class InputGuards(unittest.TestCase):
    def test_each_owned_down_control_refuses_late_ambiguity_before_event_allocation(self):
        for action in ('button', 'escape', 'reload', 'fire', 'label', 'settings'):
            ui, allocations = controller([owned(), owned(35)]), []
            ui.input_geometry_pinned = True
            ui.diagnostics = lambda: {'foreground_pid': 123, 'pointer_points': [100, 100]}
            ui.cg = types.SimpleNamespace(
                CGEventCreateMouseEvent=lambda *args: allocations.append(args),
                CGEventCreateKeyboardEvent=lambda *args: allocations.append(args))
            with self.subTest(action=action), patch.object(ordinary, 'require_private_userdir'):
                with self.assertRaises(ordinary.OwnedWindowChanged):
                    if action == 'button': ui.button(True, [100, 100])
                    elif action == 'escape': ui.escape(True)
                    elif action == 'reload': ui.reload_key(True)
                    elif action == 'fire': ui.fire_button(True)
                    elif action == 'label': ui.click_label(capture(), 'DEPLOY · OFFLINE 5V5')
                    else: ui.click_settings(capture())
                self.assertEqual(allocations, [])
                self.assertEqual(ui.event_post_attempts, 0)
                self.assertEqual(ui.held, set())

    def test_single_visible_window_pins_with_hidden_foreign_and_nonboolean_decoys(self):
        extras = [owned(35, onscreen=False), owned(36, owner_pid=999), owned(37, onscreen=1)]
        ui = controller([owned(), *extras])
        with patch.object(ordinary, 'require_private_userdir'):
            ui.pin_for_input(capture())
            ui.require_target()
        self.assertTrue(ui.input_geometry_pinned)
        self.assertEqual(ui.event_post_attempts, 0)

    def test_permissions_and_private_isolation_remain_required_before_pin(self):
        for fault in ('permission', 'isolation'):
            ui = controller()
            records = []
            ui.trace = lambda event, **details: records.append((event, copy.deepcopy(details)))
            if fault == 'permission':
                ui.preflight = lambda: {'CGPreflightPostEventAccess': False,
                                       'CGPreflightScreenCaptureAccess': True}
            with self.subTest(fault=fault), patch.object(ordinary, 'require_private_userdir') as private:
                if fault == 'isolation': private.side_effect = RuntimeError('synthetic default/private mismatch')
                with self.assertRaises(RuntimeError): ui.pin_for_input(capture())
                self.assertFalse(ui.input_geometry_pinned)
                self.assertEqual(ui.event_post_attempts, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
