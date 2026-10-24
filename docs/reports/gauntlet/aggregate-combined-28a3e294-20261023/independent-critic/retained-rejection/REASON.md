# First source setup audit rejected

The 6ffe338 handoff was followed by an uncommitted change to the wrapper before
this critic's read-only audit completed. The retained 2,455-predicate audit
rejects builder cleanliness and exact committed `run_aggregate.py` bytes only.
The diff adds a terminal `seconds < 1200` predicate to the existing supervisor
whole budget. The builder separately identified this timing edge and asked for
review; I require the tightening. The frozen runtime tree remains clean at
28a3e294; all 808 file/blob/mode checks, 138 UIDs, archive/executable pin, fresh
paths and eight-port preflight pass. No native run or runtime failure occurred.
A fresh committed handoff and source audit must replace this readiness attempt;
these original rejected bytes stay retained.
