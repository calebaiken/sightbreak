# Independent R4 reader source verdict: REJECT

Frozen source `642dd0e0543698cae5d90b9046d5875beabed111`, reader SHA-256
`207beebe124a1ad5928a154fb77c99d2e43864ce236751dc7ce985878181bcb2`, accepts six
new source-impossible histories in five invariant groups. Own sparse and exact
initialized one-commit views reproduce every false accept with no errors. All
paired valid controls pass, and every case independently checks snapshot freshness.
The largest remaining gap is agreement among packet projection, live queue/ACK,
stream rejection state and the time of hidden stage calls.

R4 wins the comparison with rejected R3 on the retained old critic corpus: it
rejects all eleven previous false accepts and accepts the five legitimate cases.
It also rejects the independently isolated client counter falsifier that R3 still
accepts. These improvements do not meet the source acceptance gate because six
new invalid histories return `diagnostic_complete=true`, errors=[].

Reviewer `/root/reopened_verbose_source_critic_20261024` is independent of builder.
Root reused this existing thread after creation of a fresh thread failed. This is
explicitly not a fresh-context review; prior context concerned reopened verbose
diagnostics and contained no R4 implementation. New own review branch/worktree,
preregistration30f049aa, pre-implementation source oracle1c510c83 and independent
control plan909f6d7d precede R4 source inspection. Final-target amendment/merge
30e410e0 precedes all tests. Historical first freeze3e688c8c remains retained;
no worktree or canonical document from the prior subject/root was edited.

## Reproduced failures

Each directory below is under `own-fresh-controls-r2/` and
`depth-fresh-controls-r2/`, containing exact client/authority inputs, expected
verdict, actual result, source basis and named paired positive. All expect false
and actually return true. The source is the exact unchanged emitter, InputStream
and peer lifecycle fetched at342c3641 and verified unchanged in the candidate.

| Case | Deterministic source contradiction |
| --- | --- |
| `acknowledged_single_command_falsely_accepted` | Append a second direct receive/accept pair after command1 has been popped with ACK1. Its count1 packet has sequence1. InputStream24–38 stages only sequences greater than ACK, so the single acknowledged command cannot be accepted. Paired sequence2 accepts. Counters, current metadata, queue, actor and freshness are otherwise coherent. |
| `queue_exceeds_max_ahead` | Direct acceptance claims queue_count121. InputStream5,24–47 permits unique pending keys only in (ACK,ACK+120]; pop removes keys/advances ACK, and forget/reset only clear. The queue cannot contain121 keys. Paired queue1 passes. |
| `stream_rejected_without_rejection_call` | Final authority tick claims stream_rejected1 while cumulative input_stream_rejected is absent/0. Every accept failure increments the stream state and synchronously calls that observer stage (Match1068–1070). This observer begins before networking; the fixture has no earlier hidden rejection or stream replacement. Paired state0/counter0 passes. |
| `rejection_counter_without_stream_rejected_state` | Valid malformed→rejected→valid receive control has rejection counter1 but stream_rejected is changed from1 to0. InputStream increments rejected before the observer hook. This live binding and epoch remain unchanged, so no stream replacement can explain state0. Paired state1/counter1 passes. |
| `empty_packet_projects_nonempty_endpoint` | A raw count0 receive claims endpoints21/21. Match1249–1264 initializes both to-1 and visits no commands in an empty array. This is impossible projection metadata, independent of whether the authority permits malformed payloads. Paired empty-array and nondictionary-only malformed observations followed by rejection and valid receive both pass. |
| `hidden_accept_latest_timestamp_regresses` | An authority tick advances receive/accept counters for legitimate coalesced calls, but their latest timestamps become1 after a prior emitted wall11000. Match1269 samples monotonic Time.get_ticks_msec; later calls cannot occur before the preceding row. Paired hidden calls timestamp11001 pass and require no invented direct rows or packet identity. |

The first12-case iteration is retained with its exact script and outputs:7/12,
five false accepts. A subsequent source audit found the inverse rejection-state
contradiction in the new maintained/normalized positive fixtures; the final13-case
version adds that paired falsifier without replacing earlier outputs. Final own
and depth results are7/13, six false accepts and no false rejects. The same corrected
fixture with the old R3 reader is6/13: it additionally accepts the fresh client
counter-only falsifier. This old-reader view deliberately combines the exact R3
analyzer with the exact R4 shared helper; it is a source comparison fixture, not a
claim that a full old checkout was retested.

