# NEUTRAL — round-two retained-artifact verdict

## Outcome and exact acceptance boundary

**ACCEPT WITH QUALIFICATIONS for the narrow captured successful GET `/trades`
slice; prefer anonymous V for measured query efficiency.**

V has fewer executed SQL callbacks in five of seven workload pairs, ties in two,
and has no measured statement-count regression. All 168 retained received-response
records resolve to raw bytes whose independently reconstructed canonical bytes
equal both their saved actual canonical body and the separate expected body.
Every one of the fourteen before/after authoritative row intervals is unchanged:
all 336 table files and 28 reconstructed aggregate states verify.

**The earlier absent received-body and snapshot/hash evidence gaps are closed
for these round-two captures.** They are not retroactively closed for the
round-one requests, whose bodies were never retained. Actual-response equivalence
and **captured net row-state preservation** now receive independently recomputable
artifact-level PASS results, not merely reported-assertion credit.

**V is not a universal latency winner.** On the two count-tied small workloads,
V's retained medians are **31.989819% and 59.559476% higher** than M's; its
P95/observed maxima are **57.541601% and 149.396388% higher**. Five larger/item-bearing
workloads favor V descriptively. A blanket no-latency-regression or all-workload
speedup claim fails these retained observations, even though causal attribution
of either improvements or regressions is not established.

Confidence is **high in retained bytes/rows/hash/count consistency**. This is not
trusted independent capture, source authorization, monetary-contract, transient
write, scalability, or deployment approval. Both labels match the retained
successful public payloads and preserve the captured net rows; M's efficiency
FAIL below is a declared-budget failure, not a finding of semantic failure.

## Scope, first-verdict preservation, and blinding

The only target evidence read in this round was:

`C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-retention-r2-527acf0980f8\packet`

The only prior evidence read was my own frozen first verdict:

`C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-blind-verdict-20261019T194014Z\NEUTRAL_VERDICT.md`

Its unchanged SHA256 is:

`f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa`

No first-round file was edited. This is a **new pre-unblinding addendum**, not an
overwrite or retrospective correction of the first verdict. Input/output file
hashes and the prior report hash are checked again by the freeze procedure.

No parent directory, repository, source branch/tree, key, owner report/comment,
GitHub resource, or original private input was inspected. No source identity or
cross-round label assignment is asserted. No database, network, application,
native-project work, bulk test, source change, commit, post, or subagent was used.
Only offline artifact/arithmetic code ran under the expressly approved CPython
3.13.15 executable, with `-I -S -B`, no `-O`, and no packet edits.

**Blinding limitation:** this is identity-key/source blinding, not robust
behavioral blinding. Distinctive query-count profiles are recognizable against
the earlier report, and the packet deliberately retains original row timestamps.
A fresh M/V shuffle cannot prevent behavioral association. I did not construct,
open, or use an identity/cross-round mapping or use chronology to infer identity;
the decision is based on M/V's round-two bytes and observations alone. It would
be inaccurate to call this an entirely new performance-blind first exposure
(`README.md:30-40`; `REVIEW_QUESTIONS.md:39-43`).

References below use **zero-based** row/sample/shape indices. `M#/rows/5` means
`M/measurement.json#/rows/5`; `V#` is analogous. The external machine report has
full pointers and paths for all responses, samples, state tables, and SQL shapes.

## 1. Packet integrity and complete retention — PASS

The input `SHA256SUMS.txt` exactly matches the supplied anchor:

`dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64`

All **386 covered files** hash correctly. The packet inventory contains exactly
those files plus the manifest: **387 files**, no unmanifested/missing files,
duplicate manifest names, symlinks/junctions or reparse points. All 381 JSON files
were strictly parsed with duplicate object keys and non-finite JSON constants
rejected. All referenced artifacts are inside the packet and in the manifest;
all 378 body/table artifacts are referenced. The remaining eight covered files
are two measurements, the equivalence document, three instructions, and two
offline verifier scripts.

