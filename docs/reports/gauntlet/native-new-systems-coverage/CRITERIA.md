# Native coverage for accepted source suites

Preregistered on 2026-10-22 before changing the native runner. Base source is
`ecc2690dc783a3243291f8ac3438d44fe0151117`, from
`codex/v1-mission-playability`. Builder branch is
`codex/native-new-systems-coverage` in its own sparse worktree.

The inspected comparison bar is `scripts/run_native_regressions.py` at that
source, plus the accepted invocations in `scripts/validate.sh`: standard
`transaction_journal_test.gd` and `gunplay_rules_probe.gd` with
`--audio-driver Dummy`. This is source-suite registration, with no player
experience or release-gate claim.

The candidate must meet these criteria:

1. Append `transaction_journal` and `gunplay_rules` to the maintained default and
   CLI choices after the original twelve suites, preserving their exact order.
2. Preserve the original twelve suite commands byte for byte. Journal uses
   `--headless --script res://tests/transaction_journal_test.gd`. Only gunplay
   uses the explicit exception
   `--headless --audio-driver Dummy --script res://tests/gunplay_rules_probe.gd`.
   Unsupported identifiers remain rejected before suite preparation.
3. Preserve the 120 second suite limit, strict `native_log.failed` gate, unique
   private project and user namespace, real before/after producer receipts,
   source and copied-resource inventories, output preservation and owned cleanup.
   No game, test, warning-parser or workflow behavior changes are allowed.
4. Run the existing fourteen pure methods in
   `test_diagnose_native_input_mode.py` and `test_native_first_leak.py`, plus the
   existing native log and build-manifest controls in `test_build_manifest.py`.
   Retain raw output and exact commands. These controls use fake processes or
   temporary fixtures; they are not native engine evidence.
5. Make the frozen clean candidate available to an independent source reviewer.
   The builder cannot approve it. The parent owns subsequent actual private
   Linux focused execution, the complete aggregate and Windows/ARM execution.

No engine, OCR, service or CI launch is part of this builder task. No new test
that mirrors the implementation will be added. The remaining deficiency after
pure verification will be actual native coverage on the integrated source.