## Fixture adjudication and retained regressions

The three maintained fixture edits have a real source basis: persistent latest
and welcome/snapshot metadata, nonempty direct accepted queue, no pre-pop ACK,
and matching consumed ACK/actor input. Restamping must retain metadata; malformed
count1 endpoints must agree. Existing32 test methods and all59 assertion-call
ASTs are unchanged. The final helper now advances inserted snapshot_age_msec;
the fresh client tick positive and counter-only negative independently verify that
R4 rejection is not caused by stale snapshot freshness.

Those edits are incomplete. The maintained identity positive adds a hidden
input_stream_rejected counter but leaves stream_rejected0. Both versioned
`receive_wrong_epoch` and `receive_impossible_sequence` positives have the same
state/counter contradiction in the builder replay. FINAL_VERIFICATION.json lists
exact indices and values. Their passing reader verdicts are not source validation.
The independent malformed positive includes both counter1 and stream state1;
changing only the state to0 creates the retained inverse falsifier above.
Match1468–1479 can replace the stream during a server-lobby reset, so rejection
state/counter equality is not a universal cross-reset invariant. That function
requires zero bound peers and advances authority_epoch. These controls retain
their live binding, epoch and complete lifecycle counters, excluding such a
reset. A correction must respect this source boundary.

The preserved builder replay is run separately from independent controls. Both
views reproduce its92 required verdicts: untouched historical38 expectations match
32/38, its explicit source-corrected38 match38/38, and exact final critic16 match
16/16. The six historically inconsistent positives remain rejected and retain
original expectations/bytes; they are never represented as unchanged passes.
All164 frozen critic files copied into this report are byte-equal to committed
f8049be40286fff4ce8fe09159dbcf2db6874caf objects. The normalized fixture generator
is preserved as builder code and its further contradiction is stated above.

Selected197 maintained Python methods run in process in each view:194 passes,
the same three Windows-only skips, zero failures/errors. Relevant reader groups
are45 methods (19 observation,6 identity,7 lifecycle,13 state). The builder's11
server and11 Mac methods are excluded under this review's no-process/no-Mac scope;
no full219-method reproduction is claimed. Shell syntax passes in both views.
Passing maintained/frozen tests do not override the fresh counterexamples.

## Source identity and execution scope

Full base/candidate non-document union is512 paths: exactly five allowed changes,
507 protected paths. All512 candidate files and executable modes are materialized
and hash-verified in own and exact depth views before/after checks. The full game
emitter/collector/transport, protocol6, privacy, economy, authority, controller,
workflow and all other source remain unchanged. Handoff
`d139124e8c663c3951eb6c7aaff99d49f2ce9712` is non-document-identical to frozen642dd0e0.

Depth view `/workspace/reviews/windows-input-reader-r4-exact-depth1-20261024` is
initialized at exact642dd0e0, clean, shallow, reachable commit_count1, HEAD^ absent,
full11728-path tracked index and512 materialized non-document paths. It shares
`/workspace/sightbreak/.git/objects` as an explicit alternate. It is not independent
object storage or a self-contained clone; no large clone was created. New maintained
state tests have no Git/history lookup, and all relevant tests reproduce in this
view. Comparison/provenance checks deliberately use named base/critic Git objects.

All executions are CPU4 Python/static/shell parsing. No Godot, engine API, export,
native application/helper, process inspection/mock-process test, OS input, CI,
credential or security test, Mac review or actual dispatch ran. Unrelated actual
Windows40083894472 remains inconclusive and out of scope. No source acceptance,
actual run admission, cause, physical latency or completeness claim follows.
Coalesced counters/projections expose neither packet identity nor terminal
capture coverage, even when every supported source invariant is satisfied.

One setup read guessed nonexistent SCOPE_EXPANSION.md and exited1 after reading
the real PREREGISTRATION.md. Both expansions are appended to that real preregistration;
no check was bypassed. First freeze/test-helper confound and the thread reuse are
explicitly preserved. There are no failed fresh-case constructions: paired valid
controls pass on R3/R4, and every failing expectation is a false accept listed here.
No source file was edited by this reviewer.

## Required next step

Retain this rejection and all original failures. A separately frozen correction
must address the demonstrated projection/queue/ACK/rejection/timing invariants,
correct positive fixture stream-rejection state from the actual call order, and
receive independent review. Preserve legitimate malformed input, duplicate/unsorted
batch endpoints, immutable queued commands and coalesced hidden calls. No new
native/CI run is released by this report.
