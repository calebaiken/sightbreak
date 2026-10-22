# Declared focused native run

The root released the local native lane on 2026-10-22 after its other runtime
resources were removed. No broad aggregate or concurrent unrelated run is planned.

Use the pinned executable
`/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64`.
Freeze both sources clean before launch: baseline `b97fd81`, sparse
`/workspace/sightbreak-client-receipt-baseline`, and this candidate worktree.
The harness records the exact commit, game tree and clean status before/after;
any source change fails the run. All user data, preferences, journal files and
output live in newly created fixture directories outside both checkouts.

The native lifecycle probe runs unchanged against both projects. Its API is an
in-process stub: original store request loses its reply; retry returns 409;
another request loses its reply, signs out, then recreates the UI. It records
actual pending state, logout/token clearing, original calls and final server-read
balance. It does not claim an HTTP, PostgreSQL or rendered-input result.

The process-kill campaign uses a loopback HTTP server with a new durable SQLite
ledger per case. There are three routes (store, case, market) and four boundaries
(before commit, after commit, delayed original commit after retry409, and forced
kill after the observed409 before teardown), one declared repetition each:
12 cases per source. Each candidate case must reuse the original key, route,
method, parsed payload and raw body bytes; recover the ledger's exact confirmed
result; have exactly one mutation/debit; exclude the synthetic credential from
the journal; and remove the journal only after confirmation. Delayed cases
require rejected retry < release < original commit and retained journal bytes.
The baseline is expected to lose all restart receipts and both lifecycle intents.

All values are synthetic: fixture account `fixture-account`, memory-only token
`fixture-memory-only-credential`, store/key definition `key`, synthetic case/key
and market listing identities, fixture item `one-authoritative-instance`, initial
balance 10,000,000 units, store/case cost100, market cost10,000,000 and fee300,000.
These SQLite cost rows are not authoritative PostgreSQL wallets or real items.
The lifecycle stub uses a separate synthetic account/token and server balance0.

From the clean candidate checkout, with a fresh outside output path:

```sh
python3 scripts/validate_transaction_restart.py \
  --godot /workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64 \
  --baseline /workspace/sightbreak-client-receipt-baseline \
  --candidate /workspace/sightbreak-client-result-recovery \
  --out /workspace/sightbreak-client-receipt-runtime-r1 \
  --repetitions 1 \
  --boundaries before_commit after_commit late_commit recovery_kill
```

Then run only affected candidate suites in a private state directory through
`scripts/godot.sh`: transaction_journal_test, economy_recovery_test,
armory_state_test, menu_state_test and economy_ui_test. Capture full output,
return codes, duration, Godot identity and source before/after; reject native
errors on either stream. The journal suite includes a competing native process,
account/server mismatch, storage truncation/unwritability and malformed replies.
The maintained validator now includes that suite; the root owns the final whole
aggregate after independent review and integration.

Retain failed attempts. The critic must inspect original observations, journal
snapshots, timelines and SQLite receipts rather than accepting the harness pass.
Native headless tests do not establish player input/pixels, visual quality,
PostgreSQL settlement, postmatch UX, remote-host behavior or host power loss.
