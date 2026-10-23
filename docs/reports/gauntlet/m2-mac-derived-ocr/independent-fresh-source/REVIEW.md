# Fresh source review: rejected

Frozen source `cbd01547a5f0b2a435fa2c24a827468a963535aa`, report handoff `a282b3f55c4014072144f3184e91fbefbafc0077`, base `c08889b8c1118c89e83c151079df4dc224076760`. Review branch `codex/review-mac-derived-ocr-fresh-20261023`; own sparse worktree `/workspace/reviews/mac-derived-ocr-fresh-source`.

**Source readiness is REJECTED.** The new registered source-control suite depends on baseline Git history that the workflow does not fetch. This is a reproducible blocker before another ordinary Mac attempt. No supported production selector/helper defect was found in the reviewed source. Actual confidence improvement, resized-image orientation and native gameplay remain unverified.

## Blocking finding

`scripts/test_macos_deploy_ocr.py:241` and `:254` run `git show c08889b:<path>` to compare baseline source bytes. `.github/workflows/desktop-alpha.yml:30` uses the pinned `actions/checkout` with no `fetch-depth` override; its default fetch contains one commit. The workflow now runs the new suite at `:134`, and the ordinary native step requires `macos_ordinary_controls.outcome == 'success'` at `:136`.

Two independent local depth-one checkouts of exact handoff `a282b3f` reproduced the failure. Both report `--is-shallow-repository=true` and identical test source SHA-256 `ef9a6505763fa7d1fdb2db9d03a0717a8993d26c52fedfc975b8927614812927`. The pure suite runs 13 tests and exits 1 with one error: `fatal: invalid object name 'c08889b'`; its child `git show` exits 128. All other 12 test methods pass. This is a source-control failure, with no CI or native execution performed.

Retain the exact [first falsifier](shallow-deploy-controls.txt), [checkout/command identity](shallow-falsifier.json), and [immutable-ref replay](shallow-exact-replay/deploy-controls.txt). To reproduce from this branch:

```sh
python3 docs/reports/gauntlet/m2-mac-derived-ocr/independent-fresh-source/replay_shallow.py \
  --ref a282b3f55c4014072144f3184e91fbefbafc0077 \
  --output /tmp/sightbreak-deploy-review-fresh-output --expected-exit 1
```

Correct the test so its strict byte comparison works from the retained source in a depth-one checkout, or explicitly provide and verify the immutable baseline objects. Do not skip the check, weaken its comparisons, or treat the existing history-rich green run as CI readiness. Re-review the corrected exact source with this shallow-checkout falsifier before considering source acceptance. Acceptance itself releases no native work.

## Source findings within the passing scope

The helper uses `CGContext(data:width:height:bitsPerComponent:bytesPerRow:space:bitmapInfo:)`, `.interpolationQuality = .high`, one `context.draw(image, in:)`, and `context.makeImage()` at `scripts/macos_window_capture.swift:44–61`. It draws the same captured `CGImage` uniformly at 2x, with no crop or alternate-scale search. It writes the distinct derived PNG through the same ImageIO API family as the existing native PNG, then uses `VNImageRequestHandler(cgImage:options:)` with one accurate `VNRecognizeTextRequest`, en-US, language correction disabled and no custom words. SHA-256 uses `CryptoKit.SHA256.hash(data:)` on each retained file. The source uses no UIKit coordinate transform, manual flip or EXIF orientation override. That is a consistent source construction; this review does not establish what a compiled helper or native Vision request produces.

The added branch allows only the named profile and a distinct nonexistent derived path. It preserves the original PNG and native observations. The permission/preflight, owned-window, ScreenCaptureKit configuration, raw PNG write and raw Vision body are byte-identical to the base; their shared body SHA-256 is retained in the audit. The full helper is changed, including argument parsing and the CryptoKit import. Its default compile and execution still need native verification.

The Swift resize checks source pixels <=4,194,304, derived pixels <=16,777,216 and derived dimensions <=8192. Python validates actual PNG file SHA-256 values and dimensions before binding. The controller validates current owned PID/window/bounds, the existing chrome/DPI mapping, helper success, zero posted input and zero permission requests before the analysis binding (`scripts/verify_macos_ordinary.py:138–148`). The binding checks source/analysis hashes, matching identities, native pixel scale, full-image crop extent, 2x dimensions, normalized coordinate declaration and recognition settings. Its frozen dataclass plus receipt digest is an in-process capability that ordinary JSON cannot supply. Mutating any receipt field after binding invalidates it.

