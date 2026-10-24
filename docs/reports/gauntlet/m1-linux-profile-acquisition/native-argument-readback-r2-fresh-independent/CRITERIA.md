# Fresh independent fingerprint type review

Registered 2026-10-24 before changed code or test-output inspection.

Reviewer: `/root/linux_thread_types_review_20261024`, independent of the builder,
same task, environment, account and model. Own sparse initialized worktree:
`/workspace/reviews/linux-native-fingerprint-types-fresh-critic`, branch
`codex/linux-native-fingerprint-types-fresh-critic-20261024`.

Exact candidate: `8da2add4279f3087320d4708c047f500baffd0ee`.
Rejected comparison: `93f32edf`.
Original fresh critic: `a8cf0d06386a49a4aba05fc30a0a4e83ed9aab4a`.
Builder preregistration `602980d7` is reported to predate the correction and will
be checked, rather than taken as approval.

The bar is the retained rejected source and the unchanged original independent
controls. Their reported four false accepts replace the hashed initial or
terminal fingerprint thread booleans with `1` or `1.0`, recompute the hash, and
exploit Python equality between booleans and numbers. This review requires the
candidate to reject those fixtures while accepting literal true values.

Pass gates:

1. Inspect the exact Git delta. The correction must touch only the existing
   validator, controller source pin, and existing readback test path. The
   candidate must retain strict outer thread booleans and require both initial
   and terminal fingerprint thread fields to be literal true and identical to
   those outer values. Check validation order, hash recomputation, and literal
   types independently for both snapshots.
2. Run all maintained focused acquisition/fixture/readback methods and the
   exact unchanged ten-method independent rig in the initialized own checkout.
   Run an additional separately retained adversarial rig covering both snapshots
   and both fields, numeric true equivalents, false/missing/null/string/container
   values, altered valid literal booleans, and hash tampering/order behavior.
   Invalid fixtures must fail for a relevant guard rather than setup errors.
3. Acquire a genuinely initialized depth-one source view using a bounded source
   packet/shared objects. Record its exact ref, shallow status, history count,
   initialization, source identities and acquisition limits. Re-run the same
   pure controls in that view. Do not claim an independent network clone.
4. Verify the original rig bytes against `a8cf0d0`, retained original outputs and
   archives, source/runtime/API/formulas/caps/pins/graphics preservation, and the
   three-path correction against rejected `93f32edf`. Parent-owned handoff and
   preservation audits may be supporting evidence, but source and acquisition
   conclusions require direct checks.

Every command stays on CPU 4 and uses source/Python only. No Godot invocation,
native/version/import/export/render/service run or CI dispatch is authorized.
No raw evidence is deleted or replaced. Retain failed setup/check attempts and
their corrections. Commit the verdict and raw receipts on the review branch.

Acceptance is source-only. The strict V-Sync/software-driver environment blocker
remains unchanged. This review cannot release R4, establish performance/H1, close
the mission, or authorize a native run. The builder cannot self-approve.
