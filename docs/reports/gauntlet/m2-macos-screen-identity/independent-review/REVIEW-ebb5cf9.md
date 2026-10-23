# Independent source review: REJECT

Exact source: `ebb5cf9dc23794f8ae4cee70b19485a49f6e86b7`. Base: `f8b7e8272a104aadf890328b5ff4fc26374b5daf`.

Reject this commit for native dispatch because its new `unique_screen_label` accepts a positive box starting at normalized x=1 or y=1. For example, `FIELD SETTINGS` with `[1.0, 0.1, 1e-20, 0.1]` qualifies because floating addition rounds x+width to 1.0. The box extends beyond the image and violates the preregistered in-bounds criterion. This is an explicitly synthetic numeric edge, not an actual Vision observation.

The 27 packaged controls pass. Independent controls test 146 synthetic cases across ten methods; eight cases fail, covering both edges for each of the three home roles and the settings heading. All other independent cases pass. The separate reproduction is in `bounds-defect-reproduction.json`; full independent output is in `independent-controls-ebb5cf9.log` and `independent-controls-results.json`.

The screen-role choice is supported by the actual originals and source UI declarations. I visually inspected all three retained original PNGs, recomputed their SHA-256 values, and directly compared the three committed JSON fixtures with their raw originals. All JSON copies match byte for byte. The returned PNG is `c17ca318ef148c0e444136048f8f914bade3770366c29acb6d619cb71427adeb` and its JSON is `3b087c989452ec9b24068b4abdddf849e5822686afcc824de582c2b50e72f1eb`. Both home images show the large SIGHTBREAK hero, OPERATOR RECORD, and SETTINGS; the settings image shows FIELD SETTINGS. The title bar exists on both screens. The returned masthead is confidence 0.5 and cannot qualify at 0.8. See `original-fixture-audit.json` and `baseline-observer-replay.json`.

Native adapter/helper, preflight, manifest, pinning, strict-log and focus source remain unchanged. Driver orchestration functions are AST-identical to base. See `unchanged-guard-crosscheck.json`.

Run 39732825169 at b09cfe1 stays FAILED. Its original result has five CG event attempts and fails 03 screen confirmation; later normal success-path close checks were not reached. Stored replay proves observer behavior only. No engine, OCR, native API, CI dispatch, or native input was run in this review.

The builder subsequently corrected both identity and pointer geometry in 893dac1. This report preserves the exact rejected iteration; final review is separate.
