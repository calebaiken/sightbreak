# NEUTRAL — frozen pre-unblinding critique

## Decision first

**ACCEPT WITH QUALIFICATIONS for the narrow retained measurement slice; prefer anonymous K.**

K wins the executed-SQL-statement criterion, not merely a timing contest: it has
strictly fewer recorded statements in five of seven workload pairs, ties in two,
and regresses in none. Every one of the ten timed samples in each record has the
same count. The largest reproducible *arithmetic* gap is **1,643 → 8 statements
per request at `(40,20)`: 1,635 fewer, or 99.513086%**. At `(501,0)`, the gap is
**504 → 5: 499 fewer, or 99.007937%**. Both enrichment dimensions have meaningful
cross-500 evidence. These are recomputations of retained observations, not a new
application execution or a source-level proof.

**Neither label independently clears the entire semantic/state-safety bar from
this packet.** Matching hashes are hashes of expected fixtures, not captured
actual responses. All authoritative before/after hashes are null/not_retained.
The documented successful equality assertions support the measured outcomes,
but cannot be independently replayed here. The qualification is substantive:
this is not broad performance, correctness, monetary-contract, deployment, or
production acceptance. If the decision requires independently auditable actual
responses and authoritative snapshots as a prerequisite, the decision is
**NEEDS MORE EVIDENCE for both**, not an unconditional acceptance of K.

Confidence is **high for the retained count ordering and arithmetic**, conditional
on reported methodology for successful response/state checks, and insufficient
for population latency, source safety, or production generalization.

## Evidence and blinding boundary

- The only supplied input directory inspected was
  `C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-read-f12a80a71bbd\packet`.
  This report's own external output directory is not additional target evidence.
- Review began with `README.md` and `REVIEW_QUESTIONS.md`. No repository, GitHub,
  branch, mapping/key, original/private inputs, owner report, or surrounding
  source directory was opened. No identities were requested or inferred.
- No application, database, native test, bulk test, Python, source edit, commit,
  post, or delegated agent was executed. Independent arithmetic and byte hashing
  used PowerShell/.NET only. The packet's `verify_packet.py` was read, not run.
- The successful independent audit was generated at
  `2026-10-19T19:43:21.6275673Z`. The later fresh freeze UTC is recorded in
  `FROZEN.json`; that artifact is the freeze event, not the directory name.
- Measurement-runtime versions are the *recorded* common environment, including
  Python 3.12.14 and PostgreSQL 17.11, not a newly reproduced runtime. The routine
  and fixture source/fingerprints are not in this packet (`METHOD.md:5-9`).

References below use **zero-based JSON row/sample/shape indices**. For example,
`K#/rows/5/samples/0` means
`K/measurement.json#/rows/5/samples/0`. The machine artifact gives full pointers
for all fourteen records, all 140 samples, and all 58 retained shape entries.

## 1. Integrity and arithmetic — PASS within the supplied anchor

The supplied manifest SHA256 is exactly:

`d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36`

All seven manifest-covered files match. Recursive packet inventory, including
hidden entries, contains exactly those seven files plus `SHA256SUMS.txt`; there
are no extra/missing files, duplicate manifest entries, or packet reparse points.
The three JSON documents have no duplicate object keys. Both variant environment
records agree. The fourteen workload records match the declared ordered grid
exactly, with **10 timed samples each = 140 retained timed samples**. Two warmups
per record are *stated*, not retained as raw observations: 28 additional requests
are described by the method, not an additional 28 independently auditable samples.

The independent `audit_packet.ps1` checks every timing is finite/nonnegative,
every count is a positive integer, each query-count set, each ordinary median,
each nearest-rank P95, all budgets, all equivalence references, and every complete
retained SQL string including sequential placeholder names. Sorting is also
cross-checked against an independent numeric-duration sort. All checks pass.
Recorded binary floating-point medians reproduce; their long decimal tails are
not contradictions. Human tables below round only for display.

For all fourteen records, `ceil(10 × .95) = 10`, so P95 is **the maximum retained
sample**, not a fitted population tail or confidence bound (`METHOD.md:41-44`).
The machine artifact retains all sorted order statistics and median components.

