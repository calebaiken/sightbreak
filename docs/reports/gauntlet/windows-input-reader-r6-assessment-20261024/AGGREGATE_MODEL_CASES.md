# Added persistent packet-aggregate relation, before execution

The initial13 model tests and outputs remain unchanged. The updated captured
unfrozen prototype0ac7310b is a model-coverage iteration, not a frozen candidate.
It must not be called ready merely because individual prior cases are patched.

Register a further source-derived pair, selected before execution:

One sole count2 accepted packet exposes two distinct fresh keys1 and2 and has
fire aggregate1, queue2. There are no later accept, reset, forget or skip calls.
The source stages both immutable command values. If pop1 has fireFalse, pop2
must have fireTrue; bothFalse contradict the same single packet. Similarly,
bothTrue contradict aggregate1. Individual unknown flags are correlated, not
independently replaceable over time. This does not infer a complete unreported
packet: the count2 projection exposes both identities and the queue has only
these two fresh commands.

The positive independent oracle accepts [1False,2True], then pops both. A
counterfactual keeps the first false pop and claims the second also false, with
accepted aggregate1, all call counters/ACKs/queue sizes unchanged. To preserve
source emission feasibility, a repeated unchanged second consumed control may
coalesce into a later authority_tick rather than inventing a same-control direct
row; record that projected variant separately. Both variants violate the same
immutable aggregate relation irrespective of emission.

Expected: positive VALID; both negative projections INVALID. Preserve old rig
and each exact new raw truth/projection/result. This extends the earlier
MODEL_CASES#8 requirement that one persistent feasible history must explain all
rows, rather than choosing different unknown command bodies per pop.
