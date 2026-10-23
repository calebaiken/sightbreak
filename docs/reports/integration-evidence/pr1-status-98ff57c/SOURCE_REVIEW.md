# PR1 status fitting follow-up: source review / pending execution

Exact candidate: `98ff57c4a9ec6735db68c4e65ad36f6fe5a26ca6`.
Previous independently tested foundation: `227d6c8245a75522b8144c8004de2a86d61b833b`.

The candidate adds a MarginContainer around the status Label and recomputes horizontal margins from permitted stretches between actual drawn touch targets. It preserves the original full row when touch controls are disabled. Gameplay, account, backend, weapon/hit volume and protocol code are unchanged. Existing tests are preserved; landscape assertions grow from196 to325. New tests exercise four display sizes, four text scales, buy/attack/defuse/long notification, and desktop centering.

This is a reasonable targeted correction of the default-layout defect previously observed at130%. Runtime acceptance remains pending fresh independent execution, deliberately held until the parent's isolated rendering measurements finish.

## Specific edge cases requiring execution

1. **No available stretch:** `free` can be empty for a permitted custom HUD, but the function leaves `span` at the original full row. At960px with150% buttons, place the11 drawn targets evenly across the status band. Their radii plus8px clearance fully cover the row. The code therefore has no custom-layout fallback that preserves clearance. This is likely a limitation of the broad custom-layout claim rather than a newly introduced defect.
2. **Narrow center stretch:** the interval holding screen center is preferred regardless of width. Two utility buttons around center can leave a6px interval while much wider side intervals remain. Wrapping may then exceed the assumed three-line band and expand the HUD vertically. This could introduce a new regression for previously saved custom layouts; verify actual Label minimum sizing and resulting HUD bounds.
3. **Actual line height:** CJK/fallback text and narrow wrapping can exceed the assumed three-line vertical band. Default English notifications do not establish all custom or fallback behavior.
4. **Test gap:** added tests use default touch positions and default button size. They do not test custom positions, maximal button scale, empty free intervals or narrow intervals. On-screen assertion checks top and horizontal edges but omits bottom edge. The new helper estimates a multiline text block, so actual Label bounds/line count should also be inspected.

`status_edge_probe.gd` is an outside-checkout fixture prepared for these cases. It records text and Label rectangles, line counts, all drawn-target intersections, bottom HUD bounds, convergence and the touch-disabled reset. It can write native PNGs with `--capture-dir=...`. No source UI edits made.
