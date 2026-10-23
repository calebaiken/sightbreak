# Independent b09cfe1 aggregate review

Accept the complete maintained Linux aggregate at exact source
`b09cfe1b661ec153f2bd57d45e695cc70e9717b0`. The original command reaches every
required step and its completion marker, with matching clean source receipts.
This closes the requested combined regression check for that source and
configuration. The same-source macOS source-suite failure remains FAILED.
No whole release gate is promoted.

Reviewer: `/root/combined_validation_critic`, independently of the builder and
coordinator. I reused the installed original Gauntlet Loop, No AI Slop and project
gauntlet instructions, read the current mission/acceptance/resume records and
relevant accepted component reports, then inspected the actual logs and source.
A requested read-only helper follow-up was unavailable because of the agent
thread limit; this audit was completed directly. No Godot, native input, OCR,
rendering, backend or database workload was started. A blind visual comparison
does not apply to this source/output audit.

## Source and execution binding

Original checkout: `/workspace/sightbreak-validate-b09cfe1`.
Original outputs: `builds/combined-validation` and
`.local/validation/run-3uEIWG`.

`command.json` and `result.json` retain `./scripts/validate.sh` without
`--backend`, the checkout path, no DISPLAY, backend interpreter
`/workspace/sightbreak/.venv/bin/python`, and tools directory `/workspace/tools`.
The command starts at 06:21:19.038145 UTC and its receipt completes at
06:29:04.184582 UTC on 2026-10-22. It records exit 0 and 465.033044934 seconds;
this is execution evidence, without a performance comparison.

Before and after source JSON are identical:

| Field | Exact value |
| --- | --- |
| Commit | `b09cfe1b661ec153f2bd57d45e695cc70e9717b0` |
| Game tree | `fb6be859e05812d8707be1ef5c6f747d2588c1e9` |
| Shipping content SHA-256 | `f148106d4ed189f2a5d49e798f55bf0fb30f612126ec203037377f88d332855e` |
| Validation SHA-256 | `8b5b1d9c202f237afa1e38d5186f56459f729b4e43cac49bc4dc56fadea4c845` |
| Whole-source / game dirty flags | Both false before and after |
| Executable engine SHA-256 | `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e` |

I rehashed the actual pinned engine file and matched its hash to both receipts.
Every engine log identifies Godot 4.7.2. The executed validation script matches
its committed Git bytes. The additional report CSV/stamp, shipped arms GLB and
every tracked backend/server file also match b09cfe1 directly; their hashes are
retained in `audit.json`. This supplements the source helper, whose content and
validation digests do not include those backend/server/report files. The
restored contact fixture is present and remains bound to the actual shipped GLB.

The comparison checkpoint `b72baddc12bf538b8b38c6728d32ec6ab550e6e5` has identical
game, backend, server, scripts and workflow trees. The exact tree IDs are in
`audit.json`. That equality preserves the shipping-content relationship; this
run remains source b09cfe1 and is not relabeled as a later whole HEAD. Later
observer revisions require their own focused evidence and source identities.

## Required commands and actual observations

All 52 unconditional `run_godot` commands have original nonempty logs. I inspected
their summaries and checked the complete Linux stdout, each per-command log,
both smoke-client logs and all six lifecycle logs for error/leak signatures.
No engine error, parse error, traceback, failed unittest summary, ObjectDB leak,
leaked-instance or warning line occurs in those Linux logs. Expected protocol
rejection messages in negative controls remain visible.

The unchanged aggregate enforces timeout, pipefail and engine-error checks.
Its built-in error matcher does not include the native runner's ObjectDB leak
predicate. The no-leak observation here comes from independent inspection of
the original Linux bytes, rather than exit status alone.

| Required command or scope | Original observed result |
| --- | --- |
| Game, authority, privacy, input and recovery source suites | Every required log reached; all assertion summaries pass |
| Consumed-command activity / bot symmetry | 32/0 and 2,722/0 over all 960 bot samples |
| Input mode / landscape / UX / overflow | 462/0, 9,217/0, 2,227/0 and 2,435/0 |
| Objective HUD fixture | 1,535/0; complete 1,458-sample desktop/touch flood set, zero wrong role frames |
| Stock bot lifecycle | Ten rounds, 7:3, 60 kills, halftime, observed plant, one result report, 325.9 simulated seconds |
| Server unittest discovery | 11 pass |
| Account network / match output controls | 4 pass / 15 pass; synthetic validator evidence |
| Reload sequence / audio source / contact | 92/0, 29/0 and 24/0 |
| Real-time Dummy audio capture | Reload 14/0, cancellation 11/0, simultaneous shot/seat 15/0 |
| Two-client real ENet smoke | Both clients report movement, snapshots, reconnect and authoritative hit/impact success |
| Real ENet lifecycle | Silent, joined-idle and rejection clients all report `ok:true`; all three servers end with zero peer entries |
| Actual backend serializer catalog check | Committed fixture matches all 29 definitions |
| Build-manifest controls | 24 pass |
| Observation-reader controls | 4 pass; 3 native-Windows-only skips |
| Planted-guidance context controls | 4 pass |
| Exact OCR-caption controls | 5 pass |