| Retained object | Audited total | What it means |
| --- | ---: | --- |
| Anonymous variants | 2 | M and V only; source identities withheld |
| Workload records | 14 | Seven declared workloads in each variant, exact ordered grid |
| Warmup response records | 28 | Two per record, each now linked to actual body bytes |
| Timed response records / timing samples | 140 / 140 | Ten per record, all samples retained in order |
| All received-response records | 168 | 84 M + 84 V, not 168 distinct body files |
| Raw-body files | 14 | One content-addressed raw file per workload/variant, referenced twelve times |
| Actual canonical-body files | 14 | Separately retained from raw and expected bodies |
| Expected-body files | 14 | Each rehashed and canonical-byte checked |
| Full per-table snapshots | 336 | 14 records × 2 phases × 12 declared authoritative tables |
| Reconstructed aggregate states | 28 | Hash body reconstructed from complete table arrays, no aggregate file required |
| Snapshot row instances | 11,728 | Includes repeated before/after/variant instances, not unique production rows |
| Retained SQL-shape entries | 58 | 25 M + 33 V, not executed-query totals |

The packet's reviewed standard-library verifier completed with exit code 0.
Its exact stdout is retained as `packet_verifier.stdout.json` (841 bytes,
SHA256 `a16f5beace65ce145e301b8789d9d8611f1d2cacd056ec9c6d731b849041a23b`);
stderr is retained and empty. `packet_verifier_execution.json` records the exact
approved executable/flags, timestamps, exit status and output hashes.

The independent `independent_audit.py` neither imports nor reuses the supplied
verifier's functions. It separately checks inventory, all file/descriptor hashes,
strict JSON, full actual-response canonical bytes, public field sets, table rows,
aggregate hashes, cross-variant differences, observable fixture semantics,
every timing/count summary, budgets derived from actual visible IDs, and exact
SQL text/placeholder sequences. The independent audit completed at
`2026-10-19T20:11:29.345099+00:00`.

No missing/hash-only required artifact was found. The aggregate hash is not a
missing-body defect: its canonical body is fully reconstructible from all twelve
retained table files under the documented representation (`METHOD.md:99-112`).

Limits: all declared event records are internally retained; the files do not
prove that no previous run/event was omitted, that each reference was genuinely
captured at its claimed execution point, or that the original database contained
no rows/tables omitted by the capturer. Hashes anchor the received packet, not a
third-party attestation of original execution or complete schema coverage.

## 2. Received-response equivalence — PASS for every retained event

For **each of 168 response descriptors**, not just one per workload, I checked:

1. Retained integer status 200; exact raw artifact path, bytes and SHA256 agree
   with both descriptor and manifest.
2. Raw JSON is the complete envelope `{"trades": [...]}` with no extra top-level
   fields, duplicate keys or non-finite constants. Every nested trade/item field
   set is checked, not an extraction that discards unknown fields.
3. Canonicalization preserves the full envelope and every nested array, sorting
   only the top-level trades by ID plus JSON object keys. Serialization is
   UTF-8, sorted keys, compact separators, `ensure_ascii=True`, `allow_nan=False`,
   with no newline (`METHOD.md:65-83`).
4. Reconstructed canonical **actual bytes** equal the saved canonical actual
   file bytes and the separate retained expected-file bytes. Both file hashes
   reproduce; equality is not inferred from expected fingerprints or flags.
5. Recomputed actual-hash sets equal measurement and equivalence metadata. All
   24 responses in each M/V workload pair have identical canonical actual bytes.

The raw hash sets also match across M/V for all seven pairs; in this packet there
is one raw body per variant/workload. Raw and canonical files are separately
verified even when byte lengths coincide: equal lengths are not byte equality.
Content-addressed deduplication is not missing retention. It also is not 168
independently authenticated captures: the event-to-body associations remain
capture-provenance claims, not signed or externally witnessed receipts.

