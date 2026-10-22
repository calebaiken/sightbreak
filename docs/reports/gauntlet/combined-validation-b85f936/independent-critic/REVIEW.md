# Independent combined integration validation review

Accept the maintained aggregate **as run at `b85f93600e122b36e8dcd70edd9bc168e9820b08`**.
The complete unmodified retry reaches its original completion marker with no
failing required step. This is bounded integration regression evidence. Every
release-candidate gate remains open unless its separate acceptance evidence says
otherwise.

Reviewer: `/root/combined_validation_critic`, with a separate read-only
`validation_gate_map` source auditor. I read AGENTS, mission/progress/acceptance,
NEXT_SESSION, contributor contracts, the original gauntlet-loop and No AI Slop
skills and eval, project gauntlet, and the accepted authority, activity, bot,
account, LEAVE and touch component reports. I inspected the actual aggregate
output and original child logs. I launched no Godot, rendering, OCR, backend or
native input workload. This is an identified source/evidence review; a blind
visual comparison is inapplicable.

## Exact source and execution

The historical checkout directory is `/workspace/sightbreak-validate-a23e349`.
Its retry HEAD is **b85f936**, not a23e349. The command is `./scripts/validate.sh`
without `--backend`, with no DISPLAY or test-timeout override and with
`SIGHTBREAK_BACKEND_PYTHON=/workspace/sightbreak/.venv/bin/python`.
I inspected that command and selected environment entries directly from the
running aggregate processes before completion. The selected interpreter was
used for the real catalog serializer check.

The externally captured source-before and source-after JSON are identical:

| Identity | Value |
| --- | --- |
| Commit | `b85f93600e122b36e8dcd70edd9bc168e9820b08` |
| Game tree | `e877ba16bdc7f63994930a77f32e484e8f12d890` |
| Shipping content SHA-256 | `db3c976711ef8d91b75604fdfe05309599445cfc5bdf59e5f6fbdf669a859fc5` |
| Validation SHA-256 | `0fd96995226efdf47fb351860eedda3a8ca1b0086b3ef291a5e99f640766abc3` |
| Whole-source / game dirty flags | Both false before and after |
| Executed validate.sh SHA-256 | `97a04cb5c12fa8e2c2e9ef35a6b4ce71d6476db9c0743f163f2e0a537dc08c98` |

The executed validation script matches its committed Git bytes. All 52
unconditional Godot invocations have their original, nonempty per-command logs
under `.local/validation/run-utj57N`. Each follows the unchanged timeout,
pipefail and engine-error enforcement. I inspected every summary, the full
aggregate and the native ENet child logs; no `SCRIPT ERROR`, `ERROR:`, parse
error, traceback or failed unittest summary appears. Expected protocol rejection
messages in negative controls remain visible and are not execution failures.

`audit.json` records every Godot command, source line, original-log hash and
summary. The six non-Godot test summaries occur in the original script order:

| Required command | Actual result |
| --- | --- |
| `python3 -m unittest discover -s server/tests -v` | 11 tests pass |
| `python3 scripts/test_account_network_output.py` | 4 synthetic validator controls pass |
| `python3 scripts/test_account_match_output.py` | 15 synthetic validator controls pass |
| `python3 scripts/test_reload_contact.py` | 24 checks pass against the committed CSV and actual GLB hash |
| `./scripts/test_network.sh` | Both real ENet clients report movement, snapshots, reconnect and authoritative hit/impact success |
| `python3 scripts/test_connection_lifecycle.py --out ...` | Silent, joined-idle and rejection scenarios pass; each server finishes with zero peer entries |
| Backend Python `scripts/export_catalog_fixture.py --check` | Actual backend serializers match the committed fixture, 29 definitions |
| `python3 scripts/test_build_manifest.py` | 24 tests pass |
| `python3 scripts/test_native_observation.py -v` | 4 pass, 3 native-Windows-only tests skip |
| `python3 scripts/test_offline_export_ocr.py -v` | 5 exact-caption controls pass |

The integrated corrections are reached rather than inferred from older component
counts: phased authority passes 178 assertions; consumed-command activity passes
32; bot symmetry covers all 960 samples with 2,722 assertions and zero failures;
the revised touch/input-mode suite passes 462. The stock bot lifecycle completes
ten rounds, 7:3, with 60 kills, halftime, an observed plant and one result report
over 325.9 simulated seconds. Layout/UX and overflow suites also complete. These
observations establish their declared source-runtime regressions, not bot quality,
player experience or hardware performance.

