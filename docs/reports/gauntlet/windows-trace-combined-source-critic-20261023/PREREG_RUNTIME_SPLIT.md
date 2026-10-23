# Independent runtime-only split assessment

Registered 2026-10-23 at 12:10:57 UTC, before inspecting the proposed runtime
files or their diffs. No split implementation exists or is assumed. This is a
new source-only component question under root's explicit request, distinct from
accepting the rejected complete trace/reader candidate.

The proposed collector copies exactly these four paths from `c0738163`:

- `game/scripts/gameplay/match.gd`
- `game/tests/movement_prediction_test.gd`
- `scripts/fixtures/export_integration.gd`
- `scripts/verify_integration_export.py`

It omits `scripts/analyze_input_consumption.py`,
`scripts/test_input_consumption_observation.py` and the diagnostic addition to
`scripts/validate.sh`. Root proposes combining it with exact accepted initial
pulse `ea6c330a` and reviewed dispatch adapter `b4a2cf4a`, against protected
Windows base `49ae54b0`. No reader completeness claim may be made. R1/R2 reader
rejections and every original native/gameplay failure remain in force.

The original preregistration's source/default/erasure/privacy gates still apply.
The following scope-specific criteria precede new implementation inspection:

1. Check every import, CLI path and execution site in all four proposed files.
   Omission of the reader must not cause import failure, a missing subprocess,
   missing-result dependency or replacement of gameplay success predicates.
2. Check the observation's actual default, role/build/host/scenario gating,
   scalar schema, bounding/failure behavior, output preservation and privacy.
   Inspect all runtime hooks in context and reverse only authorized observation
   additions to exact protected source, retaining all authority, RPC/wire,
   prediction, lifecycle, stock schedule and gameplay/assertion behavior.
3. Inspect the seventeen new Godot controls as source: determine whether they
   exercise the collector's meaningful invariants, whether they are reachable
   from the existing maintained suite, and whether any omitted reader Python
   test supplies a necessary collector safety check. Do not call their source
   presence a compile or native pass.
4. Distinguish a supported source blocker from an untested native/API/type or
   observational limitation. A raw collector need not prove the reader's
   completeness contract, but retained observations must not be represented as
   correlated completion or a cause of the Windows failure.
5. If source-safe and operationally separable, identify the exact minimal source
   set eligible for a separate compile/raw-acquisition qualification. This
   assessment itself authorizes no native execution, dispatch or release.
   Root must freeze the implemented exact union and request independent final
   source validation before its separately admitted preflight/native trial.

All executable review checks use CPU 4; only this report directory is edited.
Evidence, failures and candid limitations will be committed and explicitly pushed.
Initial status: **PENDING**, before runtime implementation inspection.