| Row / workload | Actual canonical SHA256 (both labels; all 24 records) | Canonical bytes |
| --- | --- | ---: |
| 0 / `(0,0)` | `f771460c52dcc981b042605bb698fa708e379f61b47a8739ebf976b4401738cd` | 13 |
| 1 / `(1,0)` | `08bca430de63bc3080c7d34da1733e50b5d586fe21eccb450d2a7f7dfdcf5dc4` | 533 |
| 2 / `(1,2)` | `d916e390faf016ded1772727c7ecd1256824eb160a882bf62d9aa8cc0c46412b` | 1,997 |
| 3 / `(10,1)` | `6d5c6fbd77490d8beb68bd9180b544df36c32bc953cddccbcad3366185b26e34` | 12,545 |
| 4 / `(40,1)` | `95e5b462050c402fb59ac4fa52de06c93bbe8fc0c61b43e04426609243da4010` | 50,205 |
| 5 / `(40,20)` | `b404b245c8aa93b5cdec2b64bc00190f9698d8256c28c0d855d959678647f6db` | 607,857 |
| 6 / `(501,0)` | `8bbf30baca3b1e0d3f25f011c0b94d727946b3496037f1941d1664d24c4a823b` | 264,658 |

Example traceable receipt: `V#/rows/5/samples/0/response/raw` resolves to
`V/workloads/05-40-20/responses/<raw-sha256>.json`; its canonical descriptor points
to `V/workloads/05-40-20/canonical-responses/b404b245c8aa93b5cdec2b64bc00190f9698d8256c28c0d855d959678647f6db.json`.
The separate expectation is `V/workloads/05-40-20/expected-response.json`.
The machine report records the literal raw hash/path and every other descriptor,
including both warmups. No body hash is substituted for an expected fingerprint.

### Observable semantics checked against retained rows

The evidence is now stronger than merely matching a fixture blob. For both labels
and all seven workloads, I independently compared the agreed public body with
the retained before-state rows:

- The unique fixture player named `Viewer` has exactly the returned participant
  trade set. One hidden unrelated trade exists in **every** snapshot, including
  `(0,0)`, and is absent from every public body. Zero visible trades is not an
  empty-database control.
- Trade IDs, participants, revision, state, confirmations and stored offers match
  their rows. Offer/confirmation array order is preserved. `offer_items` IDs
  follow stored offer order exactly; item pattern seeds are in the reversed
  fixture construction order. At `(40,20)`, all 1,600 offered IDs are present in
  the right public arrays; this is actual output coverage, not SQL-shape inference.
- Both participant display names match current snapshot player rows. Item IDs,
  definition IDs, rarity, pattern seeds, variants and acquired-at fields match
  item rows. Display names/collection/kind/eligibility and wear serialization are
  fully equal to the retained expectation; catalog/eligibility rule source is
  not supplied, so their universal rule correctness is not independently proven.
- Every public trade has exactly `a`, `b`, `confirmations`, `id`, `names`,
  `offer_items`, `offers`, `revision`, `state`. Public item field sets are checked
  in the machine report; no player password/token/credits fields or internal
  item owner/reservation/consumed fields appear as extra fields in these bodies.
- Viewer position is both sides on multi-trade fixtures: 20/20 at forty trades,
  251/250 at 501. The latter contains 167 each open/completed/cancelled trades.

These facts establish retained-fixture scoping/order/metadata observations, not
universal participant authorization. Bearer headers/raw tokens are not retained,
so the request's authenticated principal is not independently reconstructed from
an original request. There are no outsider/expired/inactive/unauthenticated
requests, malformed/legacy/duplicate/missing references, failure-path responses,
or metadata-change-between-requests controls. Equal static metadata does not
prove refresh/invalidation behavior after changes. Top-level trade order is
explicitly unspecified; normalization is not proof of an ordering contract.

## 3. Captured net authoritative row-state preservation — PASS, bounded

Every before/after table file is a canonical full array of row objects, with
matching row count and SHA256. Each array's row ordering reproduces under its
canonical-row-byte sort. Unique retained row identities are checked. The
aggregate canonical object mapping all twelve table names to complete arrays is
reconstructed and hashed independently, not inferred from per-table hash strings.
All per-table and aggregate before/after bytes/rows are equal within every
workload, agreeing with the recorded `read_only` flag.

