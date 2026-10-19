# ACK snapshot diagnostic evidence

This directory is a distinct follow-up to the immutable PR21 gate-evidence
checkpoint `6a6d18ac295d43bea3be657b0f4575e282e813c0`.

## Reading order

1. Give a fresh critic **only `blind-outcomes.zip`**. It contains the two neutral
   native outcomes, named probe/maintained-gate logs and metric-window instructions.
2. After the outcome-only verdict, inspect `mapping.json`, `manifest-r3.json`,
   `matched-r3.zip` and the report. The manifest identifies exact source, cache,
   engine, workload, commands and raw hashes. Both it and the label key disclose
   source identities and must be withheld from the outcome-only review.
3. `checksums.json` hashes every retained evidence file except itself. The directory's
   Git attributes preserve exact raw bytes across Windows checkouts.

The matched ZIPs contain the original driver output directories without changing
their native JSON or logs. Extract with any standard ZIP tool to inspect all
raw per-tick/snapshot/packet-ledger records. The final archive can be audited without
launching Godot:

```powershell
python scripts/audit_ack_snapshot_evidence.py docs/reports/ack-snapshot-observability-v3/matched-r3.zip
```

## Attempts retained separately

- `preflight/parse.log`: initial fixture parse failure (two missing explicit types
  on values reached through the optional diagnostic interface). No runtime pass
  was claimed. `parse-r2.log`, `parse-r3.log`, `parse-r4.log` retain corrected/native
  parse checks as the fixture was extended.
- `preflight/source-audit*.json`: Git-blob audit proving that removing the five
  diagnostic additions restores the exact original predictor, with only the
  new helper/predictor differing among runtime scripts.
- `initial-r1.zip`: source/workload `06034326b7b005340453383cf7c25909f34253f3`.
  Coverage and legacy equality passed, but the old source could not run the
  helper-specific lifecycle controls. It did not yet include the common lifecycle
  timeline or full recovery drain.
- `initial-r2.zip`: source/workload `f5603d6a362cf195e7f8b68a3dae713af475fafd`.
  Both sources also executed the common 14-event lifecycle timeline; comparisons
  passed. It still ended the six main schedules at tick 540.
- `matched-r3.zip`: final workload `1a941e8fb3041eb7467977d31467824b6cf711eb`.
  Adds the critic-requested packet ledger, explicit percentile windows, known-offset
  receipt and complete 90-tick recovery/drain. All three runs use the same runtime
  `0fbce120d8c17db58596d280f7d8401ab2aa0937`.

Earlier PR21 memory-exhaustion, checkout and exploratory attempts remain in
`../prediction-timeline-v3/`; they are not overwritten or reclassified here.
This evidence concerns diagnostic coverage and preserved execution, not gameplay
accuracy, ENet, Relay Yard, rendering, performance or prediction activation.
