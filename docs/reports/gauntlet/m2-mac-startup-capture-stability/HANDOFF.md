# Same-read capture guard evidence handoff

Frozen candidate source: `d5277180a7705befd64d2f40a362ad566e83d91b` on own branch
`codex/m2-mac-startup-capture-stability`, checkout
`/workspace/sightbreak-mac-startup-capture-stability`. Base is exact R3 source
`4854aed946d25d27482af66c332f84aa51cea8fb`; preregistration
`a7b60823d87dc9345ada43e77e70995628fdcb01` preceded code edits.
Read [the preregistration](PREREGISTRATION.md). This is an unapproved diagnostic
candidate. The builder gives no source approval, native release, or product fix
claim. Root owns canonical mission updates.

## Original failure and remaining uncertainty

Actual run `39943145541` / job `120379229239` remains FAILED in 39.528253 seconds
before focus, pin, input or AX. Its original capture receipt reports
`Captured pixel dimensions or owned-window bounds changed`; there is no PNG,
Vision result, accepted capture, focused menu, AX request/tree or query prerequisite.
The ordinary close returns zero and all three owned process groups disappear
without signals. Those original native results belong to the independent actual
critic, not to this source-only builder.

The byte-exact 859-byte original is retained at
[`scripts/fixtures/macos_capture_diagnostics/original-failure-39943145541.json`](../../../../scripts/fixtures/macos_capture_diagnostics/original-failure-39943145541.json),
SHA-256 `d63129b91900c6ad5d2a99767e6d4c35dacc8ec254e54be28981a1613adb1ecf`.
Original QA and receipts archives remain read-only at the critic-owned path
recorded in the preregistration; this component does not duplicate or replace them.

The reported initial CG frame, SCWindow frame and filter content dimensions are
1024 by 684 at scale 1; the reported captured image is also 1024 by 684. Exact
attested source therefore satisfies both image-size predicates. Its final
`ownedWindow` call must have returned a frame for the same PID/window with
visible layer zero, since identity lookup failure has a distinct thrown message.
The remaining false predicate is `closeRect` against that returned frame, beyond
its original 0.5-point tolerance. These are source-bound inferences from retained
inputs and the exact failure message. The actual second frame is absent. There
is no basis to name a destination geometry, blame initial coordinate mapping,
label the change legitimate startup behavior, or predict a later retry result.

## Exact source change

The helper adds three fixed-shape report fields:

- `configured_image_dimensions` records the existing width/height configuration.
- `post_capture_validation_stage` is one of `pixel_dimensions`,
  `exact_owned_window`, `bounds_agreement`, or `complete`.
- `post_capture_owned_window_bounds_points` records the exact CGRect already read
  by the original post-capture guard, after that read returns successfully.

The original combined guard is split to retain those inputs. Dimension mismatch
still throws the same error before a post-capture ownership read. Dimension
agreement still performs exactly one `ownedWindow` read; that function's owner,
PID, window, layer, visibility and rectangle checks are byte-identical. Its
thrown errors propagate. A returned frame still passes the unchanged `closeRect`
check before any PNG or Vision work. The original false result and exit code
remain until the original complete success path finishes. The stage `complete`
means only that this geometry guard passed; it grants no screenshot acceptance.

No new native call, retry, exception catch, permissive path, clock query, input,
focus request, permission prompt, private data read, or deadline reset is added.
Controller, AX observer/contract/AppKit adapter, gameplay, ordinary selector,
workflow and budgets are byte-identical to base. The game tree is unchanged:
`55691684d31d44f1680141954bbe530443de9d1f`. This changes diagnostic evidence;
it does not fix rendering, window sizing, input, or Deploy recognition.

## Preservation and pure evidence

The immutable original helper fixture has its original SHA-256
`6b64561032d86b60dc1276aea1a642f427b48a1b5257934e89b71afb4269f71f`.
The new helper SHA-256 is
`6fa1ca610e84daecc988c9fa46c980fce50e10d1a5029242b2e8da0cc480b6a9`.
The two existing helper-preservation assertions apply only an exact reverse
replacement of the registered block, then run their original unchanged digests
and golden-body assertions. All original fixture bytes/digests remain intact.
Any changed native API, privacy setting, tolerance, scale bound, passed default,
permission count, or any byte outside that exact block still fails preservation.
The legacy six-method native-boundary replay remains byte-identical, SHA-256
`e7e16c77d8529d10cb424d141aefd9d3b6300a6aaf148a2ba9558ae21b6973f6`.