| Row / workload `(trades, items/side)` | K median ms | R median ms | K P95/max ms | R P95/max ms | K/R P95 sample indices |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 / `(0,0)` | 10.61035 | 12.74365 | 12.4832 | 14.3006 | 5 / 4 |
| 1 / `(1,0)` | 13.09705 | 14.50690 | 14.0893 | 17.1316 | 7 / 6 |
| 2 / `(1,2)` | 17.18585 | 23.61450 | 18.9844 | 44.4686 | 3 / 0 |
| 3 / `(10,1)` | 21.04595 | 66.73300 | 22.6162 | 98.3006 | 8 / 2 |
| 4 / `(40,1)` | 33.62525 | 220.83345 | 64.6221 | 295.2011 | 8 / 9 |
| 5 / `(40,20)` | 249.12310 | 3309.74890 | 369.7471 | 4141.7075 | 0 / 3 |
| 6 / `(501,0)` | 101.95485 | 1176.56865 | 177.5231 | 3303.8036 | 3 / 7 |

No missing or dropped samples are visible **relative to this declared packet**.
That does not prove no earlier workload, failed run, or original measurement was
excluded before packet construction. Completion/database-dropped fields are
recorded true, not independently authenticated execution or cleanup evidence.
Byte integrity proves consistency with the supplied anchor, not measurement
authenticity, random label assignment, or controller provenance.

## 2. Deterministic efficiency — K PASS; R FAIL on the stated budget

Every count in this table applies to **all ten timed samples**, not just a mean
or the final request. The budget is a common declared threshold, not measured
work. It independently recomputes as
`3 + ceil(unique_items/500) + ceil(unique_participants/500)`.

| Row / workload | Unique items / participants | Common budget | K statements | R statements | Saved by K | Percent fewer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 / `(0,0)` | 0 / 0 | 3 | 3 | 3 | 0 | 0% |
| 1 / `(1,0)` | 0 / 2 | 4 | 4 | 4 | 0 | 0% |
| 2 / `(1,2)` | 4 / 2 | 5 | 5 | 8 | 3 | 37.500000% |
| 3 / `(10,1)` | 20 / 11 | 5 | 5 | 33 | 28 | 84.848485% |
| 4 / `(40,1)` | 80 / 41 | 5 | 5 | 123 | 118 | 95.934959% |
| 5 / `(40,20)` | 1600 / 41 | 8 | 8 | 1643 | 1635 | 99.513086% |
| 6 / `(501,0)` | 0 / 502 | 5 | 5 | 504 | 499 | 99.007937% |

K meets the budget on all seven workloads; R meets it only on rows 0 and 1.
Across the deliberately equal-sized retained workload samples there are 350 K
callbacks versus 23,180 R callbacks, 23,530 combined. This aggregation is **not** a
production-weighted workload, throughput rate, or independent replication count.

K's observed counts fit the budget exactly. R's counts fit
`3 + trades + 2 × trades × items_per_side`. This is strong observational evidence
of avoiding repeated per-item/per-partner work; without source and full traces,
the per-table execution multiplicities remain an interpretation, not directly
retained facts. The *total* callback reductions themselves are directly retained
and do not depend on that interpretation or on host timing noise.

### SQL shapes and both batch boundaries

`sql_shapes` is deduplicated text from the **last timed request only**
(`METHOD.md:34-39`). It is not a query execution log. All **58 shape entries**
(33 K, 25 R) match the expected full SELECT templates. The common three shapes
are byte-identical across all records: session-token lookup, account primary-key
lookup, and a trade query with `trades.a = ... OR trades.b = ...`. No unexpected
SQL, inconsistent projection, malformed placeholder sequence, or duplicated
deduplicated shape is present.

| Row | K unique shapes / executed | R unique shapes / executed | K enrichment IN placeholder sizes retained |
| --- | ---: | ---: | --- |
| 0 | 3 / 3 | 3 / 3 | none |
| 1 | 4 / 4 | 3 / 4 | participants 2 |
| 2 | 5 / 5 | 4 / 8 | items 4; participants 2 |
| 3 | 5 / 5 | 4 / 33 | items 20; participants 11 |
| 4 | 5 / 5 | 4 / 123 | items 80; participants 41 |
| 5 | 6 / 8 | 4 / 1643 | items 500 and 100; participants 41 |
| 6 | 5 / 5 | 3 / 504 | participants 500 and 2 |

- **Item boundary:** `K#/rows/5/sql_shapes/3` has 500 placeholders and shape 4
  has 100, not 1,600. With 1,600 unique items and eight total statements this is
  consistent with four item batches `500/500/500/100`, one 41-participant batch,
  and the common three. The three 500-sized executions would deduplicate into
  one shape. There are **six shapes, not six executed statements**. Bound IDs
  and individual shape execution multiplicities were not retained; disjoint,
  complete item coverage cannot be reconstructed from these shapes alone.
