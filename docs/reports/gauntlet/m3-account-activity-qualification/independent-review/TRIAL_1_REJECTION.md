# First current-source trial: independent qualification blocked

Execution source is `e2c61ac2ecbd38ab55bc9edb712b028322c1490f`, game tree
`fb6be859e05812d8707be1ef5c6f747d2588c1e9`. The unchanged builder harness passes
in 529.336562 seconds. Independent current-source qualification is **BLOCKED**
because no retained actual SQL observation is timestamped after duplicate replay.
The strict oracle failure is preserved in `recompute-current-run.txt`.

The observer retained its last actual SQL row at
`2026-10-22T06:18:50.186645+00:00`. The replay checkpoint is
`2026-10-22T06:18:50.187242+00:00`, 0.597 ms later. The SQL query was already in
flight when its output handler noticed the new checkpoint file. The handler
attached that checkpoint to the older query and then discarded subsequent rows
whose tables and observed checkpoint set were unchanged. A checkpoint-seen tag
cannot establish that a query began after the checkpoint.

The initial progress message said post-replay SQL was retained. Exact UTC
recomputation rejected that statement; it was corrected immediately to the lead
and builder. Later polling counts or HTTP profiles cannot replace the missing
retained actual SQL row. The owned database is now removed, so this trial cannot
be repaired by another query. A new match must use new accounts and resources.

The first retained committed SQL row is genuinely before acknowledgement release:
`06:18:49.871659`, before the lost-worker-killed checkpoint at
`06:18:49.910004`. Other independently established evidence is preserved:

- Ten actual zero-wallet players and ten consumed scoped tickets, with no ledger,
  reward or match operation at the baseline.
- One actual committed operation, ten reward rows and ten ledger rows for the
  fresh match `9b937147-af16-4709-a45b-ecec3193b642`. The observed wallets total
  2,875 Credits and 2,650 XP. These observed numbers do not close the missing
  post-replay boundary.
- Fresh earned payload SHA-256
  `a62c9357a634f11da4a3fc0025307062c13f29c0872b27f17f838e98d1e0a20c`, distinct
  from the historical benchmark payload. No prior payload was substituted.
- Byte-identical clean before/after source and pinned engine receipts, eleven
  independently inspected native engine children, and wildcard IPv6 game UDP
  binding on port 37622.
- Independent absence of all 17 builder child PIDs and 17 observer psql PIDs,
  the exact owned container, and API/PostgreSQL/game listeners. The engine/CPU
  lane was released after these checks.

`source-execution-join.json` passes its source/process/SQL/cleanup identity join;
it does not override the strict timing rejection. The raw SQL samples, observer
report/errors, process receipt, before/after source and cleanup receipt remain
in this directory. The original builder runtime archive is owned separately by
the account-match builder.

The next observer must retain every recovery sample and perform an explicit
owned read-only query initiated after seeing the replay checkpoint. An in-flight
query/checkpoint race needs a synthetic negative control and fresh independent
review before any new runtime. No game, harness, timer, score, activity, reward
or economy rule changes are part of that correction. M1's separate complete
plant journey remains failed. G3 and G16 remain in progress.
