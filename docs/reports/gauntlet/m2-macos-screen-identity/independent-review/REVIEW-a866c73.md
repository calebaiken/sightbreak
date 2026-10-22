# Independent source review: ACCEPT for one bounded actual ARM attempt

Exact source: `a866c73b9cd656b1eb461b8626cd4679bdeb345c`. Base: `f8b7e8272a104aadf890328b5ff4fc26374b5daf`. This approval covers the screen identity observer, its fixtures and workflow control addition, and the separately added failure-only verbose input_mode diagnostic. It establishes source readiness only.

I reviewed exact committed blobs in an external snapshot. I did not review the builder's uncommitted documentation, edit implementation, change canonical records, run an engine/OCR/native API, or dispatch CI. The repository AGENTS.md, CLAUDE.md, gauntlet-loop, sightbreak-gauntlet, No AI Slop and its eval, criteria, native driver/adapter/helper, and inherited regression harness informed this review.

## Screen evidence and decision

I visually inspected retained 01, 02, 03 original PNGs and verified the committed JSON fixtures against the raw originals byte for byte. The original 03 PNG SHA-256 is `c17ca318ef148c0e444136048f8f914bade3770366c29acb6d619cb71427adeb`; JSON SHA-256 is `3b087c989452ec9b24068b4abdddf849e5822686afcc824de582c2b50e72f1eb`. The three home roles are each exact confidence 1 observations in both home captures. FIELD SETTINGS is exact confidence 1 on the settings capture; that capture lacks the home trio. The title bar is shared and cannot prove home identity. Source main.gd declares the hero and home controls in the menu flow and FIELD SETTINGS in the settings flow.

The baseline observer accepts 01/02 and rejects 03 because the returned masthead observation merged to S/B TACTICAL OPERATIONS at confidence 0.5. The new observer passes 01/03 as home and 02 as settings while rejecting the opposite classifications. It keeps the 0.8 confidence threshold and uses exact normalized labels. Required roles need unique qualifying observations and positive finite in-bounds boxes. Any qualifying home role blocks settings; the qualifying settings heading blocks home. The final criteria clarify that only finite numeric observations at least 0.8 count for uniqueness and opposition. Malformed required observations cannot supply a role.

Independent 146-case controls cover each single opposing home label, opposite heading with invalid geometry, normalized duplicates, title/decorated/merged/confusable text, invalid confidence types, malformed rows and boxes, exact-edge valid boxes, row reordering, and foreign owner/window/geometry rejection by the independent pointer guard. All pass. The original eight float-edge failures are closed in both screen identity and pointer geometry by comparing extent with remaining in-image space.

## Diagnostic evidence and decision

The original strict input_mode result has exit 0, clean_log=false, 462 checks, zero assertion failures, and `WARNING: 2 ObjectDB instances were leaked at exit`. The original suite stops there. Its isolation receipt has unchanged source/copied resources, removed temporary project and owned namespace, and no finalization failures. Its source game tree is `fb6be859e05812d8707be1ef5c6f747d2588c1e9`, equal to this candidate's unchanged game tree.

The diagnostic selects only a proven final input_mode exit-zero/unclean-log ObjectDB failure with clean source/owned cleanup receipts and matching current game resources. Missing or malformed proof skips without launching a runner; missing named hashes are null rather than invented. It creates a new random namespace/private project through the existing harness, runs only the maintained input_mode suite with --verbose, and records native producer paths, raw logs, produced-file hashes, and cleanup. Its import/probe processes are prerequisites, not additional gameplay suites. Every process uses a new owned session, bounded wait, and owned-group reap. The 240 s budget is checked during processes and after finalization/source/original-receipt checks; the workflow limit is 6 min.

Independent lifecycle controls exercise the real Python inherited harness with every engine process mocked. Fourteen runs cover clean repeat; leaky repeat; import/probe warnings; owned-group cleanup failure; timeout; execution/finalization/source-check overruns; changed source; changed original evidence; and each missing original receipt. They verify retained produced-file hashes, before/after synthetic engine path receipts, removal of owned namespace/private project on validated paths, preservation of unrelated user data, and zero launch for missing proof. All pass. A clean repeat keeps strict_gate_repaired=false and leaves original bytes unchanged; warning/import/probe/cleanup/deadline failures cannot qualify.

## Unchanged gates and checks

The game tree, Swift capture helper, no-event preflight, build/source manifest, engine pin, strict log filter, inherited source-suite harness, and focus controls are byte-identical to base. Driver orchestration, source/preflight, capture/focus, deadlines, events, normal close, and final cleanup functions are AST-identical. The adapter class is unchanged; its only function change tightens pointer-box bounds. The original strict native regression command remains unchanged and has no continue-on-error. The failure-only diagnostic runs in a separate step; it cannot repair that step or relabel its result. See `unchanged-guard-crosscheck-a866c73.json`.

| Checks | Result |
| --- | --- |
| Packaged menu/focus/screen/diagnostic methods | 35/35 pass (11+9+7+8) |
| Independent screen cases | 146/146 pass across 10 methods |
| Independent diagnostic lifecycle runs | 14/14 pass across 8 methods |
| Earlier ebb5cf9 iteration | REJECT, eight float-edge cases retained |
| Earlier 4df02e9 combined iteration | REJECT, three missing-proof and two deadline cases retained |

Logs and machine-readable results are in `candidate-controls-a866c73.json`, `test_screen_identity_independent-a866c73-results.json`, and `test_diagnostic_independent-a866c73-results.json`. Reproduction scripts are `test_screen_identity_independent.py` and `test_diagnostic_independent.py`; use --source exact-source-a866c73 to select this frozen snapshot.

## Limits for the actual attempt

Run 39732825169 at b09cfe1 remains FAILED. Its original five event attempts, receipts and PNGs are historical evidence. Replaying stored JSON establishes observer behavior; it authorizes no native event and proves no new delivery, clean close, permission, focus, or device qualification.

The largest remaining gap is actual native execution: the revised screen observer has no fresh ARM result, and the two leaked ObjectDB types and their cause remain unknown. All remaining original source suites after input_mode are unreached in that failed native run. The diagnostic is observation, with no product fix or warning suppression. On a bootstrap probe failure before its engine path is validated, the inherited harness can preserve an unvalidated unique user-data namespace; that diagnostic fails and does not claim successful namespace cleanup. Unknown user state is preserved.

Accept this exact source for one bounded actual ARM attempt under the unchanged native guards. Native results must be independently reviewed from the new exact returned source, owned processes, original screenshots, receipts, strict logs and cleanup. This does not close platform stability, physical input/gameplay, presentation, or release gates.