- **Participant boundary:** `K#/rows/6/sql_shapes/3` and `/4` contain 500 and 2
  placeholders. There are 502 participants including the viewer, no items, and
  five total statements. R records 504 with only three shapes; its account and
  participant reads can reuse the same player primary-key SQL text. There is no
  contradiction in that deduplication.
- K participant-enrichment projections are only `players.id, players.display_name`.
  R has the full player primary-key projection already used for the account,
  including password hash/credits/etc. This is evidence about data *loaded*, not
  proof those extra columns are returned or leaked. Both labels retain the same
  item-field projection; fewer calls are not an excuse for dropping fields.

Boundary coverage is meaningful but incomplete: there are no exact 499/500/501
unique-ID sweeps, repeated-partner/item-ID cases, or a single workload crossing
both enrichment boundaries simultaneously. The budget is not O(1) for arbitrary
history. Fewer callbacks do not quantify database CPU, logical reads, bytes,
plans, or total rows materialized.

## 3. Timing confidence — descriptive only

K has lower retained medians and maxima in all seven pairs. In the five strictly
count-improved pairs, even K's largest sample is below R's smallest. For example:

- `(40,20)`: K 236.5004–369.7471 ms, R 2854.5519–4141.7075 ms; median ratio
  `R/K = 13.285596`. The endpoints are `K` samples 1/0 and `R` samples 2/3.
- `(501,0)`: K 90.1573–177.5231 ms, R 740.3392–3303.8036 ms; median ratio
  `R/K = 11.540095`. The endpoints are `K` samples 6/3 and `R` samples 5/7.
- Keep the outliers: `K#/rows/4/samples/8 = 64.6221 ms` and
  `R#/rows/6/samples/7 = 3303.8036 ms` are retained, not silently removed.

These are large observed separations, consistent with the count improvement,
but they are **not controlled causal speedup estimates**. There are only ten
sequential samples per record, after two warmups; independent runs were not
interleaved, execution order/absolute timestamps are withheld, and host load was
uncontrolled (`METHOD.md:11-16`). The empty-history control has identical three
SQL calls yet differs by a descriptive median ratio of 1.201058; common runtime,
order, or implementation overhead effects are not isolated by this design.

Timing is an in-process TestClient call through loopback PostgreSQL, with a new
ORM Session, not external HTTP serving. Fixture/snapshot queries, driver pool
pings, protocol messages, and the post-timer JSON assertion are excluded
(`METHOD.md:23-39`). Reject population P95/P99/SLO, throughput/QPS, cold-start,
concurrent-load, production-network, scalability, and precise causal-speedup
claims. No significance test or average of these runs repairs that design.

## 4. Equivalence and authoritative-state proof

All seven `equivalence.json#/rows/0..6` expected-digest pairs agree with the
corresponding K/R `response_sha256` values, and all seven equality flags are
internally correct. **These are expected-fixture fingerprints.** Actual response
bodies, actual-response digests, and expected bodies are absent; the expected
digest cannot even be independently recomputed from a retained payload here.
Two copies of the same expected hash are not independently captured actual-body
proof (`README.md:25-28`; `METHOD.md:53-66`).

The documented routine asserts status 200 and complete equality to the expected
canonical fixture response after every warmup and timed request. Reported
completion therefore adds substantive successful-fixture evidence beyond hash
equality, conditional on the routine description and provenance. The actual
measurement routine is withheld; its assertions are described, not source-audited
or re-executed in this review. Canonicalization sorts the top-level trade list
and object keys, **not** nested offer/confirmation arrays. Top-level response
ordering differences can be erased; nested stored offer order is said to remain
significant.

All fourteen `read_only` values are true, and the equivalence file accurately
copies them. The method describes full sorted row snapshots of these twelve ORM
tables before warmup and after all measured requests: players, sessions, ledger,
items, operations, audit, listings, trades, rewards, rate_buckets, game_tickets,
loadouts (`METHOD.md:68-91`). This is useful **reported before/after net-state
equality**, supported by the routine's reported SELECT-only callback assertion.

