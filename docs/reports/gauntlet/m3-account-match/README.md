# Account match and earned-result recovery

Candidate scope is a real Godot 4.7.2 server and ten real protocol 6 clients,
HTTP account/ticket authentication, and PostgreSQL result delivery on loopback.
The backend uses ten newly registered fictional accounts. The harness starts a
uniquely named, pinned, cached PostgreSQL container with an ephemeral data layer
and a random loopback port. It removes only that container and its own children.
It never reads a saved server key or changes an existing database.

## Bar and criteria declared before execution

The inspected comparison is the integrated gameplay at `2a2b732`, whose product
gameplay is the frozen `0ca125d`, and its existing account/result contracts:

- `scripts/test_account_network.py` proves authenticated identity and admission.
- `scripts/simulate_network.py --account-tickets` supports ten identities, but its
  probe overrides live phase and round time for movement measurement.
- `scripts/test_result_outbox.py` proves durable crash recovery, but its Godot
  probe injects account IDs, score, duration and activity before submission.

Those existing tests remain useful unit/integration fixtures. They do not prove
that ten account clients finish a production match and deliver its earned result.
The new harness must satisfy all of the following:

1. Register ten distinct accounts through the real HTTP API, obtain ten scoped
   one-use tickets, and admit all ten through the production protocol handshake
   and ticket inspection/consumption. Each client must retain its expected actor
   identity and authenticated display name.
2. Observe waiting round zero, automatic ranked start, and every buy/live round
   through match over with ten connected clients. Preserve stock 15-second buy,
   100-second round, 3-second plant, 5-second defuse, 35-second device and seven-win
   rules, automatic halftime and reward eligibility. Never assign server score,
   phase, timer, roster, activity, timestamps or result fields.
3. Submit gameplay through ordinary client `set_local_input` only. Actor 1 uses
   shared map navigation to plant during its attacking half. Other clients turn
   at spawn; actor 1 holds after halftime. This is a controlled no-combat match.
   The activity policy must accept the actual input stream. No human play,
   combat quality, network impairment or performance claim follows from it.
4. Observe a non-draw completed match after at least 300 simulation seconds,
   all ten eligible activity fractions, and all ten replicas receiving results
   and queued-delivery status. The production `_end_round` and
   `_submit_ranked_result` must create exactly one spool record. Wallets, ledger
   and rewards must remain zero until the worker delivers that record.
5. SIGKILL the actual game after its earned handoff. Deny connections only to the
   owned local database; observe a durable pending SQLite result after HTTP 500
   and kill the worker. Restore the owned database and lose the HTTP response
   after its real commit; SIGKILL/restart the worker with the exact payload.
   Replay the original spool record. All paths must retain one match operation,
   ten rewards and ten ledger entries with no second wallet grant.
6. Compute expected credits/XP from the unchanged economy config and earned
   participants; agree with PostgreSQL wallets, reward details, ledger and each
   authenticated HTTP profile/history. Preserve logs, transitions, payload hashes,
   exact source identity, failure state and cleanup receipts. Engine errors fail.

## Execution

Use an existing backend interpreter; do not install dependencies or start the
shared development database. Import the project once before launching ten clients.
Avoid other native/network workloads during this correctness run.

```sh
cd /workspace/sightbreak-account-match
SIGHTBREAK_TOOLS_DIR=/workspace/tools ./scripts/godot.sh --headless --editor --import --quit
/workspace/sightbreak/.venv/bin/python scripts/test_account_match.py \
  --out builds/account-match-stock-1 --timeout 1200
```

`--timeout 90` is a bounded diagnostic that must fail as incomplete. It never
promotes partial rounds to a completed match. Latest reports and transitions are
retained on failure. `completed-*.json` retain the completion boundary separately
from the subsequent deliberate server-kill disconnects.

The builder cannot approve this candidate. Independent review and raw-output
recomputation are required before integration. G3 and G16 remain in progress.
