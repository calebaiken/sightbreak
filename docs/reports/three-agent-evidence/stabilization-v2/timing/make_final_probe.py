from pathlib import Path
root=Path('/workspace/reviews/stabilization-v2-20261016/timing');s=(root/'reload_audio_capture_frameclock.gd').read_text()
s=s.replace('var report: Array[String] = []', 'var report: Array[String] = []\nvar negative := ""\nvar timing: Array = []')
s=s.replace('if argument.begins_with("--out="):', 'if argument.begins_with("--negative="):\n\t\t\tnegative = argument.trim_prefix("--negative=")\n\t\telif argument.begins_with("--out="):')
s=s.replace('\tvar audio: SBReloadAudio = actor._reload_audio', '''\tif negative == "mute" or negative == "cancel-voices":
		var old_audio: Node = actor._reload_audio
		actor.remove_child(old_audio)
		old_audio.free()
		actor._reload_audio = MutedAudio.new() if negative == "mute" else UnstoppedAudio.new()
		actor.add_child(actor._reload_audio)
	var audio: SBReloadAudio = actor._reload_audio''')
s=s.replace('\t\tevent_frames[int(entry.id)] = captures[voice].get_pushed_frames() - origin_frames[voice]', '\t\tevent_frames[int(entry.id)] = captures[voice].get_pushed_frames() - origin_frames[voice]\n\t\ttiming.append({"kind": "event", "event": event, "wall_us": Time.get_ticks_usec(), "frame": event_frames[int(entry.id)], "since_mix_ms": AudioServer.get_time_since_last_mix() * 1000.0})')
s=s.replace('\tvar started := Time.get_ticks_usec()', '''\tprint("PROBE_CAPTURE_READY clock=frames origin=%d" % origin_msec)
	if negative == "early-unlogged":
		audio._voices[0].stream = SBReloadAudio._streams["unlatch"][1]
		audio._voices[0].play()
	var started := Time.get_ticks_usec()''')
s=s.replace('\t\tactor.tick_visual(delta)\n\t\tfor i', '\t\tactor.tick_visual(delta)\n\t\ttiming.append({"kind": "pull", "wall_us": Time.get_ticks_usec(), "wall_from_origin_ms": Time.get_ticks_msec() - origin_msec, "pushed_frames": captures[0].get_pushed_frames() - origin_frames[0], "available": captures[0].get_frames_available(), "discarded": captures[0].get_discarded_frames(), "since_mix_ms": AudioServer.get_time_since_last_mix() * 1000.0})\n\t\tfor i')
s=s.replace('\t\ttext.store_string("\\n".join(report) + "\\n")', '\t\ttext.store_string("\\n".join(report) + "\\n")\n\t\tvar clock_file := FileAccess.open(output.path_join("clock.json"), FileAccess.WRITE)\n\t\tclock_file.store_string(JSON.stringify({"negative": negative, "origin_ms": origin_msec, "origin_frames": origin_frames, "rate": rate, "marks": timing}, "  "))')
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
