# Integration evidence index — 2026-10-14

Exact export/runtime source: `60cf125bb2c05606e71a4a68482d31ec26dc69bb`. Matrix source4ae4e5c has identical shipping runtime; later probe barrier changes are excluded from artifacts. Earlier experiments retain their own exact heads. **Request changes; diagnostic development preview only.**

## Reports and reproducible records

- [Combined report](../COMBINED_INTEGRATION_REPORT.md)
- [Refreshed47-group matrix](matrix-98/summary.json), with per-group logs, protocol/account/economy/resource evidence. Nested protocol ObjectDB warnings are retained.
- [Final independent engineering QA](network-independent/final-review.md), including hashes, actual native binary interaction and quality rubric.
- [Corrected Unicode foundation review](pr1-independent/REVIEW.md) and [new98ff57c custom-layout regression](pr1-status-98ff57c/REVIEW.md).
- [Independent graphics review](art-independent/REPORT.md) and [performance assessment](art-independent/performance-assessment.json).
- [Original ten-client conditions](network-campaign/campaign.json), reconnect follow-ups and close-loss failure. Terminal-blackout failures are intentional negative controls; the close-loss failure is a real unmet gate.
- [Fresh native+9 headless trial](network-native-shared/summary.json), [actual final exported Linux run](final-native-ui/results.json), [artifact manifest](build/manifest.json), [package checksums](build/checksums.txt), [toolchain](build/toolchain.json).
- [Default aspect metrics](aspect-98/metrics.json), matched profiles in `profile-pr1`/`profile-combined`, three scenario metrics and weapon-cost log. Software-render diagnostics do not establish phone performance.

## Comparable native images

| Evidence | Before | After / next frame |
| --- | --- | --- |
| Reload staging, same1280×720 camera |[e896c81](art-independent/before-reload.png)|[d084e500](art-independent/after-reload.png)|
| Custom saved HUD, same960×720 layout |[227d6c8 stable](pr1-status-98ff57c/before-captures/narrow_center-960-buy-00.png)|[98ff57c broken frame](pr1-status-98ff57c/saved-captures/narrow_center-960-buy-01.png)|
|98ff57c consecutive frames |[ordinary](pr1-status-98ff57c/saved-captures/narrow_center-960-buy-00.png)|[next frame, offscreen HUD](pr1-status-98ff57c/saved-captures/narrow_center-960-buy-01.png)|
| Final exported Linux reload |[visible RELOADING0.8s](final-native-ui/07-after-authority-reload-completion.png)|[settled30/86](final-native-ui/08-settled.png)|

Images are actual native Godot captures; none substitute for in-engine geometry. Fallback counterfactual images are explicitly runtime material probes. Capture names05/06 in final-native-ui lag authority events and still show pre-fire images; do not infer shot/reload stage from filenames. Fixture MP4 playback rate is simulated time, not measured FPS. Art aspect fixtures fill the requested viewport; shipping keep-aspect behavior is documented separately.

## Portable delivery

GitHub **draft prerelease**, visible to repository collaborators: https://github.com/calebaiken/sightbreak/releases/tag/untagged-e823a7a6d70f480c54cb . **The draft exists but has no uploaded assets.** Both normal and approved upload attempts returned Forbidden from `uploads.github.com`. Build and raw-evidence packages are verified locally under `/workspace/sightbreak-integration/builds/`; curated evidence is committed here. See `delivery-assets.json` for the actual failure. The saved cloud configuration draft adds that hostname while retaining `api.github.com`; review/save/publish the environment configuration before retrying. Draft saving does not apply network policy.

- `sightbreak-linux-debug.zip`, `sightbreak-android-debug.zip`, `sightbreak-ios-xcode-project.zip`; direct `sightbreak-debug.apk`.
- `sightbreak-curated-evidence.tar.gz`: this indexed subset, reports and checksum manifest.
- `sightbreak-raw-art-evidence.tar.gz`: all nine115-frame native motion sequences, all source stills/CSVs/contact sheets/videos and reviewer fixtures. Original art SHA manifest covers the full collection; it is not a manifest of the smaller Git subset.
- `sightbreak-raw-network-evidence.tar.gz`: full server/client trajectories for campaign, failed and successful reconnect trials and native trials.
- `sightbreak-raw-render-evidence.tar.gz`: all rendering/aspect/custom-HUD and final native-UI captures and metrics, without runtime caches or saved state.
- `delivery-checksums.txt`: SHA256 of the prepared local payloads (upload blocked). `SHA256SUMS` here covers the curated Git evidence files; verify from this directory with `sha256sum -c SHA256SUMS`.

Curated data omits repeated screenshots, archived source trees and caches; corresponding full raw archives retain measurement files. Runtime state, database files, debug keystore and account secrets are excluded. Build manifests identify unsigned iOS project versus executable/APK explicitly. No Android device installation, Xcode compilation, physical touch, cellular, GPU, thermal or battery acceptance is claimed.
