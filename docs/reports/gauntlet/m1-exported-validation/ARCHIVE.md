# Local exported-validation archive

The final [native review](independent-review.md), its
[brief](native-critic-brief.txt), the delegated
[source review](helper-source-review.md), the catalog output and source receipt
are verbatim originals. Their historical absolute workspace paths remain intact.
These integration notes map those paths to the preserved evidence separately.
The native critic confirmed its local report was final before preservation;
its new CI review is outside this archive.

[evidence.tar.gz](evidence.tar.gz) has 445 regular files, 37,721,872 payload bytes
and 32,970,412 compressed bytes (31.4 MiB). The archive is below its 90,000,000-byte
compressed ceiling and GitHub's 100 MB cap. The payload ceiling is 128 MiB. Original
file content is unchanged; sorted tar members use zero timestamps/UID/GID and
mode 0644, and gzip's timestamp is zero.

[Preservation checks](ARCHIVE_CHECKS.md) and their saved result retain the archive
verification separately from gameplay acceptance.

[manifest.json](manifest.json) supplies every member's original relative path,
size and SHA256. Outer [checksums](sha256.txt) cover the archive and companion
records. Verify from this directory and extract into a fresh directory:

```sh
sha256sum -c sha256.txt
python3 verify_archive.py
mkdir -p /tmp/sightbreak-m1-exported-validation
tar -xzf evidence.tar.gz -C /tmp/sightbreak-m1-exported-validation
```

Members start with `root/`, then retain their original repository-relative path.
For example, `root/builds/mission-m1/plant-candidate-r2/results.json` is the
original root receipt. The evidence contains:

- Both plant candidates and the defuse candidate: all available original PNGs,
  commands/PIDs/actions, native logs, traces/status and full results.
- All three external raw snapshot files (`*-status.jsonl.gz`), including the late
  r1 retention and the exact-tick r2/defuse proofs, plus `retain_status.py`.
- The original plant-r1 native video and capture log. No r2, defuse or layout video
  was provided; none was synthesized.
- The complete failed four-size layout folder, including 21 declared captures,
  every retained OCR original/TSV, per-case/all-case results and native logs.
- Both critic folders, their original 346-reference manifest, source snapshots,
  independent checks, receipt verifier, model probes and 1.5-second-delay finding.
- Candidate export source/command/log receipts and plain-text Godot licenses;
  integrated validation stdout, all 79 raw per-suite/unit-fixture files and the
  separate catalog-fixture output.

There are 154 PNG files (including derived critic video frames and OCR originals),
100 OCR TSVs, one original MP4, 19 raw Godot logs and two anonymous synthetic
settings profiles. Both retained profiles have `scope=offline_training`, zero
matches/XP/Credits and empty histories. One records the failed layout's touch-off
setting; the other belongs to the simulated input-mode test. They contain no
real player's progression or authenticated credentials.

The critic's original `critic-native/MANIFEST.json` has 346 entries. All 346 were
matched before copying. Of these, 336 are embedded with identical original paths
under `root/`; the other ten refer to baseline files already in the committed
[baseline archive](../m1-native-approach/baseline-native.tar.gz).
[baseline-references.json](baseline-references.json) records those member paths,
bytes/hashes and the existing archive hash; each actual member was verified.
The baseline and [menu archive](../m1-menu-focus/INDEPENDENT_ARCHIVE.md) are not
copied again. The critic's newly derived baseline video frame and matched X11
negative-control module/results remain in its own folder as review evidence.

[Exclusions](exclusions.json) record the compiled candidate ELF and generated
launcher paths, sizes and hashes, plus 864 discarded cache files. No compiled
app/engine, downloaded template archive, key, Python bytecode, font/Mesa/shader
cache or unrelated game state is included. Raw Godot logs, headless unit-fixture
observations and the two checked synthetic profiles remain. Existing archives
are referenced without repacking or modifying them.

Exact command arrays from original result/export receipts are also copied into
[controller-commands.json](controller-commands.json); raw receipts remain inside.
The broad-validation/catalog text does not preserve its complete launching
argv/environment, so this record does not invent those fields. Scripts named by
the critic's source hashes are snapshotted from exact 6a0d8d5 Git blobs. The full
project/toolchain remains reproducible from that ancestor and its pinned setup
instructions; these snapshots are source evidence, not a portable game package.
The excluded ELF's expected SHA256 remains in the original source receipt. This
preservation step did not perform a bit-for-bit rebuild experiment.

[RESULTS.md](RESULTS.md) separates the observed objective passes from the full
layout failure and source-model limitation. Original reports are immutable
historical evidence. Future corrected runs must carry their own source-bound
receipts; they cannot change this run's failed outcome. No mission worklog,
progress matrix, next-session file or implementation is changed by this archive.
