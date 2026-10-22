# Independent capture-fence revision review

**Source verdict: ACCEPT `65c3b8b` for exact-source native qualification. Native output and pixel acceptance remain UNVERIFIED.**

Candidate `65c3b8bfdfa14342411c9aa6519244628cc12c81`, preregistered criteria
`3e3b40a3d532fbcb3d5a561a5d81bf84772a1dab`, base
`9d11f1dc4ebc31ad3beea7594b6868ef437bb0d8`; reviewed 2026-10-22. The earlier
`aaa1929` rejection, exact frozen source and independent counterexamples remain
intact at `../offline-capture-phase-critic-aaa1929/REVIEW.md` with verified hashes.
This reevaluation changes that source verdict only for the revised candidate.

The revised `rendered` predicate compares drawn-frame, observer-wall and physics
counters with the last validated sample, including samples that do not yet
satisfy two drawn frames. It retains the rejected pair before raising. This
closes the acknowledged-frame-only comparison gap. After raw capture, the new
barrier is read and a strictly newer native publication must arrive before the
final after-state can be accepted. A state published during pre-capture binding
can supply the barrier but cannot supply the sole post-capture proof.

I independently rechecked the revised helper with my own polling harness and
the exact original counterexamples. Eight controls pass:

| Declared control | Observed result |
| --- | --- |
| Intermediate drawn-frame rollback | Rejects before raw capture |
| Intermediate simulation-tick rollback | Rejects before raw capture |
| Intermediate observer-wall rollback | Rejects before raw capture |
| Valid state buffered before screenshot, then stopped producer | Raw capture retained; barrier retained; transaction times out without accepted after-state |
| Valid new publication after post-capture barrier | Accepts declared scheduling control |
| New publication after barrier loses buy phase | Rejects after raw capture |
| Original deadline expires at post-capture barrier | Rejects; no new grace period |
| Normal monotonic two-frame sequence with later barrier publication | Accepts declared scheduling control |

`recheck.py`, `independent-recheck.json` and `independent-recheck.log` retain the
independent controls, sampled counters, rejection messages and receipt stages.
The exact frozen builder suite separately passes all 15 groups, including
source/PID/trace/loaded-profile mutations, actor/life/focus/pause/phase/context
loss at each bracket, invalid counters, stalled/one-frame conditions and the
original 160/30-second absolute budgets. Its stdout/stderr is retained in
`frozen-builder-controls.log`. Earlier independent five-caption and four
filesystem passes, with three Windows-only skips, remain in the first report.

The revision adds one observation publication wait within the same supplied
absolute deadline. The 160-second natural-round budget, 30-second reopened
profile budget and default 300-second whole-flow budget remain unchanged. The
old Round 2 log contract and the reopened stock-event/exact-profile checks remain.
The reopened trace is selected before current-state queries. The same source,
current native PID/process, trace path and reopened loaded/disk settings are
checked around the transaction. The declared controls reject sampled binding
changes and expiry. I found no further concrete source blocker in this scope.

The complete base-to-revision diff leaves product, arena, authority, backend,
server and canonical mission/roadmap/engineering documents unchanged. Native
input operations and other capture paths are unchanged. The source checkout is
clean at the exact candidate; the diff passes whitespace checks. Only this
external review directory was written by the critic. Installed quality skills
were reused; no Godot, native rendering or OCR ran.

The named regression bar is independently verified: the retained original
Windows a8 CI39728129445 `06c` visibly shows round-1 POST/dead, and `10` visibly
shows the prior main menu. The three fixture objects exactly match original
JSONL objects and both retained PNGs match original bytes. Full provenance and
raw hashes remain in the earlier critic report. These original failures are
not revised into pixel successes by the new source controls.

The biggest remaining gap is actual output from the corrected observer.
Account qualification still owns the CPU lane. Root must release/coordinate
that lane and freeze the exact combined source before a native slice. Retain
all raw images and action/state/frame receipts, failure output, source identity
before/after and original deadlines. A separate pixel critic must inspect the
living round-2 buy HUD in `06c` and reopened living game HUD in `10`. If either
boundary is unreached or its pixels disagree, that native gate stays open.
Source review and declared fixtures establish no new pixel result or whole
ordinary-journey qualification.

Reproduce from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 recheck.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace/sightbreak-capture-fences/scripts python3 frozen/scripts/test_offline_capture_fences.py -v
```

The independent recheck loads the unchanged first report's retained polling
harness and frozen baseline to replay its original rejection, then binds that
harness to this directory's exact revised observer. Utility modules come from
the source worktree; their hashes are retained in `source-provenance.json`.
