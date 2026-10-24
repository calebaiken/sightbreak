# Independent mandatory-drop finding and next correction

Independent critic206e71fc identified a conditional-validation gap before
execution: f48c8461 permits a carrier to die while objective/carrier fields stay
unchanged. Match _eliminated507–510 unconditionally drops a carried device when
its carrier is eliminated. Derive the required transition from protected
before/after actor death, not from the receipt claiming an objective change.

Before editing the helper, generate a full-stream counterexample at the last
forward action interval: carrier dies/deaths+1/health0 in consumer-before/after
and authority-after, but objective remains carried. Recompute only its local
consumer predicate so that typed schema and local objective application remain
consistent. Save exact gzip input/hash/source/result; require old f48 acceptance
as the retained failure. Then require rejection after the minimal guard fix,
with valid post-movement carrier-drop/capped-kill/world-death positives unchanged.
Add the integrated maintained negative; no fixture or production changes.

First f48 results remain preserved:21 maintained pass; unchanged13-case rig
meets11/13 with all six scoped handoff mutations rejecting and two perception
false accepts remaining. Those results do not validate this newly identified gap.
