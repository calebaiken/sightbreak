# Independent R3 observer/analyzer source review

Verdict: **ACCEPT within source scope** exact freeze
`73cdfc2d8d6956eef1cd2e14e1461b93152afc80`, preregistration `e0e0f75`, on
`codex/audio-exit-lifecycle-20261023`. R3 corrects the two retained R2 baseline
incompatibilities through an explicit policy amendment. This accepts only the
inspected observer/analyzer source and policy. It approves no acquisition,
compile, runtime behavior, leak fix or release gate.

## Verified source and pure evidence

All four commands in `receipts.json` exit 0:

- 23 maintained tests.
- Seven unchanged R2 critic controls, including its two formerly failing
  baseline controls and five chronology groups.
- Three unchanged R1 critic controls.
- Three independent focused identity controls, including eight malformed
  engine-identity subcases and direct context parsing of both original ARM logs.

`retention-check.json` compares 17 R1 and 22 R2 retained critic files directly
against original `800f605` and `40b640d6` Git bytes; all 39 match. Old failed
outputs and incompatible policies remain historical evidence. The copied critic
programs are unchanged. `source-audit.json` recomputes all 422 original game and
script hashes: all match the reviewed `809dbc0` source. The observer hash is
`0e6eda0f2a6bcfd64a0daf5a2ea4443f19daa69eb96d393347b81dafa49c78a1`.
The earlier byte-exact reconstruction of the input-mode test therefore remains
valid; actions, assertions, awaits, quit/teardown, product audio and original
runners/scanner stay unchanged. R3 changes no driver or runtime argv.

## Original headless/verbose context is preserved

The original ARM QA ZIP hash remains
`6452eac95a8f55fd84d1bcba9e62a50763fda7d419b7c453d25d009aa0f8dfb7`.
Both original suite contexts parse correctly: the ordinary log's banner is line
1; the verbose log's banner is line 2 after its original
`WorkerThreadPool: 3 threads, 1 max low-priority.` line. That verbose log remains
SHA-256 `f51e5f285cd74732e25acdbfeab5446026a002d9ce04bcf4a3a83556f75becdd`.
`actual-context.json` binds these original bytes again. Uninstrumented original
logs still fail complete probe analysis because the required observations are
absent; accepting their engine context does not fabricate diagnostic evidence.

The independent control combines the exact original verbose prefix with a
complete saved R2 Dummy probe input. It passes, retains driver `Dummy`, reports
banner line 2 and the accepted preamble, keeps the strict leak failure, and
retains all 15 forced weak windows. Its input and accepted report are saved as
`actual-prefix-complete.synthetic.log` and `.report.json`. They remain synthetic
compatibility evidence, not a new native attempt.

The explicit R3 amendment correctly treats Dummy as pinned Godot's default for
the original `--headless` argv. The unchanged pinned-source and original-argv
evidence is retained in R2. The analyzer reports actual probe context and says
`ownership and strict exit only; no audible or physical qualification`; it also
says exact argv/engine binding is required separately. It no longer mistakes the
preserved default for a substituted driver. No audible output, physical audio,
hardware progress or server drain follows from this context.

## Engine identity and chronology remain bounded

The parser requires exactly one complete pinned banner line. It accepts no
preamble or one source-format worker-pool line; arbitrary prefix text, buried,
wrong, missing, partial, quoted, split, duplicate and conflicting identities fail
the maintained or independent controls. It retains the original full text for
strict scanning and the CLI retains raw byte hashing. This parser is not a
substitute for separately binding the executable and argv in an acquisition
receipt.

All R2 chronology logic is unchanged. Complete forced snapshot windows still
require every registered object's normalized ID exactly once, with matching
weak stage and separately required repeated HUD pairs. Dynamic registration,
empty/partial incremental windows and repeated player states pass the unchanged
critic controls. Missing rows in every forced window, signed/unsigned alias
duplicates, backward clocks and every post-final record kind remain rejected.
Final player liveness still comes solely from the sealed final weak snapshot.

The observer retains only WeakRefs and primitive descriptors between calls.
Synchronous sampling/hashing/printing adds time and briefly acquires references;
this acceptance makes no noninterference claim. Latest public playback coverage,
first-observation WAV descriptors and unknown owners retain their stated limits.
Matching ARM/bot leak classes establish no shared cause; strict native failures
remain unresolved.

The largest remaining gap is actual owner coverage on an exact, isolated,
bounded diagnostic acquisition. No Godot/import/UID generation/GDScript compile/
native/CI/OCR, nested agents or acquisition wrapper ran during this review. The
separate wrapper must receive its own exact-source review before runtime work,
with original 120/240-second bounds, source/copy and private-userdata inventories,
engine/argv/driver provenance, original raw strict output and owned cleanup
receipts. GDScript compilation, actual joins and AudioServer state remain
UNVERIFIED. No canonical root files were edited.
