# Independent source review

Verdict: REJECT `c91d9b98a293ef8605d99ae6e83402d3af983519` for diagnostic-method
readiness. The maintained ten methods pass, but fourteen independent malformed or
incomplete receipt controls receive acceptance. The optional production API also
retains old trace fields across calls. These are evidence-method defects; this
review finds no source-visible bot-policy correction or demonstrated gameplay
regression. No native acquisition is released.

Preregistration is commit `eca565bc`, written before detailed code/output
inspection. This report owns only `docs/reports/gauntlet/m5-objective-observability/independent-source`.
The inspected source is the immutable candidate above, never the later review
commit. Original installed Gauntlet/no-ai-slop/eval and mission instructions were
read and reused. No nested critic, Godot, import, export, native application,
renderer, CI or dispatch ran.

## Corrections required before another source review

1. In `bot_ai.gd:558`, a dead/non-live actor returns before touching the supplied
   dictionary. Disabled, release and online collection paths also leave prior
   data intact. Reusing an enabled dictionary after a successful live decision
   therefore leaves `decision` present on a call that made no decision.
   `navigation_destination`, `target_distance` and `aligned` survive later
   branches that do not write them. At `bot_ai.gd:354`, direct `acquire_target`
   calls replace only `candidates`, leaving any previous decision fields.
   The existing test subclass creates fresh dictionaries, so its current caller
   avoids this issue. The production optional API has no fresh-result contract
   or invalidation and no repeated/early-return controls. Give each call an
   unambiguous current status/result, invalidate prior branch-only fields, and
   cover live-to-dead, LIVE-to-POST, enabled-to-disabled and branch changes.
   Explicit boolean opt-in also deserves a strict type check: the gate currently
   uses `bool(...)`, while the reader requires `enabled is True`.
2. In `verify_bot_objective_observation.py:131`, forward authority rows are
   checked only for their label and tick sequence. The maintained synthetic
   “complete contract” contains no forward `dt`, actor inputs/poses, objective
   state or progress. It passes unchanged. Negative durations, impossible
   objective states and empty actor dictionaries also pass. Forward decision
   position/tick is unbound to authority state. Require the complete observation
   schema and bind every expected decision and authority tick to its state,
   fixed positive timestep, source pose and actual command. Missing evidence
   must fail before it can be interpreted as a decision or interaction result.
3. In `verify_bot_objective_observation.py:136`, the control summary supplies the
   claimed outcome independently of the authority rows. Before/after objective
   fields are not required or checked; they may contradict the summary and pass.
   Progress is checked inside each row but never across rows. A fabricated jump
   then reset passes, as does negative final progress. Negative `dt` with a
   compensating later duration passes, and a two-step 1.5-second plant passes as
   stock 60 Hz execution. Validate finite, typed, positive fixed-step durations,
   monotonic consecutive ticks, cross-row progress continuity, the exact first
   completion threshold, cleared progress and actual final transition/reward.
   Complete the command schema: deleting fire/reload/weapon/utility fields also
   passes. Pair decision pose/tick and plan/effective destination inconsistencies
   need validation rather than relying on the emitter's apparent intent.
4. Bind the complete acquisition source and scene dependencies separately from
   the five-file erasure audit. All six current candidate-manifest hashes match,
   and Relay Yard geometry is procedural in the hash-bound `arena.gd`; this is
   not evidence of a changed map. However, the maintained audit never checks the
   probe or candidate manifest, and accepts a probe whose `super._objective_tick`
   call is removed. It also accepts changes to dependencies such as `utility.gd`.
   The exact candidate commit supplies a full source identity today; the future
   wrapper must verify the frozen script/resource/project/UID inventory, not
   present the five-file audit as complete scene provenance. Trace objective
   timer, phase and post-position/reward state if the method is to explain
   expiry/early-return outcomes; the observer currently omits those values.

5. Complete the missing-state declaration. `_prepare` calls `reset_for_round`,
   which also resets deploy time, weapon cooldowns, shot index, stance/head
   height and previous fire/jump/grenade/smoke button edges; it clears match
   damage history as well. These gameplay-relevant resets are absent from the
   header's exact seven-item `missing_state_reset` list. Restoring recorded
   weapon/ammo/velocity does not recover those missing values. Extend the
   assumptions and protect the relevant state in comparisons, especially for
   forward movement/actions. The paired snapshot currently also omits objective
   position/timer/contributions and several action/movement fields, so its
   “protected state” is a declared subset rather than a complete outcome proof.

The independent controls are in `independent_controls.py` and their unchanged
original output is `independent-controls.json`: 20 controls, six expected
outcomes, fourteen unexpected acceptances, process exit 1. Five intended rejection
controls do reject wrong protocol, missing terminal, changed paired ammo, wrong
hold duration and retained invalid progress. A valid maintained synthetic
receipt still passes. The failures are not caused by wholesale reader bypass. Three final type-boundary
controls also accept a boolean actor ID, boolean time scale and a floating protocol
value where the emitted fields are integer/numeric scalars with declared roles.
The first 17-control run is preserved separately under `first-independent-controls`;
the subsequent run only adds these three previously untested boundaries.

## Source safety and ownership findings

