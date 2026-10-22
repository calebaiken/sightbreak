# Independent integrated Linux validation review

**ACCEPT the maintained Linux aggregate and the separate strict private two-suite
check at `05277154c6b8c92b80fd7c25e8365de9efdc4fae`.** The original aggregate
reaches all 54 mandatory Godot commands, nine Python unittest groups and the
completion marker, then exits zero. Source stays clean and identical. This
accepts the declared combined regression scope; whole release gates stay open.

Reviewer: `/root/final_combined_validation_critic`, separate from the builders
and coordinator. Preregistration commit `53119a0682cb4710df927b1d4b519fed5f8e6386`
is dated 07:30:13 UTC, before the actual driver starts at 07:33:12 UTC. I reused
the installed original Gauntlet Loop, No AI Slop and project gauntlet, read the
mission and accepted component reports, then audited original files and source.
I launched no Godot, renderer, OCR, native input, server, database or CI workload.
A blind visual comparison does not apply to this source and output audit.

## Exact source and actual commands

Frozen checkout: `/workspace/sightbreak-validate-0527715`, branch
`codex/validation-0527715`. Original sequential output:
`builds/final-validation-0527715`. Original maintained logs:
`.local/validation/run-at7Rc5`.

| Identity | Exact value |
| --- | --- |
| Commit | `05277154c6b8c92b80fd7c25e8365de9efdc4fae` |
| Game tree | `1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48` |
| Shipping content SHA-256 | `6bebcf50351c29d4c9959bfe4b33418f8f7b4a2e963e65336f361e99891f07b5` |
| Validation SHA-256 | `c126856c6e596c067783e51fa5e6cd3190d04f92a3bf3f6295733454c9543228` |
| Executed validate.sh SHA-256 | `896601b49bb48cef0487d161d9ef1338448afcd5e0e37cdded59bf6fbb62fc93` |
| Actual engine SHA-256 | `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` |

The driver runs these commands sequentially, with DISPLAY and an inherited state
override removed, tools `/workspace/tools`, and catalog interpreter
`/workspace/sightbreak/.venv/bin/python`:

1. `python3 scripts/run_native_regressions.py --output <original-output>/native-two-suites --suites transaction_journal gunplay_rules`.
   Actual exit 0, 13.002677813 seconds, 07:33:12.582238–07:33:25.584904 UTC.
2. `./scripts/validate.sh`. Actual exit 0, 469.486058706 seconds,
   07:33:25.642421–07:41:15.128478 UTC. No `--backend` or DISPLAY is supplied.

The archived wrapper equals `/workspace/sightbreak-final-validation-driver.py`.
Each original command/result agrees on argv, cwd, process/group identity and
start time; each result binds the unchanged source. The final driver receipt
reports success at 07:41:15.256995 UTC. Durations describe these executions and
support no performance comparison.

I independently recomputed both source digests and checked 430 actual files
against their frozen Git blob bytes: 319 game, 16 backend, three server,
85 scripts, four workflow and three hands/log fixtures. All 341 launch-input
hashes also agree afterward. Both contact CSVs and the stamp are present; the
stamp matches the actual shipped arms GLB. The engine executable matches its
receipt, the installed archive matches the pinned toolchain SHA512, and the
archive contains those executable bytes. All mandatory engine logs identify
`4.7.2.stable.official.ed1daf0bf`.

## Maintained aggregate observations

The audit derives the command ledger from the frozen script. All 54 mandatory
Godot logs are nonempty. The five DISPLAY-only logs are absent as declared.
The actual log inventory contains exactly those 54 files plus reload contact;
all six lifecycle logs and four smoke logs are retained. The audit scans complete
original stdout, every required log and private native/user log for runtime,
parse, traceback, failed-summary, warning, leaked-instance, ObjectDB and
resources-still-in-use predicates. None occurs. Expected protocol rejection and
fixture account-submission diagnostics remain visible.

| Scope | Original observation |
| --- | --- |
| Mandatory Godot commands | All 54 reached, including the new journal and M4 registrations |
| Journal / gunplay | 41/41; 2,840 checks with zero failures and all 52 unique weapon/case keys |
| Activity / bot symmetry | 32/0; 2,722/0 over 960 samples |
| Input / landscape / UX / overflow | 462/0; 9,217/0; 2,227/0; 2,435/0 |
| Objective HUD | 1,535/0; all 1,458 context samples, zero wrong role frames |
| Armory / recovery / menu state | 748 checks; 12 assertions; 51 checks, all pass |
| Stock bot lifecycle | Ten rounds, 7:3, 60 kills, halftime, observed plant, one result report |
| Reload sequence / audio source / contact | 92/0; 29/0; 24/0 |
| Dummy mixer captures | Reload 14/0, cancellation 11/0, shot/seat 15/0 |
| Actual ENet smoke | Both clients report movement, snapshots, reconnect and authoritative hit/impact success |
| Lifecycle | Silent, joined-idle and rejected clients report `ok:true`; all three servers finish with zero peer entries |
| Backend catalog serializer | Actual check matches all 29 committed definitions |

The nine Python unittest groups appear in source order with actual counts
`11, 7, 4, 15, 24, 7, 4, 5, 15`: server discovery, receipt oracle, account network,
account match, build manifests, observation reader, role guidance, OCR captions
and capture fences. These are 92 methods, including three explicit Windows-only
reader skips. The new receipt oracle has seven methods; the capture-fence group
also adds coverage relative to b09. Their helper/fixture results do not establish
new account settlement or actual captured pixels.

