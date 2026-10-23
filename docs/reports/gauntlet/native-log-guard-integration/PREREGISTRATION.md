# Strict native log guard integration preregistration

Source-only component based on exact root
`358b240ebadb8f32b581922ab99baec11ff9ed81`, own branch
`codex/strict-native-log-integration-20261023`.

The inspected reference is accepted `scripts/native_log.py` at
`aae1f0a5e963a01dceb4aed1d9c3b0c40520c76f`, independently reviewed by
`4a7afae841ac55bf763991c09826fefe78f9390f`. The actual failure is original
`input-mode.log` from source `26a1c59ab6d141529a3254ac7f8e68ee4ae99d8b`,
review `ae6abe14f031bf40f25ba81f7428f6202166462e`, at
`/workspace/sightbreak-audio-exit-lifecycle/.local/audio-owner-r1-20261023/input-mode.log`.
It is 2,000,315 bytes, SHA-256
`a50a819152083c3d73564f21a5f15d36571c1b79c7178831667092f07537a218`,
with 353 orphan StringName rows at lines 6,939–7,291 and a positive summary at
line 7,292. The existing root matcher falsely reports this full log clean.

Before replacing the matcher, add a standalone stdlib test with roughly five
meaningful methods and run it against the root matcher. Retain the expected red
result. Then copy the accepted matcher blob byte for byte. Require the same test
to pass for the original full corpus, every original orphan independently, the
positive summary independently, LF/CRLF/unterminated forms, quoted/embedded and
zero-summary/noise controls, and existing error/leak formats. Track the full
original corpus and its provenance under `scripts/fixtures/native_log`; tests
must need neither audio modules nor report paths nor prior Git commits.

Register the pure test in `scripts/validate.sh` and `desktop-alpha.yml` beside
existing packaging controls. Preserve every existing native step, condition,
matrix and budget. Run this test plus build-manifest and QA-receipt packaging
controls, check shell syntax and byte identity of the accepted matcher, and run
the same pure groups from an exact depth-one checkout after committing. Record
all commands, exits, corpus hashes, unchanged game tree and bounded scope.

No engine/import/export/UID/native/CI/OCR/service/heavy aggregate or nested agent
work is included. Audio observer/analyzer/wrapper/probe modules and their history
stay outside this patch. Existing actual native failures and their historical
receipts remain unchanged. This strengthens future strict gating; it makes no
leak-fix, retaining-cause, audio, gameplay or release acceptance claim. Root owns
canonical mission documents and fresh independent review before integration.
