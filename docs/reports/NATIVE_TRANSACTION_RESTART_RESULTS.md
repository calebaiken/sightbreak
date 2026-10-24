# B-21: real PostgreSQL/native receipt recovery

## Outcome

**Exact shipping source `7b6f379a3f8c809d0985a64e883cbadfdd78d135` recovered
3/3 committed market receipts after native process termination before response
delivery. Frozen V2 `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` recovered 0/3.**
All six purchases committed exactly once. In every case, the complete captured
economic state remained identical after termination, recovery, and the second
restart. The candidate's recovered result equals the original committed HTTP
result and the real PostgreSQL `Operation.response`, including every item field,
buyer balance and fee. The recovered request bytes also equal the first request.

This closes the focused PostgreSQL/native after-commit response-loss evidence gap
for this exact source. The initial target was `cda6372`; its candidate invocation
stopped at cache provenance preflight. **These are fresh `7b6f379` measurements,
not relabeled `cda6372` results.** The completed V2 run was retained across the
server interruption and was not repeated.

## Matched workload and authoritative outcome

| Integer expected price | Buyer debit | Seller credit | Fee burned | Buyer balance after | Seller balance after | V2 receipt recovery | `7b6f379` receipt recovery |
| ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: |
| 400 | 400 | 388 | 12 | 1,600 | 2,388 | No | Exact |
| 401 | 401 | 389 | 12 | 1,600 | 2,389 | No | Exact |
| 10,000,000 | 10,000,000 | 9,700,000 | 300,000 | 1,600 | 9,702,000 | No | Exact |

Each case added exactly **one Operation, two Ledger rows and one
`market_settled` Audit row**. The item moved from seller to buyer, its reservation
cleared, and its listing became `sold` with the correct buyer. No additional
economic rows or wallet/ownership changes appeared on replay or second restart.
Before each case, buyer balance was `price + 1,600` and seller balance was 2,000.
These fictional seed balances are explicitly marked `fictional_test_fixture` in
the real PostgreSQL ledger; they are not gameplay earnings or SQLite fixtures.

The external probe constructs the production UI, signs in through
`EconomyUI._authenticate`, and calls the production `_perform` with an integer
price and original UUID receipt. A loopback proxy forwards the request unchanged,
receives the complete real backend response, and holds every client response
header and byte. A separate read-only PostgreSQL connection verifies the commit
before the harness terminates and waits for the native process. It then discards
the held response. The candidate reloads its journal and calls `_retry_pending`
after signing in to the original account with a fresh real session. A third
native process signs in again and confirms no pending receipt/no purchase request.

All cases recorded three distinct native-issued token digests, matched to real
PostgreSQL session rows for the same account. Published fixture/authentication
logs redact plaintext passwords and bearer tokens. The original key/body and raw
credential-free journal bytes remain available. Exact receipt equality is
structured JSON equality: PostgreSQL JSONB can reorder response object keys.

### Candidate process barriers

| Price | Initial PID | Recovery PID | Second-restart PID | Hold → termination acknowledged | Termination acknowledged (UTC) |
| ---: | ---: | ---: | ---: | ---: | --- |
| 400 | 22304 | 24420 | 22552 | 235 ms | 2026-10-23 00:37:43.282638 |
| 401 | 14060 | 2368 | 21868 | 219 ms | 2026-10-23 00:37:51.027315 |
| 10,000,000 | 16160 | 19404 | 21184 | 250 ms | 2026-10-23 00:37:59.077654 |

These UTC times are October 22 in the host's EDT timezone. The baseline ran on
October 19 at 20:15 UTC. Timings establish ordering, not a performance comparison.
Each timeline proves `response held → independent committed snapshot → terminate
request → exit acknowledged → held response discarded → recovery process`.
No original purchase response was delivered. Every native launch observed an
unoccupied native slot; processes within this harness were strictly serial.

## Exact source and frozen harness

| Component | Identity |
| --- | --- |
| V2 measured commit | `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd` |
| V2 game tree | `2d2b174c2145e9755ddfc78a1369e74443fcc400` |
| Candidate measured commit | `7b6f379a3f8c809d0985a64e883cbadfdd78d135` |
| Candidate game tree | `026b711f887038a9e953b448dcad0f1208e5210b` |
| Identical backend tree | `67027b4fa17674ef067c84401af76eb1524419ac` |
| Final pre-measurement harness freeze | `31438cbcea6ef08a131ae312c65b94f7e3e882c3` |
| Harness SHA-256 | `1b9489c29c8da2cbe58711da49fd6438513a48980430247586aac4837ad05373` |
| External probe SHA-256 | `075e3982712ea710c3bcfa92efc7a5e03314cc401445d14e45c902e718353fbe` |
| Godot executable SHA-256 | `ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424` |

Both completed arms used those identical harness, probe and official
`4.7.2.stable.official.ed1daf0bf` executable bytes, Python 3.12.14, PostgreSQL
17.11, and unmodified production backend code. Each measured `git archive`
contained only the exact revision's game/backend source. Clean checkout status,
archive hash, per-file source manifest, copied import-cache manifest and unchanged
extracted source were recorded. The candidate used a dedicated detached
`7b6f379` checkout/cache, avoiding the changed shared checkout.

