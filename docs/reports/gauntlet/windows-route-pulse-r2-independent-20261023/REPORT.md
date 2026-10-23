# Independent R2 route-pulse source acceptance

ACCEPT the narrow source component at exact code
`a4899dd5534553ae832a433dd704f3539914a421`, handoff
`d3b0fc1676b8904b96f69cf738edb0c312f1981a`. This approves the source behavior
and source-only review recipe. It does not release Windows, native or CI
execution. Independent R2 criteria `9294d996` precede this inspection and tests;
builder preregistration is `e0503e79`.

R2 is better than the rejected `977633e4` for the concrete source comparison:
both original real-key-path falsifiers now send only W down and W up. After W
changes foreground or target ownership, a fresh complete check fails before D
is attempted. The rejected source sends D down in the invalid context. Original
rejection `bf47f7c9b15a5d8be8aa3dcc0f815fb3c60961f2`, its source, all raw
controls and its failure verdict remain unchanged.

The largest remaining gap is actual source-bound Windows delivery to stopped
living cover inside the original corridor and deadlines, followed by the
settings/LEAVE/reopen/focus journey. Source controls establish no native speed,
latency, physical key interval, game consumption, survival or route success.

## Independent controls and retained failures

All replays below run the actual `WinUI.key` -> `_input` path with fake User32,
clock and sleep. No Windows API or engine executes.

| Check | Observed result |
| --- | --- |
| Exact two original falsifiers, unchanged | 2 pass on R2 |
| Full original rig, unchanged | 21 pass, 1 failure, 1 error; retained |
| Original assertions with two semantic fault-stage selectors | 23 pass on R2 |
| Same semantic rig against rejected 977633e4/handoff 9a3d7356 | 21 pass, the exact 2 original failures |
| Additional independent per-edge boundary methods | 8 pass |
| Maintained groups in fresh scripts-only depth-one checkout | 104 discovered, 101 pass, 3 original Windows-only skips |
| Independent base-scope/source/original audit | 20 checks pass |
| Independent preservation, exact-source and control-integrity audit | 33 checks pass |

The two failures in the unchanged full rig are stage-selection drift, not
missing release attempts. Its old `read_error[2]` now fires in the first
per-down check before any attempted key. The method retains that error, sends
no down and has no owned up to send; the old assertion expects two ups. Its old
single-key `read_error[3]` now fires in `after_down`, so the original OSError
propagates after D is released; the old assertion expects the RuntimeError
used for an after-release verification failure. Complete output and receipts
are retained in `unchanged-full.log` and `unchanged-full-receipts.json`.

`semantic-selection.patch` records every adjustment. Two error-hook assignments
select `after_down` and `after_release` from observed edge/check state. All
original test assertions remain exact; the integrity audit normalizes only
those two selectors and proves AST equality of the complete original control
class. The semantic rig still rejects the original source on the same two
focus/owner cases. No old failure output is overwritten or relabeled as passing.

The additional independent controls change each relevant condition before the
first or second down: foreground, owner, visibility, window thread, pinned HWND,
pinned PID and external A/S/D/LMB. They exercise unknown reads, OSError,
KeyboardInterrupt and SystemExit, failed up calls, full release attempts after
context loss, fixed-hold exhaustion and absolute-cap exhaustion. All retained
per-down snapshots include W/A/S/D, LMB, focus, ownership, identity and monotonic
brackets; valid two-key dispatch recognizes only previously owned attempted
keys. Full raw receipts are in `boundary_controls-receipts.json`.

## Source and deadline scope

Each down now has a fresh complete predicate check, retained separately in
`down_checks`. A non-neutral unowned key, LMB, changed pinned identity, hidden
window, missing thread, different owner, wrong foreground or unknown read fails
before that down attempt. Existing owned attempted keys are allowed. Each
check consumes the original fixed requested hold and absolute deadline. No
fresh hold is started after a read or dispatch. The original post-down and
post-release samples remain.

The helper still attempts every owned attempted up in `finally`, even after
cancellation, context loss, lateness or an earlier up failure. Receipts retain
call/read brackets and errors in memory through release attempts. Controller
publication remains after those attempts; failed release leaves controller
held-key ownership for outer cleanup. Strict late callback/trace controls from
the original rig continue to reject completion under the unchanged route cap.

