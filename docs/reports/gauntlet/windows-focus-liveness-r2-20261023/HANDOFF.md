# R2 correction handoff, unapproved source

Corrected fence freeze `fa718ef`, own branch
`codex/windows-focus-liveness-fence-20261023`. Rejected `19304d5`, original
handoff `0823cee` and independent rejection `0d4f7e0` remain preserved. Exact
review copies and their hashes are in `rejected-review/`; no rejected output
was overwritten or relabeled. This is builder evidence, not independent approval.

Available focus publications now receive structural/schema/counter validation
before `observed()` compares freshness. The predicate exposes its validator to
the existing wait; no new wait or deadline exists. Valid stale snapshots do not
replace the fence's last valid state. A genuinely unavailable read retains the
original empty-publication wait behavior; an available empty JSON object still
fails the actual reader's scope contract and records structured loss.

Nested objects and finite numeric movement vectors validate strictly, including
boolean element rejection. A non-object snapshot retains its exact raw JSON
value rather than `{}`. The reader preserves its scope/type guard, attaches the
raw decoded value to the error, and the active focus fence classifies it as
`FOCUS_PRECONDITION_LOST`. Direct focus reads retain the same raw value before
the existing context fence runs. Baseline null actors now reject structurally.

The unchanged independent probe has SHA-256
`cc2efb2fd551fb47852bef688aacb5cd92a1d83501940062c68b29d80b699248`.
`replay_independent.py` invokes its unchanged case definitions and actual
controller AST, captures all 77 outcomes, then checks corrected expectations.
The old probe's assertion that a missing dead-state timestamp reproduces false
acceptance now fails as expected. Its original 49 defect-reproduction assertions
remain unchanged. All 77 corrected outcome checks pass; full raw receipts are
in `independent-replay.json`. This does not claim the old defect assertions pass.

The focused group now has 16 methods, including actual extracted reader/wait/
freshness logic. Added positives accept integer/float ordinary movement after
a declared publication gap, a valid stale buy/round snapshot and a fresh neutral
snapshot. Counterexamples reject malformed timestamps before later living
movement, malformed nested/non-object states, scope changes and boolean/wrong
movement values while retaining raw values and W-up handling.

All five pure groups pass: 16 focus, 15 capture, 11 Mac menu, 7 reader and 5
OCR-token methods, 54 discovered with the original three native-Windows reader
skips. `source-preservation.json` confirms original captures, literal stage
budgets, whole/transition waits, generic tap, held-neutrality checks, HUD pause
handling, game tree and CI unchanged. The controller observation wrapper changes
only to validate before filtering and to retain/classify reader errors.

No engine, import, UID, native input, OCR executable, export, CI, service or
canonical mission file was touched or run. The original Windows attempt stays
failed and the candidate living-input response is unverified. A later timing
hypothesis will have a separate preregistration and source freeze; independent
review and exact combined-source approval must precede any single native retry.