Example: `M#/rows/5/state_before` and `/state_after` both reconstruct aggregate
`6fb1481a26542bb9055e14c468d1132cac4b66920e9199f9abd3e4114ca9c62c`.
The V counterparts both reconstruct
`9810904983605577e65cb4040ef25a0bbde3681aaf2d9d7711ca007ccdb2dfee`.
The input table bodies are directly under
`M/workloads/05-40-20/state/{before,after}/<table>.json` and the corresponding V
paths. The machine artifact preserves every per-table digest/count/path and all
28 aggregate digests.

The following counts hold for both labels and for **each** phase:

| Row / workload | Players | Sessions | Trades (includes hidden) | Items | Eight other tables |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 / `(0,0)` | 3 | 2 | 1 | 0 | all empty |
| 1 / `(1,0)` | 4 | 2 | 2 | 0 | all empty |
| 2 / `(1,2)` | 4 | 2 | 2 | 4 | all empty |
| 3 / `(10,1)` | 13 | 2 | 11 | 20 | all empty |
| 4 / `(40,1)` | 43 | 2 | 41 | 80 | all empty |
| 5 / `(40,20)` | 43 | 2 | 41 | 1600 | all empty |
| 6 / `(501,0)` | 504 | 2 | 502 | 0 | all empty |

The eight always-empty tables are **audit, game_tickets, ledger, listings,
loadouts, operations, rate_buckets and rewards**. Players have zero credits and
XP, active accounts and unusable password markers. There are **236 empty-array
snapshot files**: 224 from those eight tables and 12 from item-free workloads.
They genuinely prove retained empty-to-empty equality and no *net retained*
insertion into those tables over these intervals. They do **not** exercise
populated monetary ledgers, operations/receipt histories, audit chains, retry
fingerprints, nonzero wallet conservation, replay, expected-price behavior,
foreign-key interactions or reward/loadout state. An empty ledger and all-zero
balances are not evidence that transfers conserve money.

### Cross-variant differences are not within-run mutation

I compared all full before-state tables across M/V, matching sessions by
`token_hash` rather than assuming canonical row order aligns identities. All
eleven non-session tables match byte-canonically in every pair. The session row
identities/counts match; **only `sessions.expires_at` differs**. The equivalence
document's table and differing-column metadata reproduces exactly for all seven
rows. Consequently M/V aggregate hashes differ, as expected from independently
seeded expiry times (`METHOD.md:106-112`). No timestamps were redacted or normalized
to manufacture aggregate equality. Their differing seed times do not constitute
net mutation within either run, nor are the seeds bit-identical across labels.

### What the state PASS explicitly does not mean

Snapshots bracket two warmups plus ten timed requests for each workload; there
are no per-request state snapshots. Equality constrains the **net row state over
that whole interval**, not each instant or each request in isolation. It cannot
exclude a write followed by rollback/restoration, an inserted-then-deleted row,
sequence consumption, schema changes, non-ORM tables, external side effects,
uncommitted effects or concurrent activity. A reported SELECT-only callback
assertion and the last request's simple SELECT shapes help but are not a
complete DB-side execution log or proof that no SELECT-invoked side effect ever
occurred. The packet does not independently enumerate the original database
schema or establish that the declared twelve tables exhaust all authority.

These are parsed PostgreSQL JSON row arrays. Their bytes and net equality are
auditable; original PostgreSQL row-string equality is additionally reported by
`read_only`, not independently reproduced as raw original strings. No universal
read-only, transactional consistency, concurrent-writer, sequence or production
state guarantee is inferred (`METHOD.md:114-118`).

## 4. SQL work and both batching boundaries — V PASS; M FAIL on budget

All 140 timed counts are positive integers and agree with their sorted query-count
sets. Counts are identical across all ten timed samples of each record. Budgets
were recomputed from **actual visible offered item IDs and participant IDs**,
independently checked against the fixture formulas, not accepted from metadata.