However, `K/measurement.json:20-24` and `R/measurement.json:20-24` both have
`before: null`, `after: null`, `status: not_retained`. No snapshots exist in the
packet. Every equivalence row correctly says `not_evaluable_not_retained`.
**I cannot independently validate any authoritative-state hash or equality.
Null equals null is not state evidence.** File hashes and expected-response
hashes cannot substitute for state hashes. Even independently retained net-state
snapshots would not cover sequences, schema, non-ORM/external effects, transient
changes later undone, or concurrent behavior; these are not expanded into a
no-write or complete-authority proof here.

## 5. Contract, failure, and edge controls

Positive but bounded observations (`METHOD.md:18-24,53-66`): the fixture includes
unrelated accounts/trades; the viewer occupies both participant positions; visible
histories cycle open/completed/cancelled; stored offer order is reversed relative
to item construction; names and item metadata are deterministic. The retained
participant-OR SQL filter plus documented full successful-payload assertions
support participant scoping and preservation of nested order/fixture metadata in
those cases. Empty history, empty offers, nonempty offers, item-heavy history,
and >500 participants are genuine measured controls.

Limitations that prevent stronger conclusions:

- Bound parameters, raw responses, and fixture/source definitions are absent.
  The SQL predicate alone cannot establish that the viewer ID was bound correctly
  or that no unrelated/private data reached the response. Full player-column
  loading is not, by itself, a demonstrated response leak.
- Live item/name SELECT shapes support database-backed metadata lookup but there
  is no retained metadata mutation-between-requests control. Deterministic static
  fields do not establish refresh semantics, invalidation, or current metadata
  after deletion/ownership/metadata changes.
- No retained unauthenticated, expired-session, inactive-account, outsider,
  missing-participant/item, repeated-ID, repeated-partner, malformed/legacy-offer,
  partial-failure, concurrent mutation, or exception/rollback results exist.
  There are successful fixture controls, **not a failure-path test suite**.
- Wallet conservation, authority/revision races, expected-price checking, receipt
  fingerprints, idempotency/exact retry, and write-path monetary integrity are
  **NOT EVALUATED**. A read-only successful GET measurement cannot establish
  those contracts or that an unseen change touched only this path.

## 6. Largest gap and smallest decisive falsifier — specified, not performed

**Largest deterministic measured gap:** row 5's 1,635 avoided statements per
request. It is much stronger evidence than the descriptive latency ratios.

**Most consequential evidence gap:** semantic/state equivalence is not
independently auditable. The absent actual payloads and authoritative snapshots
are a real blocker to upgrading a conditional narrow count win into a full
semantic/authority-safety verdict. Neither a passing packet verifier nor source
identity disclosure alone supplies those missing observations.

**Smallest decisive follow-up:** after this verdict is frozen and source binding
is separately recorded, make one instrumented paired reproduction of the existing
`(40,20)` successful fixture, keeping the fixture and assertion routine unchanged.
Retain the complete expected and actual canonical payloads, actual status and
independently recomputable actual-body SHA256, full ordered before/after snapshots
and independent per-table/full-state digests for all authoritative tables, and
complete statement traces with enough synthetic bound-ID information to check
batch coverage. Keep snapshot work outside the timing/counting window. One
payload difference, authoritative net-state difference, omitted/duplicated offered
ID, unrelated payload, or incompatible repeated statement trace falsifies the
corresponding safety/batching interpretation. A differing new run does not erase
the historical retained counts; it challenges repeatability/generalization. One
passing paired case would strengthen this slice only, not prove all contracts.
**No such run was performed or requested during this task.**

Next most decisive edge evidence would independently straddle **500/501 unique
item IDs and 500/501 unique participants**, with reversed order across the cut,
duplicate IDs/reused partners, and one missing/stale referenced object. The
current uniform fixture's even item counts need not support every exact item
boundary; use a deliberately specified fixture rather than pretending row 5 is
an exact-501 test. Negative authorization controls are separately necessary.

**Largest remaining performance-scope risk:** the retained trade SELECT has no
LIMIT/OFFSET or pagination in either label, and batching bounds IN-list size, not
history length, total response size, serialization, or memory. The 501-trade case
has no items; the item-heavy case has only 40 trades. No plans, large underlying
database sizes, peak memory, or concurrent requests are retained. A separately
specified large-history item-bearing case with rows/plans/response bytes/peak
memory would challenge unbounded-scaling interpretations. Controlled randomized
interleaving and substantially more repetitions would be needed for causal
latency claims. These are future evidence requirements, not extra work done here.

## 7. Acceptance ledger and blockers

