# Independent AudioStreamWAV exit-lifetime review

Engine: official Godot 4.7.2 `ed1daf0bf001b61586d9930840f2f1394092c079`, native headless/Dummy driver. Read-only review: no game or maintained test source changed by this reviewer. External probes run against `/workspace/sightbreak-three-agent`.

The reproduced exit diagnostics are delayed mixer-owned playback release when a test queues scene deletion and immediately quits. They are not evidence that ENet peers remain owned, and the observations do not establish a persistent runtime audio leak. The narrow correction is to free the test-owned world while the engine is still running and allow the audio mixer and subsequent main-thread cleanup to complete before quitting. No cue phase, waveform, polyphony, replay guard, timing tolerance, or game audio behavior needs changing.

## Reproduction and controls

`cause-shot.gd` constructs one `SBActor`, equips the rifle, plays two shot effects separated by two physics frames, queues its world for deletion, awaits one process frame, and quits. It leaks one `AudioStreamWAV` (reference count 2) and two `AudioStreamPlaybackWAV` objects. The printed playback instance IDs match the two leaked playback IDs after converting signed IDs to unsigned IDs.

Each of these independent controls is clean:

- Add 0.3 seconds after the world has been freed.
- Explicitly stop its shot player and wait 0.3 seconds before freeing.
- Explicitly stop and wait 0.3 seconds after freeing.
- Call its `AudioStreamPlayer3D.play()` directly and wait 0.3 seconds after freeing.

`cause-shot-results.json` and the correspondingly named verbose logs retain all controls.

`cause-native-only.gd` removes all Sightbreak code. It creates a camera, one `AudioStreamPlayer3D`, and a synthesized 0.18-second WAV, calls play twice, frees the world, and quits after one process frame. One of three original runs reproduces the WAV/playback exit leak; this is timing dependent. All three controls with 0.5 seconds after deletion are clean. See `cause-native-only-results.json` and `cause-native-only-{original,drain}-N.txt`.

`cause-sequence-drainalone.gd` is the maintained sequence test from Git HEAD at review start, retaining every original assertion. Its only teardown addition is:

```gdscript
world.queue_free()
await process_frame
await create_timer(0.5).timeout
```

It passes all 92 assertions with zero ObjectDB diagnostics in six runs: three sequential isolated runs and three simultaneous runs contending for the same host. See `cause-sequence-drainalone-results.json`, `cause-sequence-drainalone-{isolated,loaded}-N.txt`, and the generator `cause_drain_controls.py`. These controls do not claim a universal 0.5-second bound under arbitrary scheduler starvation. They establish this fix on the current host under isolated and concurrent native-test load, while the maintained leak scanner must continue rejecting any future residual diagnostic.

The per-section reduction agrees with the lead's independent reduction: the isolated sequence `_casings` section is sufficient for a three-object leak under immediate teardown. Reload sections alone are clean with release and drain. The complete test has more playback activity and therefore more deferred audio references at abrupt shutdown.

## Engine ownership path

Exact official engine sources were fetched from GitHub at the complete commit above and retained as `engine-audio-source.cpp`, `engine-internal.cpp`, `engine-server.cpp`, and `engine-dummy.cpp`.

- `AudioStreamPlayerInternal::notification`, lines 103–115: exit pauses the player's stream; predelete requests stopping each playback and clears the player's references.
- `AudioServer::stop_playback_stream`, lines 1289–1321: stopping a streamed playback marks it `FADE_OUT_TO_DELETION`. This is not immediate release of the server's playback reference.
- `AudioServer::_mix_step`, lines 396–409 and 533–540: the audio mixer consumes the deletion state and removes the playback node after its fade.
- `AudioServer::_delete_stream_playback_list_node`, lines 734–741: removal registers a destructor to run on the main thread; that destructor finally unrefs the stream playback.
- `AudioServer::update` / `_cleanup_lists`, lines 1621–1630: a later engine update runs list cleanup.
- `AudioDriverDummy::thread_func`, lines 57–75: the Dummy mixer is a separate thread, repeatedly processing buffers and sleeping for the buffer duration.
- `AudioServer::finish`, lines 1653–1665, and `AudioDriverDummy::finish`, lines 138–150: driver shutdown stops that thread. One process frame after queued scene deletion does not guarantee that a mixer pass and later main-thread cleanup have both happened.

Thus a scene can already be invalid while the audio server still legitimately holds its former playback until the next mix and cleanup. The independent network reviewer observed exactly this: the playback's reference count dropped about 27.6 ms after the Match became invalid when an audit reference was retained. Their detailed evidence is under `network-review/force-sidearm-track-refs/client.log`.

An early hypothesis concerned pause overwriting a deletion state. That state transition exists in the source, but this review did not reproduce it as the cause of these tests. The post-deletion drain alone passes the full sequence repeatedly, so a speculative engine workaround or new runtime stop policy would be unjustified.

## Review recommendation

Use explicit test-owner deletion followed by a bounded post-deletion mixer drain. Keep fatal scanning of ObjectDB, leaked resources, script errors, and nested child logs. Keep original cue/mixer timing assertions unchanged. Re-run the frozen full matrix on the final maintained patch; these targeted controls do not replace that acceptance gate.
