# Independent R5 concrete controls, registered before execution

Frozen reader7d8ec7dda37764e0f45fd2ea1e8d330f84bc2508; sealed handoff
eb2dbc7cc97b337fb8e0bbf601fcb0bbfd984701. Registration57f5d40d precedes source
inspection; external preregistration hash d030c78cca9acc6fa71f7d44adbab259c3e3232fa3028ca010be1402b7da223a.
No R5 test has executed in this review. Old code/fixtures/results remain intact.

Exact fixed source is the oracle: Match1066-1078 receives, synchronously accepts
or rejects with no await; InputStream14-47 stages unique sequences strictly above
ACK and at most ACK+120; Match1249-1264 projects bounded command arrays;
1266-1300 increments counters/latest/cache before deciding whether to emit;
1468-1479 can replace the stream only with no bound peers, advancing epoch and
clearing the new stream state while retaining diagnostic history.

Independent inputs start with retained hand-authored declared_rows schema
fixtures, with own constructors for appended rows and hidden metadata. They are
not an engine simulation or proof of complete source feasibility. Paired
positives exercise the particular source invariant under challenge and must
be admitted, while each negative changes real serialized fields. No mutation
is repaired after it is applied. Exact raw inputs and output/error are retained.

Register these additive cases:

1. Admitted baseline and coalesced fresh count1 sequence2 after ACK1. Change only
   latest receive/accept projections on a later authority_tick: stale sequence1,
   sequence122 above ACK+120, wrong epoch2 or count13 are impossible acceptances.
   Same action aggregates keep those stages legitimately coalesced. The source
   constraint must hold on projections first seen in a tick, not only direct
   input_accepted rows. Count3 with stale endpoints1/1 and one unexposed fresh2
   remains possible; do not infer a complete packet from endpoints.
2. Direct first count1 acceptance after queue0 has queue1. Alter its queue_count
   to2 and120 without new receives or accepted commands. Neither can result
   synchronously from one staged command. Keep separate meaningful queue120
   capacity positives from the maintained full-queue construction; this is a
   transition/count falsifier, not a proposal to lower the120 cap.
3. After a consumed ACK1, append a same-peer/generation/epoch tick with no new
   consumed calls. ACK2, ACK0, ACK-1 or queue1 are unsupported state changes.
   Pop alone changes ACK; forget/epoch reset clears queues/ACK, and these inputs
   retain the binding, epoch and complete lifecycle history. An unchanged ACK1
   and empty queue is the positive. Do not infer missing consumption when its
   cumulative counter is unchanged.
4. Cached first snapshot with positive applied counter must equal its persistent
   latest snapshot header. On the final client tick, independently clear its
   cache, restamp its cached wall time while recomputing age, or change cached
   own_ack while preserving the actual latest/counter. Each is source-impossible.
   A nonempty cache before the first applied counter is also impossible. An
   invariant-compatible later first call in [previous,current] and its cached
   subsequent copies is positive; an earlier-than-previous timestamp is negative.
   Welcome precedes apply_snapshot. Equal millisecond timestamps at the prior
   welcome boundary are allowed. Already-positive caches do not clear on welcome.
5. Append two coalesced malformed receive/rejection calls in one stream lifetime,
   observer J2 and stream state2, then a direct disconnect and zero-peer epoch
   change. Full replacement state0 is positive; unchanged state2 is possible if
   only round/epoch queue reset occurs. Partial state1 with no new rejection is
   impossible: old state either persists or a new stream starts0. Register this
   disjunction separately from the already-fixed live-binding state-drop case.
   Also retain same-epoch/live-binding drops as negatives and legitimate post-
   replacement new rejection calls as positive where construction permits.
6. Coalesced advancing metadata timestamps at previous wall, middle and current
   wall are feasible; previous-1 and current+1 are invalid. Unchanged counters
   retain old metadata. Count0 received endpoints must be -1/-1; malformed
   nondictionary count1/2 projections remain possible before stream rejection.

Keep historical R4 critic13 and builder92 separate; replay the builder's explicit
108 required verdicts only as retained regression evidence, never as independent
new controls. Preserve obsolete state0/J1 positives and their expectations.
Read the R4 critic's exact snapshot-helper adjudication when its path is supplied;
record a missing guessed document as a lookup failure, not a passed test.

After these registered checks, independently inspect/prove all513 non-doc Git
path/mode/blob identities and all working bytes, all four changed files and
inherited assertions. Run focused55 and supported in-process regression groups;
exclude server/Mac/process-specific groups under this lane and state the actual
count, without claiming the builder's full229 was rerun if it was not. Initialize
an exact one-commit source repository with explicit non-cone paths before
materialization, no parent/remotes/alternates if practical; repeat meaningful
controls and supported pure methods there. Disclose any alternate dependency.
No Godot/native/process activation/CI/Mac/canonical edits or native readiness.
