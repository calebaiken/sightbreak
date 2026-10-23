# Pre-unblinding critique request

Act as a harsh independent reviewer of the supplied evidence. Use only this
packet until your verdict is saved. Do not infer authorship/version from outside
context, request the identity key early, or execute application/database tests.
Running the packet's file/arithmetic verifier is optional and read-only.

Return answers with exact file/workload/sample references:

1. **Integrity and arithmetic:** Are all files covered by the manifest? Do all
   raw samples reproduce each median, nearest-rank P95 and query-count set? Are
   there missing workloads, dropped samples, inconsistent SQL shapes or any
   internal contradiction? Distinguish unique SQL shapes from executed queries.
2. **Efficiency decision:** Does either anonymous variant materially reduce
   executed statements on the nonempty/high-history workloads without worsening
   another measured count? Quantify absolute counts and reductions. Give a
   label-specific verdict based on deterministic observations, not presentation
   or expected author intent. Assess both item and participant batch boundaries.
3. **Timing confidence:** What latency conclusion is actually supported by ten
   sequential samples, warm-up and uncontrolled host load? Which stronger
   throughput/tail/causal claims should be rejected or qualified?
4. **Equivalence and state proof:** Do expected-response fingerprints agree for
   every workload, and what do the recorded successful assertions add? Explicitly
   address the absent actual bodies, before/after snapshots and state hashes.
   Can you independently validate authoritative-state hashes from this packet?
   Do not treat two null hashes as matching evidence.
5. **Contract coverage:** Which observations bear on participant privacy and
   preservation of offer order/current metadata? Which authority, wallet,
   receipt/exact-retry and expected-price claims cannot be established from this
   measurement-only packet? Separate observed behavior from missing source or
   adversarial evidence.
6. **Largest gap / falsifier:** Identify the most consequential remaining risk
   or unmeasured dimension. Specify the smallest decisive follow-up that could
   falsify your preferred interpretation; do not perform a new run in this task.
7. **Acceptance:** Give separate PASS / FAIL / NEEDS MORE EVIDENCE / NOT EVALUATED
   statuses for (a) packet integrity, (b) measured query efficiency, (c) latency
   generalization, (d) response-equivalence evidence, (e) independently auditable
   state preservation, and (f) source/monetary-contract safety. Finish with
   ACCEPT / ACCEPT WITH QUALIFICATIONS / REJECT for the **narrow measured slice**,
   your preferred label or tie, confidence, blockers and nonblocking findings.

Save the verdict outside this packet before the controller reveals identities.
After unblinding, record any changed judgment as a separate addendum with its
reason; preserve the original verdict.
