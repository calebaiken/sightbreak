# Corrected B handoff component accepted; whole reader remains blocked

Independently accept only the corrected action-to-objective handoff component at
`102d79f22082b9c077e2feaccefc84f8985c5875`. B is better than rejected f48: the exact
old mandatory-drop failures now reject for the intended source error, while the
exact required-drop→same-tick recovery positive still accepts. No false accept
or false reject appears in the 44 bounded component controls, in either view.

Original f48 REJECT `bdf00c937f0471cf1b9a3d393a47674b5bd4cc62` remains unchanged,
including its branch, worktree, initialized depth view and every raw result.
The whole reader still falsely accepts two score/FOV mutations. Source/API,
engine behavior, complete combat/AI, human testing, objective quality and native
readiness remain unqualified.

Root is builder. This independent reviewer used a NEW owned corrected-source
worktree and a NEW depth-one view. The existing critic thread is explicitly
reused after the supported thread limit; no fresh-thread claim is made. Own
preregistration `722e27a7e493a87859675685f6f7ef945be6d17e` was committed and pushed
before B tests. Only immutable candidate102 and builder seal
`f7f01d3cd5971785aef2ad4deecd26670c3c4217` were read; the mutable future perception
builder view was not read. The builder cannot approve this correction itself.

## Actual evidence

All runs used CPU4 pure Python/static. Full checkout HEAD was the report-only
preregistration with an identical non-document tree to102; depth HEAD is exact102.

| Check | Full source | Initialized depth-one source |
| --- | --- | --- |
| Maintained component suite | 22/22, no skips, 121.217s | 22/22, no skips, 146.211s |
| Component controls | 44/44, exit0 | Same44 input hashes/verdicts, exit0 |
| Unchanged original13 rig | Positive +10 negatives pass; two false accepts; exit1 | Identical13 raw hashes/verdicts; exit1 |
| Full source paths/modes/physical bytes | 513/513 | 513/513 |
| Current game/scripts inventory | 451/451 | 451/451 |

Recorded timings reflect these actual runs, not hardware or comparative
performance measurements. Reader SHA-256 is
`90e4429680552f310e6fdb7fe3b104376a3be8668979823338f3bbe176c1d1a6`.
Helper/test SHA-256 is
`e0df2c10a38d9adca8f334d283f617f6b8aa0d5c1c0ba4248a5cb3e9db7973c4`.

`replay-fixtures/` copies the exact compressed bytes from old seal bdf:33
projection inputs and their unchanged expectations, the complete two-stream
drop pair and root raw14458 failure. The driver verifies compressed/raw hashes
before replay. No old fixture was regenerated or normalized. Eight new boundary
controls make44 total. Full/depth receipts are identical, including input hashes
and rejection errors. Both source audits pass against the current451 inventory.

## Why the correction wins

Match._eliminated unconditionally drops a carried device when that carrier dies,
using its post-movement position and carrier0. Before B, the reader checked a
drop only when the claimed objective state changed, so an unchanged `carried`
claim skipped the obligation. B derives `carrier_died` from protected current
objective/carrier/alive state and observed death, then requires the actual drop.

All three unchanged failures reject with
`action phase omitted required carrier drop`:

- `carrier_death_suppresses_required_drop` from the old33 projection corpus.
- `dead_carrier_stays_carried_complete_stream`, exact raw SHA-256
  `ff790f5120d1ae4ad28e1d0ab8455fcf27c99ef4aa93ddee162a8fa7b28a9734`.
- Original root complete stream, exact raw SHA-256
  `14458c5f6d9dd0d699679425393283a4acda08ea5e3c16b50b3658c9924ea418`.

The unchanged complete positive
`required_drop_then_consumer_recovery`, raw SHA-256
`7d4fbd000e6c099668003a2c97da35db7d2a4571101f24cc27439c5fee4ce3c8`, accepts.
It genuinely drops before the consumer, which can recover the device and end
the tick carried by another actor. B therefore requires the source transition
at the correct boundary, rather than requiring a dropped end-of-tick state.

New faults reject forged pre-consumer recovery, a dead carrier ID retained on a
drop, a claimed plant replacing the required drop, a drop after another actor's
death and a living carrier rewriting stored device position. New positives
accept the prior carrier dying after planting, death with a device already
dropped, and independent opposing eliminations alongside a required carrier drop.
The planted case matters because planting retains the prior carrier field; the
source only drops when objective state is still `carried`.

All old33 controls retain their original expectations. Legal conditional kill/
cap/uncredited-death fields, damage without death, actor RNG/resources, living
carrier movement and post-decision match RNG remain permitted. No new source
false reject was found in this bounded corpus. These are necessary-field
projections, not a damage/physics/attribution model or universal soundness proof.
The complete synthetic pair likewise does not establish a fully executable
combat history; unrelated future model checks need their own source-faithful
fixtures and must not be mistaken for evidence of this drop fix.

## Remaining blockers and scope

The original rig is byte-exact at SHA-256
`9eaba9f1f567f4deb3d45890adf595dd4846ca9cee6833fcd1f138c58b263403`.
Both views retain all13 actual input streams; their hashes match each other and
the prior f48 replay. All four prior decision guards and six original handoff
mutations remain rejected, while the corrected schema-positive accepts.

The two actual false accepts remain:

- `fabricated_target_score_navigation_and_bot_memory`
- `in_range_in_fov_candidate_falsely_rejected_by_fov`

These are the largest remaining observed gap: target validation still accepts
fabricated scoring and an incorrect FOV rejection reason. The rig correctly
exits1. Its hardcoded historical `dce89495` source footer is preserved as a
legacy label; wrapper receipts bind the actual102 reader/helper bytes. No
whole-reader pass, source/API readiness, native behavior or human qualification
follows from accepting B's necessary handoff invariants.

## Source and recovery proof

Full and depth bindings cover the entire513-path tracked non-document union,
including Git modes/blobs and physical SHA-256, with no sparse omissions. All515
unique comparison objects are available. The B delta from f48 and combined delta
from bc9 contain only verifier and meaningful existing tests. B adds a complete-
trace regression and minimally changes the mandatory-drop branch. No synthetic
helper normalization occurs in this correction.

The new inventory binds451 game/scripts paths. R2/R3 inventories remain byte-
exact; `preservation.json` records hashes and the combined delta. The full game
tree remains `d27f5a57cfc1e22d81d4cf584824d363ecc382d1`, including probe, AI, actions,
controller, authority, protocol and economy. All27 builder-seal files were copied
from pinned f7 Git blobs; `builder-seal-binding.json` records their hashes.

The new depth repository initializes its index before tests with read-tree and
update-index, is clean, shallow=true and commit_count1 at102. Its explicit local
alternate is `/workspace/sightbreak/.git/objects`. This is not a self-contained
clone or object-closure proof. Historical sealed artifact access and the external
immutable rig/driver remain disclosed; no old depth proof was inherited.

Only this own report branch changed. Old f48 evidence, canonical documents and
other worktrees were not modified. No full-blob clone, future builder-C read,
Godot/native/CI/dispatch/process inspection, Mac-file-handling review, runtime
fix, production integration or release occurred. All actual outputs, preserved
remaining failures and exact inputs are retained for a later independent review.
