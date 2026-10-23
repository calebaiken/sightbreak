# Windows route pulse R2 source handoff

UNAPPROVED source freeze `a4899dd5534553ae832a433dd704f3539914a421`, on
`codex/windows-route-pulse-e28-20261023`, worktree
`/workspace/sightbreak-windows-route-pulse`. Preregistration `e0503e79` preceded
implementation. Independent source review is required; no native/CI run or
living-input retry is approved. The builder cannot approve this candidate.

The comparison is committed independent REJECT
`bf47f7c9b15a5d8be8aa3dcc0f815fb3c60961f2` of source
`977633e44a61352cbf666273931021ebebfe70d9` / handoff `9a3d7356`.
Those commits, reports and raw receipts remain immutable. The rejected helper
sent D down after W changed foreground or target ownership. R2 checks the full
pinned target and control state before each down. Both exact independent
falsifiers now pass unchanged, with W down/up and no D attempt. Their complete
before/after comparison is in `falsifier-comparison.json`; the separate exact
replay is in `exact-falsifiers-unchanged.{log,json}`.

Only `WinUI.key_pulse` and its pure test file changed in R2. Each check reads
visibility, window thread/owner, pinned HWND/PID identity, foreground, all four
W/A/S/D bits and LMB. It accepts previously attempted owned keys and rejects
other down bits. `down_checks` retains key, known owned keys, monotonic check
brackets, raw state and any exception; original initial/after-down/after-release
samples remain. Unknown checks fail closed. The original hold boundary includes
all read/dispatch work and never restarts. No new down occurs when a fresh read
has exhausted that boundary or the absolute cap. Every attempted key still gets
an unconditional up attempt in finally, even after changed context, error,
cancellation or lateness. Existing full receipt publication remains after
release attempts. API success and OS bitmaps never prove game consumption or a
physical hold interval.

All nine short maintained groups pass in both the own checkout and a genuine
scripts-only depth-one checkout: 104 discovered methods, 101 executed passes,
three original Windows-only reader skips. The original 93 methods remain; the
one existing delayed-release-read hook moved from read ordinal 3 to 4 to keep
selecting the release stage after the added single-key pre-edge read. Eleven
new methods use actual WinUI.key -> _input -> fake User32, covering positive
two-key/list requests and flags, both original losses, visibility/thread and
HWND/PID loss, external input, first-edge rechecks, unknown reads/cancellation,
fixed hold/absolute-cap lateness, semantic post-down/release read errors, late
release reads, partial dispatch/up errors and snapshot/request-list aliases.
`pure-checks.json`, `depth-one-checks.json` and full logs retain the results.
The depth-one checkout has exactly one history commit and no docs/reports
materialized. The local server ignored blob filtering; no transfer saving is
claimed. No maintained test requires historical fixtures.

The full independent 23-method script was also replayed unchanged. It exits 1:
21 methods pass, one fails and one errors. Both original focus/owner failures
pass. The two retained outcomes come from read-ordinal hooks: `read_error[2]`
now throws during the first per-down check before any attempted key, so the old
assertion expecting two ups fails; single-key `read_error[3]` now throws during
after-down instead of after-release, so OSError propagates instead of the old
expected release-verification RuntimeError. No error was suppressed. The
unchanged replay log, exit code and complete receipts are retained. Its local
.gitattributes preserves unittest's raw trailing space on the failing subtest
line without changing the log bytes. New
semantic-stage controls exercise the original post-down/release fault intent;
the independent critic must judge this explanation and rerun its own controls.

Fifteen R2 audit checks and five inherited base-scope AST checks pass. They bind
critic bytes to its committed rejection, compare exact raw falsifiers, preserve
the old builder report and verify unchanged game/CI/toolchain/focus Git objects.
Removing only the new pulse method leaves all other integration-module AST
unchanged. The default/coarse approach, controller schedules/caps and all route
bounds, actor/life/health/identity/weapon/neutrality guards remain unchanged.
Fourteen full declared fake User32 cases retain raw state before and after,
actual key-path call flags, per-edge/check receipts and exceptions in
`pure-real-key-receipts.json`. These are source controls, not a Windows latency
benchmark or gameplay acquisition.

The original e28 raw trace recomputes byte-exactly to the old retained JSON.
Original Windows run 39926044462 / job 120322557935 remains FAIL: living actor
100, last stopped x=-6.2700005 at tick 3159, then x=-8.6911116 / vx=-3.7 at tick
3211 outside x>=-8.5. Target x=-7.8, endpoint <.45 m, speed <=.05, two later
neutral samples, the original shared 35-second stage cap and default 300-second
whole-flow cap, and all captures remain.
Settings/LEAVE/reopen/focus are unreached. The separate original legacy reload
completion timeout remains FAIL. Neither source correction changes that result.

The original pulse requests .1545885467/.1257692308 seconds and selected-key
after-call brackets .500/.515 seconds include traced controller work. WinUI
already used in-process ctypes/SendInput. No helper-process startup, exact
physical latency, input-consumption defect or bot/product cause is established.
The route-only pulse hypothesis is work between native edges; R2 adds context
checks without changing game/AI/health/seed/rules/graphics or default input.
The largest remaining deficiency is actual source-bound Windows qualification
under the unchanged corridor and deadlines. Surviving stock combat is not
promised. Fresh independent source approval and root's exact combined-source
release must precede any native acquisition.

Replay the short maintained groups from this worktree:

```sh
python docs/reports/gauntlet/windows-route-pulse-r2-20261023/record_checks.py
python docs/reports/gauntlet/windows-route-pulse-r2-20261023/record_receipts.py
python docs/reports/gauntlet/windows-route-pulse-20261023/check_source.py
```

Replay the original independent controls without overwriting their evidence:

```sh
SIGHTBREAK_PULSE_RECEIPTS=/tmp/pulse-r2-review-NEW.json python /workspace/reviews/windows-route-pulse-source/docs/reports/gauntlet/windows-route-pulse-independent-20261023/independent_controls.py /workspace/sightbreak-windows-route-pulse
```

To isolate the exact original blockers, append these two unittest names to that
same command: `IndependentPulseControls.test_two_key_dispatch_stops_when_focus_changes_after_first_down`
and `IndependentPulseControls.test_two_key_dispatch_stops_when_owner_changes_after_first_down`.
The independent source review should retain all original controls and add
semantic fault-stage selection for the new read schedule. No runtime recipe is
authorization to run Windows/native/CI. Canonical mission records were untouched.
