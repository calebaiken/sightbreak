# Independent actual review of the one verbose bot diagnostic

Strict native verdict: **REJECT**. This diagnostic leaks one
`AudioStreamPlaybackWAV`, one `AudioStreamWAV` and the `Master` StringName.
Exit 0 and successful action assertions do not close the native gate.

The package's provenance, unchanged fixture behavior and typed failure records
are **ACCEPTED as diagnostic evidence**. I replayed the independent full raw
auditor from `b5fa18a`, which passes all 74,142 predicates. Every one of the
1,318 fixture records is byte-for-byte equal to the original baseline's record
at the corresponding position, including frame counters, full snapshots,
commands, events, summaries and terminal result. The added verbosity changes
the surrounding engine log, not any emitted fixture record.

## Frozen source, controller and immutable package

The actual source checkout is clean at
`b87afb717bf09a78c6d36b164d48906902734bdb`. Probe SHA-256 remains
`540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731`.
Pinned Godot 4.7.2 executable hashes before, after and at review match
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
The header's complete weapon/profile definitions match the inspected source.

The executed controller copy has SHA-256
`43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe`
and is byte-identical to the preregistered root `817516a` controller reviewed
before release. That source-method review reconstructs exactly seven permitted
changes from the original wrapper and verifies all ten helper ASTs unchanged.
This actual review verifies the copy against those approved Git bytes again.
The import command is unchanged; only `--verbose` is added to the probe's engine
arguments. There is no audio-driver, fixture, actor-policy or threshold change.

The independent identity audit passes 12,314 checks. It verifies all 8,933
frozen tracked entries by Git mode/blob identity; all 503 original files present
in the sparse checkout against their frozen bytes; every one of the 324 copied
game files; and original/staged before/import/after manifests. Absent sparse
files have recorded Git identities, without measured local filesystem bytes.
No original manifest or tracked game byte changes. The 63 import additions are
62 `.godot` cache files and the one diagnostic UID; all are enumerated and
hashed. The retained UID is `uid://v5jkognemvu\n`, SHA-256
`fed3c3ead085cc1445615fadb7824b5ccba403e4bbf546508d282388169aa613`.
Post-import and post-probe stage manifests are identical.

