# R2 single exhausted-primary baseline attempt

This attempt produced the registered diagnostic rows and mandatory action
witnesses, but **fails the strict cleanup gate**: baseline stderr reports
`WARNING: 2 ObjectDB instances were leaked at exit`. Exit 0 and the fixture's
18,499 reported checks with no failures do not override that warning. The exact
warning is retained; no retry, verbose rerun, threshold change or product edit
followed. Fresh independent actual-output review and root's policy choice are
still required. This is not full match, balance, rendered or release acceptance.

## Source and execution identity

The unchanged source is `b87afb717bf09a78c6d36b164d48906902734bdb`, on
`codex/m5-exhausted-primary-benchmark`, product base
`b2e0293a546961230afbd73e5cd2a1a307d69e94`. R2 source acceptance is
`5fbf3ac6d81a224635f51af0c2eabad06cfdb12f`. The rejected R1 registration
and rejection remain preserved. Probe SHA-256 is
`540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731`.
The pinned Godot 4.7.2 executable was hashed before and after:
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.

The retained `run_once.py` mechanically copied all 324 tracked project files to
a fresh staged project. Its map records each original/staged path, Git blob,
SHA-256 and size. Original manifests inventory all 8,933 index entries, with
SHA-256 values for all 503 files present in the sparse checkout. Absent sparse
files are explicitly marked absent and retain their index blob identity; their
filesystem bytes were not measured. The original manifest is identical after
the run, original HEAD/status stayed frozen/clean, and every original tracked
project file stayed byte-identical after both import and probe.

The preparation generated one new source-side UID in the staged project,
`game/tests/bot_exhausted_primary_probe.gd.uid`, value `uid://v5jkognemvu`,
SHA-256 `fed3c3ead085cc1445615fadb7824b5ccba403e4bbf546508d282388169aa613`.
It is retained only as preparation output in this report. The frozen source
fixture and source checkout were not modified. Added cache artifacts are
enumerated and hashed in `preparation-added-files.json`; full stage manifests
retain before/import/terminal inventory.

The exact controller command was:

```sh
python3 .local/exhausted-primary-r2-single-attempt-20261023/run_once.py
```

Its two native commands, with no additional engine invocation, were:

```sh
/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --headless --editor --path /workspace/sightbreak-exhausted-primary-benchmark/.local/exhausted-primary-r2-single-attempt-20261023/staged-project/game --import
/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 --headless --path /workspace/sightbreak-exhausted-primary-benchmark/.local/exhausted-primary-r2-single-attempt-20261023/staged-project/game --script res://tests/bot_exhausted_primary_probe.gd
```

`SIGHTBREAK_STATE_DIR`, the three Linux XDG homes and `ANDROID_USER_HOME` point
inside this attempt's fresh `private-state` directory; receipts retain each
exact value. HOME and proxy configuration were preserved. No profile, service,
network game, rendered output or exported build was used.

| Phase | UTC start / end | PID and start ticks | Wall time | Exit |
| --- | --- | --- | --- | --- |
| Preparation import | 06:35:38.154746 / 06:35:44.652589 | 34219 / 971492 | 6.498 s | 0 |
| Unchanged baseline | 06:35:44.709890 / 06:36:06.928515 | 34468 / 972148 | 22.219 s | 0 |

Both phases ran on 2026-10-23 under separate 120-second caps and a 240-second
whole wrapper cap, plus bounded five-second phase cleanup. Actual wrapper time
was 30.942 seconds. No timeout or cleanup signal occurred. Each native process
was the sole observed identity in its own PGID/SID. Terminal scans found no
same-session process, observed live identity or recognized Godot process.
These receipts do not prove generic descendant cleanup: a descendant escaping
and reparenting between polling observations can be missed, and the timeout
signal path was not exercised. The ObjectDB warning is an engine object leak,
which an empty OS process scan does not resolve.

## Actual diagnostic output

Raw stdout contains one header; 567 distinct matrix cells; 72 eight-step
sequences / 576 steps; five positive controls / 96 steps; 72 sequence and five
control summaries; and one terminal result. All 1,239 decision/action rows
retain shooter, full enemy and objective phases, commands, resource inputs,
actual query fields, shots, damage and elimination events.

| Mandatory control | Observed output |
| --- | --- |
| `kill_rifle`, 8 steps | One actual shot consumes its one rifle round; 10 actual damage, one elimination, target deaths +1, shooter kills +1, credits 800 → 1100; no draw or reload |
| `reload_smg`, 19 steps | Start step 0, completion step 16; final 30/0 |
| `reload_rifle`, 22 steps | Start step 0, completion step 19; final 30/0 |
| `reload_marksman`, 27 steps | Start step 0, completion step 24; final 8/0 |
| `reload_sidearm`, 20 steps | One fallback/draw at step 0; reload start step 1, completion step 14; final 15/0 |

