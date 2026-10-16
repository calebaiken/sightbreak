from pathlib import Path
root=Path('/workspace/reviews/stabilization-v2-20261016/timing')
s=Path('/workspace/sightbreak-three-agent-build/game/tests/reload_audio_capture.gd').read_text()
s=s.replace('var report: Array[String] = []', 'var report: Array[String] = []\nvar clock_mode := "wall"\nvar negative := ""\nvar timing: Array = []\nvar origin_frames: Array[int] = []\nvar event_frames: Dictionary = {}')
s=s.replace('if argument.begins_with("--out="):', 'if argument.begins_with("--clock="):\n\t\t\tclock_mode = argument.trim_prefix("--clock=")\n\t\telif argument.begins_with("--negative="):\n\t\t\tnegative = argument.trim_prefix("--negative=")\n\t\telif argument.begins_with("--out="):')
s=s.replace('\tvar audio: SBReloadAudio = actor._reload_audio', '''\tif negative == "mute" or negative == "cancel-voices":
		var old_audio: Node = actor._reload_audio
		actor.remove_child(old_audio)
		old_audio.free()
		actor._reload_audio = MutedAudio.new() if negative == "mute" else UnstoppedAudio.new()
		actor.add_child(actor._reload_audio)
	var audio: SBReloadAudio = actor._reload_audio''')
s=s.replace('\tfor capture in captures:\n\t\tcapture.clear_buffer()', '''\tfor capture in captures:
		var before := capture.get_pushed_frames()
		capture.clear_buffer()
		var after := capture.get_pushed_frames()
		while before != after:
			before = after
			capture.clear_buffer()
			after = capture.get_pushed_frames()
		origin_frames.append(after)
	actor.reload_cue.connect(func(event: String, _p: float):
		var entry: Dictionary = audio.log.back()
		var voice: int = entry.voice
		event_frames[int(entry.id)] = captures[voice].get_pushed_frames() - origin_frames[voice]
		timing.append({"kind": "event", "event": event, "wall_us": Time.get_ticks_usec(), "wall_from_origin_ms": Time.get_ticks_msec() - origin_msec, "frame": event_frames[int(entry.id)], "since_mix_ms": AudioServer.get_time_since_last_mix() * 1000.0, "pushed": captures[voice].get_pushed_frames(), "dropped": captures[voice].get_discarded_frames()})
	)
	print("PROBE_CAPTURE_READY clock=%s origin=%d" % [clock_mode, origin_msec])
	if negative == "early-unlogged":
		audio._voices[0].stream = SBReloadAudio._streams["unlatch"][1]
		audio._voices[0].play()''')
s=s.replace('\t\tactor.tick_visual(delta)\n\t\tfor i', '''\t\tactor.tick_visual(delta)
		timing.append({"kind": "pull", "wall_us": Time.get_ticks_usec(), "wall_from_origin_ms": Time.get_ticks_msec() - origin_msec, "pushed_frames": captures[0].get_pushed_frames() - origin_frames[0], "available": captures[0].get_frames_available(), "discarded": captures[0].get_discarded_frames(), "since_mix_ms": AudioServer.get_time_since_last_mix() * 1000.0})
		for i''')
s=s.replace('\t\tvar start_index := int(float(int(entry.msec) - origin_msec) * rate / 1000.0)', '\t\tvar start_index := int(float(int(entry.msec) - origin_msec) * rate / 1000.0)\n\t\tif clock_mode == "frames":\n\t\t\tstart_index = int(event_frames[int(entry.id)])')
s=s.replace('\t\tvar offset := onset_ms - attack - float(entry.msec)', '\t\tvar offset := onset_ms - attack - float(entry.msec)\n\t\tif clock_mode == "frames":\n\t\t\toffset = float(onset - start_index) * 1000.0 / rate - attack')
s=s.replace('\t\tvar quiet_until := int(float(first_msec - origin_msec - 60) * rate / 1000.0)', '\t\tvar quiet_until := int(float(first_msec - origin_msec - 60) * rate / 1000.0)\n\t\tif clock_mode == "frames":\n\t\t\tquiet_until = int(event_frames[int(audio.log[0].id)]) - int(0.060 * rate)')
s=s.replace('\t\t\tvar from := int(float(cancel_msec + 80 - origin_msec) * rate / 1000.0)', '\t\t\tvar from := int(float(cancel_msec + 80 - origin_msec) * rate / 1000.0)')
# Cancel/shot use absolute wall coordinates, so leave them initially, ensure only reload compares proposed clock.
s=s.replace('\t\ttext.store_string("\\n".join(report) + "\\n")', '\t\ttext.store_string("\\n".join(report) + "\\n")\n\t\tvar clock_file := FileAccess.open(output.path_join("clock.json"), FileAccess.WRITE)\n\t\tclock_file.store_string(JSON.stringify({"clock": clock_mode, "negative": negative, "origin_ms": origin_msec, "origin_frames": origin_frames, "rate": rate, "marks": timing}, "  "))')
s+='''\nclass MutedAudio:
	extends "res://scripts/gameplay/reload_audio.gd"
	func play(event: String, progress: float, head_height: float) -> int:
		var voice := super.play(event, progress, head_height)
		if voice >= 0:
			_voices[voice].volume_db = -95.0
		return voice

class UnstoppedAudio:
	extends "res://scripts/gameplay/reload_audio.gd"
	func stop_all() -> void:
		pass
'''
(root/'reload_audio_clock_probe.gd').write_text(s)