| Row / workload | Unique offered items / participants | Budget | M executed | V executed | V fewer | Reduction |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 / `(0,0)` | 0 / 0 | 3 | 3 | 3 | 0 | 0% |
| 1 / `(1,0)` | 0 / 2 | 4 | 4 | 4 | 0 | 0% |
| 2 / `(1,2)` | 4 / 2 | 5 | 8 | 5 | 3 | 37.500000% |
| 3 / `(10,1)` | 20 / 11 | 5 | 33 | 5 | 28 | 84.848485% |
| 4 / `(40,1)` | 80 / 41 | 5 | 123 | 5 | 118 | 95.934959% |
| 5 / `(40,20)` | 1600 / 41 | 8 | 1643 | 8 | 1635 | 99.513086% |
| 6 / `(501,0)` | 0 / 502 | 5 | 504 | 5 | 499 | 99.007937% |

The largest deterministic gap is **1,635 callbacks avoided per request** at row
5. M has 23,180 timed callbacks in total versus V's 350. That equal-sample workload
sum is not a production mix, QPS, workload-independent cost ratio or replicated
independent-host estimate. V meets all seven budgets; M misses five. The common
budget is an acceptance target, not itself an observation.

All 58 retained shape strings match exact SELECT templates and their placeholder
sequences, including full untruncated 500-placeholder text. The common session,
account and participant-OR trade queries are identical in both labels. V adds
item-ID and narrow `players.id, players.display_name` IN queries. M's item shape
is primary-key lookup; its player shape can repeat for account and partner reads.
Full player-column loading, including unusable fixture password markers, is not
itself a public data leak; actual field sets above are separately checked.

| Row | M shapes / executed | V shapes / executed | V unique enrichment shapes by placeholders |
| --- | ---: | ---: | --- |
| 0 | 3 / 3 | 3 / 3 | none |
| 1 | 3 / 4 | 4 / 4 | participants 2 |
| 2 | 4 / 8 | 5 / 5 | items 4; participants 2 |
| 3 | 4 / 33 | 5 / 5 | items 20; participants 11 |
| 4 | 4 / 123 | 5 / 5 | items 80; participants 41 |
| 5 | 4 / 1643 | 6 / 8 | items 500 and 100; participants 41 |
| 6 | 3 / 504 | 5 / 5 | participants 500 and 2 |

- Item-heavy row 5: `V#/rows/5/sql_shapes/3` contains exactly 500 placeholders;
  shape 4 contains 100. With 1,600 distinct offered IDs and eight callbacks, this
  is consistent with `500/500/500/100` item batches, one 41-participant batch and
  the common three. Three repeated 500-sized executions would deduplicate to one
  shape. **Six unique shapes do not mean six executed queries.**
- Participant-heavy row 6: `V#/rows/6/sql_shapes/3` and `/4` contain exactly 500
  and 2 placeholders, consistent with the 502 actual participant IDs and five
  callbacks. There are no items to confound that participant boundary.

The actual bodies now verify complete fixture output at both boundaries, but
`sql_shapes` still comes **only from the final timed request**. Bound IDs, exact
per-table multiplicities and complete per-request SQL traces are not retained
(`METHOD.md:46-51`). The batching execution decomposition is supported, not
independently reconstructible as a trace. M's counts fit
`3 + trades + unique_items`; V's fit
`3 + ceil(unique_items/500) + ceil(unique_participants/500)`.

No exact 499/500/501 unique-ID sweep, repeated-partner/item, missing/deleted object,
or simultaneous crossing of both enrichment boundaries exists. Callback reductions
are substantive SQL round-trip work reduction, not timing noise, but do not
directly measure plans, logical reads, CPU, total rows fetched or allocated memory.

## 5. Actual timing arithmetic and regressions

All 140 durations are finite/nonnegative. All fourteen medians and nearest-rank
P95s reproduce, with machine-retained sample order and sorted order statistics.
For ten samples P95 selects rank ten: **the maximum**, not a well-resolved tail
estimate. Rounding below is for display only. Positive V-minus-M percentages
mean V is slower; all ratios/deltas are descriptive.

