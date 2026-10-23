# Independent R2 audio lifecycle source review

Verdict: **REJECT** the complete diagnostic at exact
`03d003a9eccd239de4063e233013e248752d87a9` on
`codex/audio-exit-lifecycle-20261023`. The R1 chronology correction passes this
source review, but two existing assumptions reject the prescribed baseline
context. Correct those assumptions in an explicit source/policy amendment before
acquisition. No runtime approval follows from this review.

## Remaining baseline incompatibilities

1. **Default headless audio is rejected.** Pinned Godot source
   `ed1daf0bf001b61586d9930840f2f1394092c079`, `main/main.cpp:302`, defines
   `NULL_AUDIO_DRIVER("Dummy")`. Its `--headless` handler at 1505–1508 sets
   `audio_driver` to that value; help at 626 explicitly expands headless to
   `--display-driver headless --audio-driver Dummy`. Driver selection at
   2802–2820 preserves this nonempty CLI selection. The prescribed future command
   has `--headless` and no later audio-driver override, yet analyzer lines
   124–125 reject every Dummy report.
2. **The original verbose preamble is rejected.** The retained ARM verbose
   input-mode log begins with `WorkerThreadPool: 3 threads, 1 max low-priority.`
   and then the exact pinned Godot banner. Analyzer lines 122–123 require the
   entire log to start with that banner. A complete otherwise-valid synthetic
   trace with the original first line is rejected. Pinned
   `core/object/worker_thread_pool.cpp:822` emits this normal verbose message.

`baseline-compatibility.log` retains both errors and their complete synthetic
inputs are saved beside it. They isolate each problem: the Dummy case starts
directly with the pinned banner; the preamble case uses the previously accepted
CoreAudio header. These are pure compatibility controls, not new native output.

The largest remaining gap is faithful acceptance of the original headless,
verbose context. The original preregistration prohibits changing the audio
driver, while the handoff and maintained test additionally require Dummy
rejection. Preserve those historical requirements and failures, then explicitly
amend the diagnostic policy to record/report the expected default Dummy context
without treating it as a substituted driver. Keep its scope to ownership and
strict exit evidence. This review authorizes no product-driver change and no
audible-output or physical-audio qualification. Do not override the driver to
make the old synthetic CoreAudio assumption pass.

Recognize one exact pinned engine banner as a complete line after normal verbose
preamble. Retain the entire original byte stream and its hash; reject missing,
wrong or conflicting engine identities. A future wrapper must bind actual argv,
engine identity and the probe's reported driver, rather than infer driver
provenance from a synthetic header alone. Keep the original strict scan and all
unknown-owner/no-drain/no-cause limits.

## Actual baseline evidence and source grounding

I inspected the original ARM run 39912086121 QA ZIP, SHA-256
`6452eac95a8f55fd84d1bcba9e62a50763fda7d419b7c453d25d009aa0f8dfb7`.
`arm-headless-context.json` retains the exact commands from original
`regressions/results.json[6]` and
`source-leak-verbose/repeat/results.json[0]`. Both use `--headless`; the repeat
also uses `--verbose`. Neither has `--audio-driver` or `--write-movie`.
The actual verbose log is 20,746 bytes, SHA-256
`f51e5f285cd74732e25acdbfeab5446026a002d9ce04bcf4a3a83556f75becdd`.

Those logs contain no explicit audio-driver telemetry. The default Dummy
finding follows from original argv and exact pinned source, not from the
unrelated `TextServer: Added interface "Dummy"` line. The new probe would report
the actual driver through `AudioServer.get_driver_name`; pinned
`servers/audio/audio_server.cpp:1498` returns the singleton audio driver's name.

`engine-source-evidence.json` binds all inspected upstream URLs/byte hashes and
short line excerpts. `main.cpp` SHA-256 matches the original builder retrieval:
`1831257f5c8eb0707d278f04b21b1e4b3ba863f8dca5cab36022d4b19e36b8c1`.
The Dummy driver defaults to a worker thread and, when active, calls
`audio_server_process` (`audio_driver_dummy.h:55`, `.cpp:49–66`). Default Dummy
therefore does not establish absence of an audio-server lifecycle to inspect.
It supplies no proof of audible output, hardware progress or server drain.
Two initial incorrect audio-server URL paths returned 404; the manifest retains
those failures and their corrected locations.

The previously retained ARM strict failure and root's separate bot verbose
diagnostic remain failures. Their matching WAV/playback classes still do not
establish the same retaining owner or cause. IDs never transfer between runs.

## Chronology correction accepted within source scope

The maintained direct-script suite passes **21 tests**. The original independent
replay passes **three unchanged tests**. `original-retention-check.json` compares
all **17 retained R1 critic files** directly against `800f605` Git objects; all
bytes match, including the three original inputs and failed assertions. The old
incomplete fixture remains byte-identical. No old failure has been relabeled.

The independent `ChronologyControls` group passes **five tests** on a separate
producer-style complete trace. It covers a dynamically registered player,
structural player observations with the previous stage label, empty/partial
incremental weak snapshots, repeated raw player IDs/states and exact signed to
unsigned WAV/playback joins. Every one of the 15 forced windows is tested for a
missing weak row; signed/unsigned alias duplicates fail; each backward clock
fails; every post-final probe record kind fails. A final alive player is reported
from the final window without a drain or cause claim.

Source inspection agrees with the unchanged helper's emission order: player and
new object observations precede the synchronous weak loop; the following
checkpoint closes that weak snapshot. Weak rows now match that window's stage,
have unique normalized IDs and cover all objects registered at every forced
boundary. The six repeated HUD pairs remain separately required. Incremental
windows may have zero or partial changed weak rows. The final checkpoint seals
the stream, and final player liveness uses its validated weak dictionary.

`source-audit.json` rechecks all 323 original game files and 99 original scripts
against the reviewed `809dbc0` hashes: all 422 match. The observer also matches
exactly, SHA-256
`0e6eda0f2a6bcfd64a0daf5a2ea4443f19daa69eb96d393347b81dafa49c78a1`.
The earlier byte-exact stripped-hook reconstruction therefore remains valid.
R2 changes only the analyzer/tests and evidence; product audio, gameplay,
authority, economy, privacy, actions, awaits and teardown remain unchanged.

## Execution boundary

This was source and pure-Python work only. No Godot, import, UID generation,
GDScript compile, native execution, CI, OCR, nested agent or acquisition wrapper
ran. The root-held native lane remains idle. Compilation/API behavior, real
owner coverage and actual log acceptance remain UNVERIFIED. The next source
amendment should retain all old inputs and rerun the unchanged chronology and
baseline compatibility controls. Acquisition still needs its separate bounded
wrapper, original 120/240-second limits, private project/userdata, identity and
source/copy receipts, strict raw output and owned cleanup review.