The real Dummy-driver reload, cancellation and simultaneous shot/seat captures
all pass. They measure mixer output; no human listening result follows. The
network smoke's server is intentionally terminated with wait status 143 during
its cleanup, while the aggregate proceeds successfully. The lifecycle logs
contain actual successful JSON observations for all six processes. A subsequent
read-only `/proc` inspection finds none of the observed aggregate process IDs
and no Godot process for the frozen game path; `process-after.json` retains it.

## Retained failure and restored fixture

The original a23e349 attempt remains **failed, exit 1** under
`docs/reports/gauntlet/combined-validation-a23e349/attempt-1`.
I checked its archive SHA-256 and every one of its 57 manifest entries against
the archived bytes. Its raw output retains the missing adjacent GLB stamp and
FileNotFoundError for `clip_contact.csv`; the later network/catalog/build and
observation tail was unreached. Its matching clean source receipts do not turn
that run into a pass.

The retry restores tracked evidence rather than substituting a new oracle.
I compared actual CSV, adjacent stamp, contact validator and shipped arms GLB
bytes directly with Git b85f936. All agree; the stamp binds the CSV to GLB
SHA-256 `7c5fedb29d6dade6170493a6db0fd82b3c7343a1d92e83247ac8be9a2bf056fe`.
The original contact constraints and 61-frame expectation remain enforced.
This complete retry reports 24/0 and establishes that the remaining aggregate
commands also ran.

The source helper hashes shipping game content and validation tooling, but it
does not hash backend/server or the report CSV. Sparse omissions can also be
invisible to Git dirty status. I therefore additionally verified every actual
tracked backend/server file against b85f936 and retained those hashes alongside
the explicit fixture hashes in `audit.json`.

## Skips and source boundaries

Five rendered gates are skipped because DISPLAY is absent: reload visibility,
sunlit finish, shaded finish, viewmodel lighting and skin finish. The script
prints one shared `reload-visibility skipped` message for that entire block.
This retry supplies no new pixel or renderer result for any of those five.

The optional `--backend` branch does not run: database pytest, actual admission
capacity, result-outbox recovery, native economy and backend simulation remain
outside this aggregate. The supplied backend interpreter qualifies catalog
serialization without connecting SQL. The three Windows reader skips are
expected on this Linux host and remain skips.

Build-manifest, observation-reader and exact-caption controls exercise helpers;
they do not export a package or run an ordinary native journey. The aggregate
also contains no impaired-network campaign, full ten-account match, four-size
native layout capture, Mac input execution, physical-device test or human play.
Their independent reports retain their own earlier source identities and limits.

At comparison checkpoint `3b97a00`, the complete game, backend and server Git
trees still equal b85f936. The validation identity has changed: four Mac adapter,
capture, journey and verification files were added, and desktop-alpha.yml was
modified. `audit.json` records those exact tree IDs and paths. This b85f936 pass
cannot be relabeled as validation of 3b97a00 or any later whole HEAD. Accepted
component source reviews and blind touch stills remain separate evidence.

## Largest remaining deficiency

The current integrated gameplay has no real ten-account/backend match after the
consumed-command activity authority correction. The earlier actual settled match
is source 471fbd8. Passing synthetic output validators, a two-client smoke and
short activity fixtures cannot refresh the full match-to-earned-settlement path
on b85f936. A fresh source-bound real match and recovery observation is the
largest remaining integration evidence gap. It must preserve ordinary authority,
the existing activity policy and exact reward/SQL checks; participation quality
and AFK resistance remain separate unresolved product questions.

No release gate, 8.5/10 score, CS2 parity, physical-device performance or human
acceptance is claimed here. The original component limitations, including
multiattacker attribution, representative bot cooperation and native platform
journey failures, remain open.

## Evidence and replay

`raw-logs.tar.gz` retains 67 original files: complete retry stdout/source/exit
receipts, all per-command logs, six lifecycle child logs and four smoke logs.
`MANIFEST.json` and `archive-sha256.txt` bind every archived byte. Runtime state
directories and old large media archives are not duplicated.

Recreate the audit and archive from the preserved frozen checkout without
starting runtime workloads:

```sh
python3 docs/reports/gauntlet/combined-validation-b85f936/independent-critic/audit_evidence.py \
  --frozen /workspace/sightbreak-validate-a23e349 \
  --repository /workspace/sightbreak-v1-execution \
  --comparison-ref 3b97a00 \
  --output /tmp/sightbreak-combined-b85-review
```

The writing was checked against the installed No AI Slop eval. This review adds
source binding, command coverage, explicit skips and retained failure evidence;
it changes no product or canonical mission file.
