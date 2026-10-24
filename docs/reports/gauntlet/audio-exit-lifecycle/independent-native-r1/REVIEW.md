# Independent actual audio ownership review

Acquisition verdict: **REJECT**. Strict-sample verdict: **FAIL**. The single
Linux native attempt at exact `26a1c59ab6d141529a3254ac7f8e68ee4ae99d8b`
finished with wrapper exit 1 in 18.303288 seconds. The frozen analyzer rejects
the native header, and the complete raw log contains 353 orphan StringNames.
No historical leak blocker or release gate is resolved.

This critic preregistered at `33a2b31` before root release `1d70987` and read the
actual files only after the root terminal notification. Source-only reviews
`146dc17` and `e08b313` do not accept this runtime result. No engine, import,
UID generation, CI, OCR, service or nested agent was launched by this critic.

## Actual failures and largest gap

`input-mode.log` line 17 contains a valid native JSON numeric value
`"mix_rate":44100.0`. The producer emits `AudioServer.get_mix_rate()` directly
at `game/tests/audio_lifecycle_probe.gd:15`. The frozen analyzer requires
`type(mix_rate) is int` at `scripts/analyze_audio_lifecycle.py:68`; Python parses
this native token as a float. An unchanged pure CLI replay exits 2 with
`Audio lifecycle evidence rejected: Probe header is invalid`. `analysis.json`
does not exist. The wrapper records `final_analysis` failure, preserves both
private originals and returns 1. It never reaches the private archive's final
pre-removal seal. Earlier phase-log sealing does not complete acquisition.

The log then has 353 `Orphan StringName:` records, starting at line 6939, and
ends at line 7292 with `StringName: 353 unclaimed string names at exit.` Examples
include `ReloadAudio (static: 0, total: 280)`, player names and full node paths.
There is no `Leaked instance:` record and no ObjectDB warning in this sample.
The exact frozen `native_log.failed` expression checks SCRIPT ERROR, ERROR,
Parse Error, ObjectDB leaked and Leaked instance; it omits standalone orphan and
unclaimed StringName lines. Its return is false on these complete native bytes,
so all phase receipts say `clean_log=true`. That narrow scanner result cannot
qualify strict cleanliness. `sample_strict_clean=false` and `passed=false`
remain in the original receipt because analysis failed.

The largest supported gap is that the runtime ownership diagnostic cannot
produce an accepted interpretation of its own native serialization and its
strict scanner misses an actual shutdown failure class. No retaining audio
root or cause has been established. Observer state remains a separate concern:
`_players[id].last` retains sampled primitive descriptors at probe line 91,
while `finish()` takes the final snapshot and disconnects signals at lines
107–112 without clearing those dictionaries. The orphan names overlap player
names/path components observed by the probe. This supports investigating
instrumentation lifetime; it does not prove that it caused the orphan names or
that the product has the same retaining reference.

## Provenance, isolation and retention checks

The independent pure audit retains 8,108 explicit predicates; four acceptance
predicates fail for the acquisition, analyzer, header type and orphan names.
All other recorded checks pass. This is evidence reconciliation, not 8,108 game
assertions. Exact Git objects and current local bytes match all 428 game/script
paths in before/after/sealed manifests. The 324-file mechanical project map
matches source; its only declared modification is the fresh custom-user-dir
override. Import preserves noncache source bytes and adds one actual observer
script UID, whose syntax and retained bytes match. The preserved original
project's current full inventory equals its final native inventory.

