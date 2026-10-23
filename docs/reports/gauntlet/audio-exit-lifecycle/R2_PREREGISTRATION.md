# R2 analyzer chronology correction preregistration

Source/pure work only, 2026-10-23. Correct rejected freeze `809dbc0` on its own
branch. Independent critic `800f60536263780c87a56b61827f45492a1323e2`
accepted the observer/hooks and source-byte preservation within its source scope,
but rejected the analyzer. The exact report, replay program, three original
synthetic logs, accepted reports and original failing output are retained under
`independent-source-r1-original`, with a Git-object/SHA-256 retention manifest.
No retained original file will be edited or replaced.

The three unchanged controls prove: a post-final weak row can contradict final
liveness; final weak rows can precede all leave checkpoints; and entirely absent
post-leave weak rows can pass. These are analyzer defects in synthetic evidence,
not observed engine behavior or proof of an audio ownership bug. The actual ARM
and bot strict leak failures remain failures.

The source-grounded bar is the unchanged helper's synchronous `snapshot`:
player observations precede its weak loop; each forced snapshot visits every
registered object exactly once; its checkpoint closes that snapshot. Weak rows
must therefore belong to the interval after the previous checkpoint and before
their own checkpoint. Structural add/remove observations can occur between
snapshots with the previous stage label; those are not weak snapshots. Existing
frame snapshots may contain only changed weak values. Every pre/post-leave and
final snapshot is forced. The final checkpoint seals the probe stream; engine
verbose/strict text afterward remains untouched.

Correction gates for fresh independent review:

1. Preserve the observer and maintained input_mode hooks byte-for-byte at
   `809dbc0`; removing the existing hooks must still reconstruct c08889b exactly.
   Add no game actions, waits, sleeps, stop/free/drain calls or audio-driver change.
2. Partition weak rows into actual checkpoint windows. Reject stage mismatch,
   duplicates, missing required rows and incomplete trailing windows. Require
   one row for every object registered by each forced checkpoint, including
   every repeated post-HUD-leave window, post-final-leave and final window.
   Keep incremental existing-frame windows valid.
3. Reject every probe record after final checkpoint. Compute final liveness
   solely from the validated final window, with an explicit final checkpoint
   sequence and per-forced-window coverage in the report. Alive final players
   remain evidence, never a parser shortcut to drain or cause.
4. Retain the existing incomplete `fixture()` unchanged for the independent
   replay's third falsifier. Add a separate complete positive fixture and move
   ordinary positive controls to it. Replay the original critic program and
   all three saved raw synthetic inputs unchanged. Also demonstrate complete
   positives and isolate each defect on otherwise complete input: late records,
   early/falsely labeled weak rows, duplicate/missing per-window rows and
   repeated-stage coverage. Missing a row in any one repeated window must fail.
5. Preserve unsigned exact joins, unknown/different/shared owners, strict raw
   scanner behavior and no-fix/no-drain wording. Retain all new pure outputs and
   original rejection evidence, freeze/commit/push, then request fresh source
   review before any diagnostic. A separately reviewed bounded acquisition
   wrapper remains required; this correction adds none.

No Godot, import, UID generation, GDScript compile, native run, CI, OCR or service
will execute during this builder iteration. No source approval is self-issued.