| Row / workload | M median ms | V median ms | V − M median ms | V median change |
| --- | ---: | ---: | ---: | ---: |
| 0 / `(0,0)` | 7.85750 | 10.37110 | +2.51360 | **+31.989819%** |
| 1 / `(1,0)` | 9.35250 | 14.92280 | +5.57030 | **+59.559476%** |
| 2 / `(1,2)` | 16.03505 | 11.50260 | -4.53245 | -28.265893% |
| 3 / `(10,1)` | 54.09165 | 17.03545 | -37.05620 | -68.506322% |
| 4 / `(40,1)` | 202.74730 | 25.56070 | -177.18660 | -87.392828% |
| 5 / `(40,20)` | 1657.12235 | 126.97365 | -1530.14870 | -92.337702% |
| 6 / `(501,0)` | 942.17180 | 65.03265 | -877.13915 | -93.097581% |

| Row | M P95/max ms | V P95/max ms | V max change | M/V max sample indices |
| --- | ---: | ---: | ---: | --- |
| 0 | 8.7919 | 13.8509 | **+57.541601%** | 8 / 5 |
| 1 | 10.8182 | 26.9802 | **+149.396388%** | 5 / 0 |
| 2 | 19.1847 | 13.0818 | -31.811287% | 1 / 4 |
| 3 | 66.6315 | 23.7704 | -64.325582% | 8 / 6 |
| 4 | 292.4239 | 54.0613 | -81.512694% | 2 / 6 |
| 5 | 1827.2075 | 209.8501 | -88.515256% | 6 / 0 |
| 6 | 2704.7057 | 157.8235 | -94.164855% | 1 / 3 |

The regression maxima are specifically `V#/rows/0/samples/5` and
`V#/rows/1/samples/0`. Do not drop them or average away the empty/small workload
regressions. Conversely, M's `M#/rows/6/samples/1 = 2704.7057 ms` remains in its
summary. In the five count-improved workloads, V's largest sample is smaller
than M's smallest; this strengthens the observed separation but does not fix the
experimental design. Row 5's descriptive median ratio `M/V = 13.050915` and row
6's `14.487673` are **not** causal/production speedup estimates.

All seven workloads of one variant preceded all seven of the other, with no
interleaving, randomized alternation, host isolation or concurrent-load experiment.
The shared PostgreSQL service could host another coordinating workload in a
different database (`METHOD.md:12-19`). Even isolated fixture databases do not
isolate service CPU, disk/cache, pool or host scheduling contention.

Timing brackets the in-process FastAPI TestClient call to real loopback
PostgreSQL. Parsing, equality assertions and artifact writes are afterward;
setup/snapshots are outside counting/timing. Artifact writes *between* requests
may still alter cache and scheduling. Fresh application ORM sessions and two
warmups do not make ten sequential samples independent production replications.
The count-tied latency differences especially cannot be attributed to fewer SQL
calls. Both positive and negative latency differences need controlled follow-up
before causal attribution. Reject population P95/P99, SLO, throughput/QPS,
external HTTP/network, production, cold-start, concurrent-load and guaranteed
all-size latency conclusions.

## 6. What r2 resolves versus the preserved first verdict

