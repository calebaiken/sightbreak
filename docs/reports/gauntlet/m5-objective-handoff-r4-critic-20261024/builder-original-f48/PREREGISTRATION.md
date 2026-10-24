# Objective action/consumer continuity component

Base code is independently accepted decision component bc9f945d, report-only
head b2370e68; source game/probe remain d27f5a57. Independent final e87aa165
accepts only four decision guards and reproduces all eight remaining false
accepts. Root builds this next component in its own R4 branch/worktree.

Named correctness benchmark: exact fixed Match _eliminated/_authority_tick and
probe _control source, plus the unchanged independent13-case falsifier script.
Six current false accepts are this component's requirements: unearned100credits,
planting before objective consumption, injected progress, team reassignment,
isolated non-subject teleport and match RNG drift without a decision. The two
perception/score cases remain blocking and out of this component.

Source-derived invariants before edits:

- Movement/action phase cannot advance objective timers, progress, contributions,
  scores, rounds, phase or time_left. It can drop a carried device only when its
  carrier is eliminated; dropped position is that actor's post-action position.
  Picking up, planting, defusing or detonating occurs inside the later consumer.
- Actor teams remain fixed. Match _eliminated increments each actual victim's
  death and an opposing killer's kill counter/300credits, clamped9000. Bind credit
  changes to kill deltas, nonnegative kill/death transitions and opposing deaths;
  do not treat fabricated damage/physics as validated.
- Probe isolated controls simulate only actor6 movement/actions. Other actors'
  positions remain stationary. Match RNG after the optional thinking call must
  reach the objective consumer unchanged. Capture/validate the complete post-
  decision handoff, retaining legal subject movement/resources and combat changes.

Change only offline verifier and meaningful existing pure tests, plus a new
current acquisition inventory. Preserve old R2/R3 inventories/raw/fixtures and
source; no game, probe, AI, RNG, authority, transport, economy or native behavior
changes. Keep four accepted decision guards and original contradictory-no-op
history. No fixture normalization is planned; report source conflicts before edits.

Require unchanged13-case rig to accept its corrected schema-positive and reject
all four old decision plus six handoff mutations; the remaining two acceptance
failures keep whole-reader readiness blocked. Retain exact regenerated inputs,
hashes, errors and original comparison. Run meaningful positive elimination/
clamping/carrier-drop and no-change controls, new negatives and all maintained
methods, complete451-path acquisition inventory/all513 protected-source union.
Independent evaluator must inspect actual results in separate initialized views;
root cannot approve itself. CPU4 pure/static only. No native/CI/export or platform
claims; existing-thread reuse/alternate storage limits remain explicit.
