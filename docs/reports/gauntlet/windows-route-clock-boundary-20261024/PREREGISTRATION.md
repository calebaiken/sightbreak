# Windows route-clock boundary correction preregistration

Base exact 7101350e5d0a2f6e4afb9a913b5b1bcf2107857a. Own branch
codex/windows-route-clock-boundary-20261024, initialized sparse worktree
/workspace/sightbreak-windows-route-clock. Index was initialized with read-tree
before sparse configuration; explicit worktree restore completed materialization.
The initial checkout alone left own selected files absent; restore corrected
that setup omission before source edits/tests. Other worktrees are preserved.

Fetchable benchmark is official run 40083894472 / job 120842796227, failed before
reopened launch. Selected original bytes and exact anchors are bound in the
accompanying actual-timing JSON; originals remain owned by the actual critic.
The pulse request is 0.12567175974707734s, stored H 768.093671759747, API-down 767.968,
API-release 768.093. Original exception and release_complete=true remain failed
benchmark evidence. Literal sleep(wait) and immediate comparison samples are
unrecorded, so physical short sleep is not inferred. Read-only findings/source
hashes were pushed as 5e0a687e on the prior shutdown branch before this work.

CPython 3.12.10 upstream source implements Windows monotonic with GetTickCount64
and sleep with a separately timed relative waitable timer. Test a legitimate
fine sleeper/coarse 15.625ms tick model as well as true early wakes. Float ULPs
alone do not explain the observed 0.000671759747s boundary deficit.

Root approved the following design before edits. Preserve H=min(original same-
clock start+requested seconds, original absolute deadline), computed once before
dispatch costs. Re-read that same clock after each sleep and wait only the
positive residual. Never accept before sameclock>=H; all completion/release and
callback gates must still finish before the original operation deadline.

A separate optional elapsed_clock callable defaults to time.perf_counter and is
used only for bounded failure. Record its initial sample before preflight and
compare elapsed differences against ORIGINAL remaining operation duration,
deadline-initial_monotonic, never H-start. No watchdog absolute value is compared
with H/deadline. No renewed deadline, clock-domain substitution, arbitrary retry
cap, epsilon, sleep floor, catch-up allowance or warning filter. Each residual
sleep is clipped to the remaining watchdog allowance as well as H-now. Preserve
same operation boundary when the monotonic clock stalls. Reject nonfinite and
backward clock/watchdog readings; repeated equal coarse readings are valid.

Rejecting a clock read must not suppress attempted native key-up. Every owned
attempted key is released even if its timestamp fails, other releases continue,
and timing/read failure remains a failed receipt. No source change may weaken
focus/window ownership/visibility/physical-neutral input, life/health/corridor,
settle, route identity, original schedules, privacy/protocol/economy, native-log
or ordinary default callbacks. All Godot files and workflow stay byte-exact.

The existing 2.5s condition caps requested duration, not measured physical hold.
Original receipts explicitly disclaim physical hold proof; scheduler overshoot
could already last past H while still before the operation deadline. The new
loop keeps H fixed and introduces no physical timing guarantee. Elapsed watchdog
uses the original remaining operation cap; it cannot forcibly interrupt a
blocked OS input/sleep call. Failure/late releases remain failures. If another
binding maximum physical-hold contract is found, stop/report before weakening it.

Measurable pure gates: preserve old failure against retained unmodified method;
valid coarse tick phases and genuine/repeated early returns wait only residuals;
zero/nonzero/large epochs and adjacent floats keep absolute comparisons; state/
dispatch time consumes fixed H; deadline equality/clipping/oversleep fail and
release; frozen/backward/nonfinite clocks, watchdog faults, sleep/read errors,
interruptions and up failures release every attempted key and cannot pass.
Retain all existing 182 methods and skips; add meaningful cases, no native action.
Full 508 original non-doc path/mode/blob union must differ only in the minimal
controller/helper and test paths. Preserve complete raw pure output/failed rounds,
preregistered benchmark, exact source manifest and new independent verdict.

All work CPU4 pure/source only. No engine/native/CI/export/process activation or
retry is authorized. Fresh source critic is separately assigned. Builder cannot
approve itself. Native release needs separate root admission.