The seven Python unittest groups occur in the declared source order, with counts
11, 4, 15, 24, 7, 4 and 5. `audit.json` records the entire Godot command ledger,
source lines, original-log hashes and summaries. The audit checks the objective
fixture's complete Cartesian set of two input modes, three roles, three
operational connection states and 81 time samples. Every recorded actual role
matches the independently specified attacker/defender/spectator text, including
E versus USE. All fixture game ticks remain zero. These measurements cover
source HUD selection.

The HUD fixture's original cleanup JSON reports exit 0, original exit 0, owned
namespace removal and original user-directory restoration; its temporary native
directory is absent. Smoke cleanup intentionally terminates its owned server
with wait status 143. The original smoke cleanup PID is absent on independent
post-run inspection, and no Godot process for this frozen game path remains.
Each lifecycle process exits through its original successful observation.
`process-after.json` records the bounded read-only process check. This does not
claim hard-kill safety or removal of retained evidence/state directories.

Relative to b85f936, the maintained script adds the four planted-guidance
context controls. The existing objective HUD step now executes the expanded
1,535-check fixture. The exact script diff is retained in `audit.json`. This
aggregate supplies the final combined source regression evidence requested by
the accepted post-plant correction. Its original exported next-round deadline
failures and unreached restart remain failed in their separate native report.

## Same-source macOS failure remains

I opened the retained original macOS run 39732825169 source receipt, regression
result list, isolation receipt and input-mode log. Their committed bytes match
the native review archive, and their source fields equal this aggregate's exact
b09cfe1 identities. The native run executes only seven of its twelve declared
suites. Its input-mode suite reports 462 checks and zero assertion failures,
then prints:

> WARNING: 2 ObjectDB instances were leaked at exit (run with `--verbose` for details).

That process exits 0, but `clean_log` is false and the strict native gate rejects
the suite. Menu focus, offline diagnostics, objective HUD, activity provenance
and bot squad symmetry are unreached on that Mac run. The native isolation
receipt remains `passed:false`. Linux completing those steps supplies no Mac
execution evidence and does not clear the native failure.

No verbose instance types or ownership evidence are available. Cause remains
unknown; the different logs do not isolate an OS, runner, resource, cache or
fixture cause. The Mac menu-recognition journey also retains its separate FAILED
result. This audit accepts neither a platform fix nor a new native qualification.

## Skipped and unsupported gates

No DISPLAY means five rendered tests do not run: reload visibility, sunlit
finish, shaded finish, viewmodel lighting and skin finish. The single shared
skip message represents that whole block. No rendered result follows from the
headless render-budget or presentation source tests.

The optional `--backend` branch is outside this command: database pytest,
admission capacity, result-outbox recovery, native economy and backend simulation
are unrun here. Catalog serialization opens no database. Synthetic account-output
controls do not establish a new ten-account match or post-replay SQL witness;
the separately blocked account trial and reviewed observer retry retain their
own status and source bindings.

Three Windows reader tests remain skips. Helper controls do not constitute a
real export, ordinary native gameplay, four-size layout capture, impaired-network
campaign, physical-device measurement or human play/listening. Dummy-driver
captures inspect mixer samples, not human audio judgment.
The Mac focus/menu controls are outside this maintained aggregate and are not
re-attested here.

The largest remaining cross-platform deficiency is the same-source Mac leak
rejection with five native suites unreached. A Linux aggregate pass cannot close
that observed failure. Full plant-journey next-round/restart and independently
witnessed post-replay account settlement also remain open in their own gates.
No 8.5/10 score, CS2 parity or whole release acceptance is claimed.

## Retained originals and replay

`raw-logs.tar.gz` contains 68 original Linux aggregate files and four explicitly
separate same-source Mac context files. `MANIFEST.json` identifies each origin,
original path, byte count and SHA-256. `archive-sha256.txt` binds the archive.
The prior b85 pass and failed a23e349 sparse-fixture attempt remain retained in
their existing directories; this report overwrites neither.

Recreate this audit without starting runtime workloads:

```sh
python3 docs/reports/gauntlet/combined-validation-b09cfe1/independent-critic/audit_evidence.py \
  --frozen /workspace/sightbreak-validate-b09cfe1 \
  --repository /workspace/sightbreak-v1-execution \
  --comparison-ref b72badd \
  --output /tmp/sightbreak-b09-independent-audit
```

The report was checked against the installed No AI Slop eval. This commit changes
only independent evidence under its own report directory; frozen source and
canonical mission files are untouched.
