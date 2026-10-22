# Critic round 1: blind A/B, Relay Yard layout

Reviewer: a general-purpose Claude subagent with fresh context, read-only, no knowledge of which side was which. Same model family as the builder, so this is **not independent human acceptance**. It saw stills only.

Material: one top-down overview pair and twelve eye-level pairs, built by `scripts/ab_pair.py` with a private key. Side A is the left image, side B the right.

- Candidate under test: layout v1 (spawn screen with three exits, exit blocks, site shields; 2 m navigation grid). Source: branch `claude/relay-yard-tactical-layout-v1`, working tree before the first layout commit.
- Bar: the previous verified build, `codex/desktop-playability-p1` at `db3981e` (bar B3). This proves improvement, not parity with a shipped title.

## Decoded result

| Pair | Candidate was | Critic's winner | Truth |
| --- | --- | --- | --- |
| overview | B | B | new layout |
| 0 | A | A | new layout |
| 1 | A | A | new layout |
| 2 | A | B | previous layout |
| 3 | A | B | previous layout |
| 4 | B | B | new layout |
| 5 | B | tie | tie |
| 6 | A | A | new layout |
| 7 | A | A | new layout |
| 8 | B | A | previous layout |
| 9 | A | A | new layout |
| 10 | A | tie | tie |
| 11 | A | A | new layout |

Overview: new layout. Eye level: new 7, previous 3, tie 2. The previous layout won pairs 2 and 3 (exits looking south) on readability: the v1 exit block was a blank, unlabelled wall four metres ahead. It won pair 8 (defender spawn looking north) on sightline: v1 left the mid lane open to the horizon there.

## Findings that changed the build

1. The exit blocks and baffles were blank slabs carrying the same "RY / 07 FREIGHT SYSTEMS" sign as every container. Fixed: hardware fittings and unique tags on every layout container.
2. Container colour code (west red, east teal) was inverted on the site shields. Fixed.
3. The floor stencils "01 / FREIGHT" and "02 / RELAY" were overprinted by the new screen wall. Fixed: moved into the exits at a smaller size.
4. The central avenue had no mid-distance cover. Partly fixed (lane dividers); the yard centre is deliberately left open for test fixtures, see the layout document.
5. Sites are open aprons without staged entrances. Carried into v3 (spine extensions) and logged as the largest remaining gap.

## Report as delivered

The critic's report follows, abridged: the pixel coordinates it quoted and several repeated defect lines were removed. The full transcript was not preserved.

```
RELAY YARD A/B BLIND REVIEW (read-only; nothing created or edited)

1. OVERVIEW: B wins. B puts T-shaped container pairs in front of the attacker spawn, chicane boxes in the west and east lanes and site-adjacent containers. That gives diagonal spawn cover, pockets, and cover at the sites. A is a sparse symmetric grid: the sites have one crate each and the lanes beside the central columns are open for roughly 25 m with a single crate in each.

2. EYE-LEVEL PAIRS
- Pair 0: A. A shows a pale container about 6 m ahead with narrow gaps on either side, so the spawn exit is a corner. B shows 35-40 m of open floor to two crates and a shutter.
- Pair 1: A. A has a blank pale slab at 6 m and B has a 30 m clear avenue. A cuts the sightline but gives no information; B is a gallery.
- Pair 2: B. B has layered mid-lane cover: a crate at about 12 m, a red container, a pale container and a "STAFF" door. A is just a blank wall at 6 m.
- Pair 3: B, for the same reason.
- Pair 4: B, marginally. B adds a dark container in the gap, which adds a layer.
- Pair 5: Tie.
- Pair 6: A. A has a container 2-3 m to the right that forms a gate at the site entrance. B opens that side onto a facade.
- Pair 7: A, slightly. A leaves a slot about 2.5 m wide between the dark container and the red one.
- Pair 8: A. A has a pale container at the far centre that breaks the defender-to-attacker-spawn line. B is open to the horizon.
- Pair 9: A, slightly. A has a red container dead ahead at about 8 m, giving a choke.
- Pair 10: Tie.
- Pair 11: A. A has a pale container at the far centre. B is clear through the middle to the horizon sign.
- Tally: A wins 7 pairs (0, 1, 6, 7, 8, 9, 11), B wins 3 (2, 3, 4), 5 and 10 are ties.

3. LARGEST REMAINING GAP IN THE BETTER MAP (B)
The central avenue between the two long container rows has no mid-distance cover and gives spawn-to-spawn exposure: about 11 m wide and 35-40 m long. The sites are also open aprons with no staged entrance.

4. REGRESSIONS AND DEFECTS
- A large blank pale container with the same "RY / 07 FREIGHT SYSTEMS" sign sits dead centre at four camera positions, filling 40-55% of the frame.
- Overview: the T-head containers overprint the floor stencils, so they read "01 / FRE" and "/ RELAY".
- Overview: the central columns use red on the west and teal on the east; a teal box on the west and a red box on the east break that colour code.
- Both: a floating yellow hoist block at the top centre has no cable or rail. The far end is a flat pale band with a floating sign.
- Both: "RY / 07 FREIGHT SYSTEMS" is on every container, which weakens orientation.
- Both: very hard, near-black shadow over the defender half; sites read only through their painted outlines.
- A floor decal "KEEP CLEAR" is a hard-edged pale rectangle that reads as a texture seam.

5. COULD NOT JUDGE
Heights and climbability, collision and navigation, bot paths and rotation times, whether the T-shaped groups intersect, audio and performance.

6. OVERALL WINNER: B, narrowly. Score for B's tactical layout: 5.5/10 (record only).
```

The score is the critic's judgment, recorded for the file. It closes no gate.
