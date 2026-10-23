# Native audio evidence correction

The corrected pure analyzer parses the original native log and reports strict
shutdown failure. Builder tests pass; independent exact-source review is pending.
The original native acquisition remains REJECT and its strict sample remains
FAIL. No engine or native operation ran for this correction.

Preregistration `4cbc1f3` precedes test/failure retention `1a3e7a8`, numeric
implementation `e356343` and strict scanner implementation freeze
`aae1f0a5e963a01dceb4aed1d9c3b0c40520c76f`. All are on the new own branch
`codex/audio-native-serialization-strict-20261023`, based on exact `26a1c59`.
The final independent native review remains exact `ae6abe14`, referenced by
hash alongside its archive and all original receipts in `preserved-evidence.json`.

## Evidence and changes

Actual line 17 uses `"mix_rate":44100.0`, matching the pinned AudioServer public
float API. The frozen analyzer exits 2; the original `baseline-analyzer.stderr`
and command receipt preserve this failure. The corrected header accepts finite
positive floats and positive integers, rejects bool/nonfinite/invalid values,
and preserves the other numeric fields, chronology and evidence checks.

The original scanner misses all 353 orphan records and the positive summary at
line 7292. The corrected shared scanner recognizes complete standalone native
orphan rows and positive unclaimed summaries, including CRLF. Zero summaries,
quoted/embedded examples and ordinary verbose output remain clean. Existing
error patterns are unchanged. Exact source-format pins and relevant raw lines
are retained. `native-cases.json` contains only the actual relevant lines;
`replay_preserved.py` verifies each against the complete original log.

The new controls initially produce 1,069 failed subtests and six errors across
12 methods against unchanged production code. After the numeric change, all
four numeric methods pass, while the combined suite still fails solely on the
remaining strict scanner defect (1,071 failures, zero errors). Those intermediate
outputs remain under `numeric-only.*`. Its numeric-only raw parse still has the
old scanner result and must not qualify strict cleanliness.

After both corrections, 90 pure methods pass with zero skips: 12 new native
compatibility methods, 23 existing analyzer, 13 acquisition, eight final-byte/
archive finalization, 24 build-manifest/scanner, and ten unchanged R2/chronology
controls. The full native log CLI exits 0 for parsing, preserving its exact
2,000,315-byte SHA-256 `a50a8191…7a218`; it reports:

- 6,884 records, 437 objects and all 15 complete forced weak windows.
- Exactly 427 classified players: 70 shot, 70 hurt, 280 reload, seven device.
- No final alive observed players and no typed leaked-instance joins.
- `strict_raw_log_failed=true`, `sample_status=untyped_strict_failure`.
- Unknown server drain and unproven retaining reference/cause.

`corrected-command-receipts.json` binds all five maintained/new group outputs
and the full original-log CLI replay. `unchanged-r2-and-chronology.stderr`
retains the ten separate unchanged controls. The readable pure result is
`preservation-and-replay.json`; a second repeatable audit is retained in
`replay-preserved.stdout`.

## Scope and preservation

`source-binding.json` binds the exact implementation freeze and three changed
source paths: two production Python files and one new pure test module. Every
other existing game/script path is byte-identical to base. The entire game tree,
probe, optional hooks, existing actions/waits, audio and acquisition wrapper are
unchanged. Full native validation is outside this source/pure authorization.

Both preservation audits rehash all 437 original raw files and all 16 critic
files without any change. Original checkout stays clean at exact `26a1c59`;
original `overall.json` still has `acquisition_integrity=false`, `passed=false`
and `sample_strict_clean=false`. The complete existing 15,137,320-byte native
archive is referenced rather than duplicated. This pure interpretation supplies
no missing closing acquisition seal and does not rewrite old clean-log receipts.

## Largest remaining gap

The retaining root and instrumentation lifetime remain unknown. Source shows
`_players[id].last` keeps sampled descriptors; `finish()` takes the final weak
snapshot and disconnects signals without clearing the dictionaries. The test's
`audio_probe` variable remains bound when it calls quit. Native orphan names
overlap observed names/path components, which supports an instrumentation
lifetime hypothesis. These facts do not establish causality or ownership of any
native leaked resource. No observer correction is included.

The original public weak census (427 players dead, latest playback dead, seven
WAVs dead, two alive) cannot prove mixer drain or a leaked exit resource. Earlier
unknown-type, ARM and verbose bot audio failures remain failed with their exact
evidence. Root must obtain fresh source review before any further audio work or
native selection. No audio leak repair, listening/device quality or release gate
is accepted here.