| Earlier finding | Round-two disposition |
| --- | --- |
| Expected hashes only; missing actual received payloads/digests | **CLOSED for r2's 168 event records.** Raw bytes, actual canonical bytes and separate expected bodies independently match. Original r1 captures remain unauditable. |
| Missing authoritative snapshots and independently recomputable state hashes | **CLOSED for r2 net row equality in fourteen captured intervals.** All tables and aggregates reproduce. Not transient-write or universal authority safety. |
| Warmups described but not raw retained | **CLOSED for r2.** All 28 warmup descriptors resolve to received body bytes/status. |
| Claimed successful fixture privacy/order/current metadata | **Stronger direct evidence.** Actual fields/orders/scoping also compare with retained player/item/trade rows. Still no adversarial authorization or metadata-mutation control. |
| Missing full SQL traces/bound IDs | **OPEN.** Counts/last-request shapes and complete output support batching, but do not reconstruct every SQL execution. |
| Latency generalization and all-workload speedup | **OPEN; all-workload improvement contradicted here.** Both small workloads regress descriptively for V. |
| Source/capture provenance | **OPEN / NOT EVALUATED.** Source/runtime/fixture identities and source-bound capture evidence remain outside packet. |
| Populated wallet/ledger/receipt/exact retry/expected-price contracts | **NOT EVALUATED.** Empty operations/ledger/audit/history tables and zero balances do not exercise them. |
| Transient writes, schema/sequences/external effects/concurrency | **OPEN.** Before/after net-row equality does not address these dimensions. |
| Unbounded history/production memory/plans/load | **OPEN.** No pagination or representative resource measurements. |

"Receipt retention closed" here means **received HTTP-body/state evidence**, not
monetary operation receipts. No transaction-receipt, idempotency, wallet or replay
acceptance is smuggled into that wording. The first verdict stays unchanged; the
new PASS findings attach to new retained evidence, not retroactively authenticated
old runs or inferred source identities.

## 7. Remaining risk and smallest decisive falsifiers — not performed

### Most consequential remaining trust limit

The packet now permits a real retained-data audit, but capture and source
provenance are still asserted rather than independently authenticated. The method
claims frozen matching routines, fixture identities and backend runtime-reference
checks (`METHOD.md:5-10`); their exact source/commit/tree/routine/fixture identities
are withheld. Self-consistent artifacts could still be misattributed or produced
by an incorrect capture routine. Passing both verifiers does not turn them into
an independent witness of which implementation served each response.

**Smallest source-attribution falsifier:** only *after* this verdict is frozen,
bind each anonymous measurement's exact input hash to the externally retained
runtime/source/routine/fixture hashes and capture record. A single mismatch
falsifies the claimed attribution, not the arithmetic of the packet. Preserve
the verdict and document that result separately; no key was requested/opened
or source check performed in this task.

### Most consequential untested behavioral extension

General read-path safety against populated monetary/receipt history and
adversarial authorization remains untested. A small decisive future control
would use one source-bound isolated fixture with nonzero balances, populated
ledger/operations/receipt/audit rows and an unrelated participant's private trade,
then issue one valid authenticated **nonparticipant** GET per implementation.
Retain its actual request/response capture and full authoritative before/after
rows with independent hashes; check for an empty permitted trade set, no private
fields and no net authoritative mutation. A single leaked trade/private field or
net row change falsifies that proposed extension. A passing case would not prove
write-path wallet conservation, expected-price/retry contracts or universal
privacy. Those need separate adversarial/write-path evidence.

If the claim is specifically **absence of transient writes**, the smallest
decisive evidence must additionally observe DB-side execution/events for that
request, including effects rolled back or restored; another pair of equal row
snapshots is not a test of that claim. No such run/event capture was performed.

### Remaining performance-scope risk

Both retained trade queries are unpaginated: no LIMIT/OFFSET in the SQL shapes.
500-ID batches bound individual IN lists, not total history, response bytes,
serialization or memory. Row 5 already returns **607,857 bytes** for forty
item-heavy trades; row 6 returns **264,658 bytes** for 501 item-free trades.
Neither tests a very large item-bearing history, a large underlying table, query
plans, peak allocations or concurrency. A controlled large-history item-bearing
case measuring rows/plans/response size/peak memory could falsify unbounded-scaling
claims. Randomized alternating repeated runs under isolated load are separately
needed to attribute small-history timing regressions. These are proposed tests,
not work run or implicitly authorized here.

## 8. Acceptance ledger, blockers and nonblocking findings

