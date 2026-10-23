# Independent backend artifact review — round two

Parent-recorded verdict returned by separate critic session
`ses_eaa5392f6ffe3mRSTEBTlVTiV8`, before controller key access. This is a
record of the critic's conclusions, not a new benchmark or full transcript.
The earlier qualified first-round verdict remains unchanged.

> V wins the declared query-count metric. The safety half is PASS/tie for both
> labels on these captured GET fixtures. No blocker remains for accepting this
> narrow measured slice.

The critic inspected only the isolated neutral packet, without mappings, source
reports, GitHub or separate PostgreSQL-suite results. Manifest pin:
`dd07a3bfd69e09e27c43257be3a719d001c5d8446a9338746460829887c86d64`.

Independently verified: 386 manifest-listed files; 14 workload records; 28 warm-ups
and 140 timed requests; all 168 raw/canonical response references and hashes;
336 full-table snapshot hashes and 28 aggregate hashes; all twelve table arrays
unchanged over 14 intervals; all counts, budgets, medians and nearest-rank P95s.
Responses deduplicate to 14 raw and 14 canonical bodies, not 168 distinct bodies.

| Trades, items/side | M statements | V statements | M median ms | V median ms |
|---|---:|---:|---:|---:|
| 0,0 | 3 | 3 | 7.858 | 10.371 |
| 1,0 | 4 | 4 | 9.353 | 14.923 |
| 1,2 | 8 | 5 | 16.035 | 11.503 |
| 10,1 | 33 | 5 | 54.092 | 17.035 |
| 40,1 | 123 | 5 | 202.747 | 25.561 |
| 40,20 | 1,643 | 8 | 1,657.122 | 126.974 |
| 501,0 | 504 | 5 | 942.172 | 65.033 |

Actual-response gap closed for these captures: the hidden trade and its unrelated
participants/names are absent from every response; returned trades exactly match
viewer membership; both viewer positions and open/completed/cancelled history are
represented. Envelope/field sets, offer IDs, hydrated item order, confirmation
arrays, current names and item metadata match retained rows. Two-item seed order
`[1,0]` and twenty-item order `[19,...,0]` survive. Completed history's transferred
owners are seeded state, not evidence of executing a transfer.

Net-row preservation gap closed for all fourteen captured intervals. Cross-label
state differs only in independently seeded `sessions.expires_at`. Eight tables
are empty (`audit`, `game_tickets`, `ledger`, `listings`, `loadouts`, `operations`,
`rate_buckets`, `rewards`); players have zero balances. Their retained equality is
not new monetary/retry/price-contract coverage. Transient reverted writes,
sequences/schema and external effects are outside these snapshots.

Qualifications: small-read latency regressed by 31.99% and 59.56% in these
measurements. Larger five count-improving workloads have lower medians/maxima,
but sequential shared-host execution, possible database contention and artifact
writes prevent universal or causal latency claims. Ten-sample P95 is the maximum.
Deduplicated SQL shapes do not independently prove bound IDs or execution
multiplicities. Static single-viewer fixtures do not test intervening metadata
updates or adversarial authentication. Capture/build provenance remains separate;
hashes verify retained-byte consistency, not independent execution attestation.
Query signatures recognizable from round one limit behavioral blinding despite
new labels; the critic did not inspect an identity key.

Biggest remaining GET scalability gap: unpaginated histories. A 500-ID batch
limits query arity, not total response size, memory or work. Suggested nonblocking
next falsifier: artifact-complete `(501,20)`, budget 46, with response size and
peak memory. Count above 46, response/privacy/order mismatch or net row mutation
would falsify the respective extrapolation. This experiment was not performed.

Final: **ACCEPT WITH QUALIFICATIONS — V wins; captured safety passes/ties; no
narrow-slice blocker.** Source/monetary-contract safety was not evaluated by this
blind review. This verdict does not waive Sol's separately recorded bound-control
or imported-fixture provenance findings.
