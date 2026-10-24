# Windows route-clock correction source handoff

Frozen source `4cf6ac8e744603ed6af122a362036d276754cc76` on
`codex/windows-route-clock-boundary-20261024`, checkout
`/workspace/sightbreak-windows-route-clock`, is a SOURCE-ONLY candidate over exact
`7101350e5d0a2f6e4afb9a913b5b1bcf2107857a`. Preregistration
`e46680e4acd849c8d8e8125ed4b0a27c9e751320` precedes edits. Fresh independent
critic is `/root/objective_r2_review_recovery_20261024`; builder does not approve
its own result. No native/export/CI/retry is released or executed.

## Actual benchmark and supported correction

Official run 40083894472 / job 120842796227 fails before reopened launch with
`Native route pulse sleep returned before its requested boundary`. Initial and
reopened exit fields are null; flow 102.2349999999999 seconds; cleanup_errors empty.
Requested pulse budget 0.12567175974707734, stored H 768.093671759747, API down
767.968 and release 768.093. That difference is not physical sleep timing; exact
sleep(wait) and immediate comparison samples were not recorded. Originals remain
owned by the actual critic and are byte-bound in route-pulse-actual-timing.json.
The failed original is retained unchanged and INCONCLUSIVE for reopened shutdown.

Official Python 3.12.10 uses GetTickCount64 for monotonic in upstream source;
its relative waitable sleep timer can return between coarse clock updates. Exact
CPython source URLs/hashes and bounded excerpts are retained. No hardware clock
resolution or physical-short-sleep cause is inferred from the old anchors.
Read-only findings were pushed first on the preserved shutdown branch as 5e0a687e.

The candidate computes the original same-clock H once before dispatch costs.
After each sleep it rechecks the original operation deadline and requests only
H-now, clipped to the remaining original-operation watchdog allowance. Equal
consecutive coarse-clock reads are valid; H never moves. Acceptance still
requires sameclock>=H, successful original releases/OS state, and completion
before the original deadline. No epsilon, sleep floor, arbitrary retry cap,
deadline extension, alternate route or warning suppression exists.

A new optional elapsed_clock=time.perf_counter argument supports bounded failure
when monotonic stalls. Only elapsed_clock_now-elapsed_clock_start is compared
with deadline-initial_monotonic. No absolute epochs are mixed. Invalid/decreasing
clock values reject, as do invalid/decreasing watchdog values and nonfinite
remaining-budget arithmetic. Timing-read errors cannot suppress attempted UP
calls; all attempted owned keys still receive releases, timing failures remain
FAILED, and final timestamp failure cannot hide the original exception.

Receipt additions are bounded numeric data: original watchdog allowance,
sleep-call count and first/last wait samples. No per-iteration history or game
object is retained. Existing window/focus/visibility/input preconditions,
life/health/corridor/settle/identity checks, SendInput mapping, ordinary schedules,
privacy, economy, engine and workflow remain unchanged.

## Validation and source identity

Frozen full selection passes 194 methods: 191 pass and the same three existing
Windows-only reader skips. All 17 groups and bash -n scripts/validate.sh pass.
Pulse controls are 41 methods: original 29 plus 12 meaningful clock/release methods.
Declared model cases cover 15.625ms tick phases, actual-like fractional anchors,
coarse repeated reads, true early wakes, unrelated epochs, adjacent float targets,
state/dispatch cost, frozen monotonic with advancing watchdog, deadline equality/
clipping/oversleep/late release, persistent invalid/backward/throwing clocks,
watchdog faults, sleep interruptions and finite-input arithmetic overflow.

The unmodified old method is retained in controls/baseline_key_pulse.py and bound
to exact 7101350e by source-union.json. Its pure fine-sleep/coarse-clock model
reproduces the old exact exception and complete release, with the same retained
boundary and API anchors. This is a declared counterexample, not reconstruction
of Windows physical timing. controls/replay_baseline.py records it independently
of the production correction.

Full 508-path non-doc Git union is retained. 506 paths and all modes are unchanged.
Only verify_integration_export.py:key_pulse and test_native_route_pulse.py differ.
Replacing the one method with the exact original and erasing only the new test
model/class/import recovers both files byte-exactly. All materialized source bytes
match the frozen candidate; omitted sparse backend paths are disclosed in the
full source manifest. Game, UID tree, native_log, controller callers, workflow,
CLI budgets and all other original source are exact.

Before freeze, original 29 controls passed, then 40 and 41 as cases were added.
The first broader own-pure run reports 193 methods at preregistration HEAD and is
retained as interim, not frozen-source evidence. A final remaining-budget overflow
guard/case was added afterward. Only frozen-pure 194 at exact 4cf6ac8e supports the
final candidate. No test failures were discarded; intermediate successful logs
remain. Initial baseline-fixture serialization added an extra EOF blank line; the
failed whitespace check and first replay outputs remain, and only that serializer
newline was removed before repeating baseline/union proof. Production source did
not change. Initial empty worktree checkout required explicit restore after read-tree
and sparse setup, before any edits/tests. No other worktree was changed.

Repeat source/pure commands on CPU4 with a new output path:

```sh
taskset -c 4 python3 scripts/test_native_route_pulse.py -v
taskset -c 4 python3 docs/reports/gauntlet/windows-route-clock-boundary-20261024/controls/run_pure.py --source . --output /tmp/route-clock-pure-NEW
taskset -c 4 python3 docs/reports/gauntlet/windows-route-clock-boundary-20261024/controls/replay_baseline.py
taskset -c 4 python3 docs/reports/gauntlet/windows-route-clock-boundary-20261024/controls/verify_source_union.py
```

The two report controls write their own fixed output filenames and should be
copied into a new evidence folder before replay when preserving prior outputs.
Maintained tests require neither historical Git objects nor report fixtures.

## Limits and next action

The requested 2.5s ceiling and fixed H are preserved. They do not establish a
maximum physical hold; source receipts explicitly disclaim that measurement.
A coarse clock can observe H only on its next tick, and the elapsed watchdog may
fail later at the original operation allowance if monotonic freezes. Existing
OS calls may block past a deadline; software checks cannot interrupt them. All
such late/error completion remains failed after release attempts. The watchdog
bound assumes its independent elapsed clock progresses; two simultaneously
permanently frozen time sources cannot provide an elapsed bound.

Source/pure evidence cannot establish actual Windows route success, input
consumption, physical timing or reopened cleanup. Largest remaining gap is the
same ordinary Windows flow at the independently accepted final source under a
new root admission. Original ObjectDB classes/owners/cause remain UNKNOWN.
Wait for the fresh source verdict; retain original failures and require separate
root criteria/release before any new actual run. No Mac review was attempted.
