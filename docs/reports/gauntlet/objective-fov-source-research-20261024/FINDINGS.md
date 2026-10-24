# Objective perception: source and numerical findings

This is read-only research, not approval of root component C or a replacement
for its independent review. Own branch codex/objective-fov-source-research-20261024
starts at exact 102d79f22082b9c077e2feaccefc84f8985c5875. Root r4's observed handoff
HEAD f7f01d3c has identical game/probe bytes. All production source, canonical docs,
original fixture/result bytes and the existing route-clock branch/head stay
unchanged. No native, engine, compiler, process activation, CI or Mac review ran.
Only bounded source reads and report-local Python arithmetic/adjudication ran on
CPU4. Existing helper thread was reused for a read-only source cross-check; no
new reviewer thread or fresh-thread context is claimed.

## Source gates and state invariants

bot_ai.gd354–405 filters living enemies, then range, FOV, visibility and score in
that order. Range rejects only distance>vision_range; equality reaches FOV. FOV
uses facing=(-sin(yaw),0,-cos(yaw)) and normalized THREE-DIMENSIONAL enemy−actor
position, not an XZ-only direction. Pitch is absent. Strict dot>fov_dot is the
only geometric comparison at377–379. The specific recent attacker can bypass
FOV when elapsed−damaged_at<1.2; it cannot bypass range or can_see(). These age
checks have an upper bound only: adding age>=0 would change this source predicate.
A separate valid-history invariant may reject future damage timestamps.

After every gate passes, score starts from source-observed distance and subtracts
current-target 4.5, carried-device carrier 3.5, designated planted defuser 6.0 and
specific recent attacker 4.0 bonuses (390–398; hysteresis constant 13). GDScript float
variables here are double scalars. Strict score<best_score preserves the first
candidate in actual iteration on an exact tie (360,402–404). At exact range with
no bonus, an eligible enemy can remain unselected. Hysteresis/current target is a
score bonus; it does not bypass FOV or visibility.

_acquire_target and the perception wrapper 578–584 do not change target memory.
compute_bot_input 636–645 resets reaction/burst when target changes, then stores
target ID, last_seen position and seen_at=elapsed, increments reaction by delta,
and optionally shares a sighting. _share_sighting 442–452 records position/time/
reporter ID in the actor team's contacts. Team reports at427–440 update heard
memory, not seen memory or an acquired target.

Without an acquired target, target/reaction/burst_time/burst_cooldown reset at
719–723, while last_seen/seen_at remain. Memory pursuit at747–754 requires age
strictly below profile memory_duration, no interaction and an unplanted objective.
It changes effective navigation destination/role, not target acquisition or fire.

An acquired target always enters combat 636. It chooses combat_cover, combat_brake
or combat_strafe at685–711, even when final interaction prevents movement. Firing
also requires reaction threshold, alignment, no interaction and no burst cooldown;
held semi-auto input suppresses fire at675–683. A combat label alone does not
prove firing. Final movement is zero when interacting (800), independently of
the diagnostic movement label. Do not require interaction to erase an already
selected combat label; the label records the source branch.

nearest_defender 270–283 immediately returns the first living human defender
holding interaction within<=2.8 according to actual dictionary iteration.
Otherwise bots use squared distance<nearest OR approximate equality with lower
actor ID. A strictly closer bot always replaces; a slightly farther lower-ID bot
can also replace within source approximate equality. This is not a simple nearest
Euclidean-distance sort or a symmetric approximate-distance bucket.

## Pinned engine math

All fetched sources are pinned to Godot 4.7.2 engine commit ed1daf0bf; no other
version was substituted. Each accompanying JSON retains exact URL, full file
byte count/SHA256 and line-numbered excerpts.