Manual inspection of every added production block found dictionary writes and
copies of already computed scalar/vector/plan/command values. No added RNG draw,
selector call, visibility query, path query, physics query, actor command change,
match-state write or objective-outcome write occurs in these actual blocks.
`plan.duplicate(true)` and `actor.input_state.duplicate(true)` detach nested
container data; candidate rows hold scalar values, not actor nodes. The test
subclass uses a fresh dictionary per call and duplicates it before retention.
Neither production match, actor, arena nor weapons changes at the candidate.
No RPC, network snapshot, UI/account path, file writer or public CLI is added by
the production hook. Default callers pass no opt-in; collection uses an explicit
debug-build/offline/authority conjunction. Source inspection supports that
conjunction, while real release/online behavior remains unverified.

`source-boundary-controls.json` retains the gate, freshness findings and six
matching candidate hashes. It also demonstrates why erasure is limited: inserting
an RNG draw inside an erased marker still passes the maintained audit. This
mutation is in a throwaway copy only; it is not present in the candidate. Manual
inspection was required to find the actual added blocks passive. The probe and
utility mutation controls likewise demonstrate audit scope, not a shipping
mutation or proven gameplay defect.

The test authority subclass observes before `super._objective_tick(delta)` and
progress after it. Production authority still requires alive, held interaction,
move magnitude below 0.2, correct carrier/team/site for a plant, or defender
within 2.8 metres of the planted device. Stock thresholds remain 3.0 and 5.0
seconds. Positive controls use real computed bot input plus subject movement and
actions; the other actors stay stationary as disclosed. Wrong-site, moving and
no-interact controls seed 0.25 progress and require its removal. Actual engine
execution of these controls has not occurred. Additional target selection or
physics work in the production hook was not introduced.

## Historical source and reconstruction limits

`original-source-crosscheck.json` independently verifies the archive SHA-256
`8ef76aa1ea3809a4ee35da1adf407decd1cf417fd24def79097dd723dfe231af`, member
SHA-256 `646617ce131167ea582501364ba8d97938cafa7f4557dad199e9381438707ab4`, all 179
rows and all five selected original lines byte for byte. No original planted
state exists in this one journal. Event 126 is natural timeout; event 127 is
POST, carrier 6 alive with 100 HP and SMG 30/0. There are no planning, LOS, target
selection or held-input decisions in that journal. Other b2/e28 matches contain
bot plants, so “bots never plant” remains unsupported.

All five baseline manifest hashes match exact `022d60f`. Four gameplay files
also match original `0527715` byte for byte. AI differs by 13 added lines for the
later exhausted-primary sidearm fallback. The report must explicitly call this
a reconstruction under the newer baseline, not original-source replay. Its
fixture resets holstered ammo and runs a two-second forward slice, so that drift
cannot be silently assumed irrelevant to later decisions. No claim of original
cause can follow even if a reconstructed branch looks plausible.

The code truthfully uses event 122, the last retained LIVE pose, for its forward
slice and changes POST event 127 to hypothetical LIVE for one paired decision.
Initial seeds restart missing later RNG states. Bot/team/heard memory, recoil,
holstered ammunition and utilities reset; those assumptions are disclosed.
These choices permit a bounded diagnostic experiment. They cannot recover the
missing historical decision stream or qualify complete matches, difficulty,
perception quality, navigation quality or whole G1/G2/G17.

## Reproduction and retained setup failures

`fixture-identity.json` records the actual initialized fixture at
`/workspace/reviews/m5-objective-observability-shallow-source`: exact candidate
HEAD, shallow=true, one reachable commit, clean status, no remotes and no object
alternates. It copies complete commit/tree metadata and hydrates 410 selected
source/report paths with a 1,413,904-byte pack. The maintained reader cannot
rely on fetching an ancestor or external service. `build_shallow_fixture.py`
reproduces this bounded setup from a source repository containing the candidate;
use a fresh destination.

From the initialized fixture, CPU 4 commands were:

```sh
taskset -c 4 python3 -m unittest discover -s scripts -p test_bot_objective_observation.py -v
taskset -c 4 python3 scripts/verify_bot_objective_observation.py
```

Both exit 0; the ten methods and exact source-erasure audit pass. Original
stdout/stderr/status files use the `shallow-unittest` and `shallow-source-audit`
prefixes. An earlier own-worktree run also passes ten methods and is retained
under `initial-unittest`. The independent receipt command, run from this report's
worktree and reading only the initialized fixture sources, is:

```sh
taskset -c 4 python3 docs/reports/gauntlet/m5-objective-observability/independent-source/independent_controls.py /workspace/reviews/m5-objective-observability-shallow-source
```

It exits 1 with the fourteen unexpected acceptances. Grammar parsing with the
already installed temporary `gdtoolkit==4.5.0` accepts both GDScripts;
`grammar.json` explicitly leaves compilation false. No engine was invoked.

Setup mistakes remain in `fixture-setup-initial.txt`. Two attempted real shallow
clones reported unsupported filtering and were canceled by identity-checked
signals to their own clone/pack processes; both ended exit 143. An early dependent
sparse checkout ran before the first clone completed and exited 128 (“branch yet
to be born”); a premature HEAD check also exited 128. The first clone omitted
CPU 4 binding until its exact owned process/thread identities were constrained.
An initial cancellation script then encountered an already changed/terminated
pack PID and exited 1 after signaling its verified clone/upload-pack. Those
failures are retained, not counted as test passes. The final bounded fixture and
all substantive reproduced tests ran on CPU 4. No broad process signal was used.

Largest unresolved uncertainty: source controls and grammar parsing cannot
establish pinned Godot 4.7.2 compilation, actual debug/release/online isolation,
engine-driven decision/authority parity, performance overhead or tactical
quality. Correct the source-method failures, obtain a fresh source review, then
preregister and release a complete one-run native supervisor separately.
