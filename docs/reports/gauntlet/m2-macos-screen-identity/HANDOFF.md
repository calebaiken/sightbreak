# Native Mac screen identity and verbose input-mode diagnostic

Accepted source candidate: `a866c73b9cd656b1eb461b8626cd4679bdeb345c`, based on
root `f8b7e82`. Fresh independent review accepts one bounded actual ARM attempt.
No native APIs, engine, OCR, event posting or CI ran in this worktree.

The actual run 39732825169 at b09cfe1 remains **FAILED**. Its PID 4062/window 45
has real screenshots, observed focus, and five CoreGraphics event attempts. The
original 03 returned-menu image visually shows home, but the old observer rejected
the merged masthead at confidence 0.5. The new observer requires three distinct
exact visible home labels at the unchanged 0.8 threshold. Stored JSON replay is
observer readiness and does not turn that failed native run into a pass. Previous
PID 3996 activation failure remains zero events/no captures; the earlier preflight
PID 3571/window 35 belongs to its own separate launch.

The separate native strict-source result reports input_mode 462 checks, zero
assertion failures and exit 0, then two ObjectDB leaks. The remaining five suites
were not run. Leaked types and cause are UNKNOWN. The new ARM-only failure-followup
diagnostic retains one verbose repeat in a fresh private user-data namespace and
copied project. It records its owned process cleanup, producer paths, source
identity, logs, and unchanged original failure receipts. It leaves the strict
step's command and error/leak gate intact. A clean repeat cannot repair that gate.

Ordered implementation commits:

1. `04ba688`: criteria preregistration and byte-exact actual JSON fixtures.
2. `ebb5cf9`: exact home/settings observer; independently rejected for a positive
   text box at x=1 or y=1 whose tiny extent rounded the addition back to 1.
3. `893dac1`: subtraction-based bounds checks for both the identity and pointer
   target, with counterexample controls. The rejection is retained in review.
4. `4df02e9`: bounded diagnostic, six pure controls, strict-step ID and ARM-only
   diagnostic workflow steps; criteria clarify qualifying-label uniqueness.
5. `a866c73`: independently found missing-original evidence now skips without
   fabricated hashes or engine execution; finalization overruns cannot qualify a
   clean repeat. The prior diagnostic failure is retained in review.

The exact candidate's 35 pure controls pass: 11 menu, 9 focus, 7 screen identity,
and 8 diagnostic controls. These cover stored actual 01/02/03 discrimination,
synthetic missing/foreign/ambiguous/partial/low-confidence/nonfinite/out-of-bounds
labels, existing native input guards, exact failure selection, bounded owned
process cleanup, skip behavior, and preservation of the original strict failure.
They do not establish native behavior or the leak cause. Root owns integration
and any registered ARM/Windows workflow dispatch after independent source review.
The workflow YAML parses, step IDs are unique, and the strict regression command
and lack of `continue-on-error` are unchanged.

The fresh critic also passes 146 independent screen cases and 14 independent
mocked inherited diagnostic lifecycle runs. Its exact-source verdict, scripts,
logs, fixture audit, unchanged-guard checks, and both rejected iterations are
retained in `independent-review/`. The original reviewer hash manifest also
identifies its external frozen snapshots; those complete source copies are not
duplicated here. Reproduction scripts accept `--source` pointing to a checkout of
the exact reviewed commit. This is source readiness only.

One cleanup limitation is explicit: if a bootstrap probe fails before its native
user-data path is validated, the inherited harness preserves that unvalidated
unique namespace. That diagnostic fails and does not claim namespace cleanup.
Actual leaked object types/cause and fresh native screen success remain unknown.
