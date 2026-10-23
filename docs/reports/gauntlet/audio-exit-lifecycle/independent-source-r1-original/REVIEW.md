# Independent audio lifecycle source review

Verdict: **REJECT** exact builder freeze
`809dbc0921b1faa2abe25eb6bab3576becb48db8` on
`codex/audio-exit-lifecycle-20261023`, based on exact `c08889b` and preregistered
at `23898fb`. The analyzer accepts incomplete or reordered evidence and can
report a final player liveness value that contradicts the explicit final row.
Correct this source defect and rerun the unchanged independent controls before
source approval. No engine or native acquisition is released by this review.

## Blocking counterexamples

`python3 docs/reports/gauntlet/audio-exit-lifecycle/independent-source/replay_counterexamples.py -v`
exits 1 with three retained failures. Inputs derive from the builder's synthetic
fixture; they are not actual engine output. Each input, accepted report and
original failing assertion output is retained beside this report.

1. `late_weak_after_final_checkpoint.synthetic.log` appends an otherwise valid
   weak observation with stage `existing_process_frame`, player `1`, alive true,
   after the final checkpoint. The explicit `final_pre_quit` weak row for player
   `1` says false. The analyzer accepts the trace and reports
   `final_alive_player_ids=["1"]`. `analyze_audio_lifecycle.py:108` only checks
   whether some final weak row exists; lines 136–138 take the last weak row of
   any stage. It never seals the probe stream at its final checkpoint.
2. `final_weak_before_all_leave_boundaries.synthetic.log` moves all final weak
   rows before every leave checkpoint and renumbers the records. The analyzer
   accepts this impossible final ordering. Lines 101–109 order checkpoint names
   without validating which snapshot contains the required weak rows.
3. `missing_all_post_leave_weak_observations.synthetic.log` contains no weak
   rows at either post-leave stage. It is the maintained synthetic fixture
   without modification, and the analyzer accepts it. Preregistration gate 4
   requires post-leave and final weak rows. A checkpoint alone cannot substitute
   for the weak snapshot it claims to delimit.

The first two violate the preregistered malformed/reordered-evidence source gate;
the third demonstrates that the future post-leave coverage gate is not enforced
by the proposed analyzer. The helper's inspected synchronous implementation
does not emit these traces. The finding concerns evidence validation and the
meaning of the analyzer's final-liveness output, not an observed product leak.

The largest source gap is a validated snapshot chronology. Require the expected
weak observations in their actual snapshot windows, reject observations after
the final checkpoint, and derive final liveness from that final snapshot. Keep
unknown and incomplete evidence explicit. Retain these controls unchanged when
reviewing the correction; do not remove them to recover a passing result.

## Supported source properties

The builder's maintained direct-script suite passes all 13 tests, exit 0, in
`maintained-tests.log`. Exact unsigned ObjectID joins, unknown leak IDs, shared
and different WAV associations, strict scanner results, stopped-player limits
and clean-sample wording pass the existing controls. `strict_raw_log_failed`
still uses the unchanged `native_log.failed`; an exit-0 engine sample remains a
strict failure when its original log reports leaks.

`independent-byte-audit.json` recomputes all 323 base game files and 99 base
scripts directly from Git objects. Only `game/tests/input_mode_test.gd` differs
among original paths. Eight exact hook removals reconstruct its original bytes,
SHA-256 `3683b784175ec82b402383e46698f560da3e30b563e2dfe0c4263b676c74e52f`.
Original assertions, actions, awaits, leave/free calls and quit behavior are
therefore preserved. Product code, assets, project/platform settings, original
runners and strict scanner are unchanged. Added source paths are exactly the
probe and two Python files; there is no helper UID or acquisition wrapper.

Independent read-only probe subreview found no blocking ownership defect.
Persistent audio-object storage uses WeakRefs; the retained player-state
dictionaries contain primitive descriptors. Strong stream/playback/weak-read
locals expire when their synchronous call returns. ObjectIDs are decimal
strings. WAV hashing reads actual data and records format, rate, stereo and byte
count without changing the resource. Descriptors are first-observation records,
not a history of later resource edits. Initial network-shot classification can
be unknown until its group is added; later snapshots can classify it.

The helper does add synchronous hash/print/inspection work and briefly acquires
references. Its source supports no timing-neutrality or noninterference claim.
Node removal follows the child's native EXIT_TREE; an owning actor's stop path
can run later. `playing=false`, a dead player, public driver timing and final
weak liveness cannot establish AudioServer drain or its internal retaining owner.
Only the latest public playback is visible; earlier polyphonic voices remain
unobserved. GDScript compilation and actual object coverage remain UNVERIFIED.

## Actual benchmark and scope

I inspected the retained original ZIPs from ARM run **39912086121**, job
`120277159133`, independently reviewed at `9f2a67f`. The original input-mode log
reports 462 checks, zero assertion failures and two unnamed ObjectDB leaks.
The separate verbose repeat names AudioStreamPlaybackWAV and AudioStreamWAV,
each reference count 1, plus orphan Master. This does not retroactively type the
original unnamed objects. Both ZIP hashes and exact input-mode log excerpts are
bound in `inspected-benchmarks.json`; the strict native gate remains failed.

I also inspected root's retained b87afb7 verbose bot diagnostic at
`m5-exhausted-primary-verbose-diagnostic/actual-r1`. Its original stdout lines
1389–1392 name the same two classes and orphan Master. The raw stdout SHA-256 is
`387762da62e75de243f95c84ee66126aa408495d19ef01bd7d5e6e300de2632c`.
Matching classes do not prove a shared retaining owner or cause across processes.
No WAV/playback IDs from these runs can be joined to future observations.

This is a source and pure-Python verdict only. No Godot, import, UID generation,
GDScript compile, native execution, CI dispatch, OCR, or service was started.
No gameplay, authority, economy, privacy or offline/online behavior changed.
Probe output contains local scene/script paths, object identities and generated
audio descriptors; it adds no account, credential or network-payload logging.
Pure scripts created local report files only and started no native processes.

A later diagnostic still needs a separate independently reviewed acquisition
wrapper: exact source/argv, owned private project and fresh userdata, unchanged
source/copy inventories, before/after engine identity, original 120-second suite
and 240-second whole-run bounds, original strict output, and owned process-group
cleanup receipts. The existing exact-argv verbose replay controller must not be
weakened to accept this altered invocation. The root-held native lane remains
idle. A clean future sample cannot qualify a fix, deterministic cause, resolved
flakiness or complete platform gate.
