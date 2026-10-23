# Windows input observation reader R2 handoff

Frozen source is `86fe3cbe3f191b328c1e08bf8d5adc0a937e39b1`, based on the
initial diagnostic handoff `161d72c5f4018e5a8fb24669e1d5054bb6b12edb`.
The isolated worktree is `/workspace/sightbreak-windows-input-consumption-r2`,
branch `codex/windows-input-consumption-r2-20261023`. Preregistration
`d97b8e53ec124e5810ccec8264c9fd7af6ac0de5`, expansion `7efee4c9`, and the
additional role-stage preregistration `bc68fcc4` preceded their respective edits.
First correction `e0acf040` remains in history. This packaging changes only this
report directory after the source freeze.

The fresh critic rejected the initial reader in sealed report
`02725f9cae95b884932e556ac29b2d0ba771b215`. Its evidence exposed false completeness
for absent/stale receive metadata, unbound receives, reversed accepted intervals,
sends outside pending history, changed welcome identities, consumption before
receive/accept observations, and a foreign-role lifecycle stage. R2 corrects
that offline evidence boundary. It fixes no established production defect and
does not explain the actual Windows disconnect or missing input effects.

## Correction and preserved boundaries

Only two non-document paths differ from the initial handoff:
`scripts/analyze_input_consumption.py` and the new
`scripts/test_input_consumption_identity.py` (six methods). The analyzer SHA-256
is `555632cafffa24f9ffc8514bba530f138feea455a83f42b2600d77d27d6aa23e`.
Direct receives require fresh same-record metadata and a current observed
peer-generation/actor binding. Accepted sequence intervals must be ordered.
Each send must fit current pending history and match the current observed
welcome's transport, attempt and actor; disconnect/failure/new attempt retires
the prior welcome. Direct events, counters and retained metadata must belong to
the emitting role. Actual consumption requires earlier direct receive and
acceptance observations.

Receive is observed before payload validation, so malformed received payloads
remain legitimate observations. Coalescing also prevents strict batch pairing
between retained receive/accept/consume summaries. The unchanged independent
cases `receive_wrong_epoch`, `receive_impossible_sequence`,
`consumption_outside_accepted_batch`, and
`client_send_epoch_disagrees_with_authority` therefore remain expected complete.
Completeness establishes required observed stage coverage, never wire delivery,
effect success, gameplay qualification, or an unobserved causal explanation.

Every other non-document Git blob is identical to the initial handoff, including
all runtime hooks, guest/privacy gates, authority/transport rules, controller
schedules and waits, stock values, tests and validation registration. The source
erasure controls still recover all five original pre-observer sources exactly.
The separately accepted initial-pulse correction `ea6c330a` is not included here.
Root, contributor branches and canonical mission documents remain untouched.

## Frozen-source verification

All work used CPU 4. `packaged-full-pure/` and the properly initialized
`depth-one-pure/` each pass 199 methods: 196 passes and the same three existing
Windows skips. This comprises 173 maintained methods, the existing 20 additional
approach/menu methods, and the six new identity methods. Shell syntax passes.
Per-group raw logs and hashes are retained. No Godot, import, export, graphical
native helper or CI dispatch ran. Godot compilation, type/API behavior and native
observer overhead remain unmeasured.

`packaged-final-controls/` and `depth-one-controls/` each reproduce all 29 sealed
independent expectations: 25 original cases plus four supplemental cases. The
scripts in `unchanged-critic-controls/` retain the critic's exact bytes:

| Rig | SHA-256 |
| --- | --- |
| independent_controls.py | 0a9d9117abb25bb995e385b689d3d860df346ae07145241508c94bf80c255e80 |
| supplemental_controls.py | 250fea854a64e932c50f4468f46834b20c62c0f587521a1b267ceeacd3bfffd5 |

Those scripts retain their original hardcoded `c0738163` candidate label.
`binding-results.json` independently binds the actual checkout HEAD and analyzer
hash, checks those against each rig's recorded HEAD/hash, and requires all 29
expectations. No original label, input or expected result was rewritten.

`source-bindings.json` verifies the two-path delta, all other protected Git blobs,
and 474 available code/instruction/fixture paths byte for byte against the frozen
Git blobs and shallow source. The shallow checkout has exactly one commit at
`86fe3cbe`, an initialized 11,178-path index and clean status. Its files were
materialized before the final checks.

## Original failures and retained development records

The official ordinary-input client/server logs remain read-only. Separate copies
under `original-native-log-bytes/` retain their original CRLF bytes and SHA-256s
`ec5fe22c681a9bd5ea0577773e9421d7f0eca6d2711b77c8c124f4cdefff4ba4`
and `61937ac0d1c75f29f790ffc339a4dabaa0a29eac65e9c5da5b4c526835ed0757`.
Direct CLI replay returns exit 1 and incomplete observations for both roles in
`original-native-raw-replay/`. The unchanged critic rig uses text-mode newline
normalization; its derived logs and their separate hashes are explicitly bound.
Neither replay retrofits a diagnostic pass onto the original failed run.

The initial reader's unchanged 25-case replay met only 16 expectations;
`original-independent-replay/` preserves all nine false passes. Intermediate
candidate/final replays and original root pure logs remain unchanged. Their
recorded HEADs precede source commits because they ran on the then-uncommitted
implementation; the packaging results above bind the committed final source.
The first two focused runs correctly rejected inputs but failed two assertions
about rejection-message text. Their complete stderr remains retained, alongside
the later passing focused/identity outputs. The tests were not weakened.

Two builder packaging setup corrections are disclosed separately. The first
depth-one attempt materialized files with an empty index; its passing output is
retained under `depth-one-before-index-initialization-pure/` and excluded from
initialized proof. After exact index restoration and clean-status verification,
both pure and independent checks reran. The first raw-log binding assertion
incorrectly compared official CRLF bytes to the frozen rig's text derivative;
the checker now retains and verifies both forms separately. Neither correction
changed candidate source, critic cases, or the original evidence.

Actual run `39940242244`, job `120369601915`, remains failed. The original
reload-start timeout, disconnect/reconnect, stale snapshot gap, absence of observed
authority fire/reload effects, pre-pulse corridor failure, and separate historical
legacy completion failure are preserved. The living-route failure precedes every
new pulse. No unused pulse path is attributed a cause.

## Review and remaining uncertainty

Fresh critic `/root/windows_connection_trace_fresh_source_critic` preregistered
R2 at `2f709b129987dcc0b681e62deede058083bad3dd` before inspecting changed source
or results. The independent verdict is **REJECT**, sealed at
`8cd68f818d8642953c4d4bda38ee14cccb55a9c5`. Although all 29 earlier cases pass,
seven additional impossible identity/order cases falsely complete, and a valid
unordered two-command authority header is falsely rejected. In particular, the
ordered accepted-interval criterion above was a meaningful root mistake:
`input_stream.accept` does not require array order. This rejected source and its
original criteria/results are preserved. Any R3 correction is separately
preregistered and cannot amend this frozen source or the critic's cases.
Root owns combination, source qualification, admission and any native release.

The largest uncertainty is still the actual disconnect origin and the native
physical/local/send/authority-consumption sequence through reconnect. The runtime
observer has not executed. A production correction needs its own supported
preregistration; manual rebind, stale-generation acceptance, replayed input and
fabricated effects are not introduced here.

Reproduce with fresh output directories:

```sh
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r2-20261023/run_pure.py --source . --output .local/r2-review-pure
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r2-20261023/replay_controls.py --source . --output .local/r2-review-controls
taskset -c 4 python3 docs/reports/gauntlet/windows-input-consumption-r2-20261023/bind_source.py
```
