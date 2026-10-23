# Wrapper R2 retained-byte integrity correction

Source/pure only. Independent wrapper rejection `062147c` plus raw-log retention
`337d82aa` reject `90d3baa`. Both exact review trees are retained separately under
`independent-wrapper-r1-<commit>` with Git-object/SHA-256 manifests, including all
original synthetic raw logs, reports, controls and failed assertions. Observer/
analyzer acceptance at `73cdfc2` is unchanged; this iteration edits only wrapper,
its pure controls and component reports.

Three real-flow synthetic faults pass incorrectly: a suite warning appended after
its phase scan, a later import warning/hash change, and an archive copy that
returns normally but corrupts destination bytes before original deletion. These
prove wrapper integrity defects, not actual native events or leak causes.

Correction gates:

1. Scan/hash each phase from one byte read. At finalization retain one explicit
   final byte snapshot per attempted phase; bind its hash, size and strict scan
   together. Reconcile phase-time receipts with final snapshots and persist
   mismatch evidence. Analyze the suite from that same final snapshot; derive
   sample strict cleanliness from its analyzer/scanner agreement. Do not trust
   an earlier `clean_log` after later work. Any phase drift must fail integrity.
2. Reconcile every attempted phase, including version, import and native probes,
   through finalization. Verify persisted phase receipts and final raw log
   agreement. Recheck source logs after archive work before deletion. Keep old
   phase-time hashes/results rather than overwriting evidence of drift.
3. Compare archive inventory/content with the final private-state source
   inventory; verify source remains unchanged across copying. Verify retained
   UID bytes too. Any missing/changed/extra archive file, source change, raw drift
   or other failed finalization check preserves owned originals and fails the
   attempt. Record archive inventories, mismatch status and preservation flags.
4. Replay unchanged original controls. The old corrupt-archive control includes
   `private_state_removed=true` as a witness of the rejected behavior. Run and
   retain that unchanged assertion, then explicitly replay its unchanged Harness
   and copy fault with the corrected requirement: exit 1, failed integrity,
   mismatched archive and original private bytes preserved. Do not relabel the
   original assertion as passing. Add complete positives, unchanged ordinary
   leak/timeout/interrupt controls, every-phase late drift, post-copy raw changes,
   missing/extra/corrupt archive and source-during-copy failures.

Keep all argv, driver policy, source/copy identity, 120/240-second limits, PID/
start/group/session cleanup, original strict scanner and no-cause/no-drain limits.
No game/helper/input-mode/analyzer/timing changes; no engine/import/UID generation,
native/CI/OCR/service or nested agents. Freeze/commit/push and obtain fresh exact
wrapper review before any diagnostic. Builder issues no acceptance.
