# Second-round independent critique

Save your first-round verdict before inspecting this packet. Judge only these
anonymous artifacts until this round's verdict is also saved. Do not request the
key, browse surrounding repositories or run application/database tests. Optional
`python -B verify_packet.py` is a read-only local artifact check; independent
rehashing is encouraged. Use exact file/workload/sample references.

1. **Integrity and complete retention:** Does the manifest cover every packet
   file? Are all seven workloads, two warm-ups and ten timed samples present for
   each variant? Can every returned response be followed to raw body bytes and a
   canonical actual body? Identify any hash-only claim lacking its required body.
2. **Actual response equivalence:** Rehash and canonicalize received bodies,
   preserving nested arrays. Check full envelope/field sets, fixture equality
   and cross-variant actual payload equality. Distinguish this evidence from the
   earlier round's expected-fixture hashes. Is the earlier response-retention
   gap closed for these exact captured requests?
3. **State preservation:** Rehash all twelve tables before/after each workload,
   compare complete rows and reconstruct aggregate hashes. Explain differing
   cross-variant session times. Which tables are empty, and what cannot be
   inferred about populated ledgers/receipts, transient writes or wider database
   state? Is the earlier missing-snapshot/hash gap closed for net row mutation
   within these captured intervals?
4. **Query efficiency and timing:** Recompute counts, medians and nearest-rank
   P95. Check both 500-ID boundaries. Quantify improvements and regressions for
   each label; reject claims that sequential shared-host timing establishes
   production speedup, throughput or well-resolved tail latency.
5. **Remaining risk and proof limits:** Distinguish a full retained row/body
   audit from trusted capture, source authorization and monetary-contract safety.
   State what unpaginated history leaves unresolved. Identify the smallest
   decisive falsifier for the most consequential remaining claim; do not run it.
6. **Verdict:** Give PASS / FAIL / NEEDS MORE EVIDENCE / NOT EVALUATED separately
   for packet integrity, actual-response equivalence, captured net row-state
   preservation, measured query efficiency, latency generalization and
   source/monetary-contract safety. Finish with ACCEPT / ACCEPT WITH
   QUALIFICATIONS / REJECT for the narrow measured slice, preferred label or
   tie, confidence, blockers and nonblocking findings.

Save a second-round addendum outside this packet. Explicitly identify which
earlier findings this new evidence resolves and which remain. Preserve both
verdicts before unblinding. If query signatures or timestamps let you associate
labels across rounds, disclose that limit on identity blinding. Any judgment
change after the key is opened belongs in a separate post-unblinding addendum.
