# R3 baseline-context policy amendment

Source/pure work only, 2026-10-23. Independent R2 critic `40b640d6` rejected the
complete diagnostic at `03d003a`, accepting its chronology correction within
source scope. Its original review, raw synthetic inputs and controls are retained
byte-for-byte in `independent-source-r2-original` with a retention manifest.

This explicitly supersedes the earlier Dummy-rejection policy. Pinned Godot
`ed1daf0bf001b61586d9930840f2f1394092c079` main.cpp defines NULL_AUDIO_DRIVER as
Dummy and selects it for `--headless`. Original ARM ordinary and verbose suite
argv both use headless with no driver override. Retaining that default preserves
the benchmark context. The probe must report its actual driver, including Dummy;
this supplies ownership/strict-exit evidence only, with no audible or physical
audio qualification. No audio-driver or argument substitution is allowed.

The same original verbose ARM input_mode log starts with exactly
`WorkerThreadPool: 3 threads, 1 max low-priority.` followed by the pinned complete
Godot banner. The worker-pool source emits this normal verbose preamble. Its
original bytes/hash and pinned upstream excerpts are retained in the R2 critic
archive. The old `text.startswith(ENGINE)` assumption rejected it.

The correction will accept exactly one complete pinned banner line, either at
the beginning or after exactly one normal worker-pool verbose line matching the
source format. It will reject arbitrary prefix text, buried/quoted/partial
banners, missing or wrong identities, and duplicate/conflicting engine mentions.
The entire original log and its SHA-256 remain retained. Reported driver alone
cannot prove argv provenance; the later separate wrapper must bind exact argv,
pinned executable hash/version and reported driver.

Gates: preserve all observer/hooks and 422 original game/script hashes, all
snapshot chronology guards and strict scanning. Run the unchanged R2 baseline
compatibility controls, its five chronology controls and the original three
falsifiers. Add complete positives for both prescribed headless/verbose cases
and meaningful negatives for engine identity/preamble corruption. Preserve the
old failed inputs and outputs. Freeze/commit/push this analyzer/policy amendment
before implementing the separately reviewed acquisition wrapper.

No engine/import/UID generation/GDScript compile/native/CI/OCR/service is part of
this iteration. No runtime/source acceptance is self-issued. Actual strict leak
failures, unknown retaining owner and no-drain/no-cause limits remain unchanged.