The executable matches the pinned existing Linux Godot 4.7.2 SHA-256
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`
before, after, at seal and when independently read. Its native version output
is exact. All five phase commands match the frozen source. The suite uses the
owned project path, `--headless --verbose --script res://tests/input_mode_test.gd
-- --audio-lifecycle-diagnostic`, with no audio-driver substitution.

Both standalone native identity JSON objects exactly equal their embedded
`overall.native_before` / `native_after` values. Both identify the owned project,
private XDG data root, unique custom namespace and default Dummy driver. The
initial native profile and diagnostics are absent; the final native profile
exists in that namespace. Its archived JSON contains fresh offline training
state with zero matches, XP and credits. All eight private-state files match
the final, archive and post-copy inventories and both current retained trees.
Private originals remain present, as the failed attempt requires.

All original raw phase hashes, lengths, scans, persisted receipt objects,
retained snapshots and closing seals agree. In particular, the suite is
2,000,315 bytes with SHA-256
`a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218`.
The original outer tool receipt records wrapper exit 1; wrapper stdout/stderr
are empty. None of those receipts was edited to report a later interpretation.

| Native phase | Wall seconds | Phase cap | Exit |
| --- | ---: | ---: | ---: |
| Engine version | 0.120 | 30 | 0 |
| Private import | 9.834 | 120 | 0 |
| Identity before | 0.238 | 30 | 0 |
| Input mode diagnostic | 5.664 | 120 | 0 |
| Identity after | 0.317 | 30 | 0 |

The whole attempt stays inside 240 seconds; no phase timeout or cleanup signal
occurs. All six observed PID/start identities, including the import shell,
have no terminal survivors, original process group or session. An independent
later `/proc` read confirms those identities/groups/sessions are gone and finds
no recognized Godot process. Polling cannot prove cleanup of unseen escaped or
reparented descendants, and cooperative syscall checks establish no hard bound
against a stalled operating-system call.

`actual-native-evidence.tar.gz` retains 375 native files, including all unique
logs, snapshots, identities, receipts, actual generated UID, both state copies
and the complete noncache copied project. Every member was reread and verified
against `artifact-retention.json`, which also records the outer SHA-256 and
15,137,320-byte size. Only 62 `project/.godot/` cache files are omitted from the
pushed archive; their complete names, sizes and hashes remain in the retention
manifest and audit. The original raw tree, including native caches and private
originals, remains untouched at the expected `.local/audio-owner-r1-20261023`
path. Archive completeness does not reverse the acquisition rejection.

## What the raw census supports

The native footer independently reports 462 checks, zero assertion failures,
`graphical_pointer=false` and `baseline=false`. The 6,884 contiguous records
contain one header, 437 object registrations, 1,849 player observations, 4,374
weak observations and 223 checkpoints. Frame/time values are monotone. All 15
forced weak windows cover every object registered at that moment exactly once,
in the original six HUD before/after pairs followed by final before/after and
sealed final-pre-quit order. No probe record follows that final checkpoint.

The independent role census is exact: 70 actor-shot players, 70 actor-hurt,
280 reload voices and seven match-device players, totaling 427. The final weak
window reports all 427 players dead, the one observed latest WAV playback dead,
seven WAV resources dead and two WAV resources alive. Those two WAV descriptors
have hashes `ae60148f…aa143b6` and `eb3d120e…4520b7`, observed previously in
actor-shot and actor-hurt stream fields respectively. They remain only public
weak-liveness observations. With no typed native leak record, they cannot be
joined to a reported leaked ObjectID or labeled leaked exit resources.

Default Dummy identity, stopped players, latest playback, dead weak references
and public mix-clock fields do not acknowledge mixer drain. Earlier polyphonic
voices, retaining roots and cause remain unknown. The raw census is useful
partial evidence; the frozen analyzer has not accepted it. Linux headless Dummy
provides no audible-quality, listening, physical-device or Mac qualification.

## Required next step

Retain this failed sample and make a narrow, separately reviewed pure-source
correction for real native numeric serialization and standalone StringName
strict rejection. Add controls using these exact retained bytes, preserving the
original analyzer exit 2 and scanner false result as historical failures. Audit
observer descriptor lifetime without assuming an audio cause. Any future
native selection remains root-controlled after fresh exact-source review; this
review authorizes no retry and applies no implementation change.

The original unknown-type baseline remains failed. The ARM
AudioStreamPlaybackWAV / AudioStreamWAV / Master StringName failures and verbose
bot diagnostic remain failed with their previous evidence. Matching classes
would not establish common ownership or cause; this different one-sample census
cannot repair or supersede those failures.
