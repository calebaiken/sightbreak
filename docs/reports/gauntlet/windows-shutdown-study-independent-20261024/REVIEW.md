# Independent source verdict: REJECT, execution stays BLOCKED

Frozen implementation: `c90fedfd56a09bd0ba13cce5565ccd160891c3fb`.
Sealed builder handoff: `239fa222ab2c34e6f9c640e468f8855e9163594d`.
Original source: `8ee93ac725d519c9f6d7f1ffbb3f7c9ee960baf8`.

The actual fixed retention preflight correctly blocks before the owner, runtime
identity reader, native driver, dependencies, export or engine. This is not a
native-admission bypass finding. Two independently reproduced source/model
failures prevent accepting the complete blocked-source handoff: source_binding
can certify materialized bytes it never hashes, and incomplete trial receipts can
be promoted to strict success and then whole-study success. The frozen source,
builder checkout and original evidence remain unchanged. No native run occurred.

## Independence and registration

Root reused reviewer thread `/root/input_reader_r4_builder_20261024`, which had
implemented a different input-reader component. This reviewer did not implement
the shutdown study. Thread reuse is explicit; no fresh-context claim is made.
Initial preregistration `cd82f40d` preceded implementation/handoff inspection or
tests; source-derived controls were added at `9e3e62c8` before execution. Further
additive registrations and retained iterations are in PREREGISTRATION.md and Git.
The builder supplied a read-only scope adjudication after the missing-receipt
case, confirming that no handoff clause authorizes that success.

Own review branch is `codex/critic-windows-shutdown-study-20261024`. Own exact
source view and initialized depth-one view both have c90fedfd HEAD. Index read-tree
preceded materialization. Both views contain all512 physical non-doc files. The
one-depth repository reports shallow=true/count1 and uses a disclosed shared
object alternate. The worktree shares the existing object store. Neither is a
full clone or an independent-object-storage claim.

## Supported failure 1: physical source bytes are not bound

`shutdown_study_retention.py:37-51` checks HEAD and Git porcelain, then computes
both tree and model-source identities from Git objects. Its comment requires
materialized model bytes to agree, but no materialized byte read enforces that.

The registered control appends a harmless marker to the actual materialized
`scripts/shutdown_study_retention.py` and marks its index entry assume-unchanged.
Git status is empty. source_binding returns the identical baseline identity,
including the original model-source SHA256, although the file SHA256 differs:

- Original `6ddaa38f4fc8d5f16a9a2e303a82c412a644e0d0e757bff591604e12c1f3c46b`.
- Altered `4c007cba58fab958b476a1443c02054ae5228cc035ffb790b4170395c5a245d9`,
  8,924 bytes versus8,858 original bytes. Both exact files and the unchanged
  returned binding are retained.

This is a byte-identity counterexample under an ordinary Git index flag. It does
not establish altered runtime behavior or execution authorization. The plain
skip-worktree variation in this cone checkout is correctly rejected as dirty;
Git noticed the materialized change. That valid rejection and the initial harness
stop are retained, and are not called a false accept. Exact physical bytes and
flags were restored after every variation; both source views finish clean.

Reproduction: `fresh_controls.py`; own/depth receipts
`assume-unchanged_materialized_source_mismatch.json`. Both report accepted source
binding with changed physical bytes. A separately registered fix needs direct
physical-byte agreement for required materialized execution/model source, with
explicitly bounded handling of any permitted platform text conversion. Repeating
Git show/status alone cannot close this finding.

## Supported failure 2: absent receipts become strict and study success

`windows_shutdown_study.py:152-176` tolerates absent client/reopened logs, records
missing initial seed events as UNREACHED_OR_UNRESOLVED, defaults OCR receipts and
close observations to empty lists, and uses vacuously true all() checks. A
directory containing only `results.json` with `{"passed":true}` returns:

- `strict_passed=true`, `original_stream_retention_complete=true`;
- zero native logs, OCR receipts or close observations;
- both initial seed events unresolved.

The additive propagation test uses actual collect_trials and its default actual
trial_evidence loader with fake controller-only job observations and identity.
Each of the four fake driver calls writes only that exact result file. The final
report has four fixed-order attempts and `passed=true`. No owner cleanup runs.
The same result reproduces in the exact-source and depth-one views. These are
synthetic incomplete-receipt counterexamples to validation, not claims that the
unchanged native driver can normally emit passed=true without its files. A file
loss/incomplete evidence boundary cannot substantiate the required complete
source/profile/seed/close evidence merely by trusting that boolean.

Paired controls correctly fail when a present native log has an ObjectDB warning
or when a declared OCR receipt is truncated. Driver exceptions remain failures
even with optimistic injected evidence; final ownership uncertainty also fails.
The builder confirmed read-only that there is no explicit scope clause allowing
missing required logs/events/OCR to count as strict success. A correction must
source-derive required successful-flow receipt presence/schema/identities and
retain partial failed flows as failures, without changing native behavior.

