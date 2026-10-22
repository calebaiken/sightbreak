# Field menu focus candidate

Builder: `/root`. Independent acceptance: pending fresh-context critic and native exported keyboard proof.

The ordinary FIELD MENU had no initial focus owner. Opening it now selects RESUME,
so a keyboard/controller user can accept, tab through all four actions, and resume.
No labels, settings, gameplay timing or ownership rules changed. The existing focus
style is reused.

The same scene test against baseline561d0cb main reports9 checks/3 failures (the
three repeated missing-focus prerequisites). With the three-line product correction,
30 checks pass: initial RESUME, SETTINGS order, forward/reverse overlay cycle,
ui_accept routing, offline pause/resume and focus release over three cycles.
The maintained input-mode regression passes31 checks. These are synthetic action
and scene-state tests, not hardware or graphical quality acceptance.

Commands, each with a fresh `SIGHTBREAK_STATE_DIR` under builds/mission-m1:

```sh
git show 561d0cb:game/scripts/main.gd > builds/mission-m1/menu-focus-baseline-main.gd
./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd -- --baseline-source="$PWD/builds/mission-m1/menu-focus-baseline-main.gd"
./scripts/godot.sh --headless --script res://tests/menu_focus_test.gd
./scripts/godot.sh --headless --script res://tests/input_mode_test.gd
```

Raw failures and candidate/regression outputs are retained beside this file.
The new test is registered in the maintained suite and native desktop CI. No CI
run is claimed yet. Next: exported OS-keyboard Escape/Return proof and independent
review; then update G6/G7 only to this correction's demonstrated scope.
