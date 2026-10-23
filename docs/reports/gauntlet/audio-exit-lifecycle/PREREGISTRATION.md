# Audio exit ownership diagnostic preregistration

Source-only component, 2026-10-23. Base is exact
`c08889b8c1118c89e83c151079df4dc224076760`. No engine, import, GDScript compile,
native run, CI dispatch or service is part of this builder's work. A fresh
independent source critic must review the pushed freeze before any diagnostic.

## Inspected benchmark and bounded hypothesis

The real regression bar is the unchanged `input_mode_test.gd` and strict
`native_log.failed` scan from the base, against actual ARM run 39912086121,
job 120277159133. Independent actual verdict `9f2a67f` retains both original
ZIPs in `m2-mac-journey-recovered/native-actual-c088-independent` and records:
seven suites / 1,584 assertions; input_mode 462 checks / zero assertion failures /
exit 0; strict exit-leak failure; eight remaining suites unrun. The separate
verbose repeat names one `AudioStreamPlaybackWAV` and one `AudioStreamWAV`, both
reference count 1, and orphan `Master`. Original IDs only identify objects in
that process. Prior strict-clean b2e0293 runs prevent a deterministic-cause or
flakiness-resolved claim from a passing sample. The b87afb7 bot diagnostic is
separate; its untyped ObjectDB leaks are not audio evidence.

Inspected pinned engine sources are linked below, with downloaded byte hashes
in `upstream-retrieval.json`. The first two incorrect source paths returned 404;
those retrieval failures remain in the manifest. No engine code is vendored.

* [AudioStreamPlayer3D](https://github.com/godotengine/godot/blob/ed1daf0bf/scene/3d/audio_stream_player_3d.cpp):
  `play` creates a pending playback and starts it on internal physics; `stop`
  cancels the pending request and calls `stop_basic`.
* [AudioStreamPlayerInternal](https://github.com/godotengine/godot/blob/ed1daf0bf/scene/audio/audio_stream_player_internal.cpp):
  EXIT_TREE pauses; PREDELETE stops and clears the vector. `stop_basic` also
  requests AudioServer stop and clears that vector.
* [Node](https://github.com/godotengine/godot/blob/ed1daf0bf/scene/main/node.cpp):
  children exit first, then script `_exit_tree`, `tree_exiting`, native exit
  notification and SceneTree `node_removed`. Actor `_exit_tree` therefore runs
  after its audio children have received their pause notification.
* [AudioServer](https://github.com/godotengine/godot/blob/ed1daf0bf/servers/audio/audio_server.cpp)
  and [state definitions](https://github.com/godotengine/godot/blob/ed1daf0bf/servers/audio/audio_server.h):
  normal stream stop changes state to FADE_OUT_TO_DELETION. Mixing erases the
  list node; main-thread `maybe_cleanup` releases its reference. `finish` stops
  drivers and frees buses; the destructor calls `_cleanup_lists`. These are
  separate lifecycle steps. No public GDScript drain or mix-count API is bound.
* [AudioStreamWAV](https://github.com/godotengine/godot/blob/ed1daf0bf/scene/resources/audio_stream_wav.cpp)
  and [playback fields](https://github.com/godotengine/godot/blob/ed1daf0bf/scene/resources/audio_stream_wav.h):
  each instantiated playback has a strong `base` WAV reference.
* [SafeList](https://github.com/godotengine/godot/blob/ed1daf0bf/core/templates/safe_list.h):
  cleanup applies registered erase callbacks; destroying a list of pointers
  does not infer AudioServer's custom node deletion routine.

Game ownership inspected: actor shot/hurt and four reload voices already stop
in actor `_exit_tree`; reload cancellation uses `stop_all`. The match owns a
device WAV/player, transient network shots own their player under the match,
and grenade audio lives under utility. Match `_exit_tree` has no explicit device
stop. However, input_mode never plants the device, and child PREDELETE already
requests stop. There is insufficient evidence for a product ownership fix.

Hypothesis to test later: the exit leak may be a still-retained AudioServer
playback after a player stop/free request, with its WAV retained through `base`.
The alternative includes an unobserved playback or a different owner. A read-only
ID join can distinguish observed owners from unknown ones without claiming to
inspect internal vectors or the AudioServer state machine.

## Proposed diagnostic and gates

Add an opt-in `--audio-lifecycle-diagnostic` hook to the maintained input_mode
test only. With the flag absent, no helper loads or observation callbacks run.
With it present, observe AudioStreamPlayer3D creation/removal, existing process
frame boundaries, each existing leave call, and the existing final pre-quit
boundary. Retain only primitives and WeakRefs between observations. Record
player ID/path/source owner, role, WAV ID/format/rate/byte count/SHA-256, latest
public playback ID, playing/paused/tree/queued state, weak liveness, driver and
public mix timing readings. Object IDs are strings to preserve all 64 bits.

The diagnostic must not play, stop, free, pause, replace a stream, clear a cache,
change the audio driver, add waits/frames or suppress an engine diagnostic.
Observation costs time and briefly acquires references while reading; no timing
or noninterference claim follows. Public `get_stream_playback` exposes only the
latest voice for a player, so coverage of earlier polyphonic voices stays unknown.
Public mix timing is not a drain acknowledgment. Weak liveness cannot reveal
the retaining owner after a player is gone.

Source/pure acceptance gates for the independent critic:

1. Every `game/scripts`, asset, project, platform, authority/economy/privacy and
   existing runner/scanner byte equals the base. The only maintained test edits
   are optional observation hooks; its assertions, input actions, original await
   count/order, leave/free/quit calls and 462-check expectation stay unchanged.
2. Probe uses WeakRefs and primitive records only between calls. It observes all
   created 3D players, including device, actor, reload, utility and network shot
   owners if those exist; owner identification has an explicit unknown fallback.
3. Pure analyzer controls reject malformed/absent probe data and normalize signed
   decimal ObjectIDs; exact WAV/playback joins cannot substitute an unknown leak,
   borrow an owner from a different WAV or infer a drain from `playing=false`.
   Shared stream owners remain a list. A log without a leak remains a sample.
4. Future actual output must retain exact source/CLI/isolation/process receipts,
   all 462 assertions and strict raw scan. Engine verbose IDs must join exactly
   to observed objects or be reported as unobserved. Post-leave and final weak
   rows must exist; no clean sample closes the leak blocker. Any missing runtime
   coverage or compile failure stays a failure with original output retained.

Builder performs source and pure-Python checks only. GDScript compile, actual
owner attribution, driver progress, actual strict cleanliness and platform
regression gates remain UNVERIFIED until separately released and independently
reviewed. No player-experience or shipped-quality comparison is claimed.
