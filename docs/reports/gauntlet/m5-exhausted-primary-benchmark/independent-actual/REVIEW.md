# Independent review of the single actual exhausted-primary baseline

Strict native verdict: **REJECT**. The original baseline exits 0 and emits its
registered diagnostic witnesses, but its original stderr reports two leaked
ObjectDB instances. That warning remains a failure. It is not resolved by an
empty OS process scan, the fixture's claimed 18,499 checks, a source approval,
or an independently consistent resource timeline.

The retained actual observations are usable as a bounded diagnostic. My own
all-row recomputation passes **74,142 predicates** without a mismatch. It does
not import or call the builder's partial `witness_oracle.py` or resource audit.
This approves the stated observations and provenance only; it does not approve
a new tactical policy, a leak fix, a complete match, or a release gate.

## Exact evidence and source identity

The tested source is `b87afb717bf09a78c6d36b164d48906902734bdb`;
probe SHA-256 is
`540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731`.
Source-only approvals `3359120` / `5fbf3ac` remain separate from actual output.
The immutable builder package is
[`700abf8c9d43279518c5257edfdbaee513569cea`](https://github.com/calebaiken/sightbreak/tree/700abf8c9d43279518c5257edfdbaee513569cea/docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2).
The builder's own audits are evidence to inspect, not independent acceptance.

I read the original local attempt under
`.local/exhausted-primary-r2-single-attempt-20261023`, then independently checked
the published package against those bytes. All 23 inventory entries match their
Git objects. All six compressed originals restore the exact originals. Baseline
stdout is 8,558,093 bytes, SHA-256
`e6606c22b5d5cc5c33090a97b1a832e60a376465a0edfa112146b7f743b10d7f`;
stderr is 131 bytes, SHA-256
`9e2ab4e47a34b3ea04e249930eab8e7920772ac79ef434b2354b5f019068a56b`.

The separate identity audit passes 12,314 checks. It compares every one of
8,933 recorded tracked entries to the frozen Git tree, including modes and blob
IDs, and hashes all 503 files physically present in the original sparse checkout
against their Git objects. The other entries are explicitly absent; their local
filesystem bytes were not measured. The complete original before/after manifest
is identical. All **324 tracked game files** match the frozen blobs, copied
source-map receipts, all three stage manifests and the extant staged files.
No tracked game byte changes during import or probe.

Import adds 63 enumerated files: 62 under `game/.godot/` and the one diagnostic
UID `game/tests/bot_exhausted_primary_probe.gd.uid`. Its retained bytes are
`uid://v5jkognemvu\n`, SHA-256
`fed3c3ead085cc1445615fadb7824b5ccba403e4bbf546508d282388169aa613`.
The post-import and post-probe stage manifests are identical. The UID remains
preparation output; it does not modify the frozen source.

The pinned executable hashes before, after and at review match
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
The raw header reports official Godot 4.7.2, engine source hash
`ed1daf0bf001b61586d9930840f2f1394092c079`. All emitted weapon definitions,
including colors, and all difficulty-profile fields match the inspected source.

## Actual commands and scoped process cleanup

The retained controller has SHA-256
`cc2ef4365971871a87497256667554df89983360e8fcae4527b224a7438a5142`.
I inspected its fresh-attempt/freeze guards, mechanical copy, exact `Popen`
arguments, private environment, process identity discovery, deadlines and cleanup.
Its native commands are the pinned binary followed by:

```text
--headless --editor --path <attempt>/staged-project/game --import
--headless --path <attempt>/staged-project/game --script res://tests/bot_exhausted_primary_probe.gd
```

The full absolute arguments and cwd are retained in the independent identity
receipt and the two original phase receipts. No `--verbose` or alternate audio
driver appears in this original attempt. The original proposed audio-Dummy
example is not evidence that this attempt used that flag.

| Phase, 2026-10-23 UTC | Start / end | PID / start ticks | Wall time | Exit |
| --- | --- | --- | --- | --- |
| Import | 06:35:38.154746 / 06:35:44.652589 | 34219 / 971492 | 6.498 s | 0 |
| Baseline | 06:35:44.709890 / 06:36:06.928515 | 34468 / 972148 | 22.219 s | 0 |

Both phases remain inside their original 120-second caps; the whole wrapper
uses 30.942 of 240 seconds. Each engine is the observed leader of its own
PGID/SID, with the pinned executable identity. No timeout or termination signal
occurs. Original terminal scans find no observed live identity, same-session
process or recognized Godot. Review-time inspection also finds both original
PIDs absent. `SIGHTBREAK_STATE_DIR`, the three XDG homes and
`ANDROID_USER_HOME` point into this attempt's `private-state` directory; HOME
and the inherited environment are preserved.

This is successful cleanup within the declared observed-identity/session scope.
The 50 ms polling can miss a previously unobserved descendant that escapes and
reparents between observations. The timeout signal path did not run. The
receipts and controller establish the recorded launch arguments and observed
identity; they are not an independent OS audit of every possible descendant.

The complete original stderr remains:

```text
WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).
   at: cleanup (core/object/object.cpp:2536)
```

The controller's `error_lines` matcher detects script/parse/ERROR lines but
does not classify this WARNING. An empty `error_lines` array therefore provides
no evidence of a clean strict native result.

## Full raw recomputation and positive witnesses

There are exactly 567 CASE rows, 576 STEP rows in 72 eight-step sequences,
and 96 CONTROL_STEP rows in five controls. I independently generate the full
ordered registration and compare every label, step and scenario dictionary.
The six matrix groups have 324 / 54 / 27 / 81 / 54 / 27 cells. Every sequence
and control summary, including full initial/final control snapshots, binds to
its raw rows, and the terminal control list binds to those summaries.

For every action row I check the complete shooter, target and objective field
sets; exact initial resources and registered poses; uninterrupted actor states
between steps; all three planning equality fences; and objective action purity.
I independently reconstruct every active/holstered/unknown/unowned resource map,
per-weapon projected total, stock equip default, reload transfer, deploy timer,
cooldown, trigger edge and complete shooter action snapshot. I also recompute
the baseline weapon request, reload and fire causes from profile, range,
reaction, interaction and resource state. This does not simulate requested
movement, crouching, navigation or full match objective timers.

Actual query endpoints bind to each registered pose and fixed yaw/pitch. Frame
counters demonstrate settled poses. Independent intersection arithmetic over
all 26 inspected stock solid AABBs agrees with every emitted world-clear flag
and world-hit position; independent target capsule/head-volume intersections
agree with every stock center trace. Ordinary through-45.5 m lanes are clear;
the declared 60 m diagonal can cross freight. This source arithmetic checks the
raw physics observations rather than substituting for their execution.

For fired shots I independently trace the actual emitted direction against the
world and target volumes, apply the stock distance falloff/head multiplier and
health clamp, then compare all damage, elimination and reward snapshots. The
33 global event serials occur exactly once, with damage before elimination
before the corresponding shot recorder. This verifies 13 shots, 13 damage
events, seven deaths, 610 total actual damage and +2,100 ordinary credits across
all rows. Every shot consumes exactly one round of its own weapon.

| Mandatory control | Independently verified actual witness |
| --- | --- |
| `kill_rifle` | Step 2 consumes its one rifle round; 10 clamped actual damage; one elimination; victim deaths +1; shooter kills +1 and credits 800 → 1100; no equip or reload |
| `reload_smg` | Start 0, completion 16; timer starts at 1.85 s; final 30 / 0 |
| `reload_rifle` | Start 0, completion 19; timer starts at 2.25 s; final 30 / 0 |
| `reload_marksman` | Start 0, completion 24; timer starts at 2.8 s; final 8 / 0 |
| `reload_sidearm` | One equip at 0 with 0.3 s deploy; reload starts 1, completes 14; full 1.45 s start timer; final 15 / 0 |

Every reload start leaves clip/reserve unchanged, every completion transfers
exactly the legal reserve amount, and elapsed time is within one action tick
after its configured duration. The four reload controls emit no shot, damage
or elimination and preserve the full target. Reload and deploy can overlap in
the stock consumer; no invented sequential delay is imposed.

The raw file reports 18,499 fixture checks and zero fixture failures. My
74,142-predicate count is a separate audit, not a relabeling of that number.
It protects the emitted phases and event causes. Intermediate event-array
counts immediately after planning are checked inside the frozen fixture but
not emitted as raw phase counters. Unlogged transient planning events are
outside what this independent output audit can establish.

## Exhausted-primary behavior and controls

All 567 independent first decisions emit no shot, because the controlled first
decision has not passed a profile's reaction delay. The matrix includes 54
actual sidearm equips, all normal/hard, near and without an interaction.
Across all 1,239 action rows there are 67 equips, 626 zero-reserve empty reload
requests and 188 empty-clip fire requests without a shot. Those last two
categories overlap and include controls and legitimate in-progress reloads;
they must not be summed as a defect count.

For the eight-step sequences below, each profile column aggregates the three
separate primaries. `R` counts exhausted-primary reload requests; `F` counts
empty-clip fire requests with no shot. Each sequence lasts 0.96 simulated
seconds; this is not a complete match or proof of permanent deadlock.

| Setting | Easy | Normal | Hard |
| --- | --- | --- | --- |
| Exhausted primary, loaded sidearm, visible 24 m | No equip/shot; R24, F10 | No equip/shot; R24, F15 | No equip/shot; R24, F18 |
| Exhausted primary, loaded sidearm, hidden target | No equip/shot; R24 | Same | Same |
| Exhausted primary, loaded sidearm, visible 6 m | No equip/shot; R24, F10 | Three equips; six sidearm shots; three deaths; +900 | Same outcomes, earlier shots |
| Exhausted primary, loaded sidearm, visible 45.5 m | No acquisition/equip/shot; R24 | Same | Acquired; no equip/shot; R24, F18 |
| Reloadable primary, loaded sidearm, visible 24 m | No equip; all three primary reloads start | Same | Same |
| Exhausted primary, reserve-only sidearm, visible 6 m | No equip/shot; R24 | Three equips and three sidearm reload starts; no completion in 0.96 s | Same |

The six normal/hard near-loaded sequences each consume two sidearm rounds,
deal 100 actual damage, cause one death and earn +300. Their first sidearm hit
is a source-volume headshot dealing approximately 83.858, and the second clamps
to the remaining approximately 16.142 health. The separate longer mandatory
sidearm control proves a reserve-only sidearm can complete its stock reload.

The observations preserve several policy distinctions:

- All 81 loaded-active cells, including 27 contradictory-cache controls, retain
  their primary and one loaded round on the first decision. All 189 reloadable
  cells conserve reserve; 24 normal/hard near cells equip a sidearm under the
  existing clip-only fallback, and the other 165 accept primary reload starts.
- Easy's 189 matrix cells never request an equip. All 54 carrier/defuser cells
  request interaction and suppress fire/reload/equip. Exact 20 m does not meet
  the stock `<20 m` fallback; 60 m is outside every profile's acquisition range.
- Hard acquires 45.5 m while easy/normal do not. That distance exceeds the
  sidearm's defined 45 m trace range. Acquisition, fallback distance and weapon
  range remain separate, observed controls.
- Loaded, reserve-only, known-dry, unknown and unowned sidearms stay distinct.
  Known-dry and unknown near cells can still trigger the existing fallback.
  An actual unknown equip receives stock 15 / 60 defaults; projected conservation
  accounts for that default without claiming it was previously known available.
  All 27 unowned-sidearm cells preserve nonownership and make no equip.
- Active clip/reserve always override contradictory active-cache entries in
  all 81 stale-cache cells. Active-cache values remain stale until stock equip
  writes them; treating the stale cache as extra active ammunition would be wrong.

The 24 m and hidden-target sequences demonstrate repeated commands which
cannot use the exhausted active primary despite known holstered ammunition.
The data do not choose whether a future policy should change selection, range,
idle handling or another behavior. Any proposal needs its own exact scope and
preserved controls after root decides the intended policy.

## Critic checks, remaining gap and smallest next diagnostic

The independent auditor rejects 14 mutations of in-memory copies of the actual
records, retaining the rejection reason for each. These include a continuous
wrong 20 m positive lane and a continuous timeline that returns the spent kill
round, the two classes that the partial witness oracle was known to accept.
Other controls cover identity, target/objective planning mutation, illegal
transfer, absent damage/reward, event-snapshot forgery, stale initial cache,
unsettled pose, ray endpoints, missing control and terminal-summary binding.
These mutations are synthetic oracle tests; the originals are untouched.

The largest strict gap is the unidentified two-instance leak. Source inspection
shows `m.queue_free()` followed by one `process_frame` before quitting, without
an emitted destruction/audio-drain fence. The real shot path plays audio;
`SBActor._exit_tree` stops shot/hurt/reload players, while actor and weapon/reload
scripts retain shared stream/model caches. These facts support investigating
shutdown ordering and retained shared resources. They do not establish a cause
or leaked class. Procedural model templates are explicitly freed by
`SBWeaponModel.pack_children`, and combat-effect pools are children of the match;
neither is evidence of an orphan in this result.

The original log has no verbose leaked-instance list. Another suite's named
audio leak cannot identify this probe's leaked types. The smallest justified
next measurement is one separately preregistered, fresh staged/private run of
this exact probe with only `--verbose` added to the baseline engine arguments,
the same pinned engine, source/hash, matrix, seed, DT, controls and original
120-second phase / 240-second whole caps. It must retain the original strict
failure, all new streams, exact new controller/command/source identities and
the same scoped cleanup limits. It is a leak diagnostic, not retry acceptance;
its leaked types describe that diagnostic and do not retroactively name the
original objects. Root requested and received method support for that bounded
proposal. I then independently reviewed the concrete root `817516a` controller:
its exact SHA-256 is
`43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe`.
Exactly seven allowed text replacements reconstruct its bytes from the original
controller, all ten non-main helper ASTs are identical, and all 324 game files
in its new clean `b87afb7` source checkout match Git. `verbose_method.json`
records **ACCEPT source/method support for root to release exactly one verbose
diagnostic**. This critic ran no engine and grants no runtime release.

Replay the report's pure audits with `audit_identity.py`, `audit_raw.py`,
`check_package.py` and `falsify_raw.py`; exact commands, outputs and hashes are
retained in `pure_receipts.json`. `identity.json`, `raw_audit.json`,
`package.json` and `falsifiers.json` contain the derived evidence. The earlier
auditor-development failures are retained separately; no fixture failure or
engine warning was suppressed to correct the auditor.

This review read AGENTS/CLAUDE, mission/progress/acceptance, NEXT_SESSION,
PARALLEL_WORK, BARS, both original quality skills and No AI Slop's eval, the
SIGHTBREAK workflow and the source critic. I also applied the Git Workflow and
Versioning skill to the own report branch. Only this independent report
directory changes. No canonical document, product/fixture source, engine,
import, UID, native, OCR, service, export, CI or nested agent runs here.
