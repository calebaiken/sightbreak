# Source freeze handoff

This component supplies a read-only diagnostic, not an audio fix. No engine,
import, UID generation, GDScript compile or native/CI/service run was performed.
The builder cannot approve it. Preregistration is `23898fb`; exact implementation
identity is the source freeze commit containing this file.

The opt-in helper reports all AudioStreamPlayer3D additions/removals and changes
observed at the original input_mode process frames. It keeps only WeakRefs and
primitive descriptors between calls. Existing pre/post-leave points and final
weak liveness have explicit checkpoints. Public latest-playback IDs join to the
same process's engine verbose IDs as exact 64-bit strings. WAV descriptors retain
sample format, rate, size and SHA-256 without editing data. Driver timing readings
and `playing=false` cannot establish AudioServer drain. Older polyphonic voices
remain unobservable through the public player API.

The real pinned source supports investigating a retained server playback after
stop/free. It does not establish that this occurs here. Match device audio lacks
an explicit stop, but this test never plants the device and engine PREDELETE
already requests stop. Adding a product stop call now would be speculative.

After preregistration, root provided a separate b87afb7 verbose bot diagnostic.
Read-only inspection of its original `verbose-diagnostic-probe.stdout.log` at
`/workspace/sightbreak-exhausted-primary-verbose-r2/.local/verbose-leak-diagnostic-r1-20261023`
confirms lines 1389–1392 name AudioStreamPlaybackWAV, AudioStreamWAV and orphan
Master. Its stderr retains the two-instance ObjectDB warning. These are that
diagnostic's types. They neither type the earlier baseline's original unnamed
instances nor establish a shared retaining owner with the ARM input_mode leak.
Root owns its independent actual review and raw archive.

## Source and pure checks

Run `python3 scripts/test_analyze_audio_lifecycle.py -v` from this checkout.
Thirteen synthetic-log controls pass. They cover exact unsigned joins, unknown
playbacks, different/shared WAV owners, weak/stopped observations, malformed or
reordered evidence, missing final boundaries, Dummy rejection, engine/assertion
identity and untyped strict failures. A pure fidelity control removes only the
declared optional hooks and reconstructs the base input_mode source exactly.

`source-checks/source-parity.json` compares every one of the 323 base tracked game
files against Git. Only input_mode_test.gd changes. Product scripts, project,
audio synthesis, assets and platforms remain byte-identical. The added helper has
no generated UID. Existing runner/scanner bytes are unchanged.

The first module-style unittest invocation failed because this repository's
scripts use sibling imports; it is retained in
`source-checks/initial-module-invocation.log`. The corrected direct script result
and the earlier passing source iteration are retained separately. No failed
engine output has been replaced or reclassified.

## Independent review and future acquisition boundary

Review `PREREGISTRATION.md`, the exact source diff and pure falsifiers before
releasing any engine work. GDScript syntax/API correctness has source inspection
only and remains UNVERIFIED until an independently released compile/run.

The future suite argument tail is:

```
--headless --verbose --script res://tests/input_mode_test.gd -- --audio-lifecycle-diagnostic
```

It belongs in a separately source-reviewed bounded acquisition wrapper using an
owned private project, fresh native userdata, existing source/copy inventories,
before/after engine identity probes, original 120-second suite / 240-second whole
diagnostic bounds and owned process-group cleanup receipts. This freeze contains
no acquisition wrapper and grants no runtime release. Do not weaken the existing
exact-argv verbose-replay controller to accept this altered diagnostic.

Analyze the retained combined stdout/stderr with
`python3 scripts/analyze_audio_lifecycle.py <raw-log>`. The report binds the exact
input bytes by SHA-256, preserves the strict raw scan result, lists all observed
associations for each typed leak and marks unknown IDs explicitly. It reports
expected fixture owner counts: 7 device players, 70 shot players, 70 hurt players
and 280 reload voices. Incomplete coverage remains visible. No leak-free sample
qualifies a fix, deterministic cause, resolved flakiness or complete native gate.

The next uncertainty is whether a future leaked playback/WAV ID joins an observed
owner and remains weakly alive after its player disappears. Even that witness
cannot identify AudioServer's internal state or the retaining reference by itself.
