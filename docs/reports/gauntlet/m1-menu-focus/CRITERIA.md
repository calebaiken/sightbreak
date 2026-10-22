# Field menu keyboard focus

Builder: Codex root. Baseline:561d0cb, game tree45b6c6e. Engineering/input component of M1.
Before changing the product, reproduce the missing initial focus in the actual
Godot main controller. A keyboard/controller user opening FIELD MENU must land on
RESUME, navigate to SETTINGS/LEAVE MATCH and explicitly resume without gameplay
input leaking through the menu. Existing pause/focus-release/mobile policies stay
intact. No new strings, geometry or timing rules are needed.

Acceptance: actual scene focus and ui_accept routing checks pass; repeated
open/close leaves no stale focus owner; focus restoration retains the existing
explicit-resume policy; targeted input regressions pass. Test via native exported
keyboard input where available. Synthetic actions alone do not certify hardware,
visual quality or the complete desktop flow. Critic independently reviews actual
outputs. CS2 media parity is outside this mechanical correction's scope.
