# Source and attribution

This is builder source support, not independent acceptance. A separate read-only
agent inspected Claude PR28 head `2641ddf` and authored bot delta
`0871bc92b014fdb020cb1ac681fe70637f6cf6cd` before adaptation. The product base is
root `42ff3dc`, including independently reviewed phased authority `f13ed03`.

Commit `06092d0` preserves Claude's author identity, Claude Sonnet 5.5
co-authorship, source commit and PR URL. Its entire `bot_ai.gd` blob exactly
matches the authored PR28 bot blob. PR28's shuffle and shuffle tests were excluded.
Commit `c2b3ded` separately adds our two root-authorized sine-phase adaptations.
No arena, actor, match authority, network, platform or economy product file changes.

The original delta supplies `squad_index = (actor_id - 1) % 5` for actor IDs 1–10:

| Habit | Candidate mapping |
| --- | --- |
| Habit crouch | Slots 0 and 3 in both squads |
| Noncarrier attacker smoke | Slots 0, 2 and 4 in both squads, subject to existing gates |
| Unstick direction | Positive X for slots 0, 2 and 4; negative X for 1 and 3 |
| Defender destination | Normal/hard anchors 0–4; easy sites 0,1,0,1,0 |
| Combat strafe phase (our extension) | Existing sine keyed on slot 0–4 |
| Idle scan phase (our extension) | Existing sine keyed on slot 0–4 |

The old defender anchor formula gives low IDs `[0,2,3,4,0]` and high IDs
`[0,1,2,3,4]` with signed GDScript remainder. Original prose describing every low
slot as shifted overlooks `-5 % 5 == 0`. The candidate gives both `[0,1,2,3,4]`.

Modulo-five attack roles, planted hold offsets and buy variation were already
paired under ID+5. Identity keys, carrier/target equality and reporting IDs stay
as identities. The shared RNG stream and actor iteration are unchanged; equal
fixture RNG state is not a claim of identical random exposure in complete matches.

## PR28 observation limits

The inspected PR28 `bot_objective_metrics.gd` runs at time scale 4 by default,
which changes physics delta. Its seed option does not seed PR28's `_order_rng`.
Its `--reverse-order` reverses dictionary insertion, but PR28 then shuffles it;
later rounds also assign spawn slots and carrier through that iteration order.
Its start swap flips teams and repeats round-one setup. Its statistical reader
does not require complete terminal records or exact seed/start coverage.

The optional retained tooling here uses no order override, validates terminal
coverage and records winners by actual squad IDs. It also repeats round-one
setup after seeding in both initial-side conditions. Swapped starts and time
scale 4 remain artificial controls. No observation match was run in this slice;
root omitted the fixed eight-match set before any sample started to prioritize
the original-budget native layout rerun. Tooling is retained for future work,
not presented as verified match measurements or earned progression.
