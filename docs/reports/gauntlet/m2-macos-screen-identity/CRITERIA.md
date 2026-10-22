# Native Mac screen identity and leak diagnostic criteria

Base: f8b7e8272a104aadf890328b5ff4fc26374b5daf. Preregistered before implementation.
This is a source observer iteration. Run 39732825169 at b09cfe1 remains failed.

## Inspected benchmark

The actual owned PID 4062/window 45 screenshots show the home menu, then FIELD
SETTINGS, then the returned home menu after five real CoreGraphics event attempts.
The returned original PNG SHA-256 is
`c17ca318ef148c0e444136048f8f914bade3770366c29acb6d619cb71427adeb`.
Its JSON SHA-256 is
`3b087c989452ec9b24068b4abdddf849e5822686afcc824de582c2b50e72f1eb`.
Vision merged the small masthead into `S/B TACTICAL OPERATIONS` at confidence 0.5;
the current 0.8 gate correctly rejects that observation. The large `SIGHTBREAK`
hero and the `OPERATOR RECORD` and `SETTINGS` controls are each exact, distinct,
and confidence 1 in both actual home captures. The actual settings capture has
`FIELD SETTINGS` at confidence 1 and lacks that home trio. The title bar reads
`SIGHTBREAK (DEBUG)` on both screens and cannot establish home identity.

Source `game/scripts/main.gd` declares the home hero and controls in `show_menu`
and the settings heading in `show_settings`. The new criterion uses those visible
screen roles. It does not infer navigation from artifact names or event attempts.
The original JSON fixtures are retained byte for byte with a provenance manifest.

## Required screen observations

- Home requires exactly one normalized, exact `SIGHTBREAK`, `OPERATOR RECORD`,
  and `SETTINGS` observation, each with finite numeric confidence at least 0.8,
  a positive box, and a finite normalized box entirely inside the original image.
  Case and whitespace normalization remain supported; substrings, fuzzy matches,
  title-bar suffixes, and low-confidence masthead text cannot qualify.
- Settings requires exactly one normalized, exact, in-bounds `FIELD SETTINGS`
  observation at the same 0.8 threshold. Home rejects that settings heading;
  settings rejects any qualifying home identity label. Uniqueness and opposing
  labels concern qualifying finite numeric observations at confidence at least
  0.8, as in the existing target gate. A required label cannot be supplied by
  missing, foreign, partial, malformed, nonfinite, low-confidence, or out-of-bounds
  evidence; duplicate qualifying labels and mixed screens fail.
- Retained actual 01 and 03 receipts must qualify home and reject settings;
  actual 02 must qualify settings and reject home. Invented counterexamples must
  remain explicitly synthetic. Helper success, exact current owner/window/bounds,
  own helper permission, screenshot geometry/DPI, foreground, neutral state,
  profile absence, source/export binding, deadlines, events and cleanup retain
  their existing independent gates. No screenshot identity change accepts a
  foreign window. Prior PID 3996 failure remains zero events/no captures.
- A fresh source critic must approve before root dispatches one actual ARM retry.
  Replaying stored receipts establishes observer behavior only. It cannot turn
  the original failed native gate into a pass or qualify new event delivery.

## Separate strict-source failure diagnostic

Actual native `input_mode` reports 462 checks, zero assertion failures, process
exit 0, and `WARNING: 2 ObjectDB instances were leaked at exit`. The strict suite
stops there; the remaining five suites have no result. Original object types and
cause are UNKNOWN. Product fixes and comparison fixtures wait for actual types.

After an ARM native-source-suite failure, a separate bounded diagnostic may run
only when the original retained receipts establish that exact `input_mode`
exit-0/unclean-log failure. It repeats only `res://tests/input_mode_test.gd` with
the pinned engine, the same native private-project mechanism and `--verbose`.
It uses a new unique owned user-data namespace and temporary copied project,
records engine-reported paths before/after, preserves raw logs and produced-file
hashes, and records source/owned-process/private-path cleanup. It never reuses or
deletes unknown user state. Timeout cleanup targets only newly owned process
groups. Strict import/probe/log/cleanup failures remain failures in the diagnostic.
The diagnostic has a 240 s whole-run deadline and a 6 min workflow timeout, and the
original strict step remains failed even if the repeat is clean. A missing or
different original failure skips execution honestly. Pure controls cover this
selection, verbose command, deadlines, cleanup, and failure preservation without
running an engine locally. No warning filter or general suite gate is changed.
