# R7 expiry builder-validation handoff — uncommitted, not independent approval

Owned additions only: scripts/test_input_consumption_expiry.py and this report
prefix in /workspace/sightbreak-windows-input-consumption-r7. Root prereg
 e5f8ac42cdd3d27d57f5014cc9a5fba063b3cc13 precedes implementation/tests.
Root owns reader, source freeze and commits. No reader/old helper/test/fixture/
canonical document was edited by this builder-test task. Nothing was staged or
committed. Existing objective_r2 critic remains sole independent final R7 reviewer.

Reader under both runs SHA256
 e5a08fea8ed4b5b813c87156774b277fb0469a7aaed6896719de5d1e6636e4e7
was unchanged before/after. Physical PeerLifecycle is byteexact to HEAD/hash
 8a57cc07bdc007fe143a5e8c51c99238732fcc4acf9f209fd4718af937f22078.
Initial read mistakenly used game/scripts/peer_lifecycle.gd without network;
actual game/scripts/network/peer_lifecycle.gd was present. No sparse omission,
restoration or skipped source check occurred; correction is retained explicitly.

New fourteen methods build a manual source-transition oracle, then canonical
witnesses close every selected projection's rejected/unrejected alternatives.
Unrejected deadline fixes connected_at=deadline-JOIN; unjoined last=connect.
Joined admission at connect plus active steps<IDLE reaches any later last_input,
because active ignores the original join deadline. Rejected deadline fixes
rejected_at=deadline-REJECT; monotonicity and frozen postreject admission/activity
require last<=reject<=now, constructed by connect/admit at last then reject.
Each witness is executed through the independent source model and must reproduce
the requested fields before its actual source expired() predicate is evaluated.
UNKNOWN requires explicit eligible and ineligible source witnesses. No finite
history-grid absence proves impossibility. The6084 grid selects projected queries,
not candidate histories. An additional256 arbitrary concrete histories have only
one-way feasibility assertions; they cannot label UNKNOWN from incomplete search.

Closure applies to the projected guard under nonnegative monotonic clocks and
representable, nonoverflowing source integer arithmetic. Chosen clocks are small
and safely in that domain. Python integers are unbounded, so the helper is not
proof of native int64 overflow behavior. Neither closure nor parser consistency
proves every full Match callback/packet history or expired-entry survival across
future service calls. Existing read-only builder-support thread checked these
source implications and identified this domain caveat; that is not final approval.

A separate authority fixture repairs lifecycle projection only, preserving old
hand-authored helper byte-for-byte. Actual connected row is age0/rem20000; admission
and accepted-input activity preserve fixed join deadline and update last_input.
Old helper age=-1/rem=-1 at peer_connected stays a schema fixture, explicitly not
source-faithful. No native/global fixture is relabeled. These are synthetic parser
controls, never acquired gameplay, physical or actual-log evidence.

Coverage includes JOIN20000/REJECT500/IDLE30000 at±1, missing/negative/future age,
type corruption, c882 joined age0/rem20000 false-complete rejection, current peer/
generation/retirement/reuse/order guards, explicit latent-rejection UNKNOWN,
natural-idle CONSISTENT and later INVALID after deferred UNKNOWN. Full-reader
JOIN/REJECT cases use a source-connected unbound second peer, preserving current
owned bound guest. Deferred-UNKNOWN negatives exercise reordered index, regressed
clock, input after retirement and same-generation reconnect.

Pure-r1:88methods=13new+75unchanged focused methods, allpass/no skips,1.412s.
Coverage review added a14th full-reader method to make JOIN/REJECT±1 and IDLE+1
explicit in full-reader calls as well as the direct source oracle. Pure-r2:
89methods=14new+75unchanged, allpass/no skips,1.205s. Each run used one CPU4 Python
unittest process; no source changed during either. No test failure was hidden or
reclassified. Commands and per-module counts are retained in COVERAGE/pure JSON
and full stdout/stderr. No engine/native/proc/helper/CI/actual-reader-log replay
occurred. No merge/source qualification or independent acceptance follows.

Root can review and seal these additions, then request the existing independent
critic against an exact frozen target. Remaining gap is whole R7 independent
review and later separately admitted actual replay, not builder test count.
