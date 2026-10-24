# Independent R6 source-transition cases before execution

Registered after read-only interface inspection and before running these models.
This is an interim model assessment, not final R6 source qualification. The own
checkout remains the pre-implementation registration4f0a1906 with R5 product code.
A read-only copy of current builder working analyzer will be retained with its
SHA-256 and unapproved/unfrozen status if its transition class is exercised.
Only InputTransitions is under prototype assessment; no whole-reader pass/fail
or native/API result will be inferred from that isolated class.

Independent source oracle: queues are maps keyed by sequence. Valid accepted
commands above ACK are staged; existing queued keys/payloads stay immutable.
Pop sorts keys, truncates to the largest two only when size>6 while counting
removed keys, pops the minimum retained key and stores ACK. Received/accepted/
consumed counters are cumulative globally; queue/ACK is per peer. The source
observer changes selected peer on each positive-peer call, updates counters and
latest before its emission decision, and may coalesce calls with unchanged
control aggregates. The oracle is separately written from these source rules,
not from the candidate transition equations.

Register model pairs/cases:

1. Direct accept commands[1(false),2(true),1(false)] at ACK0 yields queue{1,2},
   projection count3/first1/last1 and queue_count2. Valid first pop is1, remaining
   queue1, skipped0. Counterfactual pop2/ACK2 with the same queue count/skips is
   impossible under EVERY hidden-middle assignment: fresh endpoint1 is mandatory.
2. Queue1/fireTrue was accepted first. A later count3 packet with duplicate1/
   fireFalse and a new2/fireFalse cannot replace the old key1 payload. Valid
   pop1/fireTrue remains; pop1/fireFalse is impossible. Uncertainty about other
   command bodies cannot erase a proven existing signature.
3. The count3 queue becomes observed empty after valid pops1 then2. This must
   re-establish exact keys={}, even if its body was previously unknown. A later
   coalesced fresh count1 accept3 must leave queue1 with no pop/skip/reset. Its
   counterfactual queue0 is impossible. Known-empty is exact observation, not
   packet reconstruction.
4. A valid seven-command queue with distinct keys1..7 has backlog pop6,
   skipped5, remaining key7. Counterfactual pop2/ACK2 cannot result, even when
   only endpoints and queue_count7 expose the earlier packet. Uniqueness and
   positive sequences imply the second-largest of seven keys is at least6 at
   initial ACK0. Include sparse valid keys to avoid assuming adjacency.
5. Multiple small exact receives build known queues; an opaque/multi-accept
   interval may add unknown keys but cannot remove mandatory old keys when
   there are no pop/skip/reset calls. Later skipping the known minimum must
   reject. Preserve source-implied must-keys alongside unknown may-keys.
6. Peer B has a known one-key queue and pops that key in a coalesced call. A
   later peer-A receive selects A in the next emitted row, with explicit latest
   consumed identity B and global consumed delta1. Ownership is proved by the
   metadata; absence of a current B projection is a model coverage issue, not
   unprovable ownership. Preserve/validate B's derived state when sufficient.
7. Multiple peers with different ACK contexts: a hidden count1 projection can
   identify its owner by excluding ACK contexts where it would be fully stale
   or outside+120. Contrast a genuinely ambiguous header possible for both.
   UNKNOWN is appropriate only where a needed fact remains unprovable; do not
   label explicit ownership or all-equivalent safe contexts unprovable merely
   because the model does not yet carry the required alternatives.
8. Equal-millisecond accept/pop calls have source-order alternatives. Retain
   the UNION of feasible queue/signature states over time, not unrelated
   per-transition existential choices. A later row must extend one prior
   feasible history; it cannot switch hidden packet contents retroactively.
9. Reconnect same numeric peer with a fresh generation, live-bound round reset,
   zero-bound lobby replacement, connected-but-unbound peer and delayed actual
   disconnect after expiry require separate contexts. InputStream forget/reset
   clears queue/ACK; only replacement clears global rejection/skipped state.
   Counters/latest persist across lobby reset. Keep full reset/no-reset union.

Prototype checks, if run, use exact captured source, serialize ground-truth
queues/events separately from projected/counterfactual rows, and label invalid
acceptance versus deliberate UNKNOWN coverage separately. No expectation or
source fixture is repaired after mutation. Original R5 108/30 and source/depth
artifacts stay byte-exact. Source-generated positive/negative pairs and all
failures will be preserved for later exact frozen full-reader review.
