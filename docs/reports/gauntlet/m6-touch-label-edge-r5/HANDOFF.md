# Frozen R5 measurement investigation handoff

Fresh independent method/source review is required. This report does not accept
its own proposal or authorize native work. Product quality and every existing
release gate retain their previous status.

Report source commit: `259018f6bde618ade64583bd53a2e90cb423621f`.
Worktree: `/workspace/sightbreak-touch-label-edge-r5`.
Branch: `codex/m6-touch-label-edge-r5`.
Exact report directory: `docs/reports/gauntlet/m6-touch-label-edge-r5`.

The initial draw-repair assignment was narrowed by root to measurement validity
after the fresh actual critic verified the original pixels. Product, original
fixture/instrumentation, old analyzers and geometry remain unchanged from
`108d1cdc6cf471daa7390298c234bb1c087ae865` / handoff
`b9bd7e62c70d3f5a061c4177ede6c73c21dc9d35`. No engine process, native import,
rendering, capture, export, UID generation, CI or new acquisition ran here.

The complete [proposal](FUTURE_METHOD.md) identifies actual JUMP negative-bearing
support outside the nominal label rectangle, fetchable official pinned
Font/TextServer API evidence, the missing native glyph metric receipts, and a
direct native per-action footprint alternative. The dormant report prototype
requires every grouped label pixel exactly once with byte-identical coverage,
its correct source component, unchanged hit circle and independent ownership.
It refuses the old captures because the required new per-action label images
do not exist. Its positive and negative arrays are synthetic controls.

Preregistration preceded implementation at
`4e6dd56509e9916dcf4079fdb14b785f11565719`; the stronger byte-coverage requirement
was committed before its implementation at `e77826e9`.
[SOURCE_FREEZE.json](SOURCE_FREEZE.json) binds 340 report/input files and has
SHA-256 `cee73e7fe8ffc7915f79a73c0dccc1a61d37803d81a0e7c2c33aea1d92b7c84d`.
This handoff is intentionally outside that earlier freeze.

The [retained manifest](retained-inputs.json) binds 322 exact original inputs
totaling 11,370,602 bytes, including all seven gated row inputs, all sixteen
mobile label/group/component inputs, and the complete original result/freeze.
[Postcheck](original-input-postcheck.json) confirms every corresponding original
raw input remained byte-identical. The unchanged old functions still reject
all seven gated rows and all sixteen mobile affordance records. Their original
FAIL is preserved. Native log warnings and descendant cleanup observations stay
separate in the actual-run review; this proposal makes no claim to fix them.

Final checks on CPU4, each under its original 60-second outer cap:

| Scope | Result | Wall seconds |
| --- | --- | --- |
| Report controls, old-failure replay and source fences | 20 methods pass, exit 0 | 35.736709 |
| Original geometry/method/receipt/declaration controls | 60 methods pass, exit 0 | 41.283386 |

Exact commands, source hashes and unchanged-after checks are in
[final-20-command.json](final-20-command.json) and
[unchanged-60-command.json](unchanged-60-command.json). The earlier 19-method
pass and exact matching initial prototype/check sources are retained separately.
These checks establish bounded source behavior and preservation, not native
method validity, visual quality or physical accessibility.

The [quantization investigation](quantization-investigation.json) keeps the seven
spread-2 rows failed under the frozen predicate. A separate closed `±0.5`
final-code interval leaves each observed neutral-difference candidate only one
endpoint. This is a necessary condition under an incomplete model; it proves
neither neutrality nor a valid native blend and is disconnected from every
acceptance result. A defensible pinned-renderer error model remains missing.
No opacity change, arbitrary rectangle padding, tolerance increase, support
pruning, threshold change or counterfeit native receipt is proposed.

Review the new evidence requirements and falsifiers first. Any production
fixture/analyzer revision needs a new exact preregistration, fresh independent
source/method acceptance, truthful new image/source identities, and a separate
root release before acquisition. Preserve every current failure. Source-only
reproduction, from this worktree:

```sh
timeout 60s taskset -c 4 env PYTHONPATH=scripts python3 docs/reports/gauntlet/m6-touch-label-edge-r5/checks.py
timeout 60s taskset -c 4 env PYTHONPATH=scripts python3 -m unittest -v test_touch_geometry_r4b test_touch_method_r4b test_touch_receipts_r4b_r2 test_touch_declaration_r4b_r3
```