- [Vector3 fields/constructor](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/vector3.h#L63-L73)
  use real_t; constructor226–227 converts component values to that type.
- [real_t definition](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/math_defs.h#L138-L147)
  is float unless REAL_T_IS_DOUBLE is defined.
  [SConstruct192](https://github.com/godotengine/godot/blob/ed1daf0bf/SConstruct#L191-L193)
  defaults precision to single;596–597 sets the double define only for double
  builds. This is pinned source/default evidence, not a runtime precision readback.
- [Vector subtraction405–406](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/vector3.h#L405-L407),
  length532–545 and normalize548–571 operate on real_t. Normalization tests
  length_squared()==0 exactly and returns zero for that case; it does not apply
  is_equal_approx. Nonfinite input components are also zeroed by normalize.
- [Dot252–254](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/vector3.h#L252-L254)
  sums real_t component products. Python math.dist/math.hypot and float64 vector
  calculations do not automatically reproduce those intermediate roundings.
- [Variant sin/cos43–48](https://github.com/godotengine/godot/blob/ed1daf0bf/core/variant/variant_utility.cpp#L43-L49)
  take/return double and call Math sin/cos; math_funcs.h41–52 delegates to std::sin/
  std::cos. Conversion to Vector3 then occurs. A profile fov_dot held in GDScript
  float remains a double threshold; do not round it to binary32 merely because
  the dot result originated in Vector3.
- [Variant is_equal_approx351–352](https://github.com/godotengine/godot/blob/ed1daf0bf/core/variant/variant_utility.cpp#L351-L353)
  calls the double overload. [math_funcs.h528–538](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/math_funcs.h#L528-L538)
  checks exact equality first, then abs(left−right)<max(CMP_EPSILON*abs(left),
  CMP_EPSILON). [CMP_EPSILON](https://github.com/godotengine/godot/blob/ed1daf0bf/core/math/math_defs.h#L50)
  is 0.00001. This strict/asymmetric tolerance concerns nearest_defender's squared
  distances; it is NOT an FOV tolerance. Reusing it to accept near-cutoff FOV
  labels would weaken the source condition.

core/typedefs.h was fetched but no real_t definition was found there; the exact
same pinned revision's math_defs.h contains it. The empty search result and file
hash remain retained rather than treated as a missing pinned version.

## Independent fixture adjudication

The three original captured pose tables 120/122/127 contain 106 living actor/enemy
pairs: 52 outside vision range and 54 in-range FOV passes in the source float64
geometry model. That subset alone contains no in-range FOV rejection. It does
not establish LOS or certify native cutoffs. ALL_CAPTURED_ACTOR_GEOMETRY.json
retains the rows; original bytes remain hash-bound.

The actual synthetic helper's defuse control changes actor 6 to team 1 and position
[-15,0,10] while preserving yaw −3.13781332969666 (test helper98–101). Its living
enemies 8,9,10 are in range, but their dots are respectively−0.86991594,
−0.81421278 and−0.70443729 against threshold−0.15. Thus the helper's unconditional
in-range visibility label at41 is source-inconsistent for those defuse rows.
CONTROL_PLACEMENT_GEOMETRY.json retains exact positions/yaw and computed margins.

For the known clear-positive mutation, captured pose 122 actor 6→enemy2 has distance
33.20634512187203 and model dot 0.9937165070415048, far above−0.15. A recorded fov
rejection contradicts that source geometry. Keeping those captured positions but
using report-only yaw 0 gives dot −0.9983745963273363, a clear source-model rejection.
This second geometry is explicitly synthetic; original yaw was not changed.
CLEAR_AND_UNRESOLVED_CASES.json preserves both and exact-axis constructions.

Minimum fixture correction is a source-ordered classifier: range first; then
strict FOV with the specific-attacker exception; then declared blocked visibility.
Do not change original fixture bytes/results. Make a new fixture revision, retain
the old defuse mislabels, and label declared LOS as synthetic rather than a native
ray-query observation. Other visibility/eligible distinctions still need actual
can_see evidence; FOV geometry alone cannot establish either.

## Minimal predicate and unresolved boundaries

Report-only fov_reference.py computes the source formula from captured positions/
yaw and includes the zero displacement behavior and recent-specific-attacker
predicate. It is not installed in production validation. Its strict adjudicator
accepts trusted native-dot bounds only as verifier policy/calibration, never as
an untrusted trace field. If no such bounds exist or they straddle the strict
threshold, it returns UNRESOLVED_NATIVE_NUMERICS. That status is neither a pass
nor permission to accept either reason. Recent-attacker timing must independently
be unambiguous before using that exception.

Both Python float64 and the recorded nominal sequential-binary32 shadow are
source arithmetic tools. The shadow uses host libm and explicit rounding; it is
not compiled Godot, a verified compiler/FMA configuration or a portable native
sin/cos error bound. Agreement between the two does not certify a cutoff. No
fixed broad epsilon or uncalibrated ULP allowance is proposed as acceptance.

Remaining calibration needs, under separate root native admission, are the exact
pinned binary precision/build/architecture; Vector3 construction/subtraction/
normalize/dot outputs at representative source values; double sin/cos conversion;
zero/underflow/overflow behavior; comparisons just below/at/above each relevant
profile cutoff; and serialization roundtrip. Capture the actual dot and threshold
or a defensible bound tied to the exact primitive sequence. Near 1.2-second damage
age and nearest-defender approximate-equality edges need their own source-domain
adjudication. No such native math/calibration was run here.

The original impossible-history cases must still reject. Ambiguous numerical
rows remain unresolved/blocked until their bound is established; they cannot be
silently passed to preserve a historical positive. Root C may proceed with the
separate source-observed-distance/double-bonus checks, clear source-geometry
controls and a disclosed unresolved cutoff gate. This research approves none of
that implementation or native behavior.
