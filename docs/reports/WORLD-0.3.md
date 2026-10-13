# Relay Yard world presentation — 0.3 development

## Screenshot findings

The actual native 0.2 approach, site and overview captures under
`docs/reports/media/environment/*-after.png` were reviewed before editing.
The five strongest world deficiencies were:

1. A flat, generic perimeter with little recognizable architecture.
2. A crane silhouette that lacked the structural detail expected at its scale.
3. Cargo containers and low cover that read as clean boxes rather than equipment.
4. Sparse human-scale utilities and a weak connection between relay objectives and the setting.
5. Homogeneous surface response, large floating-looking labels and limited lighting depth.

## Implemented changes

- Transfer hall docking doors, frames, roller slats, impact stripes and service lamps;
  roof fascia, columns, elevated side walkways and rooftop air handling units.
- Paired crane I-sections and diagonal struts, column feet, trolley and hoist block.
- Broad articulated sidewall bays, louvered service recesses, graphite/crimson route
  fascia and restrained ground resurfacing give the yard a coherent architectural rhythm.
- Fitted container corner castings, hinges, locking details and data plates;
  reinforced low-cover transit cases with handles, latches and corner protection.
- Flush wall cabinets, vents, cable ladders, ground drainage and buried relay routes.
- Graphite structures, crimson cargo and muted-gold engineering accents. Teal remains
  a secondary route cue. Shallower warm sun and cooler ambient illumination provide depth while retaining target contrast.
- Small original, reproducible 128px normal and roughness maps. The low graphics preset
  removes both optional maps; there are no screen-space effects or additional dynamic lights.

All additions are actual engine geometry. Decorations remain on existing collision
shells, outside the playable boundary, or above player clearance. The existing 25
navigation obstacles, 26 physics bodies, ten spawn points and two objectives remain.
This preserves the tested combat layout; the additions are an art pass rather than a new map.

## Cost and ownership

`world_test.gd` reports 1,460 box instances in 75 shared-material batches. This is
construction evidence, **not** a total renderer draw-call measurement. The hardware
pieces share one unit cube mesh; empty temporary construction nodes are released.
There is one directional light and the retained shared `RELAY_SKY` resource.

Nine 128px world surface maps bound the source texture set. Six companion maps add
roughly 0.5 MiB of uncompressed RGBA storage including full mip chains; actual renderer
texture allocation is measured by the separate benchmark. Low preset disables optional
lookups but does not unload the retained textures or remove readable structures.

`python3 scripts/generate_surfaces.py` regenerates all maps using seeded Python standard
library algorithms; no external photography, downloaded assets or runtime noise shader
is involved.

## Verification

`./scripts/godot.sh --headless --script res://tests/world_test.gd`:
25 assertions passed, including objective routing, batch bounds, cleanup, finite
instance transforms, shared-sky identity, mipmaps, graphics-quality toggling,
roof equipment support, loading-door sign clearance and inward wall text orientation.
All nine generated PNGs were also regenerated and confirmed byte-identical.

Rendered comparisons and independent scoring are recorded separately in `QA-0.3.md`.
Headless assertions do not establish visual quality or physical-device performance.

## Iteration after the first native captures

The reviewer found two visible first-pass defects: one rooftop air handling unit sat
beyond the actual roof, and a new loading door obscured part of the old wall brand.
Both were corrected in geometry/sign placement and covered by regression assertions.
The reviewer also requested broader architectural composition rather than more small
hardware. The second pass adds full wall bay framing and route fascia, reduces exaggerated
paint normals, grades the palette, and subdivides the broad ground plane with maintenance
surfacing. Independent scores remain the reviewer's assessment in `QA-0.3.md`.

Final fixed-view native captures are saved in
[the before/after gallery](media/v03-world/README.md). The independent reviewer
confirmed all three discovered presentation defects closed: supported roof units,
clear brand lettering and correctly oriented side-wall labels. The final world
scores remain below the requested 8.5 gate; see the independent rubric report.
Broad material planes, primitive construction and simple daylight are the next art
quality limitations to address. No physical mobile thermal, battery or performance
claims follow from these software-rendered pictures.
