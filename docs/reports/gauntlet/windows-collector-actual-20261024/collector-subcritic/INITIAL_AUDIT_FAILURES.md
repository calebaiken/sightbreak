# Retained first actual audit failure and corrections

The first fresh decoder run against the official bounded receipts/evidence
returned0 with384 decoded rows (including userdata sink replicas), zero malformed
prefixed JSON lines,18,796 passing predicates and290 provisional failing
predicates. Original script, facts and CSV are preserved as initial-* files.
This was an audit failure, not an accepted actual verdict.

280 failures came from an overstrict snapshot-header assumption: source
match.gd1286 assigns the same header Dictionary to diagnostic.snapshot and, at
1288, diagnostic.latest[reason]. At1289 adding wall_msec to the latter also
updates the aliased snapshot. Actual raw correctly has the four keys
tick/epoch/own_ack/wall_msec; the source-bound corrected decoder must allow and
compare those four keys, retaining snapshot_age separately.

Ten ordering/counter failures came from treating the shared Godot userdata
log sink as one process stream. That godot.log contains77 client rows then a
partial authority tail. Its line85 starts in the middle of authority row85 and
contains no SIGHTBREAK prefix. Source stdout client.log/server.log remain
separate canonical process streams. The auxiliary sink must retain projection
checks and replica/fragment facts, without inventing a single process order.
This correction does not erase the auxiliary mixed/truncated sink limitation.
