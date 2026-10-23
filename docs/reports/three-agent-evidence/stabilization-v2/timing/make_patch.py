from pathlib import Path
import difflib
root=Path('/workspace/reviews/stabilization-v2-20261016/timing')
old=Path('/workspace/sightbreak-three-agent-build/game/tests/reload_audio_capture.gd').read_text();s=old
s=s.replace('## event the actor logged (the wall-clock millisecond it played, and the voice) the capture of that voice is searched', '## event the actor logged, the capture frame counter is marked at its cue and that voice is searched')
s=s.replace('## latency of a phone\'s audio output.', '## latency of a phone\'s audio output. Capture frame counters, not elapsed wall time, define this clock: the Dummy\n## driver sleeps a buffer duration AFTER processing, so processing/scheduling delays otherwise accumulate as false early audio.')
s=s.replace('\tvar shot := {"msec": -1}', '\tvar shot := {"msec": -1, "frame": -1}')
start=s.index('\tactor.reload_cue.connect(');end=s.index('\tvar started := Time.get_ticks_usec()',start)
s=s[:start]+'''	# A cue follows play() on the same main-thread call. Mark the independent mixer frame counter here;
	# never align a sound by using its measured onset (that would hide a genuinely early sound).
	var origin_frames: Array[int] = []
	for capture in captures:
		var before := capture.get_pushed_frames()
		capture.clear_buffer()
		var after := capture.get_pushed_frames()
		while before != after:
			before = after
			capture.clear_buffer()
			after = capture.get_pushed_frames()
		origin_frames.append(after)
	var event_frames: Dictionary = {}
	actor.reload_cue.connect(func(event: String, _p: float):
		var entry: Dictionary = audio.log.back()
		var voice: int = entry.voice
		event_frames[int(entry.id)] = captures[voice].get_pushed_frames() - origin_frames[voice]
		if scenario == "shot" and event == "seat":
			shot.msec = Time.get_ticks_msec()
			shot.frame = captures[SBReloadAudio.VOICES].get_pushed_frames() - origin_frames[SBReloadAudio.VOICES]
			actor._shot_audio.play())
	var origin_msec := Time.get_ticks_msec() # diagnostic wall timestamp only; not a sample-time origin
''' +s[end:]
s=s.replace('\tvar cancel_msec := -1','\tvar cancel_msec := -1\n\tvar cancel_frames: Array[int] = []')
s=s.replace('\t\t\tcancel_msec = Time.get_ticks_msec()', '\t\t\tcancel_msec = Time.get_ticks_msec()\n\t\t\tfor i in SBReloadAudio.VOICES:\n\t\t\t\tcancel_frames.append(captures[i].get_pushed_frames() - origin_frames[i])')
s=s.replace('''	# The sample index of wall-clock millisecond m on a bus: the capture was cleared at origin_msec and then ran
	# continuously, so index = (m - origin) * rate / 1000 (the loop above pulled every frame, none was dropped).''','''	# The cue marks and captured samples share the AudioEffectCapture frame clock. Under CPU load the
	# Dummy driver's sample count advances more slowly than wall time; that is not early playback.
	for capture in captures:
		check(capture.get_discarded_frames() == 0, "the capture dropped no frames")''')
s=s.replace('''	# Where in the capture each logged sound starts. The capture's clock is the mixer's, which runs a little ahead
	# of or behind the wall clock by up to a mix chunk, so the offset between the two is not assumed: it is the
	# median over the sounds of (the onset found in the capture, less the sound's own attack, less the wall-clock
	# millisecond play() was called), and what is checked is that each sound's onset sits on that one offset.''','''	# Search around each cue's independently recorded capture-frame mark, retaining the original
	# windows and tolerances. The median compensates chunk phase, not cumulative wall-clock drift.''')
s=s.replace('\t\tvar start_index := int(float(int(entry.msec) - origin_msec) * rate / 1000.0)', '\t\tvar start_index := int(event_frames[int(entry.id)])')
s=s.replace('\t\tvar offset := onset_ms - attack - float(entry.msec)', '\t\tvar offset := float(onset - start_index) * 1000.0 / rate - attack')
s=s.replace('"heard at ', '"heard at ')
s=s.replace('heard at %.0f ms after play() with its %.0f ms attack', 'heard at %.0f ms after the cue in capture frames with its %.0f ms attack')
s=s.replace('float(f.onset_ms) - float(entry.msec), f.attack', 'float(f.offset) + float(f.attack), f.attack')
s=s.replace('the mixer\'s offset from the wall clock is %.0f ms (between -45 and %.0f: output latency plus the mix chunk)', 'the mixer\'s offset from the cue frame mark is %.0f ms (between -45 and %.0f: playback latency plus the mix chunk)')
s=s.replace('\t\t\tvar from := int(float(cancel_msec + 80 - origin_msec) * rate / 1000.0)', '\t\t\tvar from := cancel_frames[i] + int(0.080 * rate)')
s=s.replace('\t\tvar from := int(float(int(shot.msec) - origin_msec - 40) * rate / 1000.0)', '\t\tvar from := int(shot.frame) - int(0.040 * rate)')
s=s.replace('\t\tvar seat_from := int(float(int(seat_entry.msec) - origin_msec - 40) * rate / 1000.0)', '\t\tvar seat_from := int(event_frames[int(seat_entry.id)]) - int(0.040 * rate)')
s=s.replace('\t\tvar first_msec: int = audio.log[0].msec\n\t\tvar quiet_until := int(float(first_msec - origin_msec - 60) * rate / 1000.0)', '\t\tvar quiet_until := int(event_frames[int(audio.log[0].id)]) - int(0.060 * rate)')
(root/'reload_audio_capture_frameclock.gd').write_text(s)
(root/'frameclock.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/game/tests/reload_audio_capture.gd',tofile='b/game/tests/reload_audio_capture.gd')))
