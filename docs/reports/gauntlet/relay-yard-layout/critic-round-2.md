# Critic round 2: blind A/B, Relay Yard layout

Reviewer: a second general-purpose Claude subagent, new instance, fresh context, read-only, no access to round 1. Same model family as the builder, so **not independent human acceptance**. Stills only.

- Candidate under test: layout v2 (round 1 findings applied: unique tags and hardware on every layout container, consistent colour code, stencils moved into the exits, lane dividers, second mid baffle). Captured before the second mid baffle was dropped.
- Bar: the previous verified build, `db3981e` (bar B3).
- Pairs were rebuilt with a new seed. The A/B assignment is re-randomised per pair, which the critic noticed and worked around by naming each side by what it shows.

## Decoded result

The critic named its winner's layout in every pair. Every naming matches the private key.

| Pair | Candidate was | Critic's letter | Truth |
| --- | --- | --- | --- |
| overview | A | A | new layout |
| 0 | B | B | new layout |
| 1 | A | A | new layout |
| 2 | B | B | new layout |
| 3 | A | A | new layout |
| 4 | B | B | new layout |
| 5 | B | B | new layout (near tie) |
| 6 | B | B | new layout |
| 7 | B | B | new layout |
| 8 | B | B | new layout |
| 9 | A | A | new layout |
| 10 | A | A | new layout |
| 11 | B | A | previous layout |

Overview: new layout. Eye level: new 11, previous 1. Pair 11 was lost because the camera stood 0.4 m from the face of the second mid baffle; that baffle was removed afterwards (it blocked the test fixtures on x = 0). Pair 11 is not re-captured; the loss is recorded as is.

The critic scored the winning layout 5/10 as a record. It closes no gate.

## Largest remaining gap (critic)

> The sites and the south apron are unchanged and weak. Each site is a bare 7 m square on a 45 m wide, 15 m deep open apron, 14 m in front of the defender spawn. One crate each, and nothing breaks the 31 m site-to-site line. A shipped map gives the site a protected plant pocket, a second entry and post-plant cover.

Response in this milestone: the two long spines were extended south (layout v3) so each site sits in its own compartment and the site-to-site line is cut. Plant pockets and post-plant cover remain open work.

## Defects the critic listed

Introduced by this work and fixed afterwards:

- Label plates covered only the first line of a two-line tag, leaving line two grey on grey. Plates are now tall enough for two lines (applies to every container).
- Pair 11, camera inside a baffle: removed baffle.

Already present on the base and not changed here (carried to the visual-polish backlog):

- Floating yellow hoist block with no cable or rail (pair 8).
- Flat, detail-free far wall and tiny garbled far sign (pairs 8, 11).
- Gantry canopy overprinting the "TRANSFER STATION" and "RELAY YARD CONTROL" lettering (pairs 4, 5, 6, 10).
- "KEEP CLEAR" decal hard-edged, and upside down for anyone facing south (pairs 0, 2, 5, 11).
- Hard-edged lighter floor wedge on the defender apron (pair 8).
- Sun glare disc in the attackers' eyes (pairs 4, 6).
- Site letters are small floor decals partly hidden by the plinth; no overhead site marker (pairs 7, 9).
- Developer name "SIGHTBREAK" on a world sign (pair 10).
- Near-black shadow over the defender half (pairs 6, 7, 9).

## Could not judge (critic)

True gap widths, elevation, bot pathing and balance, grenade and smoke lines, sound, spawn timing, true scale, and whether the T-shaped container groups intersect.
