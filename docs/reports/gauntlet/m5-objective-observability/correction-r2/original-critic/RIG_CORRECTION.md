# Original rig correction

The builder's objection is valid. In the unchanged original rig,
`valid_maintained_synthetic_receipt` and
`forward_rows_have_no_dt_pose_command_objective_or_progress` both call
`lambda rows: None`, then submit identical `synthetic_records()` input while
expecting opposite outcomes. Counting the second as an independent negative
falsifier was my mistake. Calling the baseline “valid” also implied a completeness
guarantee that the sparse synthetic data does not establish.

The original script SHA-256 is
`af4a712cdd9f195203ad4caec4c9351da4a0ebf221d80ef23e54cd2ec3489813`.
It matches the script stored at original review HEAD `705de403`. Both inputs
serialize to SHA-256
`52b2b8f0a10945bcbd4cef43fce3f0df73f32457a8438a2dc9b15e22e6b8387f`.
The original unchanged CPU 4 replay exits 1 and produces the same result object
as the preserved `independent-controls.json`. `rig-adjudication.json` records the
ASTs, input equality, hashes and corrected counts. The original script and outputs
are unchanged; `rig-original-rerun.*` retains the follow-up replay separately.

Interpret the original twenty named cases as nineteen distinct cases: one
baseline acceptance smoke case and eighteen actual mutations. Thirteen mutated
receipts are accepted and five rejected. Exclude the defective no-op negative
from mutation counts. The baseline's 120 forward authority rows contain only
`label` and `tick`, so the missing-field observation remains factually supported;
it is not an independent deletion experiment. A future deletion falsifier needs
a complete accepted baseline followed by an actual field-removal mutation.

Other accepted mutation receipts and the source findings still support REJECT
for original candidate `c91d9b98`. This adjudication neither inspects nor approves
the builder's corrected candidate. No new source review or native work occurred.

Reproduce from the own review worktree:

```sh
taskset -c 4 python3 docs/reports/gauntlet/m5-objective-observability/independent-source/adjudicate_original_rig.py
```

The adjudication itself exits 0 when the original-script identity, replay equality
and contradiction checks succeed; it separately records the original rig's
expected retained exit 1. Source/pure CPU 4 only. No nested agents or engine.
