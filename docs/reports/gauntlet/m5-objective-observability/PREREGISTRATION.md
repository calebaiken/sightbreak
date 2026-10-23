# M5 objective decision observability

This is a diagnostic source candidate. It changes no bot policy. Builder work
starts from `022d60faa830696af3f03c554e99356c1beac0dd`, branch
`codex/m5-objective-observability-20261023`, in its own initialized sparse
checkout. Native execution, import, export, CI and aggregate validation are held
for root release and a fresh independent critic. Pure checks use CPU 4.

## Inspected bar and failure

The concrete correctness bar is the current production AI/authority source,
retained in `benchmark-identity.json`, and the original stock Windows match at
`0527715`, archive `windows-qa-12409593990.zip`. The archived 179-event journal
was read directly. `original-timeout-slice.jsonl` contains five unmodified original
lines: initial seeds/rules, two LIVE poses, timeout notification, and POST pose.
The archive, member and selected bytes have separate SHA-256 identities.

Event 126 records a natural time expiry at tick 19210. Event 127, tick 19213,
shows carrier 6 alive, 100 HP, SMG 30/0, four attackers and two defenders alive.
The journal lacks AI memory, actual selected target, LOS result, goal, waypoint,
input, RNG state and per-bot interaction rejection. A terminal pose and facing
cannot establish any of those. POST also neutralizes input. Earlier `a089473`
has zero plants; inspected `b2e0293` records one stock plant and the later
`e28c8e9` review reports broader objective events. Preserve those counterexamples.
No blanket never-plants claim or whole G1/G2 acceptance follows.

## Components and bounded implementation

1. Perception and planning: an optional caller-owned dictionary records only
   values already computed by the real `SBBotAI.compute_bot_input` and
   `acquire_target`. Record each candidate's range/FOV/visibility rejection,
   selected target, plan/effective destination, movement branch and waypoint,
   role, final command and RNG state. Do not call a selector, visibility query,
   navigation query or RNG a second time to create a trace. Disabled/default,
   nondebug and nonoffline paths collect nothing.
2. Authority and interaction: a test-only `TacticalMatch` subclass observes the
   existing `_objective_tick` before and after `super`, with actual actor pose,
   input, site/distance, eligibility and `_interactions`. Production `match.gd`,
   actor, map, weapons, economy, authority ordering and shared RNG stay unchanged.
3. Bounded fixture: read the retained original pose/seed data. Reconstruct one
   actual decision at each of the three poses, and a short forward slice from
   the terminal pose under the stock rules. Missing historical memory/recoil,
   holstered resources, utility and RNG state are declared reset assumptions,
   not a replay. No source pose, seed or gate is selected by outcome. Include
   at-site plant/defuse and wrong-site/moving/no-interact authority controls.
   Do not require the reconstruction to plant or win.

## Falsifiers and evidence contract

- On/off paired computation starts from identical bot/team/heard/input state
  and identical match/actor RNG state. Require identical final input, bot/team
  state, actor resources and RNG. Reject mutation or missing pairs.
- An erasure audit must recover the byte-identical baseline AI after removing
  only marked observation additions and restoring the two call signatures and
  call argument. Hash all unchanged gameplay files against the inspected base.
- The future native fixture must use real Relay Yard physics and production
  visibility, navigation, movement, action and objective consumers. A query is
  preceded by two physics-frame barriers. No injected visibility.
- Positive controls must reach actual 3-second plant and 5-second defuse through
  ordinary bot interaction commands and production authority; negative controls
  must reject invalid interaction and reset existing progress.
- A strict offline parser must reject truncated/duplicate/missing records,
  malformed traces, changed commands or protected state, missing controls,
  missing terminal result, and any nonempty native failure list. Synthetic parser
  inputs are unit controls, never native evidence.
- Native work requires a new root release. Proposed acquisition: one fixture
  invocation, stock time scale 1, at most 60 seconds for the fixture and separate
  120-second import cap, fresh private state/output, strict stdout/stderr and
  source/UID/cleanup receipts. No retry, long campaign or tuning is authorized.
  Source-only success does not establish GDScript compilation or runtime parity.

The largest open gap is the absent historical decision stream. This fixture can
explain a bounded reconstruction and qualify passive observations for later stock
matches; it cannot retrospectively identify why the original carrier timed out.

Implementation clarification, after writing the fixture source and before any
native execution: the forward slice uses event
122, the last retained actual LIVE pose. POST event 127 has a 4.95-second POST
timer, which cannot stand for unknown remaining LIVE time. Event 127 is used for
one paired decision only, explicitly changing its phase to LIVE. The forward
slice retains event 122's original LIVE phase and remaining time. Isolated
interaction controls keep other actors stationary while the subject uses real
movement/actions and every actor remains subject to the objective consumer.
