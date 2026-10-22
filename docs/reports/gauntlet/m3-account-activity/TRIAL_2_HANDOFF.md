# Corrected-activity account match: second trial

Status: **harness PASS / strict independent bounded PASS**. A new stock match on
the corrected integrated product created its own earned result and recovered it
exactly once. The reviewed v2 observer retained genuine pre-ACK and post-replay
SQL, and issued a separate successful read-only query initiated after replay.
The first trial remains unchanged as harness PASS / independent BLOCKED.

Fresh independent bounded acceptance is committed as `255074a`; see
[TRIAL_2_REVIEW.md](../m3-account-activity-qualification/independent-review/TRIAL_2_REVIEW.md)
for the actual SQL/time/source/process/cleanup joins and strict v2 recomputation.

## Exact source, new resources and scope

Root authorized clean source `3b5cf7640e256dff404b401bf2b27ffaff157bdd`, game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`. New sparse worktree:
`/workspace/sightbreak-account-activity-r2`; branch:
`codex/m3-account-activity-second-trial`. It was created directly at that exact
commit, without cherry-pick relabeling. Fresh independent before/after records
confirm unchanged clean source, engine and contracts. All 15 pure controls and
initial pinned-engine import passed before runtime.

The existing final account harness/probe/validators and product code were
unchanged. All ten fictional HTTP accounts/tickets, container, API/ports, spool,
output and payload were new. Independent actual SQL verified the identities were
disjoint from the first trial and wallets/rewards/ledger started at zero. Neither
prior payload was used. No authority, timer, score, timestamp, roster, activity,
eligibility, reward threshold or wallet was injected or modified.

This trial follows the integrated consumed-command activity correction; the
earlier `471fbd8` account evidence predates that correction. Nine clients still
deliberately turn at spawn under the allowed unchanged look-activity policy.
This does not qualify substantive participation or resistance to AFK farming.

## Execution and observed result

```sh
cd /workspace/sightbreak-account-activity-r2
SIGHTBREAK_TOOLS_DIR=/workspace/tools SIGHTBREAK_STATE_DIR="$PWD/builds/import-state" \
  ./scripts/godot.sh --headless --editor --import --quit
/workspace/sightbreak/.venv/bin/python scripts/test_account_match.py \
  --out builds/account-activity-stock-2 --timeout 1200
```

The v2 critic was ARMED before import/runtime. UTC:
`2026-10-22T06:38:57.317822+00:00` to
`2026-10-22T06:47:39.310979+00:00`; 521.837095 measured wall seconds, exit 0.
Driver PID `108257` executed the unchanged orchestrator. Native Godot version
`4.7.2.stable.official.ed1daf0bf`, binary SHA256:
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.

| Observation | Fresh actual result |
| --- | --- |
| Admission | Ten new HTTP identities, consumed scoped tickets, authenticated names and actors 1–10 retained |
| Match | Six ordinary plant/detonation wins; automatic 6:0 → halftime 0:6 → final 0:7 after the seventh stock defended timeout |
| Stock rules | Buy 15s, live round 100s, plant 3s, defuse 5s, device 35s, seven wins; protocol 6, ranked policy and formulas unchanged |
| Terminal duration | 499.666667 ranked simulation seconds; payload timestamps span 500 wall seconds |
| Activity/objectives | Ten participants each record 499 active seconds; actor 1 earned six objectives; first five original identities won |
| Combat | Zero kills, deaths and assists; scripted no-combat scope |
| Before delivery | Actual independent ten-account zero-wallet baseline; no ledger, rewards or match operations |
| Production recovery | Earned Godot spool handoff/SIGKILL; real owned-DB outage/pending SQLite HTTP 500; worker SIGKILL; backend commit with held ACK; lost worker killed; exact restart and duplicate source replay |
| Economy after recovery | One match operation, ten rewards and ten ledger rows; 2,875 credits / 2,650 XP; unchanged config, SQL wallets/rewards/ledger and authenticated HTTP profiles/history agree |
| Harness/replay | All seven harness checks and both unchanged pure raw validators pass |

Fresh match UUID: `a209820c-31d7-4903-9fbe-ae72ddab9434`.
Earned payload SHA256:
`12d6dd70a601297bd57b7b3c236c783e2a6681eddf03e0731e394d40c97dff58`.
These actual values were recomputed from this new match and identities. Equal
totals in earlier matches were not assumed or reused.

## Strict independent live SQL and provenance

Root reviewed the observer-retention correction and its 16 pure controls before
this retry. Observer SHA prefix `d1ec8562`, oracle SHA prefix `09599411`; actual
before/after tool hashes were rechecked by the fresh critic. The observer retains
every recovery row, defers incomplete checkpoints and performs a distinct final
SQL query after replay. A seen-checkpoint tag alone cannot satisfy acceptance.

The fresh critic's strict v2 recomputation and source/process/socket/SQL/cleanup
join passed. All times below are actual UTC on 2026-10-22:

| Required witness | Actual order |
| --- | --- |
| Committed SQL before ACK release | First committed SQL `06:47:37.836219` precedes lost-worker-killed checkpoint `06:47:37.858313` |
| Retained actual SQL after replay | Recovery stream extends through `06:47:38.979303`, later than duplicate replay `06:47:38.139812` |
| Separate query initiated after replay | Requested `06:47:38.142011`, actual SQL `06:47:38.240910`, same operation/rewards/ledger/wallets |
| Source/native/provenance | Exact clean source/engine/contracts before and after; eleven new native children and actual sockets independently checked |
| Cleanup | Actual builder/observer PID list absent, exact container absent, API/DB/game ports released |

The missed first-trial SQL sample remains preserved with independent rejection
`313278a`. Its 0.597ms failure was not relaxed, inferred away or relabeled. This
second trial used new resources and actual observations to meet the same boundary.

## Ownership, cleanup and remaining limits

Owned container: `sightbreak-account-match-f1672c68d71a`, pinned cached PostgreSQL17
image and ephemeral data, with no shared database mutation. API:
`127.0.0.1:36727`; PostgreSQL: `127.0.0.1:32770`; inherited wildcard IPv6 game UDP:
port `40937`. Client traffic was loopback. No saved development key or process
credential was read, printed or committed. Independent SQL used credential-free
read-only psql on only the exact owned container.

All 17 builder children were reaped and the owned container removed. The fresh
critic independently checked the full 32-child builder/observer list, actual ports
and container absence; its observer exited 0. Exact source-after was captured
before tracked archive work. The exclusive native/CPU lane was explicitly released
to root. No match, native process, API or container remains running for this trial.

This bounded pass does not close G3/G16 or prove AFK resistance, substantive
participation, combat fairness, prediction feel, impairment, remote hosts,
production deployment, power-loss/storage guarantees or human play. The inherited
wildcard game listener is explicit. No product feature or canonical mission file
changed in this branch. The two actual local full-plant journeys still failed
their unchanged 12-second next-round wait; this account match does not erase them.
Root's full aggregate result is a separate source-bound receipt, not relabeled here.

## Evidence and handoff

[round-2/sha256.txt](round-2/sha256.txt) indexes unmodified fresh native logs,
client/latest/completion reports, earned payload, SQLite/transient checkpoints,
preflight/import/15-control receipts, driver identity, physical cleanup and pure
replay. The separate bounded verdict leaves the original raw harness report intact.
First-trial HANDOFF/round-1 files remain unchanged. Root owns canonical mission
updates and the next supported milestone; integrate only with the separate fresh
independent verdict. No background work is promised.
