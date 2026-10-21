# Final S12 ARM macOS evidence review

Exact source `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`, game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`; [run 39673232413](https://github.com/calebaiken/sightbreak/actions/runs/39673232413), job119476278111. Native host macOS15.7.9 arm64, image20260907.0337.1; official engine4.7.2 ed1daf0bf. The whole ARM job succeeds. This reviewer ran no engine or application: this is inspection of its actual native execution evidence.

Original QA artifact12380618439 is951274bytes and matches uploaded SHA256 `52dfc530251cec07479efc80b79c4974c42fb31c21cf9cc17a2ffaecfc49c958`. Fresh safe extraction: `arm-s12-qa-extracted/`. All five original PNG SHA256 values agree with trial receipts; no image was modified. Source/tool digests agree with S12, source remains clean/unchanged, baseline comparison says original artifact bytes verified.

| Original native graphical PNG | Dimensions | SHA256 |
| --- | --- | --- |
| editor-minimal-2d-default |1024×656|`7b4d87f94cd14522d33ba68ca32fb9b7ff361b559b5d34c4a9e78edba14d1ea1`|
| editor-minimal-3d-default |1024×656|`88732a66cf27bd86f1c387655c45bee8229539fdc0ac98c1f1a0a99468e0ef63`|
| export-minimal-3d-default |1024×656|`88732a66cf27bd86f1c387655c45bee8229539fdc0ac98c1f1a0a99468e0ef63`|
| frozen-game-default |1004×564|`55b3cfe597446acf84c7ed53dd2a515ae89392d0fe4f7d854d7e7a658f87c513`|
| candidate-game-default |1004×564|`8d15a901be633de7966bd2144ce9195ac8ad0e40bedcfc4ceca363ba5e9e149c`|

Each graphical process exits itself0, reaches its capture marker, has clean logs, and leaves no owned process group. ANGLE Metal/Apple Paravirtual device is selected. Visual inspection confirms actual readable minimal2D label, visible lit3D box in both minimal3D cases, and visible frozen/candidate SIGHTBREAK menus. Menu button labels/training record/Relay Yard operation block are complete at the recorded1004×564 viewport; version changes0.3.2-dev→0.3.3-dev as intended. This viewport is hosted-desktop constrained and does not establish1280×720 or physical high-DPI acceptance.

Minimal, frozen and candidate lipo receipts each exit0 with `x86_64 arm64`; their native codesign verify receipts each exit0. This verifies Universal2/ad-hoc development boundaries, not notarization or DeveloperID. The eight actual native source-suite receipts each exit0/clean: actor, match, state_privacy, movement_prediction, peer_lifecycle, input_mode, offline_diagnostics, hud_objective_hint. These headless/source suites remain separate from graphical startup and unimplemented macOS gameplay input.

The exact S12 inner Mac development ZIP is77698200bytes, SHA256 `885f6d217850e3eec39f55f955d8bd4cc93117b2689a059beae6b6e7dd6b5f37`; native executable SHA256 `8daac9e63dfe437acc2b803da123ddeaba699ea956e109622a297f9d363ebb66`. The downloadable outer development artifact is12379898900. Ordered timings are cache-sensitive observations, not comparative performance evidence. No physical Mac gameplay, controller, audio, frame-pacing or quality-score acceptance follows.
