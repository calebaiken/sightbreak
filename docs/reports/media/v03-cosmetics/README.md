# Native cosmetic presentation, 0.3.0

Screenshots in this directory are captured from the running Godot application on Xvfb/Mesa llvmpipe at 1280×720. They are not concept art. The inventory, account balance and committed reward in the capture harness are explicitly fictional QA fixtures, not earned player property or a live random case result. The field knife is an unowned reference model: it is not in the economy catalog and cannot be equipped, minted, sold or traded.

## Changes

- Replaced the flat scrolling case panels with an original 3D Relay hardcase, modeled protective corners, latches, handle, embossed insignia, physical hinged lid, and a lift transition displaying only the server-committed reward. Skip and reduced motion finish immediately without changing the item.
- Shared the gameplay rifle model with inspection: chamfered receiver, actual barrel, detailed attachments, magazine and stock. Original collection finishes have distinct painted/circuit/camouflage patterns, metallic response and metadata-derived wear.
- Added a native studio pedestal and three inexpensive lights; rarity illumination uses the actual item's rarity. No sky, reflection probe, dynamic shadow, external asset or postprocessing effect is needed.
- Added a genuinely three-dimensional beveled field-knife reference with handle ribs and pins. The UI explicitly distinguishes reference previews from owned instances, including catalog previews.
- Added owned-inventory rarity cards and filters; marketplace has local name/rarity filtering, price/name sorting, own-listing filtering and wear metadata. Requests, authoritative values and settlement behavior are unchanged.

## Rendering budget and behavior

Only the selected inspector and an open reveal own a SubViewport; inventory cards do not create individual 3D renders. The viewport renders at logical display resolution up to a 1024×512 bound with 2× MSAA, reducing its resolution for larger layouts. Static case and knife parts are batched by material. The inspector requests a single render on selection, resize, drag or zoom, and remains idle afterwards. Opening animates requests for its 2.8-second duration. Three studio lights cast no shadows. This is a cost-conscious implementation, not a physical-device battery, temperature or FPS measurement.

## Reproduce

```sh
DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1 \
ECONOMY_CAPTURE_DIR="$PWD/.local/screenshots/v03-economy" \
./scripts/godot.sh --audio-driver Dummy --script res://tests/economy_ui_test.gd

./scripts/godot.sh --headless --script res://tests/cosmetic_presentation_test.gd
```

The previous comparison images are `../stabilization/item-inspector-fixture.png` and `../stabilization/case-result-fixture.png`. Inspection retains the same default camera distance (3.5), field of view (32°), camera position and initial model rotation; the old placeholder is replaced by the shared weapon, with centering and scale matching its actual physical dimensions. The reveal now has a larger popup and actual 3D content, so this is a UI comparison rather than a pixel-matched 3D camera comparison.

## Screenshot-driven corrections

The first actual render exposed a missing knife blade. Its generated triangles were unindexed before batching with indexed primitive meshes; indexing the blade before batching preserves the rendered tip. The blade also uses Godot's clockwise front winding. Two regression assertions now require referenced tip triangles and an outward-facing front surface.

The same review found that half-resolution rendering blurred the display models and that the pedestal dominated the frame. The revised studio uses bounded native-resolution demand rendering, larger weapon/knife framing and a smaller, lower pedestal. The independent reviewer requested a second collection/rarity fixture to verify that finish variation and rarity illumination are actually visible; the Crimson Archive / Iridescence example uses fictional Legendary instance metadata and is labeled accordingly.

`cosmetic_presentation_test.gd` passes 26 assertions. The independent `cosmetic_lifecycle_test.gd` passed 19 assertions over six rendered open/close cycles, with tracked texture memory stable at 4,350,915 bytes and scene-owner weak references released. These are native software-rendered resource checks, not phone memory/FPS measurements.
