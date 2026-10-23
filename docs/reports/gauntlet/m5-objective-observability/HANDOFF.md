# Objective diagnostic source handoff

Candidate only. No gameplay correction or G1/G2 improvement is claimed. Original
stock output does not identify a source-provable objective defect. This branch
implements the missing observation and a bounded fixture; it is ready for fresh
source criticism. The builder does not approve it.

Own checkout: `/workspace/sightbreak-objective-observability`.
Branch: `codex/m5-objective-observability-20261023`.
Exact inspected base: `022d60faa830696af3f03c554e99356c1beac0dd`.
Preregistration before implementation: `09a3ea84`. The retained clarification
truthfully distinguishes its later source-writing time from native execution.
`candidate-identity.json` binds the six source/fixture files. This report and all
raw source evidence belong to this component; canonical mission files are left
for root coordination.

## Findings and resulting source

The original `05277154c6b8c92b80fd7c25e8365de9efdc4fae` archive contains 179
events and zero planted-state rows. Natural timeout notification 126 occurs at
tick 19210. The first retained POST pose, event 127 at tick 19213, has carrier 6
alive at 100 HP with SMG 30/0, four attackers and two defenders alive. The two
living enemies are geometrically 36.1313 and 36.7822 metres away, with facing
dots 0.98919 and 0.99482. These are POST-pose calculations. They do not prove
actual target acquisition, visibility or the preceding LIVE decision.

The actual production planning predicate asks the carrier to interact at a site.
With a visible target, combat movement can cover, brake or strafe instead of
following the objective destination. Without a target, remembered sightings can
replace that destination before navigation. Authority then requires a living
actor, held interact, move magnitude below 0.2 and the matching objective/site.
The archive logs none of those bot decisions. Inferring any one branch from the
terminal pose would be unsupported. One stock plant in inspected `b2e0293` and
broader objective events reported at `e28c8e9` also remain counterexamples to a
blanket never-plants claim.

`bot_ai.gd` accepts an optional caller-owned observation dictionary. Collection
requires explicit `enabled`, a debug build, offline mode and authority. It records
values from the actual candidate checks and decision branches. It adds no
visibility, navigation, selector or RNG call. Default callers collect nothing;
there is no public CLI, RPC, account access or file output in the production hook.
Marked additions erase back to byte-identical inspected AI source. Production
match, actor, arena and weapons remain byte-identical to the base.

The new test-only match subclass captures objective inputs before the production
consumer and progression after it. Three original poses get paired OFF/ON
decisions with full resource, command, memory and RNG comparison. A two-second
forward slice uses the last retained LIVE pose, event 122, with its original
phase/timer and normal two-phase authority. The POST pose gets only a hypothetical
LIVE decision, with that phase change disclosed. Initial recorded seeds restart
the missing later RNG state; bot/team/heard memory, recoil, holstered ammunition
and utilities reset as declared assumptions. This is a reconstruction, not replay.

Isolated positive controls use real bot commands and subject movement/actions
through the normal objective consumer for plant/defuse. Other actors remain
stationary in these controls. Wrong-site, moving and no-interact controls must
erase existing progress. No plant, kill, win or tuning target is imposed on the
reconstructed original poses or forward slice.

## Source-only evidence

All execution stayed on CPU 4. Ten Python test methods pass, covering complete
synthetic receipts and changed resources/commands/memory/RNG, unperceived targets,
missing paired decisions, missing forward authority ticks, invalid interaction,
truncation/duplicates and strict native warning rejection. Synthetic receipts are
parser controls only. Source audit verifies baseline erasure, four unchanged
gameplay files and exact original/fixture bytes. See `pure-checks/` for originals.

The temporary ignored `gdtoolkit==4.5.0` parser accepts the two GDScript files.
This checks grammar only. Godot 4.7.2 compilation, actual parity, real geometry,
plant/defuse controls, strict shutdown and complete aggregate validation remain
unexecuted. This lane ran no Godot, import, native application, renderer, export,
service, CI, or nested agent. No native run is released by this handoff.

Live read-only ownership refresh preserved PR26 map `778c89a6820e688d776c509854a077742cfdfb78`,
PR28 bot/order `2641ddf89265c5ded188a350eb39d95abfdae9c1`, and the clean contributor
checkout `work@4d8cdb33ce18a6adcf6e2af5556b6f083535536c`.

## Next commands and remaining risk

Fresh source critic can run, without an engine:

```sh
taskset -c 4 python3 -m unittest discover -s scripts -p test_bot_objective_observation.py -v
taskset -c 4 python3 scripts/verify_bot_objective_observation.py
git diff 022d60faa830696af3f03c554e99356c1beac0dd -- game/scripts/gameplay/bot_ai.gd game/tests/bot_objective_observation_probe.gd
```

Review the actual GDScript beyond the erasure result: erasure proves preservation
of the original statements, not that an inserted block cannot mutate state.
Inspect optional-dictionary isolation, every copied value, gate behavior, the
test subclass's authority ordering, paired reset completeness, original source
identity, source-only limitations and parser falsifiers.

After independent source acceptance and root native release, a fresh critic must
start before one bounded acquisition: separate import cap 120 seconds, one probe
cap 60 seconds, time scale 1, fresh private state/output, unchanged source/UID
inventories and strict logs/descendant cleanup. Proposed inner probe command is
`./scripts/godot.sh --headless --audio-driver Dummy --script res://tests/bot_objective_observation_probe.gd`.
This is not a complete approved supervisor or acquisition recipe. Root must bind
the final exact source, observer and output before release. The offline reader is
`python3 scripts/verify_bot_objective_observation.py --log <original-probe-stdout>`;
the supervisor must separately reject nonzero exit, timeout, stderr warnings,
source changes and incomplete cleanup. Retain every failure; no manual continuation
or second invocation is authorized here.

The largest remaining gap is the original missing decision stream. Passing this
fixture would qualify a bounded observation method, not establish the original
timeout's cause, full-match objectives, difficulty, aim or whole G2 quality.
