# R2 source handoff for fresh review

Corrects the analyzer rejected at `809dbc0` by independent `800f605`. R2 was
preregistered at `8af9934`. This handoff describes source and pure-Python checks;
the builder issues no source approval or runtime release.

The analyzer now assigns weak rows to the window after the preceding checkpoint
and before their own checkpoint. It rejects stage mismatches and duplicate IDs.
Every forced pre/post-leave and final window must contain one weak row for every
object registered by its checkpoint, including each of the six repeated HUD
leave pairs. Incremental existing-frame windows may remain empty or partial.
The final checkpoint seals the probe stream. Final player liveness comes only
from that validated final window. Reports expose its checkpoint sequence and
each forced window's object/weak counts. Raw engine text after the probe stays
under the original strict scanner; no internal drain or retaining owner is
inferred.

No GDScript or input_mode hook changed in R2. The pure fidelity control still
reconstructs the c08889b test body exactly after removing the already reviewed
optional hooks. Product scripts, sound bytes/timing/levels/spatial settings/voice
counts, actions, waits, leave/free/quit calls, original runners and scanner are
unchanged. No engine, import, UID generation, GDScript compile, native execution,
CI, OCR or service ran.

## Retained rejection and pure results

`independent-source-r1-original` retains all 17 original critic files byte-for-byte
from `800f605`, including its three raw synthetic inputs, accepted reports,
replay program and failed assertions. `retention.json` identifies their original
Git paths and SHA-256 hashes. The old incomplete `fixture()` remains unchanged
so the critic's replay continues to generate exactly its original falsifiers.
A separate `complete_fixture()` supplies positive traces.

`python3 scripts/test_analyze_audio_lifecycle.py -v` passes **21 tests**. New
controls accept complete forced snapshots, empty/partial incremental windows
and a valid final alive-player observation without cause/drain claims. They
reject every post-final probe record kind, early/falsely labeled final weak rows,
duplicate rows, incomplete trailing windows and a missing weak row in each of
all 15 forced windows. Original ID/owner/strict-result controls remain.

The first R2 maintained run exposed a test migration error: its old hardcoded
indices now referred to two same-stage weak rows in the larger positive fixture.
`r2-pure/maintained-r1.log` retains that failure. The test now selects the actual
checkpoint records before swapping their stage labels; it passes without a
parser relaxation. `r2-pure/maintained-final.log` retains the complete result.

`r2-pure/replay_counterexamples.py` is an unchanged byte copy of the original
critic program in a fresh output directory. Its **three tests pass** in
`unchanged-independent-replay.log`; generated synthetic logs and rejection
summary are retained there. The analyzer also rejects all three originally
saved raw inputs directly. Some original traces fail at their first missing
post-leave window before reaching their later defect; the isolated complete-input
controls separately verify final sealing and misplaced-final rejection.

`r2-pure/receipts.json` binds commands, outputs, original-input hashes and checks
that retained critic evidence remained unchanged. `source-audit.json` binds the
unchanged observer/hooks and fixture, plus the R2 source file hashes. This is
builder evidence for the fresh critic, not independent acceptance.

The strict actual leak failures remain unresolved. GDScript compile/API behavior,
actual owner coverage and acquisition remain UNVERIFIED. Fresh exact-source
review and a separate reviewed bounded acquisition wrapper are required before
any diagnostic. The existing exact-argv verbose replay controller stays unchanged.