| Receipt | Observed source/pure result |
| --- | --- |
| [registration-sparse-setup.txt](receipts/registration-sparse-setup.txt) | Initial staging failed because the new report was outside the sparse definition. Only that own report path was added; registration then committed before edits. |
| [candidate-first-diagnostics.log](receipts/candidate-first-diagnostics.log) | Retained test-only failure: a whole-deadline-overrun case incorrectly expected an ordinary-close success field. |
| [candidate-corrected-diagnostics.log](receipts/candidate-corrected-diagnostics.log) | All eight new methods pass after correcting only that assertion. No runtime change followed the test correction. |
| [original-4854-missing-guard-inputs-falsifier.log](receipts/original-4854-missing-guard-inputs-falsifier.log) | New suite against clean exact old depth-one source exits 1: missing diagnostic block, plus a mutation-test premise that requires the new block. Original receipt/controller failure remains rejected. This is retained as an old-source negative, not a candidate test result. |
| [original-4854-focused-missing-evidence.log](receipts/original-4854-focused-missing-evidence.log) | Focused two-method old-source check fails because the original lacks the registered evidence block. |
| [pre-freeze-maintained.log](receipts/pre-freeze-maintained.log) | All 15 commands / 139 top-level methods pass with recorded pre-freeze dirty status. |
| [exact-depth-one-d5277180-maintained.log](receipts/exact-depth-one-d5277180-maintained.log) | All 15 commands / 139 top-level methods pass from clean exact frozen source; shallow true, one reachable commit, empty initial/final status, CPU affinity `[4]`. |

The 139 methods are the existing 131-method R3 matrix and eight new methods.
The new suite checks exact source reconstruction and rejects changes outside the
registered block. A limited interpreter of the byte-bound Swift guard statements
compares short-circuit reads over 45 dimension/bounds/unavailable-window cases.
It is not a Swift compiler or native API execution. Fixed report shapes contain
only two configured dimensions, four bounds values and a finite stage string.
The original actual failed receipt replays through the unchanged controller as
one failed capture with zero focus/input/AX and preserved raw SHA-256. Synthetic
resize/move/identity/mapping/size faults, bogus stage labels and one-sided
passed/exit-code claims stay failed. Late failed helpers preserve the original
stage/whole caps and cannot claim successful close after the whole deadline.

The preserved raw runner logs contain trailing spaces on their empty Git status
lines. Authored code/prose passes whitespace checks; those raw stdout lines are
kept verbatim.

## Reproduction and next boundary

Candidate clone `/workspace/reviews/mac-capture-stability-depth1` is clean and
contains one reachable commit, exact `d5277180`. Original reference clone
`/workspace/reviews/mac-capture-original-4854-depth1` is clean and contains one
reachable commit, exact `4854aed9`. No history lookup is needed by any test.
The candidate was cloned with `--depth 1 --filter=blob:none --no-checkout
--single-branch --branch codex/m2-mac-startup-capture-stability` from the local
repository; the server warned that filtering is unsupported. Initialize the
index using `git read-tree HEAD`, select sparse paths, then materialize using
`git checkout-index -a` before checking clean status. Required sparse paths are
`scripts`, `.github`, `.claude`, `docs/engineering`, `docs/roadmap`, this report,
`docs/reports/gauntlet/m2-macos-screen-identity/fixtures`, and
`docs/reports/gauntlet/m2-mac-derived-ocr/original-native-39912086121/macos-ordinary-input`.

From a clean exact checkout, write output outside that checkout:

```sh
taskset -c 4 python3 docs/reports/gauntlet/m2-mac-startup-capture-stability/run_pure.py \
  --root "$PWD" --output /tmp/mac-capture-guard-independent.log
```

Biggest remaining gap: actual post-capture geometry and cause remain unknown.
Swift compilation, macOS ABI, actual evidence emission and later AX traversal
are unverified. No native API construction, Apple compile, engine/import/export,
OCR executable, CI or dispatch ran for this component. Fresh source critic
`/root/mac_capture_guard_fresh_source_critic` registered `314cc65e` before detail
inspection and owns approval. A later native attempt requires separately reviewed
admission and root release. No retry is justified or released by this handoff.
