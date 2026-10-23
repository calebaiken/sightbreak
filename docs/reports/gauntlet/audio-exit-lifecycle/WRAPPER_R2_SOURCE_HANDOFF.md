# Corrected wrapper freeze for fresh exact review

Preregistered at `7026f73`, correcting wrapper rejection `062147c` / raw retention
`337d82aa`. Both full original review trees are retained separately with exact
Git-object/SHA-256 manifests: 179 files and 223 files, including all original
synthetic raw logs and failed assertions. No original evidence was edited.

Each phase now computes its closing hash, byte count and strict result from one
byte read. Finalization retains an explicit byte snapshot of every attempted
phase, checks persisted receipt equality and closing/final hash/size/scan
agreement, then analyzes the suite from those same retained bytes. The report
derives sample strict cleanliness from that final analysis/scanner agreement.
Earlier receipt fields remain intact when later bytes differ. Late phase drift
fails acquisition integrity even if a previous scan was clean.

After archive work, the wrapper rechecks all original logs, retained snapshots,
phase receipt hashes and analysis. `final-phase-snapshots.json` and
`phase-seal.json` preserve expected/current hashes, strict results and mismatch
details. Private-state source, archive and post-copy inventories must match;
both source and archive are rechecked immediately before removal. Generated UID
archives are checked too. Any mismatch or failed finalization preserves the
owned private project/state and fails the attempt. Archive inventories and
preservation flags remain in the overall receipt. A known, unchanged suite leak
still has valid acquisition integrity and returns strict exit 1.

Pure results for this freeze:

* 13 maintained wrapper tests pass.
* Eight explicit replay groups pass using the retained critic's unchanged
  actual-flow Harness, real temporary Git, and mocked engine processes. They
  verify the original three faults, every phase's raw drift during archiving,
  receipt/snapshot/analysis drift, missing/extra/corrupt archive files, source
  changes during copying, UID corruption and changes after initial archive
  verification. Complete clean and ordinary strict-leak positives remain valid.
* The unchanged 14-group critic replay passes 13 groups, including both original
  late-log rejection tests. It still exits 1 at its old archive witness assertion
  `private_state_removed=true`. The corrected wrapper reports false and retains
  the originals, so that historical assertion must fail. Its exact code/output
  remains unchanged in `wrapper-r2-replay-final`; this is not claimed as a passing
  unchanged suite. The explicit archive replay requires false, exit 1, failed
  integrity, changed archive bytes and original private bytes still present.

`wrapper-r2-pure/corrected-*` retains three newly replayed fault outputs, final
snapshots, corrupted archives and the preserved original private bytes. Each
`corrected-witness.json` identifies synthetic scope and rejection/preservation.
`source-retention-audit.json` verifies all 402 retained original critic files and
all 425 source paths at accepted analyzer freeze `73cdfc2` byte-for-byte. Only
wrapper/pure controls/report files changed. Observer/analyzer acceptance remains
separate and untouched; the builder issues no acceptance of this correction.

Linux scope, exact argv/default Dummy, native path/identity/source/executable
pins, 120/240-second limits, PID/start/group/session cleanup, strict scanner and
no-cause/no-drain limits remain. File operations use cooperative deadline checks;
this does not promise a hard bound against a stalled OS syscall. No engine,
import, actual UID generation, GDScript compile, native/CI/OCR/service or nested
agent ran. A fresh exact wrapper review is required before selecting one actual
diagnostic; actual strict leak failures remain unresolved.