Only `WinUI.key_pulse` and its pure test file differ from the original handoff.
The base-scope comparison independently proves unchanged existing WinUI methods,
default/coarse approach, Windows-only optional hook, route guards and other
controller schedules/caps/OCR/assertions after removing the declared extension.
Game, CI, toolchain and focus-helper Git objects are exact. The aggregate source
change remains the single pure test command. No aggregate or native suite was
run by this reviewer.

The six exact source hashes are in `source-and-originals.json`. In particular,
`scripts/verify_integration_export.py` is SHA-256
`6de6b78597d5af681f3ee883886422b065ebe2c2f96a72f628ff52e502f698fe`.
All six files in the depth-one checkout match the exact code freeze.

These checks are sequential Win32 observations and call brackets. They do not
make global SendInput atomic with asynchronous OS focus changes or prove
physical delivery. Acceptance covers the freshly checked context and the
retained failure/release behavior, including the original avoidable gap between
successive downs.

## Historical failures and setup

All three original result/action/legacy file sizes and SHA-256 digests verify.
The retained full original route, all selected pulse edge rows, error and base
source digests equal the original receipts. Run 39926044462 / job 120322557935
remains FAILED: same living actor at 100 health, last stopped x=-6.2700005 at
tick 3159, then rejected x=-8.6911116 / vx=-3.7 at tick 3211 outside x>=-8.5.
Target x=-7.8, endpoint <.45 m, speed <=.05 m/s, two later neutral observations,
identity/life/health/weapon/ammunition checks, shared 35-second route stage and
whole-flow cap remain exact. Settings/LEAVE/reopen/focus remain unreached.
The separate original delayed held-fire reload completion timeout also remains
FAILED. Later authority completion and workflow success do not erase it.

Original requests .1545885467/.1257692308 seconds and after-call driver brackets
.500/.515 seconds remain controller observations. Original r/d/w diagnostics
provide no independent A bitmap. WinUI already used in-process ctypes/SendInput;
no per-key subprocess startup, missed-input cause or physical timing claim is
supported. The original independent actual review `2020cfa9` remains valid.

All prior critic manifest hashes, original critic HEAD/clean status and original
builder report Git objects verify unchanged. The old report's setup failure
and all rejected control rounds remain retained. No product implementation,
contributor branch, canonical mission file or old receipt was edited here.

The fresh checkout `/workspace/reviews/windows-route-pulse-r2-depth-one` has
exact handoff HEAD d3b0fc16, one history commit, shallow status true, and no
materialized docs/reports directory. Maintained tests and independent controls
execute there with no historical report fixtures. The audit of old raw evidence
is separate from candidate runtime dependencies. Full commands, exits, log
hashes and source binding are retained beside this report.

## Source-only replay recipe

Use a new receipt destination for every replay. From the review worktree:

```sh
SIGHTBREAK_PULSE_RECEIPTS=/tmp/pulse-R2-unchanged-NEW.json python docs/reports/gauntlet/windows-route-pulse-r2-independent-20261023/original_controls.py /workspace/reviews/windows-route-pulse-r2-depth-one
SIGHTBREAK_PULSE_RECEIPTS=/tmp/pulse-R2-semantic-NEW.json python docs/reports/gauntlet/windows-route-pulse-r2-independent-20261023/semantic_controls.py /workspace/reviews/windows-route-pulse-r2-depth-one
SIGHTBREAK_PULSE_RECEIPTS=/tmp/pulse-R2-boundaries-NEW.json python docs/reports/gauntlet/windows-route-pulse-r2-independent-20261023/boundary_controls.py /workspace/reviews/windows-route-pulse-r2-depth-one
```

The first command intentionally retains exit 1 from the two stale ordinal
selectors; the other two pass. `original-replay.json`, `semantic-results.json`
and `depth-one-checks.json` contain the exact observed commands and exits.
Any combined source needs exact-source integration review before a separately
released actual acquisition. No Windows/native/engine/CI/OCR executable,
services, Apple compile or nested agent ran in this review. No whole release
or player-experience gate closes.
