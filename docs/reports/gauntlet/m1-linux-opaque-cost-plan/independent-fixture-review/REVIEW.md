# Independent fixture review

Reviewed 2026-10-23 at exact source
`12901729f7be29d0f64d87a0d92219a84500f1a6`.
**Verdict: REJECT runtime readiness.** Correct the two controller failures below
and retain fresh pure controls before requesting a new implementation verdict.
This review grants no import, compilation, export or native-run release.

The source and estimator address the prior plan review, but the controller does
not enforce its declared hard process bound or establish live owned-Xvfb
readiness in the socket-publication race. These are the largest remaining gaps
for the next bounded diagnostic. They require no engine run to reproduce.

## Reproducible failures

Run from this own sparse worktree:

```sh
python3 docs/reports/gauntlet/m1-linux-opaque-cost-plan/independent-fixture-review/audit.py
```

[Audit source](audit.py), [recomputed evidence](recomputed.json) and
[independent pure-suite output](pure-controls.txt) retain the exact source
identities and results. The audit invokes the supplied pure Python tests and
uses fake process objects for the controller counterexamples. It never launches
Xvfb, Godot, an exporter, an importer, a profiler or another native workload.

1. **The full block accepts clients past 180 seconds.**
   `scripts/linux_profile_overhead.py:432–472` checks the deadline only while a
   readiness path is absent. Once metrics exist, driver-library observation,
   payload hashing and the finish acknowledgement can cross the deadline.
   `wait(timeout=max(0.001, until-now))` then accepts an already completed child.
   No final elapsed-time predicate repairs this. My falsifier runs the actual
   `NativeRunner.condition` and `run_block` code with four causal fake clients:
   startup takes 178 seconds, the fixed cold/warm/measured/readback schedule
   takes 1.947 seconds, and the final host observation takes 1.1 seconds. Both
   15-second fixture handshakes remain within their bounds. Every client ends
   at **181.047 seconds**, yet `block.json` reports `passed=true` and all four
   conditions launch. These are virtual times, not measured native timings.
   Require deadline checks after blocking observations, before finishing the
   handshake and after waiting; retain actual start/end/elapsed observations.
   The declared hard bound also needs a mechanism that bounds blocking host I/O,
   rather than relying solely on a polling deadline.

2. **A newly appearing socket can pass with a dead owned Xvfb.**
   `scripts/linux_profile_overhead.py:407–420` checks `poll()` only inside
   `while not socket.exists()`. If the socket appears before that loop test,
   the loop body never runs. My pure falsifier makes the prelaunch socket check
   false, the next socket check true, and the owned Xvfb's `poll()` equal 1.
   `NativeRunner.start()` returns successfully. A competing display launch can
   therefore supply the observed socket while the owned launcher has failed.
   This establishes a false readiness acceptance; it does not claim an actual
   native block ran on another server. Check owned-server liveness and identity
   on the success path and establish that the ready display belongs to that
   server. Reject existing display locks/sockets and retain failure evidence.

A smaller evaluator defect is also retained. Replacing only
`cold_before.clock_usec` with negative infinity makes `evaluate()` return
`comparable=true` and an infinite `cold_anchor_ms` because lines 209–213 test
only ordering. The later strict JSON writer rejects infinity, so this is **not**
a full-block false acceptance. Validate finite, nonnegative endpoint clocks
and a finite positive cold duration directly, with a dedicated negative control.

## Source and method findings

I independently verified all five implementation-ledger lengths and hashes,
the eleven retained upstream source identities, the unchanged shipping game
tree `55691684d31d44f1680141954bbe530443de9d1f`, and no game/original-controller
delta from the declared base. The candidate adds only the declared diagnostic,
tests and component reports. Canonical mission files are unchanged.

The cold anchor is consistent with the pinned synchronous source: post-draw
signal emission precedes profile processing, and `main.cpp` increments drawn
count after draw returns. Later post-draw intervals chain one drawn identity
and callback serial. The separate later callback for fingerprint/image readback
keeps that work beyond the retained 64 measured endpoints. Atomic ready/metrics
and acknowledgement publication avoids partial-JSON observation. The current
pure tests do not verify GDScript signal execution or property enumeration.

The source freezes one five-actor approach view, disables world processing and
preserves manual authored-arm processing. Its fingerprint traverses structural
paths, local/global transforms, visibility, geometry/material/mesh/skin state,
stored resource properties and shader parameters, multimesh instance data,
skeleton poses, camera, lights, environment and settings. Frozen file hashes
and deterministic reference labels replace serialized runtime IDs. Unsupported
generated textures fail closed. Actual import resource paths, generated-resource
stability, GDScript syntax and final pixel equality still need later engine
evidence; this review cannot certify them.

The production evaluator preserves OFF/ON/ON/OFF, the separate anchor, 32 warm
and 64 measured intervals, an arithmetic even median, the original 0.90/1.10
ratio boundaries and registered drift screens. It retains total/mean/max and
the ordered samples. Its sparse-stall control correctly returns a median ratio
of 1.0 while total/mean rise by 18.75%. H1 remains a median cadence screen and
cannot bound sparse stdout stalls or complete profiler cost.

The controller checks actual selected argv/environment, driver-library hashes,
main-thread affinity, cgroup/quota/throttle observations, isolated cache paths,
payload hashes and owned cleanup. Those checks do not establish idle hardware,
per-thread warm CPU, uncontaminated CPU/page caches, physical FPS or freedom from
middle-only host disturbance. OFF/ON/ON/OFF supplies no confidence or independent
repeatability estimate. Whole-process rusage and untagged profile stdout remain
descriptive evidence. The source does not convert these into gameplay cost or
a Linux acceptance pass.

All **14 supplied pure methods pass**, without skips, in this independent rerun.
The two passing counterexamples show missing failure-path tests alongside those
positive controls. No GDScript compile/import, UID generation, export, native
runtime, OCR, CI or service action ran. Original Linux gameplay failures and all
release/physical-performance gates remain unchanged.