Only the full ordinary Deploy caption uses the new selector. It keeps existing case/whitespace normalization and adds bullet/middle-dot equivalence. It requires one matching raw row with finite confidence in [0,1], one matching derived row at finite confidence >=.8, valid native normalized boxes and reciprocal center containment (`scripts/macos_deploy_ocr.py:104–122`). Both sides reject matching duplicates at any confidence. It returns a copy of the raw row. The pointer calculation therefore uses the original native center, independent of the derived box center; provenance traces retain both observations.

The driver requests derived analysis only for `01-focused-menu`, and rejects unexpected derived metadata elsewhere. Its existing 25s capture, 60s menu, 5s focus and 300s total limits remain fixed. Unique visible owned-window guards, permanent input pinning, permission/isolation checks, neutral/release barriers and strict HUD/FIELD MENU/LEAVE recognition are unchanged. AST comparison finds only `label_point` and `MacOrdinaryUI.click_label` changed in the ordinary-input module. The Deploy-through-teardown driver suffix is byte-identical, including objective scope and cleanup. Game, protocol, prediction/privacy/economy, Windows/Linux/mobile code, platform matrix, original menu and preflight source are unchanged. The new CI test registration is ARM-only; its history dependency is the cross-checkout regression above.

## Evidence and independent checks

`checks.json` binds all seven changed source paths to both freeze and handoff bytes. It verifies all 80 builder-indexed evidence files and all 32 original indexed files. All 29 retained ordinary files match their members in the original QA ZIP byte for byte; all 21 non-image files also match the nested receipts ZIP. That receipts archive intentionally omits the eight PNGs, which remain in the QA ZIP and the component directory. I inspected the original focused menu image; visual readability does not raise its recorded Vision confidence.

The original ready/focused JSONs each contain exactly one `DEPLOY • OFFLINE 5V5` at confidence .5. The retained original selector, punctuation-only edit and confidence-only edit all still reject. Original results remain FAILED with zero event attempts, a successful ordinary close (exit 0), ten owned groups gone without fallback signals, and unchanged payload/source/default user directory. These failures remain required evidence.

In the history-rich worktree, all 83 maintained top-level tests pass, as do eight additional independent pure test methods, five aliased temporary-root suite runs and four deliberate source weakening controls. The weakened confidence, omitted file hashes, omitted reciprocal-center guard and omitted bound-receipt digest each produce an intended assertion failure. Raw outputs and exact commands/hashes are retained in `pure/` and `checks.json`.

The additional controls independently cover mixed allowed punctuation, existing case/whitespace normalization, the next representable confidence below .8, each direction of the center guard, a changed but corresponding derived center, deep-copy returns, consistent false scale, unrelated receipt mutation after binding and a JSON round-trip spoof. A full mocked controller additionally uses real SHA-256 on synthetic files: corrupting either file after receipt creation fails before any event and still reaps every mocked group. All image headers, derived observations, controllers and mutation outcomes are synthetic. None establishes native OCR confidence or input behavior.

Two review setup failures are retained. The initial artifact audit incorrectly expected PNGs in the receipts ZIP; `setup-failure-receipts-png.txt` preserves the missing-member traceback. The first broad pure run omitted `m2-macos-screen-identity/fixtures` from this sparse checkout and produced seven missing-file errors; `setup-attempt-pure/normal-test_macos_screen_identity.txt` preserves them. I restored those exact tracked fixture files and reran into a fresh `pure/` directory. Neither setup error is counted as a passing check or a production defect.

## Largest remaining gap and handoff

After fixing the shallow-checkout blocker, the largest gap is whether this exact 2x transform produces one upright, corresponding whole Deploy caption at confidence >=.8 on the actual Mac pixels within the unchanged deadline. No Swift compile, native capture/OCR/API, input event, Godot/import/export, CI or service action was run here. No gameplay gate advances. Keep the native lane idle until root separately reviews the corrected source and chooses any next action; a source acceptance dispatches nothing.