All four reload controls retain their live target unchanged and emit no shot,
damage or elimination. Every mandatory initial positive lane reports in-bounds
poses, settled mask-1 clearance and stock trace contact with actor 1. No
mandatory control is missing or reported failed. These are actual output
observations pending independent validation, not acceptance of the run's leak.

The 0.96-second behavior sequences preserve current profile and distance rules:

| Setting, across the three primaries | Easy | Normal | Hard |
| --- | --- | --- | --- |
| Exhausted primary, loaded sidearm, visible 24 m target | 0 switches, 24 impossible reload requests, 10 empty fire requests | 0 / 24 / 15 | 0 / 24 / 18 |
| Exhausted primary, loaded sidearm, no target | 0 switches, 24 impossible reload requests, 0 fire requests | Same | Same |
| Exhausted primary, loaded sidearm, visible 6 m target | 0 switches, 24 impossible reload requests, 0 shots | 3 switches, 6 shots | 3 switches, 6 shots |
| Reloadable primary, loaded sidearm, visible 24 m target | 0 switches; reload starts on each primary | Same | Same |
| Exhausted primary, loaded sidearm, 45.5 m target | 0 switches, 24 impossible reload requests, 0 fire requests | Same | 0 switches, 24 impossible reload requests, 18 empty fire requests |

Each aggregate covers three separate eight-step sequences; it is not a match
duration. The 24 m and no-target loaded-sidearm rows confirm bounded repeated
commands that cannot reload or fire the active 0/0 primary despite known
holstered sidearm ammunition. They do not alone determine a replacement rule.
The 45.5 m row is outside the sidearm's defined 45 m trace range; easy/normal
also cannot acquire it under their vision ranges. Root has not chosen whether
or how any range/profile guard should change.

Reserve-only sidearms remain distinct: normal/hard near sequences draw once
and start a legitimate sidearm reload, still in progress at 0.96 seconds;
the longer mandatory sidearm control actually completes it. Unknown sidearm
state stays unknown, and stale active cache entries never replace active
resource fields. The matrix also retains known dry/unowned sidearms, exact
20 m boundary, loaded-primary and carrier/defuser controls. The raw matrix,
not this selected table, contains every outcome.

## Separate pure audits and recoverable evidence

The frozen `witness_oracle.py` exits 0 on the five controls. Its known scope
gaps remain binding: it alone does not bind exact lane poses, whole ammo
conservation, every matrix identity, event snapshots or terminal result.

`audit_actual.py` separately recomputes the raw active/holstered resource maps,
stock ordered action consumption, per-weapon projected conservation including
unknown equip defaults, reload/deploy/cooldown transitions, actor/target/
objective planning equality, real health/death/reward transitions, registered
poses/query endpoints/settlement, matrix identities and sequence aggregates.
It reports 40,058 predicates with no mismatches. This is a builder audit whose
explicit limits are retained in its output; it cannot approve this work and
does not replace the fresh critic. It does not run an engine or infer balance.

For pure replay of the two checker scopes:

```sh
gzip -dc docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz > /tmp/sightbreak-r2-raw-stdout.log
python3 docs/reports/gauntlet/m5-exhausted-primary-benchmark/witness_oracle.py /tmp/sightbreak-r2-raw-stdout.log
python3 docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/audit_actual.py docs/reports/gauntlet/m5-exhausted-primary-benchmark/actual-r2/baseline-probe.stdout.log.gz /workspace/sightbreak-exhausted-primary-benchmark
```

Compressed stdout restores all original 8,558,093 bytes, SHA-256
`e6606c22b5d5cc5c33090a97b1a832e60a376465a0edfa112146b7f743b10d7f`.
Separate original stderr is 131 bytes, SHA-256
`9e2ab4e47a34b3ea04e249930eab8e7920772ac79ef434b2354b5f019068a56b`.
`archive-map.json` binds each compressed archive to its original byte count and
SHA-256. `artifacts.sha256.json` inventories retained report files. The exact
controller, stdout/stderr, process receipts, source/stage manifests, generated
UID and both audit outputs are retained here. Uncompressed originals and the
staged project/private state remain in the ignored local attempt directory.

The strict leak failure, stationary action-only design, injected visibility,
unlogged intermediate planning event counters and unexercised timeout cleanup
path remain limitations. No production selection policy has been edited.
