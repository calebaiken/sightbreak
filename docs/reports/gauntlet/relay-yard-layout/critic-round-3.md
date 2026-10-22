# Critic round 3: blind A/B, Relay Yard layout

Reviewer: a third general-purpose Claude subagent, fresh context, read-only, told not to look for other files. Same model family as the builder, so **not independent human acceptance**. Stills only.

- Candidate under test: layout v3 as captured before the last two changes (mid exit widened from 6 m to 8 m with navigation doors, label plates sized to their text, attackers assigned to exits). Layout v3 = v2 without the second mid baffle, plus the spine extensions, and with the deeper defender anchors drawn as yellow dots.
- Bar: the previous verified build, `db3981e` (bar B3).
- New blind pairs, new seed. The critic noticed the per-pair re-randomisation and named the layout it picked each time.

## Decoded result

Every layout naming matches the private key.

| Pair | Candidate was | Critic's letter | Truth |
| --- | --- | --- | --- |
| overview | A | A | new layout |
| 0 | A | A | new layout |
| 1 | A | A | new layout |
| 2 | B | A | previous layout |
| 3 | B | A | previous layout |
| 4 | B | B | new layout |
| 5 | B | tie | tie |
| 6 | A | A | new layout |
| 7 | B | B | new layout |
| 8 | A | A | new layout |
| 9 | A | A | new layout |
| 10 | B | B, "near tie, slight edge" | new layout (weak) |
| 11 | A | A | new layout |

Overview: new layout. Eye level: new 9 (one weak), previous 2, tie 1. The previous layout won pairs 2 and 3 for readability and staggered cover: in the new layout the exit blocks put a blank container face 4 m from the camera. The critic called the open plaza the better-looking space in pairs 1, 2, 3, 8 and 10 and the new layout the better tactical space in 0, 1, 4, 6, 7, 8, 9 and 11.

Critic's scores, as a record only: new layout 6/10 on tactics, previous layout about 3.5/10.

## Largest remaining gap (critic)

> The new layout has no sightline longer than about 25 m and no height variation. Most north-half views end in a 2.6 m container face within 4 to 7 m. The only low cover is the cream crates. No ramp, stair or platform in any view; the catwalks are wall-mounted. A shipped map of this class has one deliberate long power lane and some elevated or half-height position.

Second gap: the attacker exit in pair 0 was a corridor of about 4 m with gaps of about 1 m either side, where five players leaving together would jam.

Response in this milestone: the mid exit was widened to 8 m with two 2 m passes and extra navigation nodes (a check afterwards found the old mid exit was **not navigable for bots at all**, which is why they never used it). A long lane and elevation are not addressed; both are logged below.

## Defects the critic listed

- Sign text overflows the dark backing plate, pale grey on pale grey ("FREIGHT SYSTEMS", "CABLE DRUMS", "SPARE PLATES"). Cause: the plate was 1.9 m long and a 15-character stencil is about 2.9 m. Fixed afterwards: plate length follows the longest stencil line.
- Repeated "RY / 07 FREIGHT SYSTEMS" on the original containers weakens orientation; the new containers' unique tags help.
- Possible clipping in pairs 5 and 10 (slanted dark slabs against container ends): not confirmed by the critic. Not investigated.
- A small black spiky silhouette above a far container in pair 3 (left image): unexplained, not investigated.

Present before this change and not touched: floating "01 FREIGHT" text in the haze, a flat pale north edge with no building, hard-edged "KEEP CLEAR" slabs, a lighter trapezoid on the defender apron, near-black bomb device on a near-black floor in shadow (pairs 7, 9).

## Could not judge (critic)

Heights and jump clearances, whether gaps of about 1 m are passable, collision and navigation, rotation times, bot behaviour, the gantry strip and catwalk access, lighting at other times of day, audio.
