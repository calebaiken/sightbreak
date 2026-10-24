# R6 stream interval source candidate — unapproved

Code source `6ef4d145ab70ed943c54ec26865e0c884b64b1a9`, reader SHA256
`fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0`.
Root owns NEW branch `codex/windows-input-foundation-r6-root-20261024` in
`/workspace/sightbreak-input-foundation-r6-root-20261024`, based on frozen R5
handoff `1e045025fdc5e86a1850ebd18565ad08a12253e3`. Old R5/R3/R4 branches,
original failures and reviews remain unchanged. Preregistration72cd8697 precedes
implementation; Root cannot approve this candidate. SAME different Windows
critic registered f84cd7bd before inspecting any R6 code and is reserved.

The new StreamObservationIntervals validator runs for every deterministic row
before deferred queue inference. It compares previous observations of the same
still-bound (peer,generation,epoch), even across selection of another peer.
ACK cannot clear/regress, and cannot change with zero global consumed progress.
A newly latest consumed projection belonging to that stream fixes its ACK.
Queue size has conservative global acceptance/pop/skipped bounds. Anonymous
calls are never allocated to a local owner, accepted duplicates may add zero,
and legal large sequence gaps get no count-derived ACK upper bound. Disconnect
is checked before forget then retires history; epoch/generation changes separate
domains. Existing inference stops on its first UNKNOWN as before.

Three source additions only: one new validator class, its initialization and
one call. Removing them reconstructs the complete old reader byte-for-byte.
InputTransitions, all other engines/schema, actual observer/game/network/default
flags/privacy, SDK/native/workflows and deadlines stay exact. Only two non-doc
paths change (reader/new tests); all522 physical paths/modes and520 protected
paths verify. Every old149 method/helper file is byte-exact, containing331
assertion calls. The supported23-leaf old constructor amendment is UNAPPLIED;
its original failure remains. No normalization or assertion weakening occurs.

Builder evidence, not independent approval:

- Nine new methods pass. Added ticks complete the ordered pop loop for every
  bound peer, including backlog discard. Sixteen phase/selection/sequence-gap
  witnesses stay UNKNOWN;64 contradictory siblings reject. Pending receive,
  queued duplicates, newly accepted growth, coalesced latest pop, backlog and
  observed disconnect/reset/new-generation controls pass. Synthetic frame,
  resource/client/seed fields retain their limits; this is not native provenance.
- Exact sealed R5 source-complete necessity control improves2/5 to5/5: original
  remainsUNKNOWN, three ACK/queue contradictions and frame fault are INVALID.
  Original incomplete R1 history is not substituted or credited.
- Frozen49 earlier cases and3,060 isolated model expectations match. These are
  exact preserved controls independently authored before this candidate, replayed
  by its builder, not an independent R6 verdict or exhaustive callback proof.
- Literal158 methods:45 assertion failure events,1error,0skips; NOTPASS. All46
  failure identities match sealed R5. Full3,180 captured calls/raw failure traces
  are retained. No broad explanation or fixture approval is inferred from matching
  failure identities. The whole reader remains unqualified.
- The four preserved-control runs have zero forbidden process/API/proc attempts.
  Only control-harness reader SHA activation pins and one metadata source label
  change, registered before execution; case data/predicates/old tests remain exact.
  Source audit separately uses read-only local Git. No actual207/native, API,
  capability, SDK, engine, helper acquisition, study or CI run occurred.

Reproduce from this report with fresh output names onCPU4:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=scripts taskset -c 4 python3 -m unittest -v test_input_consumption_intervals
PYTHONDONTWRITEBYTECODE=1 taskset -c 4 python3 <report>/controls/pure_runner.py --guard-result <fresh-json> <report>/controls/later_stream_necessities_r2.py --source <source> --output <fresh-directory>
```

The same guard runs independent_models.py and capture_literal.py. The latter
intentionally returns1 for the preserved NOTPASS suite. Exact49 uses the unchanged
R5 controls/replay_registered.py and the SHA above. Materialization record pins
all178 historical fixture files before execution. No test/setup failure is skipped.

Largest remaining reader gate is independent review of these interval rules and
their interaction with genuine reset/connection/pending/multi-owner histories,
followed by the individually unresolved legacy failures. Actual207 replay and
all native/release gates remain unexecuted/unapproved. Shutdown contract approval
is pending; neither changed study nor capability run may execute.
