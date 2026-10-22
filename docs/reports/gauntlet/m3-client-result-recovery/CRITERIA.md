# M3: durable armory receipt recovery

Registered before candidate changes on 2026-10-22. Builder source is
`b97fd81b0f10f45bda92f4a873314b0d270086db`; own branch is
`codex/m3-client-result-recovery`.

## Scope and retrieved bar

This component concerns the original keyed store purchase, case opening and market
purchase intent when a client closes around server commit. PR18's B-21 does not
implement postmatch reward receipts. Match rewards already use the authoritative
server outbox. Its ten-account result-recovery pass does not qualify this armory
flow. The offline training profile is a separate local record.

The named source/runtime correctness bar is PR18
`astra/systems-v3-recovery`, retrieved from origin on 2026-10-22 at
`ccd0955a2cf5d8bcad4e9e9e2fba8ad399591f5e`. Its runtime is `7b6f379`,
with follow-up crash probe/harness `e0cd1e4`. Its base is PR16 `d2439ac`.
The baseline EconomyUI, EconomyAPI and three affected existing test files have no
diff between that base and this component's b97 source. The retained PR18 r6/r7
logs, SQLite ledgers, journal captures and timestamped process events are
retrievable Git objects. They are prior reported evidence until freshly inspected
by this component's critic; they are not new execution on b97.

The comparable measure is recovery of the same receipt, endpoint, payload and
original expected price, with one fixture mutation, no credential in the journal,
and no invented ownership or balance. A blind output comparison may compare that
bounded measure after native runs. It cannot establish visual parity with CS2.

Live dependency checks also found PR17 `320e0ef`, PR19 `89215fb` and PR21
`6d2b38d`. They remain unqualified and are outside this adaptation. No backend,
server, protocol, gameplay, art, prediction or rewind change is proposed.

## Independent components and gates

1. **Before dispatch.** Save a whitelisted original account/server-bound receipt
   before each keyed request. Failed, corrupt or changed storage must block
   dispatch. A competing process cannot stage, retry or clear the same journal.
   Close/read-back verification and an OS-released exclusive owner must survive
   an app-process exit. No host-power-loss guarantee is claimed.
2. **Recovery.** Restart and logout retain unresolved intent. Only the original
   authenticated account/server can resend it. Caller changes cannot alter the
   saved expected price. A failed retry, including 409 before a late original
   commit, cannot erase earlier uncertainty. An incomplete success cannot clear
   the receipt. A valid keyed server confirmation may clear it; ownership and
   balances come from fresh server reads.
3. **Qualification.** Source checks identify the exact baseline ordering defect;
   pure tests challenge the observation/oracle machinery. Native journal and
   recovery suites, all three routes at before/after/late commit, and a kill
   after observed retry 409 must pass on clean, fixed source before runtime
   acceptance. Retain PID acknowledgments, original request/reply/journal bytes,
   SQLite ledgers, ordering events, failed trials and source identities. Register
   the journal suite in the maintained validator. The final root aggregate owns
   the local Godot/native/OCR lane until explicitly released.

Expected baseline counterexample from inspected source: `_perform` dispatches
before recording uncertainty; `_logout` discards the only RAM receipt;
`_retry_pending` clears it before resending. A rejection of that retry is not
uncertain, so the original pending intent is lost even if an earlier request may
later commit. Source evidence is not a substituted native counterexample.

## Acceptance limits

The builder cannot approve the work. Request a fresh root critic after source and
pure outputs are frozen. Native results stay UNVERIFIED until actually run and
reviewed. Whole G3/G7/G16, player-driven consent/pixels, postmatch account UX,
PostgreSQL lost-response settlement, remote-host impairment and host power loss
remain open. Protocol 6 / Godot 4.7.2, account privacy, authoritative earned-only
economy, offline separation, opt-in prediction and live rewind off remain intact.
No client or cached record may award a wallet balance or item.