| Requested category | Status | Boundary |
| --- | --- | --- |
| Packet integrity | **PASS** | Supplied anchor, complete declared inventory, 168 response associations, 336 tables, all arithmetic/shapes verified; not trusted original execution. |
| Actual-response equivalence | **PASS — M and V** | All received raw bytes rehash/recanonicalize exactly to saved actual and expected; cross-variant actual bodies equal for this grid. |
| Captured net row-state preservation | **PASS — M and V** | Full retained before/after arrays, per-table hashes and aggregates equal in all fourteen intervals; no transient/universal state claim. |
| Measured query efficiency | **PASS — V; FAIL — M** | V wins five/ties two/no callback regression, meets all budgets; M misses five budgets. |
| Latency generalization | **NEEDS MORE EVIDENCE** | Five descriptive improvements, two descriptive regressions for V; sequential shared-host TestClient measurements are not production/causal evidence. |
| Source/monetary-contract safety | **NOT EVALUATED** | Original sources/capture identities withheld; monetary-history tables empty; no source/adversarial/write-path audit. |

**Blockers to a stronger verdict:** source/capture attestation; negative and
populated-history controls; transient-write/sequence/schema/external coverage;
missing full traces/bound IDs; reproducible latency-regression attribution;
representative memory, plans, network and concurrent-load evidence. The new body
and net-snapshot retention gaps are **not** still blockers for this captured slice.
Do not keep them marked missing once their bodies and arithmetic verify.

**Nonblocking findings for this slice:** valid content deduplication; reproducible
cross-variant session-expiry differences; lower unique shape counts than executed
queries; floating-point median tails; P95=max; retained outliers; extra internal
player columns not present in public bodies. No internal packet contradiction,
missing required body, mismatched table digest, or measured semantic/net-row
failure was found. Do not confuse absence of evidence for wider contracts with
an observed failure of those contracts.

| Broader gate | Status |
| --- | --- |
| human | **UNVERIFIED** |
| device | **UNVERIFIED** |
| 8.5 | **UNVERIFIED** |
| production | **UNVERIFIED** |
| concurrent load | **UNVERIFIED** |
| unbounded history | **UNVERIFIED** |

Final decision: **ACCEPT WITH QUALIFICATIONS — V preferred only for the narrow
retained successful response/net-state/query-efficiency slice.** High confidence
in internal retained-artifact verification; no broad source/monetary/production
acceptance and no universal latency win.

## External evidence, hashes and pre-mapping freeze

All new files are in the separate external directory:

`C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-retention-blind-verdict-20261019T200657Z`

- `NEUTRAL_RETENTION_VERDICT.md`: this detailed neutral addendum.
- `per_workload_judgments.json`: all fourteen workload judgments, 168 individual
  response receipt references with byte/hash checks, all table/aggregate hashes,
  140 samples, exact SQL-shape hashes, per-label timing improvements/regressions,
  cross-variant comparisons and the first-round gap-resolution ledger.
- `input_hashes.json`: exact path/byte length/SHA256 for all 387 packet files,
  strict parsing/coverage counts, and the preserved prior verdict hash.
  Original source/commit/tree/routine/fixture hashes are explicitly unavailable,
  not guessed from result hashes.
- `packet_verifier.stdout.json`, `packet_verifier.stderr.txt`,
  `packet_verifier_execution.json`: raw verifier output and exact execution receipt.
- `independent_audit.py`, `freeze_artifacts.py`: the independent offline procedures.
- `FROZEN.json`: fresh UTC, neutral decision, explicit gates, input/prior anchors
  and each external payload's SHA256/byte length.
- `SHA256SUMS.txt`: hashes every other external artifact, including `FROZEN.json`,
  and excludes itself; its externally returned SHA256 is the freeze anchor.

Frozen files receive a best-effort Windows read-only attribute. Hash anchors and
the refusal to rerun into a frozen output protect the pre-mapping record, not
absolute WORM immutability or trusted time. This is a local UTC/hash freeze, not
a third-party timestamp or signature. **Preserve it and the first verdict
unchanged.** Any later source binding, identity disclosure, changed judgment or
new evidence belongs in a separately named post-unblinding addendum citing these
hashes, never a retrofit to either frozen verdict.
