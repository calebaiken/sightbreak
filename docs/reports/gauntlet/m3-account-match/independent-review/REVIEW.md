# Independent account-match review

Execution source: `471fbd8fe17611c0c93728bc571ea6158838b458`.
Product reference: `0ca125dfba637868e6e8e9772ff9c40400413e32`, reached through
integrated base `2a2b732`. The source and engine review uses the already installed
project gauntlet and No AI Slop instructions. No skills were reinstalled.

## Verdict

Accept the bounded stock-match and process-crash result-delivery scenario at
`471fbd8`. Independent raw-output recomputation passes, including a separate
read-only PostgreSQL observation before cleanup. The candidate provides stronger
evidence than the inspected admission/simulation/injected-result fixtures because
one continuous production match creates the actual immutable result subsequently
recovered by the worker. No release gate is promoted by this review.

## Observed result

The run began at `2026-10-22T04:29:01.633582Z` and finished at
`04:37:47.751563Z`. The terminal match lasted 499.65 simulation seconds and the
payload's real UTC interval was 500 seconds. The later completed-server sample
reports 500.617 seconds because its ordinary elapsed clock continues after
match-over; the independent calculation recovers the actual terminal duration
from the server's emitted result summary.

Ten distinct HTTP accounts consumed ten scoped tickets. All ten retained their
authenticated display name and actor, observed every buy/live round, received
the completed summary and queued-delivery status, and switched sides at halftime.
Each payload participant has 499 activity seconds, or 99.8% of the real UTC
interval. Each client accepted 10,008–10,236 snapshots. No Godot error or exit-leak
marker appears in any of the eleven engine logs.

The score progressed 0:0 through six attacking wins, then automatically swapped
6:0 to 0:6 at halftime and finished 0:7. Buy phases lasted 14.983–15.000 seconds.
Each of the six ordinary actor-1 routes and plants took 9.083–9.117 seconds from
live start; each fuse lasted 35.017 seconds. The last round ended after its stock
100.017-second observed live period. No combat occurred.

| Participants | Won | Objectives each | Credits each | XP each |
| --- | --- | --- | --- | --- |
| Actor 1 | yes | 6 | 325 | 450 |
| Actors 2–5 | yes | 0 | 325 | 300 |
| Actors 6–10 | no | 0 | 250 | 200 |

The independently derived totals are 2,875 Credits and 2,650 XP. Initial independent
PostgreSQL reads showed zero wallets, ledger, rewards and match operations. The
final independent query matches every captured wallet, ledger and reward row,
the single operation's request fingerprint and response, and both committed
SQLite acknowledgements. Authenticated HTTP profiles also agree.

The original earned spool bytes and all canonical SQLite payloads have SHA-256
`462402a697b38c9628771384802fec3e3bdee3e3e2434a2cef7ad29ee9fadf6d`.
Eight boundary receipts establish an unchanged spool after game SIGKILL, durable
pending status after the owned database rejects connections, zero grants after
restoration, a real backend commit while its acknowledgement is held, worker
SIGKILL with pending SQLite state, exact restart acknowledgement and duplicate
spool removal. The backend's match HTTP outcomes are 500, 200, 200. Every committed
snapshot retains one operation, ten rewards and ten ledger rows; replay changes
no balance. The pending row retains the same bytes throughout.

Independent cleanup inspection confirms all 17 owned child PIDs are absent,
the exact owned container is absent, and none of the game/API/database listener
ports remains open. This review's lightweight PostgreSQL observer also exited.
Full derived figures are in `recomputed-run-471fbd8.json`.

## Source and comparison

The new dedicated probe calls production `TacticalMatch.configure` and submits
client input through `set_local_input`. Its only production-method override calls
the ordinary snapshot implementation before incrementing an observation counter.
It assigns no authority phase, score, timer, account binding, activity, timestamp
or earned-result fields. Shared navigation supplies a waypoint; actual movement,
planting, scoring, halftime, eligibility and submission remain authoritative.
The offline fixture initializer rejects network modes, so its initial-condition
fixtures cannot activate in this scenario.

Independent Git object comparison confirms unchanged gameplay scripts, assets,
main scene, project settings, export settings, backend and result worker relative
to the frozen product reference. Only a probe, its UID, Python orchestration,
validation controls and documentation were added. See `source-provenance.json`.

The inspected comparison is the existing account-admission test, account-ticket
network simulation and durable-result fixture. The network simulation assigns
live phase and an extended timer; the result fixture assigns score, roster,
duration and activity before submission. Those tests do not establish the new
scenario's complete production match-to-settlement path. This is an engineering
comparison against actual source and outputs; a blind visual A/B is inapplicable.

Four independently constructed incoherent observations passed the first
validator: seven wins from the waiting state onward, no client buy/live history,
activity belonging to unrelated actors, and contradictory client winner/score
summaries. All four reject after `471fbd8`; the maintained 13 controls also pass.
Both failed and corrected outcomes are retained. Synthetic controls establish
validator behavior, never match acceptance.

## Independent method

`recompute_run.py` imports no candidate validator. It derives the controlled
scenario's six objective contributions for actor 1, first-team winners, zero
combat statistics, exact rewards and terminal activity truncation from stock
rules and raw observations. It compares ten account identities, every client
round/side, original spool bytes, canonical SQLite bytes, transient recovery
states, exact acknowledgements, ledger, wallets and HTTP profiles.

`observe_postgres.py` independently reads the owned local database after the real
commit. Its connection uses only the generated local API configuration in memory;
no credential is retained. Initial independent reads confirmed ten consumed scoped
tickets, ten zero-balance players and no ledger, reward or match operation during
gameplay. Final independent queries are compared with the captured SQLite and
PostgreSQL operation response. A separate source-only reviewer identified and
helped close gaps in the independent recomputation before its final use.

The cached engine archive independently matches the pinned SHA-512. Its extracted
binary matches the executing engine's SHA-256, version and actual process path.
Eleven native processes were independently observed: one server and ten clients.
The owned PostgreSQL container uses the declared digest, auto-removal and an
anonymous data volume, with port `127.0.0.1:32768`. Credentials were not printed.

## Limits

The largest remaining deficiency is participation quality. Nine clients stand at
spawn and alternate yaw to satisfy the unchanged look-activity policy. This
establishes production activity computation without injecting activity fields;
it does not establish meaningful participation or resistance to AFK reward
farming. Actor 1 performs the objective path while all ten clients avoid combat.

All observed client traffic is loopback. The API and PostgreSQL listeners bind
loopback, while the unchanged production ENet game listener binds wildcard IPv6
`[::]:59371`. No public deployment or external service was used. Explicit game
bind-address support remains a local-test isolation improvement.

These are headless source-runtime clients configured directly by a test probe.
The evidence cannot qualify exported menus, rendered experience, physical
devices, human play, combat quality, real-world network conditions, impairment,
privacy attacks, performance or power-loss durability. The deliberate process
kills exercise process-crash recovery. G3 and G16 remain in progress.
