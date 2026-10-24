# Source admission notes

The preregistration `07f50bfe` and adapter-only proof `a5ec1841` precede any
combined-source review. No exact combined freeze has been supplied.

Root's first initial-pulse evidence pointer named
`windows-route-pulse-independent-20261023/REPORT.md` and its controls. Inspection
showed that directory reports the older rejected `977633e4` route component,
with 23 controls and two context-loss failures. It cannot establish acceptance
of the initial-pulse source `ea6c330a`. The copied original controls/audit remain
historical, with no verdict change inferred from the mistaken pointer.

Commit metadata for `fcbb3ca1` identifies the correct initial-pulse packet at
`windows-reload-route-actual-20261023/independent-source`. Root acknowledged the
path correction. Its unchanged `test_independent_controls.py` and
`run_maintained_pure.py` are copied here as `initial_pulse_independent_controls.py`
and `initial_pulse_maintained_runner.py`. The tracked baseline approach source
has Git blob `34493e63f4db62f78d0c880d0803cc17700c456d`, identical to
`49ae54b0:scripts/native_approach.py`.

The original trace critic's frozen `independent_controls.py` and
`supplemental_controls.py` come from `02725f9c`, with their 25+4 unchanged
expectations and coherent baseline logs. They are ready for replay at an
accepted combined source. Their embedded `candidate` label remains `c0738163`
because these original files are unmodified; replay output also records the
actual checkout and reader SHA-256. The reader and controller are not yet
present at this adapter-only checkout.

On 2026-10-23 the separate trace critic reported R2 `86fe3cbe` REJECTED in exact
packet `8cd68f818d8642953c4d4bda38ee14cccb55a9c5`. All 29 original expectations
match, but seven additional source-impossible lifecycle/attempt/order cases
still falsely report completion, and one valid unordered multi-command
authority projection is falsely rejected. This reviewer has not promoted R2
or run it as an accepted combined component. Its original rejection remains
in force, as does `c0738163`'s rejection by `02725f9c`.

`check_union.py` is prepared for root's eventual accepted exact trace and
combined source. It compares every tracked non-document path, mode, blob and
content hash against protected `49ae54b0` plus exact independently accepted
component deltas. It fails closed on overlap needing separate contextual proof.
It has not been executed because no accepted trace or combined source exists.

Combined review status: **PENDING**. The next step is root's accepted exact
trace/source handoff, followed by contextual source review and pure own/depth-one
replay. No native preflight, CI dispatch, release or Windows cause is approved.
