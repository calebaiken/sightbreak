# Critic round 4: blind A/B, Relay Yard layout (final build)

Reviewer: a fourth general-purpose Claude subagent, fresh context, read-only. Same model family as the builder, so **not independent human acceptance**. Stills only.

- Candidate under test: the shipped layout (screen wall with two exits and a solid middle, exit blocks, lane dividers, site shields, spine extensions, deeper defender anchors, label plates sized to their text).
- Bar: the previous verified build, `db3981e` (bar B3).
- Pairs rebuilt with a new seed. The critic again named the layout it picked in every pair.

## Decoded result

Every layout naming matches the private key.

| Pair | Candidate was | Critic's letter | Truth |
| --- | --- | --- | --- |
| overview | A | A | new layout |
| 0 | B | B | new layout |
| 1 | B | A | previous layout (capture artifact, see below) |
| 2 | B | B | new layout |
| 3 | A | A | new layout |
| 4 | A | A | new layout |
| 5 | B | tie | tie |
| 6 | A | A | new layout |
| 7 | B | B | new layout |
| 8 | B | B | new layout |
| 9 | A | A | new layout |
| 10 | B | tie | tie |
| 11 | A | A | new layout |

Overview: new layout. Eye level: new 9, previous 1, tie 2. Critic's score for the new layout: 6/10 on tactics, as a record only.

**Pair 1 is a defect in the capture script, not in the layout.** Viewpoint 02 stood at (0, -17), the middle of the screen wall. The mid exit used to be there; once it was closed, the camera sat inside the solid mid container, which the critic correctly reported as "the camera is inside the bar". The viewpoint now stands in the mid pocket at (0, -13). The frames in `images/` use the corrected viewpoint; the critic saw the old one.

## Largest remaining gap (critic)

> Route structure. The centre is sealed and the spawn has only two exits. The 11 m by 20 m centre alley has long stems on both sides with no connector to either site. Each site is reached through one slalom of container gaps about 2.4 m wide. Attackers choose only between A and B; defenders can stack two entries. A shipped map gives a third axis and connectors.

Note for the record: mid connects to both side lanes through the crossings at z -6.5..0, and the layout deliberately keeps mid out of the spawn exits (see the design document, "Tried and dropped"). Whether that reads as a third route to a player is a question for a human playtest.

## Defects the critic listed

Specific to this work:

- Pair 1, camera inside a container: the capture artifact above.
- Pairs 5 and 10, right panels: a thin slanted slab with a plate reads as a leaning or sheared container. Not investigated; may be the corner castings and label plate seen at an angle.
- Pair 6: the "RY / 71 SITE A STORES" plate is crossed by shadow stripes, last letters crowding the edge. The critic was not sure.
- Several frames from the spawn and the exit blocks show a plain container face filling the screen (pairs 0, 2, 3) and look worse than the open frames of the old layout.

Present before this change:

- A yellow hoist block with no cable at top-centre (pair 8), a flat pale far boundary with text printed on it (pairs 8, 9, 11), the bomb-device box nearly invisible against a near-black floor in shadow (pairs 7, 9), an almost black defender floor with one faint trapezoid decal (pair 8), and the repeated "RY / 07 FREIGHT SYSTEMS" plate on the original containers.

## Could not judge (critic)

Collision and walkability of the 2.4 m slits and a 1.3 m gap by the yellow track, container heights and anything climbable, whether the roll-up doors open, timings, bot behaviour, the east side at eye level, and which layout is which in pairs 5 and 10.