The initial freeze was `1fa754b`. Corrections `a8a525c`, `a951725`, and `31438cbc`
added early diagnostics, moved seeding to a short-lived setup interpreter, and
removed the Windows unread-pipe capture deadlock. All corrections preceded both
completed measurements. Earlier failed attempts and the pipe control are retained.
The same crash workload ran in each arm; the candidate additionally pre-seeded
separate accounts for the optional regression. Those unrelated rows were included
in the unchanged-state comparisons.

Only generated `sightbreak_receipt_<hex>_test` databases were created/dropped:

- V2: `sightbreak_receipt_b567be9ef48b1a6f_test` — drop confirmed.
- Candidate: `sightbreak_receipt_e6adb9395b08029b_test` — drop confirmed.

After the host restart, the existing recorded portable cluster was restored using
its existing data directory and loopback/port/memory options. A failed first
restart and its PostgreSQL initialization error remain in the evidence. Data was
not reinitialized; no other worker's database or process was removed.

## Existing native economy regression: original failure retained

The exact candidate `native_economy_test.gd` ran against the real service and
reported **36/37**, exit 1. Its sole recorded failure is line 124: the port-9
unreachable-server test assumes Windows reports `not_reached`; the actual request
took the timeout/unknown-outcome path. Raw stderr retains the failure/backtrace.

A separate external copy changed exactly one literal at line 122:
`http://127.0.0.1:9` → `http://native-receipt-oracle.invalid`.
That deterministic DNS-failure calibration reported **37/37**, exit 0. The
production test file was not changed. Both executed sources and logs are retained.

- Original test SHA-256: `0bde4d9c43c82c1c7b12e1d317b63fd56c950ba64a2aa6b31b3c276758678b6c`.
- Calibrated test SHA-256: `6801fdeb21f76b9afa69c985d8b62148d7291c5b0e8ffcba0d969ac00a027832`.

The calibrated pass does not erase the original failure. These supplemental
results are separate from the receipt oracle's successful `core_pass`.

PR18's maintained test now adopts that same single-literal DNS calibration. The
executed probe above has CRLF line endings; the maintained Git blob has LF endings
and SHA-256 `516aaee3ec42410c0a566861c4988d3bec618b808cbbb733df99b77c3dc9d5f2`.
Expanding those LF endings to CRLF reproduces all executed bytes exactly. The
original `7b6f379` failure remains retained. This is a test portability fix, not a
change to the measured shipping runtime or HTTP outcome classification; no new
regression run is claimed for the publication commit.

## Raw evidence and reproduction

[Evidence index](native-pg-restart-evidence/README.md) ·
[V2 summary](native-pg-restart-evidence/r9/baseline/summary.json) ·
[candidate summary](native-pg-restart-evidence/r10/candidate-7b6f379/summary.json) ·
[row/event verification](native-pg-restart-evidence/verification.json) ·
[raw Git-blob publication proof](NATIVE_TRANSACTION_RESTART_GIT_PUBLICATION.json) ·
[frozen protocol](NATIVE_TRANSACTION_RESTART_PROTOCOL.md).

Use a clean checkout of the frozen harness, an exact-source checkout with imported
metadata, and a new output directory. The candidate invocation is retained as
`native-pg-restart-evidence/r10/command.json`.

```powershell
$python = 'C:/Users/blith/AppData/Local/Temp/opencode/sightbreak-backend-trade-env/venv312/Scripts/python.exe'
$godot = 'C:/Users/blith/AppData/Local/Temp/opencode/godot/Godot_v4.7.2-stable_win64.exe'
& $python scripts/validate_native_transaction_restart.py `
  --source <clean-exact-source-checkout> `
  --revision 7b6f379a3f8c809d0985a64e883cbadfdd78d135 `
  --cache-source <clean-exact-source-checkout>/game/.godot `
  --godot $godot --out <new-outside-tracked-source-directory> `
  --repetitions 3 --expect-recovered 1 --native-economy
```

For the V2 control use revision `701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd`, its
matching cache, and `--expect-recovered 0`; omit the supplemental regression flag.
PostgreSQL must be available at the recorded `127.0.0.1:55439` development cluster.

This task adds harness/probe and focused evidence only. It exercises native UI
methods and real HTTP/SQL, not automated mouse/touch confirmation interaction,
backend-process failure, or machine power-loss durability. At initial publication,
the existing B-21 critic passes were outside this new packet and its own independent
review had not begun. PR18/PR17 remain draft handoff targets.

## Subsequent independent outcome review

The [full frozen verdict](native-pg-restart-evidence/blind-review/_FROZEN_VERDICT.md)
selects Set-8F5F7604: 3/3 exact recoveries versus 0/3. All 122 packet payloads,
six cases, 30 SQL stages and 2,078 consistency checks passed. The reviewer
recomputed fee rounding, full economic-row preservation, fresh-session binding,
exact receipt/request/result equality and zero purchases on second restart.
The verdict was frozen before identity/source access in
[PR18 comment 6355013968](https://github.com/calebaiken/sightbreak/pull/18#issuecomment-6355013968).

The subsequent [source/API binding audit](native-pg-restart-evidence/source-binding/README.md)
passes. It verifies all114 observation mappings, the measured source archives and
the production journal-to-HTTP recovery dataflow. The exact existing key is released:
Set-673EECBC is701ce2c; Set-8F5F7604 is7b6f379. A focused minimal-recovery-input control
is additional corroboration, not a remaining source-dataflow blocker. The original
packet, result flags and raw observations remain retained. In particular, baseline
flags about the original committed result or stable journal absence do not establish
successful receipt recovery. Historical cache bytes and independently attested
execution/process lineage remain unavailable.
