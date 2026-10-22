# M2 source-suite user-data isolation

Builder candidate; independent review and Windows/macOS native execution are pending.
This component does not qualify exported gameplay, physical input or any release gate.

The actual ARM Mac artifact from [run 39712752860](https://github.com/calebaiken/sightbreak/actions/runs/39712752860),
job `119607694324`, shows input-mode passing 31 checks, then menu-focus exiting 2
because `user://offline_training.json` already exists. Its raw logs and exit receipts
are retained in `evidence/ci-arm-baseline/`. `IDENTITIES.json` records the retrieved
artifact digest, exact source commit, candidate file digests and evidence digests.

The old CI loop changed `SIGHTBREAK_STATE_DIR` after Python's toolchain module had
already resolved that variable. Godot does not read it directly. The Linux and
Windows overrides also reused `input-mode-state` across the three suites; macOS
kept its native application identity. The new fresh-save guard exposed that defect.

`scripts/run_native_regressions.py` makes one temporary copy of the source project,
then sets `application/config/use_custom_user_dir` and
`application/config/custom_user_dir_name` in that copy for each suite. The engine
reports its actual user directory, native data directory, project path and selected
settings before and after each suite. A mismatch fails immediately. Each suite
gets a distinct UUID-owned directory; the source project's scripts, assets and
configuration remain byte-identical. The copy preserves LF or CRLF configuration
bytes. Only its two startup identity settings differ. Imported cache files are
excluded from the resource inventory.

The CI step retains all nine suites, their order, 120-second watchdog and native
error checks. Setup has a separate 120-second import bound and probes have a
30-second bound. No application save location, HOME, game assertion, shipping
resource or exported package was changed.

## Actual Linux results

Engine: `4.7.2.stable.official.ed1daf0bf`. Source:
`6a0d8d5d85b4fb37943903886982f51b4ed230b0`. Commands:

```sh
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-ci-isolation/.local/save-safety-current python3 scripts/test_native_suite_isolation.py --output builds/m2-isolation/save-safety-current
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR=/workspace/sightbreak-ci-isolation/.local/all-nine-final python3 scripts/run_native_regressions.py --output builds/m2-isolation/all-nine-final
python3 -m py_compile scripts/run_native_regressions.py scripts/test_native_suite_isolation.py
git diff 6a0d8d5 HEAD --check -- .github/workflows/desktop-alpha.yml scripts/run_native_regressions.py scripts/test_native_suite_isolation.py docs/reports/gauntlet/m2-native-state-isolation/CRITERIA.md docs/reports/gauntlet/m2-native-state-isolation/REPORT.md docs/reports/gauntlet/m2-native-state-isolation/IDENTITIES.json
```

The whitespace check covers code and authored documentation. Raw engine logs are
retained byte-for-byte, including their trailing blank lines.

The native save-safety test reproduced the old producer sequence: input-mode
passed and wrote its ordinary save, then menu-focus exited 2 at the unchanged
fresh-save guard. The save stayed byte-identical. With a canonical save sentinel
present, that guard still exited 2. All three isolated suites then passed using
three different engine-reported paths while the sentinel stayed byte-identical
(SHA-256 `7993151cc1165a0b5b7808712f0e976f55ede00592a215a89cab6543df0f89b4`).
Input-mode passed 31 checks, menu-focus 30 and offline-diagnostics 60.

An existing save inside an isolated identity was also rejected before the source
suite executed; its bytes stayed unchanged. Actual native startup accepted the
CRLF control config without doubled carriage returns. Original and copied resource
inventories matched; the temporary project and unique user-data namespace were
removed. These controls use the real native engine and real files.

| Final nine-suite run | Exit / native errors | Wall seconds |
| --- | --- | ---: |
| actor | 0 / none | 2.020 |
| match | 0 / none | 1.017 |
| state_privacy | 0 / none | 0.716 |
| movement_prediction | 0 / none | 6.229 |
| peer_lifecycle | 0 / none | 0.165 |
| input_mode | 0 / none | 0.917 |
| menu_focus | 0 / none | 1.318 |
| offline_diagnostics | 0 / none | 0.816 |
| hud_objective_hint | 0 / none | 0.816 |

The private import took 4.930 seconds. These measurements describe source-test
execution cost on this Linux host, not game frame rate or other hosts' performance.
Raw suite logs, producer receipts, produced-file hashes and cleanup receipts are
retained in `evidence/all-nine/`; the native baseline and save controls are in
`evidence/save-safety/`.

## Rejected iteration and remaining gap

The first candidate used the wrong setting name, `custom_user_dir`. Godot ignored
it and reported the application-name directory instead. The producer-path check
rejected that candidate before any suite ran. Its actual receipt, failure and
cleanup record remain in `evidence/rejected-wrong-setting/`. The accepted property
name in the current candidate is `custom_user_dir_name`, verified by native output.

The largest remaining gap is actual Windows and macOS execution. Linux receipts
and a CRLF control do not establish those platform results. A fresh critic must
evaluate this candidate's implementation, baseline comparison and native outputs;
new CI must then qualify the native-host paths and unchanged full suite list.
No builder quality score or self-approval is offered.
