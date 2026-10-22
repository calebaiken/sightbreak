All commands ran from `/workspace/sightbreak-offline-flow` unless stated otherwise. No new native rendering was launched.

```sh
git diff 6a0d8d5..HEAD -- scripts/verify_offline_export.py game/scripts/offline_diagnostics.gd game/tests/input_mode_test.gd game/tests/offline_diagnostics_test.gd
git diff --check 6a0d8d5..HEAD
git status --short
python docs/reports/gauntlet/m1-offline-flow-observation/compare_hud_pixels.py --captures /workspace/reviews/offline-flow-critic/r1/windows-ci6a/offline-input --output /workspace/reviews/offline-flow-critic/independent-hud
python docs/reports/gauntlet/m1-offline-flow-observation/verify_focus_trace.py /workspace/reviews/offline-flow-critic/r1/focus-unit-r5.log
python docs/reports/gauntlet/m1-offline-flow-observation/verify_focus_trace.py /workspace/reviews/offline-flow-critic/input_mode.log > /workspace/reviews/offline-flow-critic/independent-focus-predicate.json
python scripts/test_native_observation.py > /workspace/reviews/offline-flow-critic/native-observation.log 2>&1
python /workspace/reviews/offline-flow-critic/audit_packet.py
```

For Godot checks, `git archive HEAD game scripts` was extracted into `/workspace/reviews/offline-flow-critic/source`, then these commands ran there with `SIGHTBREAK_TOOLS_DIR=/workspace/tools` and a separate `SIGHTBREAK_STATE_DIR` per invocation. Exact argv/environment/exit/time are in `headless-commands.json`.

```sh
./scripts/godot.sh --headless --editor --import --quit
./scripts/godot.sh --headless --script res://tests/input_mode_test.gd
./scripts/godot.sh --headless --script res://tests/offline_diagnostics_test.gd
```

The added Linux pixel replay imports the unchanged production `read_hud_pixels`, invokes `tesseract stdin stdout --psm <6-or-7>` with the existing 20-second timeout, and records every command/text/exit/time/hash in `independent-linux-hud.json`. It checks six retained ordinary full-flow images and three focused images, with expected pairs taken from the actual rendered ammunition. All nine pass. Its original invocation was an inline Python script; the same logic is retained as `replay_linux_pixels.py`, with an output-preservation guard added. Reproduce into a new file with `python /workspace/reviews/offline-flow-critic/replay_linux_pixels.py new-linux-replay.json`.

Exploratory command mistakes were read-only: the abbreviated revision `6a` was ambiguous, then corrected to `6a0d8d5`; searching a nonexistent top-level `tests` directory and `scripts/verify_windows_export.py` was corrected by `rg` against the actual scripts. Neither ran a test or changed source.

The three supplied archives were extracted with Python tarfile `filter='data'`. Each extracted file's byte count and SHA-256 were compared against the supplied manifest, then each archive hash was compared against `archive_sha256`. Results are in `artifact-identity.json`.
