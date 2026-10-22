# Independent B-21 armory receipt review

**The bounded adaptation passes.** Clean candidate
`79e076ed83651aea3ff8e439a64c0f979d35ecf2` recovers **12/12** native
process-kill cases; clean baseline
`b97fd81b0f10f45bda92f4a873314b0d270086db` recovers **0/12** under the same
probe. This accepts the keyed store/case/market receipt component against its
inspected baseline. It does not close whole G3/G7/G16 or postmatch recovery.

The critic launched no Godot, renderer, OCR or HTTP server. This review uses
independent source/file/Python audits of the builder's actual native output,
plus read-only live PID/socket observations. There is no subjective blind claim.

## Source and original bar

The live GitHub API independently confirms PR18 is an open draft at head
`ccd0955a2cf5d8bcad4e9e9e2fba8ad399591f5e`, base
`d2439acdd5f73df7bae5ada62ee1e3dec2cf30db`. Baseline EconomyUI, EconomyAPI
and the three affected existing tests equal that base byte for byte. Candidate
production EconomyUI and TransactionJournal equal PR18 head byte for byte.
Backend/server trees are unchanged. Runtime commits preserve original authors
and `-x` provenance; the partial transport adaptation preserves the original
strict armory closed-port assertion. No whole V3/PR17/19/21 integration occurred.
See [source-audit.json](source-audit.json).

The inspected baseline dispatches before saving uncertainty, stores its only
receipt in RAM, discards it on logout, and clears it before a retry. The same
native lifecycle probe shows an actual 409 retry loses baseline pending intent;
logout followed by UI recreation also loses it. Candidate retains both, then
recovers the original key and reads the final zero balance from its API stub.
The stub is explicitly separate from the HTTP crash campaign.

I also reopened original PR18 r6/r7 Git blobs and recomputed all 72 SQLite
ledgers/native outcomes: r6 candidate 27/27 versus baseline 0/27; r7 candidate 9/9
versus baseline 0/9. Costs, keys, parsed payloads and native results match their
stored fixture receipts. R7 retained byte snapshots establish the post-409
forced-kill ordering. These are historical Windows fixture results, not execution
on the new baseline/candidate. R6 has no r7-style explicit disk-state snapshots;
its final disk absence is not independently re-proven here. See
[original-bar-audit.json](original-bar-audit.json) and its rerunnable audit script.

## Actual pinned Linux output

Godot identifies itself as `4.7.2.stable.official.ed1daf0bf`; the observed native
executable SHA256 is
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
Candidate game tree is `1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48`.
Both source identities are clean and identical before/after in the harness,
and the critic independently recorded the fixed source afterward.

The campaign covers all three routes at before-commit, after-commit,
delayed-original-commit after retry 409, and forced kill after the observed 409.
For every candidate case I independently joined original/retry method, endpoint,
raw HTTP body bytes, parsed payload and original expected price to the journal
and SQLite receipt. Every final native result equals the stored response; every
candidate ledger has exactly one mutation and expected debit. Candidate totals
12 mutations/40,000,800 synthetic cost units. Baseline totals9 mutations/
30,000,600 units because its three before-commit originals are dropped and it
never recovers. These are fixture costs, not PostgreSQL wallets.

All 24 databases pass immutable read-only integrity checks. All original kills
return `-9`; all three candidate post-409 kills return `-9` before original
commit release; final recovery processes return 0. Both clocks establish
rejection → observed pending result → kill acknowledgment → identical journal
capture → original release → original commit → final replay. The 12 candidate
saved journals contain only the six whitelisted transaction fields and no
fixture credential, Bearer, Authorization or password. All 12 final disk-state
captures explicitly record absence after recovery completion; the paths are
also absent at independent inspection. See [current-run-audit.json](current-run-audit.json).

All five affected native suites pass without errors, leaks or resources in use:
journal 41/41, recovery 12, armory 748, menu 51, and the economy native/offline/URL/
UUID suite. The journal suite exercises changed caller price, account/server
mismatch, failed retries including 409/401/429/422, incomplete successful replies,
corrupt/unwritable/truncated storage, stale ownership and a competing real
native process. Child 124347 cannot stage, claim or clear the owner's receipt;
all three return 22 and original bytes remain unchanged. Source review confirms
closed-file read-back before dispatch, bounded 8 KiB storage, retained failed
recovery, and fresh server reads for balances/ownership. No cached/local receipt
grants an item or balance.

Independent live observations see driver 122834, its candidate native descendant
and driver-owned loopback listener. Twelve distinct subsequent PID/socket states
are retained. Final read-only checks find all 63 recorded campaign/child/driver
PIDs gone and all 48 fixture/journal listener ports absent. The raw-output
manifest records 372 current files/7,285,458 bytes, including private-state logs.
See [affected-and-cleanup-audit.json](affected-and-cleanup-audit.json),
[current-output-manifest.json](current-output-manifest.json), and the live
observation files.

## Findings fixed before runtime

- The maintained validator initially omitted the new journal suite. Candidate
  now registers the journal suite in a private state directory and the pure
  receipt oracle checks.
- The original fixture accepted any POST route and retained only parsed bodies.
  It now records/refuses wrong endpoints and independently requires original
  method, route, parsed payload and raw body bytes across every inbound request.
- Prelaunch review found initial native output was unscanned, original forced
  kills lacked the alive/nonzero guard, and recovery exceptions could lose raw
  streams. Commit `79e076e` adds those guards and preserves output on failure.
  These were source findings; no rejected native trial is hidden.

The builder's seven pure adversarial groups pass. This critic independently ran
them and six additional pure guard groups, including changed-but-clean source,
wrong engine, dirty source, zero/negative repetitions, output inside source and
native stdout error retention. Every native/server entrypoint was mocked in
the critic controls. The original-bar audit's first attempt incorrectly expected
r7 disk snapshots in r6 and failed on the missing file. Its corrected audit
keeps the r6 disk-observation limitation above; this was an audit assumption,
not a product failure.

## Largest remaining boundary

Real-account, player-driven recovery against the production backend remains
unqualified. The current evidence uses a headless loopback SQLite fixture and
stub lifecycle; it does not show rendered consent/pixels, PostgreSQL lost-response
settlement, remote-host impairment, arbitrary instruction/power-loss interruption,
or new physical macOS/Windows qualification. Original Godot 4.7.2 Unix/Winsock
socket implementations support the listener ownership choice in source; this
does not replace device execution. Corrupt/unresolved journals deliberately
block later mutations rather than silently discarding an uncertain action.

The final integrated aggregate is still required. Postmatch server outbox,
earned-only/offline separation, protocol 6, prediction opt-in and live rewind-off
boundaries remain unchanged.
