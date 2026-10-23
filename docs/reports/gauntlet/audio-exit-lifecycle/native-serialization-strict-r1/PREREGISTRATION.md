# Native numeric serialization and strict shutdown correction

SOURCE/PURE only. Base is exact `26a1c59ab6d141529a3254ac7f8e68ee4ae99d8b`.
Own branch is `codex/audio-native-serialization-strict-20261023` in the new
`/workspace/sightbreak-audio-native-evidence` sparse worktree. No native engine,
import, UID generation, renderer, OCR, hosted CI, services or nested agent runs.
Root owns fresh independent review and any later native release.

## Preserved benchmark and failure

Read exact independent critic `ae6abe14f031bf40f25ba81f7428f6202166462e`,
[REVIEW.md](https://github.com/calebaiken/sightbreak/blob/ae6abe14f031bf40f25ba81f7428f6202166462e/docs/reports/gauntlet/audio-exit-lifecycle/independent-native-r1/REVIEW.md).
The actual 18.303288-second native attempt has acquisition REJECT and strict
sample FAIL, despite five native phase exits 0. Its raw root stays untouched:
`/workspace/sightbreak-audio-exit-lifecycle/.local/audio-owner-r1-20261023`.
`preserved-evidence.json` binds every one of its 437 files and the critic's
16 retained files, including the existing complete 15,137,320-byte archive.
This correction references that archive instead of copying it.

The actual raw `input-mode.log` is 2,000,315 bytes, SHA-256
`a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218`.
Line 17 contains `"mix_rate":44100.0`. The unchanged analyzer exits 2 with
`Probe header is invalid`. The frozen scanner returns false despite 353
`Orphan StringName:` rows and the positive summary on line 7292. Record those
failures before implementation, then run the same new tests after each change.
Original native receipts, acquisition failure, strict failure and private
originals remain historical evidence. A new pure interpretation cannot complete
that rejected acquisition or retroactively seal its archive.

## Component 1: header numeric compatibility

Accept positive finite JSON floats as well as the already accepted positive
integers for the header's native AudioServer mix rate. Reject booleans, missing
values, null, strings, containers, zero, negative, NaN and either infinity.
Preserve every engine/banner, source, sequence, ObjectID, descriptor, monotonic
frame/time, forced weak window, final seal and exact footer check. WAV descriptor
mix rates stay integer fields. No new observer or audio behavior is in scope.

Named source bar: pinned Godot `ed1daf0bf` AudioServer API declares `float`
(`doc/classes/AudioServer.xml:161`), its public declaration returns `float`
(`servers/audio/audio_server.h:468`) and implementation returns the native driver
rate (`servers/audio/audio_server.cpp:1679`). The exact downloaded bytes and
URLs are retained under `upstream/` and `upstream-retrieval.json`.

Measurable gates: valid integer/float controls pass; every invalid numeric/type
control rejects; all 23 existing analyzer methods still pass; original R1/R2
falsifiers still reject. Pure CLI replay of the complete original raw log must
succeed as parsing and retain raw SHA/length, 6,884 rows, 437 objects, exact
427-player role census, 15 forced windows, no final alive players and unknown
drain/unproven cause. It must report strict failure once component 2 lands.

## Component 2: standalone StringName strict failures

Extend only the shared `native_log.failed` gate. Recognize a complete standalone
`Orphan StringName: <nonempty name> (static: <nonnegative integer>, total:
<nonnegative integer>)` record and the complete standalone `StringName: N
unclaimed string names at exit.` summary when N is positive. Accept LF and CRLF.
Names may contain punctuation, spaces, Unicode and path separators. Preserve all
old error patterns. Zero summary and ordinary/quoted descriptive marker text
stay clean; no valid zero-total orphan is exempted merely for its total count.

Named source bar: pinned `core/string/string_name.cpp:91-106` emits orphan rows
when static and total reference counts disagree and emits the summary only when
`lost_strings` is positive. Keep exact source bytes and regression pins.
Measurable gates: original full native bytes, each of the 353 standalone rows,
and standalone positive summary independently reject; quoted/embedded text,
zero summary and ordinary verbose lines remain clean; old error controls still
reject. The original sample must yield `strict_raw_log_failed=true`,
`sample_status=untyped_strict_failure`, no typed leak join and no cause claim.
Mocked acquisition controls must retain strict rejection for standalone rows
and summary, while existing archive/final-byte controls stay passing.

## Completion and review

Commit preregistration first. Preserve baseline failure output, implementation,
new passing pure outputs and exact source hashes in recoverable own commits;
push explicitly to this branch. Inventory original raw/critic files again and
require equality with the initial inventory. Require no game tree, observer,
hooks, waits, actions, audio, acquisition wrapper or native receipt delta.
Builder results remain pending fresh exact-source independent review. Blind A/B
has no meaningful role for deterministic parsing and strict rejection.

The largest remaining gap is retaining-root/observer lifetime causality. The
final weak census (427 players dead, latest playback dead, seven WAVs dead and
two alive) proves public observations only. No leak repair, release, score,
audible quality, physical-device or historical audio-gate acceptance follows.
