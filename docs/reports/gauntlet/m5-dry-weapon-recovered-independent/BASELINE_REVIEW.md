# Actual baseline review

Verdict: **CONFIRMED baseline dry-return defect**. The baseline fixture remains
FAILED. The actual output at `baseline-r1`, published by builder report commit
`47f7165ceb1e6c7f571f3eaae0dc07ed8696398d`, matches the inspected production
source and the preregistered justification for a narrow fix.

I read the actual raw log, retained controller, receipt and both source snapshots.
Runtime-log SHA-256 is
`54982dfa591dbdaa5d213d4b0f53040dc6aa657e9a9d20813a3405c210298347`.
Controller SHA-256 is
`143253ae25b882cb22734d190aae57fe6405c65b1038c886875af9008f3e7086`.
The source snapshots identify unchanged `b0635964c6b819ed41a9568afdb0b5068c3d5577`
and match this critic's pre-run fixture/bot/actor hashes. The tracked diff is
empty before and after. The native marker identifies Godot 4.7.2.

The own `recompute_observable.py` derives expected case outputs and step
transitions from the registered scenarios. It does not read the fixture's
declared expected fields as its decision oracle. The actual baseline passes
1,974 independent observable predicates: all 84 cases, all 48 steps, all six
sequence summaries, the exact 40 failure labels and the final 590-check result.
Twenty-one case requests and three coupled reload expectations fail the
candidate contract, with 16 additional sequence failures. The output is
consistent with engine exit 1, duration 1.268859859 s, no timeout and no engine
error.

Each idle profile actually equips the zero-ammo rifle once and requests seven
reloads that never start. Alternating easy does the same. Alternating normal and
hard each actually switch eight times and equip the dry rifle four times. All
six sequences log zero shots, conserved total ammo 75 and zero reload timer.
This is a direct fixture defect witness using production action consumption;
it does not identify a historical full-journey timeout cause.

Seven pure derived-log falsifiers were rejected: a wrong request, reserve,
deploy timer or summary; a false baseline-pass marker; a missing step; and a
duplicate case. Their output is retained separately and is not native evidence.
Unlogged full authority snapshots remain excluded from the independent raw
recomputation; the reviewed fixture assertions cover those predicates.

Cleanup has a concrete limit. The controller observed native PID/PGRP/SID 4164,
start tick 397552. Its 120-second wall deadline was not reached; no cleanup
signal was used. The terminal scan found no member of that SID and no recognized
Godot process. It tracks SID membership rather than recursive PID ancestry,
and its signals target the original process group. It cannot prove that a
descendant which changes session/group was cleaned, or validate timeout/error
cleanup paths from this successful termination. Retain those limits in any
integration report. The copied controller also derives its repository path
from its own location; it is a retained source copy, not a directly replayable
command at the report path.

The baseline evidence supports proceeding to the registered primary-return
guard. Candidate acceptance still requires exact-source review, the same
fixture and existing required regressions.