The complete retained package is root
[`239ee99`](https://github.com/calebaiken/sightbreak/tree/239ee99/docs/reports/gauntlet/m5-exhausted-primary-verbose-diagnostic/actual-r1).
I independently read every one of its 17 archive-map members from Git, checked
archive bytes/hashes, decompressed gzip members, and compared all original
bytes/hashes against the extant raw attempt. Original local output remains in
`/workspace/sightbreak-exhausted-primary-verbose-r2/.local/verbose-leak-diagnostic-r1-20261023`.
The initial publication `0f6f5e4` omitted the two ignored original stderr files;
`239ee99` adds exactly those two files. The final package includes both exact
originals, including the empty import stderr. This publication gap is retained
in `audit.json`; it does not change the native failure.

Verbose stdout is 8,567,143 bytes, SHA-256
`387762da62e75de243f95c84ee66126aa408495d19ef01bd7d5e6e300de2632c`.
Its gzip is 150,346 bytes, SHA-256
`b3f772d2bd993c7246b0ea7b9c15ac3c03a518fb1ef20a14f5f4532492e2c3b2`.
The original 131-byte stderr has SHA-256
`9e2ab4e47a34b3ea04e249930eab8e7920772ac79ef434b2354b5f019068a56b`,
identical to the baseline warning bytes. The common fixture-record stream,
joining the exact record lines with LF, hashes to
`b2404066ef1f35b93eac638ef5070f56232d887586cfea8221f1c13e19f50cba`.

## Actual execution and cleanup scope

The exact native arguments, following the pinned executable, are:

```text
--headless --editor --path <attempt>/staged-project/game --import
--headless --verbose --path <attempt>/staged-project/game --script res://tests/bot_exhausted_primary_probe.gd
```

The full absolute argv and cwd are in the original receipts and `audit.json`.
Private state, all three XDG homes and `ANDROID_USER_HOME` bind to this fresh
attempt's `private-state` directory. Source/hash/fresh-attempt guards remain
the approved ones. Import qualifies before the probe is started.

| Phase, 2026-10-23 UTC | Start / end | PID / start ticks | Wall time | Exit |
| --- | --- | --- | --- | --- |
| Import | 06:54:27.234411 / 06:54:33.718524 | 45378 / 1084400 | 6.484 s | 0 |
| Verbose probe | 06:54:33.768593 / 06:54:56.725205 | 45630 / 1085054 | 22.957 s | 0 |

The wrapper completes in 31.890 seconds. Both native phases remain within the
original 120-second caps and the observed wrapper is within 240 seconds. Each
engine is the only observed stable identity in its own PGID/SID, with the
pinned executable. No timeout or cleanup signal occurs; original terminal
scans find no observed live identity, same-session process or recognized Godot.
Both original PIDs are absent at review time. Cleanup takes about 0.004 / 0.007
seconds, inside the original five-second phase cleanup bounds.

These are observed-identity/session cleanup receipts. The unchanged polling
scope can miss an unobserved descendant escaping and reparenting between scans.
The timeout signal path is unexercised. Empty process scans do not repair the
engine object leaks. `ROOT_SUMMARY` reports external tool session 23521 and
outer exit 0; the package retains a preregistered outer launch plan rather than
the external tool transcript or an outer PID/start identity. I do not promote
the plan into an independent observation of that outer process.

## Raw behavior and typed failures

The full replay verifies 567 matrix cells; 72 sequences / 576 sequence steps;
five positive controls / 96 control steps; all 1,239 authority-action rows;
and their 77 summaries plus header/result. It checks exact registration,
all three shooter/target/objective phases, target input, continuity, active-first
resource maps, unknown equip defaults, all per-weapon conservation, request
causes, stock equip/deploy/reload/cooldown/fire transitions, actual world and
target-volume intersections, event snapshots, ordinary damage/death/rewards,
and terminal-summary binding. The independent checker bytes are the same
committed critic bytes used for the original audit, not the builder's partial
witness oracle. Four explicit attempt-only adaptations update the prior
identity checker's phase key, PID/start constants, controller filename and
verbose argv/stderr filename; their full text and adapted hash are retained.

Observed totals remain 13 real shots, 13 damage events, seven deaths, 610 actual
damage and +2,100 ordinary credits. The mandatory rifle shot occurs at step 2,
consumes the loaded round, deals the artificial target's 10 remaining health,
and produces one death, one shooter kill and +300. Six near-loaded sidearm
sequences each fire two rounds and cause one ordinary death/reward.

| Reload control | Start / completion step | Full configured timer | Final clip / reserve |
| --- | --- | --- | --- |
| SMG | 0 / 16 | 1.85 s | 30 / 0 |
| Rifle | 0 / 19 | 2.25 s | 30 / 0 |
| Marksman | 0 / 24 | 2.8 s | 8 / 0 |
| Sidearm | 1 / 14, after equip at 0 | 1.45 s | 15 / 0 |

All four controls transfer exactly legal reserve rounds, complete within one
action tick after their configured duration, preserve their full target, and
emit no shot/damage/elimination. The sidearm retains the 0.3 s stock deploy.
All loaded/reloadable/difficulty/range/objective, unknown/dry/unowned sidearm
and contradictory-active-cache controls have exactly the baseline outcomes.
The same 626 empty zero-reserve reload requests, 188 empty-clip fire requests
without a shot, and 67 equips remain observable; the first two counts overlap.
The complete case/sequence breakdown is retained in `audit.json` and the prior
baseline review. No selection policy is chosen from this diagnostic.

After the terminal fixture result, raw stdout lines 1389–1393 contain:

```text
Leaked instance: AudioStreamPlaybackWAV:9223372369278539738 - Reference count: 1
Leaked instance: AudioStreamWAV:9223372163673757853 - Reference count: 1
Hint: Leaked instances typically happen when nodes are removed from the scene tree (with `remove_child()`) but not freed (with `free()` or `queue_free()`).
Orphan StringName: Master (static: 0, total: 2)
StringName: 1 unclaimed string names at exit.
```

Separate original stderr remains:

```text
WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).
   at: cleanup (core/object/object.cpp:2536)
```

The generic engine hint is not an allocation-owner trace. The typed records
identify this diagnostic's objects and reference counts. They do not name the
original baseline's leaked objects. Matching classes in a separate ARM test
do not establish a shared call site, retaining owner, engine defect or fix.
The controller's empty `error_lines` array omits this WARNING by design of its
regex; the independent strict verdict therefore remains REJECT.

## Remaining gap and boundary

The largest gap is ownership/lifetime attribution for this leaked playback
and stream. The log contains object classes and IDs but no allocation site,
stream-to-player mapping or last-retaining-reference history. The inspected
stock code plays shot and hurt audio, stops shot/hurt/reload players on actor
exit, and holds shared audio/model caches. The fixture queues the match for
free, awaits one process frame, emits its result and quits. These are supported
investigation paths, without a proved cause. `Master` identifies a StringName,
not a specific player's ownership.

No lifecycle product correction is justified by these class names alone.
The smallest next source step is to trace the existing audio player/playback/
stream ownership and teardown path, preserving actual shots, damage, driver
settings and fixture records. Any future instrumentation or cleanup proposal
needs a separate exact source freeze and review before runtime. No additional
engine/import/native attempt is released by this report. The original baseline
strict failure and this diagnostic strict failure both remain retained.

The unchanged raw audit still cannot observe unlogged intermediate planning
event counters or certify navigation, ordinary match objective timers, aim
quality, physical performance, full-match reliability or generic descendant
cleanup. The 18,499 checks and zero fixture failures are the fixture's reported
terminal values; 74,142 is the separate independent recomputation count.

`audit_verbose.py` reproduces this read-only review; `pure_receipt.json` binds
its exact command, output, dependencies and hashes. `audit.json` retains the
complete raw recomputation, package checks, all 75 non-fixture stdout lines,
typed failure lines, original stderr and cleanup limits. Existing AGENTS/CLAUDE
and the original quality/No AI Slop guidance remain applied. Only this own
report directory changes. This critic ran no engine, import, UID generation,
native, OCR, service, export, CI or nested agent.