Reproduction: own/depth `optimistic_result_missing_required_evidence.json` plus
`receipt_propagation.py` and `own-receipt-propagation.json` /
`depth-receipt-propagation.json`. Original four files in each model are exactly
the string recorded in the input specification.

## Retention and admission adjudication

The real fixed preflight returns BLOCKED, exit2, execution_authorized=false, with
nine reasons: six unknown aggregate families, OCR prefix truncation, unknown ZIP
headers/index/name overhead, and unknown largest member. The guarded real public
collect path calls none of WindowsOwner/runtime_identity/real_driver. Public
ADMITTED remains unreachable. The workflow places the preflight before OCR/Pillow,
toolchain/export/study steps and retains exactly two upload declarations. It was
only statically reviewed, never dispatched.

A finite three21MiB-file model has total63MiB plus4096 bytes and maximum21MiB plus
headers. assess returns RETENTION_MODEL_ONLY with no reasons, but no two32MiB bins
can hold three such indivisible members. This does not itself violate the public
admission gate: the status is model-only and execution_authorized remains false.
The actual packer correctly rejects the files atomically and retains originals.
Treat this model as necessary numerical bounds, not a sufficient partition proof.

The outer-wrapper control builds an actual inner STORED ZIP of33,554,431 bytes,
one byte below the cap. A synthetic one-member STORED outer ZIP is33,554,557 bytes,
125 bytes above32MiB. This is not an observed GitHub artifact; it proves that an
inner cap alone does not cover a delivery wrapper. The handoff explicitly retains
this unmeasured blocker. No transport/admission claim is credited for it.

The biggest remaining admission gap is still complete bounded retention. Existing
OCR prefix capacity alone is128MiB across four arms, before other outputs; producer
families are unbounded. Actual generated output may be smaller, but observations,
compression guesses and old-run duplication cannot establish a worst-case lossless
guarantee. Neither source finding authorizes changing that limit or running trials.

## Source, package and regression evidence

`BINDINGS.json`, `BINDINGS-own-final.json` and `BINDINGS-depth-final.json` verify:

- All47 actual builder members match their declared bytes/hash and sealed Git
  bytes; exact copies, including failed iterations, are under builder-evidence-exact.
- All512 non-document paths have exact physical bytes, Git blob identity and mode
  in each review source view. The original508-path union changes only the optional
  driver and adds the four declared study files.
- All16,148 protected original path/mode/blob identities remain exact. Protected
  document paths are tree-verified; this is not a claim that all16k documents were
  physically materialized. All game source files are physically checked and the
  complete game tree is exact.
- Removing only marked optional observation blocks and restoring default main()
  produces byte-exact original driver source. Driver arguments keep300 seconds;
  actual extracted close helper keeps request_close then wait(min(20,remaining())).

All28 dedicated methods and all110 earlier focused methods pass in the exact
source and initialized depth-one views on CPU4. Logs include actual counts and
commands, with no skips. The first depth repeat ran concurrently with the comment-
only binding witness; it is retained. A separate sequential final138-method run
after restoration also passes, followed by physical source verification.

Fresh13-case controls match11 expectations and expose the two groups above in
both views. Separate whole-controller propagation confirms the missing-receipt
failure. Raw exact inputs/outputs, original r1 harness failure and successful
repeats are all retained. No artifact or fixture was rewritten to hide a failure.
Large deterministic synthetic archive inputs are specified by exact repeated byte,
length and SHA256 and reconstructed by the retained script; no33MiB attachment is
needed to reproduce them.

Windows API/birth/job/list/cleanup behavior remains unobserved. Maintained pure
controls cover x64 layouts, PID reuse, ownership uncertainty, early root readback,
failed attempts, final audits, one-shot safety and unchanged close limits. The
single failure-only5s cleanup cannot qualify a normal close and never grants a
replacement arm. Actual kernel latency, nested-job behavior, transient helper
identity completeness and the original shutdown leak/cause remain unverified.
No native/API/CI/engine/export/version/helper trial, Mac, codec or field-of-view
qualification took place.

## Comparison and next action

No candidate wins the complete source/evidence/admission bar. c90fedfd is better
than the retained702463c9 model on the demonstrated one-shot cleanup and early-root
identity obligations, and its blocked public preflight is the correct outcome
under the current retention contract. It still loses the present source-quality
comparison against the preregistered physical-binding and complete-receipt bar:
the concrete controls above require REJECT. Regression counts alone do not
supersede them.

Preserve c90fedfd/239fa222 and all old/native evidence. If root continues this
component, first preregister narrow fixes and new paired controls in a separate
candidate: physical source agreement, required successful evidence validation,
and explicit model-only retention terminology/partition and wrapper gates. The
unbounded-output source must remain blocked; no actual dispatch or acquisition
follows from this review. A new independent sealed review must evaluate any fix.
