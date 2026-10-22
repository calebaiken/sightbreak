# Stock account match and earned recovery result

The controlled current-policy integration passed on frozen test source
`471fbd8fe17611c0c93728bc571ea6158838b458`. Ten distinct HTTP-registered accounts
finished seven stock rounds through real Godot clients and received results.
The resulting earned payload survived the game/worker kills, database outage,
lost acknowledgment and duplicate replay without another grant.

The independent critic accepted this bounded scope in separate commit `93f6b68`
(`independent-review/REVIEW.md` on `codex/m3-account-match-independent-review-ee89`). The
critic wrote a separate recomputation script, queried the live owned PostgreSQL
database before cleanup, verified the actual engine bytes and independently
confirmed that all owned children, container and listeners were gone. The builder
does not approve the candidate. Full G3 and G16 remain in progress.

## Frozen execution

Command:

```sh
/workspace/sightbreak/.venv/bin/python scripts/test_account_match.py \
  --out builds/account-match-stock-1 --timeout 1200
```

- UTC: `2026-10-22T04:29:01.633582+00:00` to
  `2026-10-22T04:37:47.751563+00:00`; 525.961667 measured wall seconds, exit 0.
- Godot `4.7.2.stable.official.ed1daf0bf`; binary SHA256
  `8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
- Test-source game tree `6d4ef305eafd4dfd200082d13c08b4c2e172632a` includes the new
  probe. Product gameplay, backend and result-worker files equal frozen `0ca125d`.
  Source was clean and unchanged during the complete run.
- No other native workload ran during the match. This is correctness evidence,
  without a network or performance benchmark claim.

## Observed match and recovery

| Observation | Raw result |
| --- | --- |
| Accounts | Ten API registrations; ten distinct scoped tickets consumed in PostgreSQL; actors 1–10 and authenticated names retained |
| Match start | Waiting round zero changed automatically to ranked buy round one after the tenth admission |
| Stock rules | 15-second buys, 3-second plants, 35-second fuses; six plant/detonation wins, 6:0 → halftime 0:6 → final 0:7 after the stock 100-second live timeout |
| Completion | 499.65 terminal simulation seconds; 500 payload timestamp seconds; all ten clients received result summaries and queued-delivery status |
| Activity | Each payload records 499 active seconds; 99.8% of its wall duration under the existing activity policy |
| Participation | Actor 1 earned six objectives; no kills/deaths/assists; first five original identities won |
| Before delivery | Zero ledger entries, rewards, match operations, credits and XP |
| Durable outage | Game SIGKILL after earned spool handoff; worker imported the unchanged payload, got real HTTP 500 while owned database connections were denied, and retained pending SQLite state before worker SIGKILL |
| Lost acknowledgment | Backend committed one match operation, ten rewards and ten ledger entries while the proxy held its acknowledgment; SQLite was still pending when the worker was killed |
| Restart/replay | Exact payload restart got HTTP 200 and committed; duplicate source replay left the committed row, two total delivery attempts and economy unchanged |
| Earned amounts | 2,875 total credits and 2,650 total XP, recomputed from the unchanged config, six objectives and five winners; SQL wallets/rewards/ledger and authenticated HTTP profiles/history agree |
| Cleanup | Ten clients exited 0; server and two workers exited expected SIGKILL; restart/replay exited 0; all 17 child processes reaped; only the owned container removed |

The earned payload and canonical SQLite fingerprint both hash to
`462402a697b38c9628771384802fec3e3bdee3e3e2434a2cef7ad29ee9fadf6d`.
The API logs contain the expected database-outage failure. Godot logs have no
engine error or leak marker.

## Evidence and corrected iteration

[round-1/sha256.txt](round-1/sha256.txt) indexes the exact raw outputs. The archive
retains normal/latest and separate completed-client reports, the original earned
payload, SQLite, each transient SQLite/economy/process checkpoint, all child logs,
driver output and final source/engine/cleanup receipt. The checkpoint files retain
pending/500 and backend-committed/ACK-held states before later rows overwrite them.

The initial `ee89ef4` validator accepted four independent synthetic counterexamples:
premature final scores, clients missing every buy/live round, unrelated activity
actor keys, and contradictory client result summaries. They were rejected as
evidence, corrected in `471fbd8` before native execution, and retained in the
critic's independent review. Its four counterexamples now fail. The 13 maintained
controls and 11 existing outbox/supervision tests passed before the frozen run.

Post-run, validator-only followup `0aae3f8` ties each outgoing winner, objective
count and active duration to observed server/client results and the declared
scenario. It also checks no bots/zero combat, runs its 14 positive/negative controls
with standard Python, and registers them in `validate.sh`. Both strengthened pure
validators pass replay of the frozen raw artifacts. This followup was unit tested
and replayed; the full native execution remains attributed to `471fbd8`.
No full `validate.sh`, new native export or second complete match is claimed for
the followup. The product files did not change.

## Remaining limits and next work

Nine clients deliberately turn at spawn. These ordinary input RPCs satisfy the
current look-activity rule; the run does not establish substantive participation
or resistance to AFK reward farming. It is a scripted no-combat match, without
human play, combat fairness, prediction feel, impairment or remote-host proof.

Clients used loopback traffic. The production game listener bound wildcard UDP
`[::]:59371`; the API and owned PostgreSQL bound only to `127.0.0.1`. No game-listener
isolation claim follows. Supported explicit bind-address configuration is a useful
next correction. The test uses the real result worker with supervised process
control, rather than proving a deployed launcher or power-loss/storage guarantee.

Next: integrate only after independent review; rerun the maintained suite on the
combined source. Keep G3/G16 open for the broader competitive/privacy/remote-host,
participation, restart/deployment and earned-economy requirements. Preserve the
stock run's exact source and raw receipts when adding further criteria.