| Requested category | Status | Exact meaning |
| --- | --- | --- |
| (a) Packet integrity | **PASS** | All supplied hashes, inventory, 14 records, 140 samples, summaries and retained SQL shapes check; authenticity/provenance is not established by hashes. |
| (b) Measured query efficiency | **PASS — K; FAIL — R** | K ties twice/wins five times/no count regression; K meets all common budgets, R misses five. R's FAIL is budget failure, not a semantic failure finding. |
| (c) Latency generalization | **NEEDS MORE EVIDENCE** | Retained times are descriptive only; no population/production/causal guarantee. |
| (d) Response-equivalence evidence | **PASS** | Matching expected fingerprints plus documented complete-success assertions support this fixture evidence. Independently auditable actual-body equivalence separately **NEEDS MORE EVIDENCE**. |
| (e) Independently auditable state preservation | **NEEDS MORE EVIDENCE** | Reported snapshot equality only; all actual snapshots and state hashes absent. |
| (f) Source/monetary-contract safety | **NOT EVALUATED** | No original source, adversarial/write-path/authority/price/retry/receipt evidence inspected. |

**Blockers to broader acceptance:** missing independently auditable responses and
state; withheld source/routine provenance; missing negative/adversarial/concurrent
controls; no production-representative plans, memory, network, or load evidence.
These do not invalidate the internally verified statement-count comparison, but
do prevent treating it as an implementation/deployment approval.

**Nonblocking findings for this narrow comparison:** deduplicated shape counts
below executed counts are explained; P95=max is method-consistent; floating-point
median tails are benign; observed outliers were retained; inability to assess
broader contracts is not an observed contract failure. No internal packet
contradiction was found.

| Explicit broader gate | Status |
| --- | --- |
| human | **UNVERIFIED** |
| device | **UNVERIFIED** |
| 8.5 | **UNVERIFIED** |
| production | **UNVERIFIED** |
| concurrent load | **UNVERIFIED** |
| unbounded history | **UNVERIFIED** |

Final narrow decision: **ACCEPT WITH QUALIFICATIONS; K preferred; high confidence
in retained deterministic count advantage. No broad acceptance, no identity
inference, and no independently established full semantics/state-safety pass.**

## Packet/source hashes and freeze

`source_hashes.json` records byte lengths, expected/actual hashes, and the exact
input boundary. Here "source" means the packet inputs used to derive this
verdict. **Original application source/commit/tree/routine/fixture hashes are
withheld and intentionally unverified; they must be bound separately only after
the freeze.** No source identity is invented from a result file's hash.

| Packet path | Verified SHA256 |
| --- | --- |
| `SHA256SUMS.txt` | `d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36` |
| `README.md` | `417f3e82a97946d0560a375c415ce0bcb0afe020458ddb7cacabfa75223f806c` |
| `REVIEW_QUESTIONS.md` | `fae22533831bf7a0d315d4cbd0e1ac175c8fa52fcff6b382db85614316d31363` |
| `METHOD.md` | `d06c8f3a55b97d729f5bdb37f94c0e5b19c0eba17689016d8eb4785e7fb119a4` |
| `K/measurement.json` | `63d17ce528241f32a4b0f864c4eea83b6e7e2db42dcf2e31212cf055a2f18985` |
| `R/measurement.json` | `38d0d1f01c77f90067d10587311bd3ce9c1418e71055d44e287db4b5fa521f20` |
| `equivalence.json` | `3f80d419fc02b6d7a886540ffe61c684ea753f3e8fc705a7e6ef73a586b17632` |
| `verify_packet.py` | `babc2f4657c0002bad0129ec3373e6750119b38783d1b5bd2174adfda5322c18` |

The external artifacts are `NEUTRAL_VERDICT.md`,
`per_workload_assessment.json`, `source_hashes.json`, the independent
`audit_packet.ps1`, and `freeze_artifacts.ps1`. `FROZEN.json` records fresh UTC,
the blind decision, input anchor, explicit unverified gates, and SHA256/byte
length for each payload. The external `SHA256SUMS.txt` covers those artifacts
plus `FROZEN.json` and intentionally excludes itself. Its returned digest is the
external freeze anchor. This is a local hash/time record, **not** a trusted
timestamp, cryptographic signature, or filesystem-immutability guarantee.

Preserve these files unchanged. Any post-unblinding source binding, changed
judgment, or newly learned limitation belongs in a separate addendum, with the
original freeze hashes cited and the reason stated. Do not retrofit identities
or later evidence into this pre-unblinding verdict.
