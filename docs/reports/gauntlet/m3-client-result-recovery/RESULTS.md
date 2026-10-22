# Durable armory receipt recovery

The current client loses an unresolved keyed transaction after restart, logout or
a rejected retry. The adapted PR18 runtime retains the original intent and
recovers its exact server confirmation in the declared local fixture. This
component does not change postmatch reward delivery or the offline profile.

## Exact source and adaptation

Native baseline: `b97fd81b0f10f45bda92f4a873314b0d270086db`, game tree
`41abd17652a89c554463faa5b216a7af59aec0e7`.
Native candidate: `79e076ed83651aea3ff8e439a64c0f979d35ecf2`, game tree
`1f3616afdfaaed0fb7c9ffbd0aa8e4947f7d2a48`.
Both remained clean and identical before/after execution. The independent critic
recorded source-after before the builder added these evidence files.

Live PR18 was fetched and inspected at `ccd0955`, base/merge-base `d2439ac`;
baseline is 236 commits ahead and 11 behind that branch. Its EconomyUI, EconomyAPI
and affected existing tests match the PR16 base, so the narrow runtime applied
without conflict. Production EconomyUI and TransactionJournal are byte-identical
to PR18; backend/server trees have no change. No PR17/19/21 source was imported.

The three original runtime commits preserve author and `-x` provenance:
`ac48342` → `a0c413a`, `cda6372` → `5d04aa6`, `7b6f379` → `ce2b128`.
Probe-only hunks from `223ec0c` are `499b305` with original authorship;
`e0cd1e4` → `7f4d360` preserves the recovery-kill follow-up. The Windows
closed-port relaxation was excluded; the existing strict armory assertion stays.
Own changes add native lifecycle observations, private fixture state, stricter
source/route/raw-byte/result/debit oracles, pure negative controls and maintained
journal-suite registration.

The journal saves only allowed receipt fields before dispatch. An OS-released
local owner prevents competing writers. Damaged or failed storage blocks new
requests. Logout/auth failures and rejected retries retain unresolved intent.
Recovery requires the original signed-in account/server; the server remains the
source of item ownership and balances. Credentials remain in memory.

## Observed output

Pinned Linux Godot: `4.7.2.stable.official.ed1daf0bf`, executable SHA256
`8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e`.
The same external probes ran against both projects. All values and costs were
synthetic, as declared in [RUNTIME_PLAN.md](RUNTIME_PLAN.md).

| Measure | Baseline | Candidate |
| --- | --- | --- |
| Specific receipt recovered after process restart, 3 routes × 4 boundaries × 1 repeat | 0/12 | 12/12 |
| Retains earlier uncertainty after observed retry 409 | false | true |
| Retains intent through logout and UI recreation |false|true|
| Token/account cleared on logout |true|true|
| Candidate case: one fixture mutation and expected debit |not a recovery claim|12/12|
| Candidate case: original route/method/raw body/key/parsed payload reused |not a recovery claim|12/12|
| Candidate case: exact SQLite result, journal excludes fixture token, final journal absent |not a recovery claim|12/12|
| Delayed candidate cases: 409 < release < original commit and journal retained | unexercised retry | 6/6 |

The baseline native lifecycle log shows `pending_after_lost_response:true`,
`retry_status:409`, then `pending_after_rejected_retry:false`; logout and
recreation also show false. This is the actual source counterexample, rather
than an inference from the earlier V2 evidence. Its committed fixture mutations
remain on the server; the lost object is the original client receipt/confirmation.

Five affected candidate suites pass on the same clean source: journal 41/41,
recovery 12, armory 748, menu 51, and economy native/offline separation/URL/UUID
checks. The journal suite includes a real competing process, original account and
server mismatch, corrupt/unwritable storage, actual-file truncation, malformed
confirmation and stale-owner recovery. Seven pure oracle groups also pass.
The native/import logs contain no engine error, warning or leak marker. Both
driver sessions finished and no owned native/HTTP listener remains.

The [independent receipt review](independent-critic/REVIEW.md), commit `73685c7`,
accepts this bounded adaptation. The critic recomputed all 24 cases from original native logs,
SQLite ledgers, request bytes, journal snapshots, both clocks and forced-kill
acknowledgments; it also independently checked the five affected outputs. Its
final verdict and independent artifacts are delivered separately to the root.

## Corrections and retained evidence

Before native launch, source review required exact method/path/raw-body checks,
scanning the original killed-client log, proving a live original at the kill
barrier, and preserving timeout/exception output. Commits `a9aa5e0` and
`79e076e` contain those corrections. The earlier preflight at `a9aa5e0` remains
labelled separately; only `79e076e` ran natively. No failed native attempt or
deadline extension occurred in this component. PR18's earlier rejected rounds
remain retrievable on its original branch and were not relabelled as new results.

`receipt-evidence.tar.gz` retains 373 original files, including every SQLite ledger,
native/HTTP log, timestamped PID/kill event, exact journal-byte snapshot, lifecycle
result, import output, source receipt and affected-suite driver. The final source
receipt and pure log are also in this directory. `archive-manifest.json` lists
archive hashes; `raw-manifest.json` lists all 375 raw files. Two generated Godot
editor-documentation caches are excluded from the bounded archive, with exact
hashes/reasons in `archive-exclusions.json`; both originals and the full raw
archive remain outside the repository.

## Open qualification

The largest remaining product gap is the player-driven armory recovery journey:
ordinary confirmation, lost response, sign-out/re-authentication and retry with
rendered input/pixels. These native headless probes invoke the real UI methods;
they do not prove that journey's usability or presentation. Real PostgreSQL
lost-response market settlement, remote hosts, arbitrary instruction-level kills
and host power loss also remain open. The preserved backend cannot durably fence
a permanently rejected uncertain intent, so such an intent can remain blocked;
silently forgetting it would risk an earlier request committing later.

Whole G3/G7/G16 remain in progress. Protocol 6, opt-in prediction/live rewind off,
privacy, earned-only authoritative economy and offline/online boundaries remain.
The root owns one new frozen full aggregate after integration.
