# Test-only depth-one correction handoff

Source freeze `3973447175370d64ef2d790a3551102a89bb3a8e` on `codex/m2-mac-derived-ocr`. Independent source re-review is pending. The only source changes from rejected handoff `a282b3f55c4014072144f3184e91fbefbafc0077` are `scripts/test_macos_deploy_ocr.py` and two checked-in reference fixtures under `scripts/fixtures/macos_ordinary_source/`. Every helper, selector, controller, workflow, game and other runtime byte remains identical. No fetch-depth change, skip, optional history fallback or loosened comparison was introduced.

The rejection at `bde551cb2a80a38b901d6c7b0ad5f8301947dcfb` is retained verbatim with all 55 review files in `rejected-review/`. The copied critic shallow falsifier is unchanged. Its rejected-ref replay at exact `a282b3f` reproduces 13 tests with one error and child `git show` exit 128; raw outputs remain in `rejected-replay/`. This is a source-readiness failure, not a hosted CI or native attempt.

The maintained preservation check now uses the exact 3,601-byte original c08889b default capture/OCR body, with SHA-256 `1b0f4c909a3bb274083ab72e40baf507f8b7f1984c52b1b02e08443747deabd1`. It compares the current helper body byte-for-byte with that fixture and checks the 11,726-byte original gameplay suffix hash `3a2abc588525152b922bc97ca7640d2baa8a90030fdb8f3111242c5dd18bc837`. The source-reference manifest is itself hash-pinned in the test. All other maintained test methods/assertions remain unchanged. A separate explicit full-history `audit_reference.py` verifies both references against immutable c08889b source and complete original source hashes; it is not a maintained CI dependency.

`candidate-depth-one/result.json` records a fresh exact-ref local depth-one Git checkout: HEAD is the freeze above, shallow=true, one reachable commit. The original c08889b object is still unavailable (`baseline-absent.txt`, exit 128). In that checkout all 83 maintained top-level Mac pure tests pass, five aliased-temp suite commands pass, and all eight unchanged independent controls pass. The existing four deliberately weakened selector/binding variants still fail. Three additional preservation mutations also fail: alter the golden fixture, show the cursor in the default helper, or change the gameplay reload-completion budget reference. The frozen checkout remains clean and every tested input hash is unchanged. Commands, sanitized explicit environment allowlists, raw outputs and hashes are retained there.

`candidate-critic-replay/` separately reruns the critic's exact unchanged shallow-checkout falsifier against the new freeze with expected exit zero. All 13 Deploy methods pass. `source-scope.json` verifies the three-path source delta, unchanged runtime/workflow/controller hashes, identical test method names, unchanged independent scripts and all original/native review evidence hashes.

The same controls can be reproduced with:

```sh
python3 docs/reports/gauntlet/m2-mac-derived-ocr/shallow-checkout-correction/run_shallow_controls.py --ref 3973447175370d64ef2d790a3551102a89bb3a8e --output /tmp/sightbreak-fresh-shallow-controls
python3 docs/reports/gauntlet/m2-mac-derived-ocr/shallow-checkout-correction/replay_shallow.py --ref 3973447175370d64ef2d790a3551102a89bb3a8e --output /tmp/sightbreak-critic-shallow-replay --expected-exit 0
```

Both output paths must be new. These commands run local Git and pure synthetic tests only. Historical extraction audit requires the full-history source-review checkout; maintained tests require no historical objects.

Original native run `39912086121` remains failed before CGEvents/Deploy. No engine/import/UID write, native API/input, OCR executable, Swift compile, CI, external service or retry was run. Actual derived confidence improvement, image orientation and native gameplay remain unproved. Root must obtain fresh independent source review and release any later action separately.
