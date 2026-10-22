# Independent cleanup follow-up review

Accept `daafe167d8d331a2cb5f4abf276cd85f8babc101` for the scoped Linux source-suite
isolation and cleanup-receipt truthfulness criteria. The reproduced P2 from
`1195b234` is fixed. The original rejection and its 340 hashed evidence files remain
unchanged. Actual Windows/macOS native CI and the new compact artifact's real
upload/download remain pending; no gameplay or release gate closes here.

The critic reviewed a clean detached checkout of the exact follow-up and ran the
real pinned `4.7.2.stable.official.ed1daf0bf` editor. All state directories were
new and review-owned. The game tree remains identical to the rejected candidate
and baseline, preserving all assertions and save guards. The workflow also
contains the separately reviewed compact-receipts change from `32c37fe`; this
cleanup follow-up does not alter its regression suite list or timeouts.

## Original counterexample

`recheck_original.py` copied the original critic's control and replaced only its
single owned review-root path. Its native peer-lifecycle call, PermissionError
injection and original false-success assertions were unchanged. The original
control now exits 1 at its obsolete `receipt['passed'] is True` assertion because
the follow-up correctly records `passed: false`. The recheck wrapper verifies
that exact expected failure and exits 0.

The native suite still passed 16 checks. The receipt contains a namespace cleanup
attempt with `removed: false`, the actual PermissionError, and
`temporary_project_removed: true`. The primary cleanup error propagates.
The reviewer removed only that remaining owned namespace after recording the
outcome. `ORIGINAL_COUNTEREXAMPLE_RECHECK.json` and raw logs retain the proof and
original/adapted script hashes.

## Native controls and regressions

The critic ran all five committed cleanup controls and independently read their
native logs and receipts. Every case first ran actual peer-lifecycle natively
with 16 checks and zero failures.

| Control | Required outcome | Observed |
| --- | --- | --- |
| Successful native run | Nonempty complete cleanup and passing receipt | Pass |
| Namespace PermissionError | Failing receipt, error and attempted removal; temporary project removed | Pass |
| Temporary cleanup PermissionError | Failing receipt; namespace removed; temporary removal false with error | Pass |
| Source inventory PermissionError | Failing receipt; both cleanup paths still attempted | Pass |
| Actual native error plus namespace failure | Native RuntimeError remains primary; additional cleanup error retained | Pass |

The combined case ran a real Godot script that emitted
`ERROR: Intentional native cleanup control failure` and exited 9. The original
RuntimeError object propagated, and the receipt separately recorded namespace
PermissionError. Each fault control removed its owned residual resources after
retaining the observed failure. Successful final receipt publication left no
`.pending` file; source inspection confirms same-directory atomic replacement
and preservation of an active native error if receipt publication also fails.
Receipt-publication filesystem failure itself was not injected.

All nine source suites passed again with zero native errors: actor 73, match 75,
state privacy 55, movement prediction 725, peer lifecycle 16, input mode 31,
menu focus 30, offline diagnostics 60, and HUD objective hints 33 checks.
Every suite used a different engine-reported fresh path, and every after-probe
matched its before-path. The native save-safety rerun again reproduced the shared
baseline's input-mode pass then menu-focus guard exit 2, preserved the canonical
sentinel, accepted CRLF startup, and rejected a stale isolated save before running
that suite. Normal cleanup removed the temporary projects and owned namespaces.

The independent reader matched copied produced-file inventories, all 295 original
resource hashes, each native exit/log/path, and the 120-second suite/30-second probe
bounds. All 50 preexisting workspace profile files were byte-identical after these
runs. All 340 original critic file hashes still matched. The candidate worktree
was clean after execution. Source import timings from simultaneous controls are
execution costs on this host, not game or device performance.

The follow-up wins against `1195b234` on the concrete defect: cleanup failures now
remain failures in both process behavior and retained evidence, while successful
isolation remains intact. The largest remaining scope gap is native Windows/macOS
execution on this candidate. Fresh Linux receipts cannot establish those results.