The independent HUD audit reconstructs the complete two-mode × three-role ×
three-connection × 81-sample set, checks actual role text including E/USE, and
checks zero game ticks. Its original cleanup receipt records successful owned
namespace removal and original directory restoration; the native directory is
absent afterward. The short bot observation's `planted=false` remains in its
original log; it does not negate or replace the separate lifecycle observation.

## Strict private selection and cleanup

The original native default had twelve suites. The frozen source appends
`transaction_journal` and `gunplay_rules` as suites 13 and 14, preserves the
original twelve in order, and maps gunplay to the Dummy-audio probe. **This run
selects only those two added suites.** It does not execute or qualify all
fourteen defaults, nor any Mac source gate.

The selected strict outputs pass journal 41/41 and gunplay 2,840/0 with 52 records.
Original 120-second per-suite and 30-second producer budgets remain. All five
engine-produced directory receipts identify the same private project and unique
namespace, with distinct bootstrap/journal/gunplay children and no preexisting
profile or diagnostics. The original and independently rehashed 319 game resource
hashes agree. The runner checks unchanged copied resources before removing the
temporary project; retained produced user files match their recorded hashes.
Separate copied-resource post-run inventory bytes are not retained, so that
comparison is supported by the inspected runner and original finalization receipt.

The actual child PID 128902 reports claim, clear and stage each blocked with 22,
and unchanged receipt bytes. Selected process group 128618 has no members after
completion. Its temporary project `/tmp/sightbreak-native-tests-9stg53ai/project`
and namespace `SIGHTBREAK-native-tests-da692e20aeb04f20967f4e238a9e809e` are absent.

Independent `/proc` inspection also finds aggregate group 128986 empty and the
recorded driver, smoke-cleanup and native-child PIDs absent. No Godot process
matches either actual project path. All eight source/readiness-bound server
ports are absent: 27991, 29900–29902 and 33540–33543. Native journal guard ports
are not printed by these suites; their owning process group is gone. Smoke
cleanup records owned server TERM/wait status 143, with no SIGKILL escalation.
Lifecycle servers finish through their own successful cleanup observations.
No unrelated process was signaled by the critic. Retained evidence and ordinary
test-state/cache directories are outside the owned namespace-removal claim.

## Preserved failures and remaining gaps

The older complete aggregate remains source **b09cfe1**, 465.033 seconds and
52 mandatory Godot logs; it is not relabeled as this source. Its separate Mac
run reaches seven of the original twelve suites, then rejects input mode despite
462 successful assertions because two ObjectDB instances leak. Later accepted
mission records also retain the separate actor-first Mac rejection with eleven
suites unreached. No Mac execution or fix follows from this Linux result.
The failed a23e349 sparse-fixture aggregate and its original exit-1 archive remain
in their existing report. This new run has no failed native attempt to omit.

The largest remaining observed platform gap is the strict Mac leak rejection
and incomplete native source coverage. The Linux next-round deadline failure
also remains open at its own measured source. For B-21, the largest product
boundary is ordinary player-driven receipt recovery with actual input/pixels
against the production backend. The accepted 12/12 crash-fixture campaign remains
bound to `79e076e`; this aggregate does not repeat that campaign or create a new
PostgreSQL lost-response settlement witness.

No DISPLAY leaves reload visibility, sunlit finish, shaded finish, viewmodel
lighting and skin finish unexecuted. The optional backend branch (database tests,
admission, outbox, native economy and backend simulation) is unrun. Three Windows
reader cases skip. No exported gameplay, impaired remote match, human play,
listening, physical latency/device performance, CS2 parity, Steam or whole
G1–G20 release acceptance is claimed. Dummy mixer samples and headless source
presentation checks retain their engineering scope.

## Originals and replay

`raw-logs.tar.gz` retains 100 originals / 3,364,950 uncompressed bytes: 68 aggregate,
24 strict selected-native and eight shared driver/source files. It includes every
file under the original sequential output directory, required aggregate/lifecycle
logs and original smoke logs. Generated aggregate state/cache directories outside
that raw-log selection remain at their original paths. `MANIFEST.json` records
origin, original path, size and SHA256 for every member. Every archived member was
reopened and matched to that manifest. The archive SHA256 is
`efa75f0618806e8a74260ced7ac2c9ba89d76713b80d95c413f51d4a4333da2c`.

`audit.json` records 2,129 independent passing predicates, the complete command
ledger, raw summaries, all source hashes and original native receipts.
`process-after.json` records the independent live cleanup observation. The
precompletion private-only audit is retained separately. No failed audit or
runtime result was overwritten.

Re-run this file/source audit without launching runtime workloads:

```sh
python3 docs/reports/gauntlet/final-combined-validation/independent-critic/audit_evidence.py \
  --frozen /workspace/sightbreak-validate-0527715 \
  --run /workspace/sightbreak-validate-0527715/builds/final-validation-0527715 \
  --expected-source 05277154c6b8c92b80fd7c25e8365de9efdc4fae \
  --driver /workspace/sightbreak-final-validation-driver.py \
  --output /tmp/sightbreak-final-independent-audit
```

The report passed the installed No AI Slop eval. This review changes only its
own evidence directory; the frozen source, root branch and canonical mission
records are untouched.
