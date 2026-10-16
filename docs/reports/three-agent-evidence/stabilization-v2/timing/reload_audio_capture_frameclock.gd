extends SceneTree
## Records the reload's real audio as the mixer produces it, and checks it against what the actor scheduled. Needs a
## display-less or native run with an audio driver (`--audio-driver Dummy` mixes in real time like a sound card does,
## and has no speaker), so unlike reload_audio_test.gd (which steps simulated ticks) it runs in REAL time: the reload
## takes its 2.25 seconds.
##
## Each of the reload's four voices (SBReloadAudio) is routed to a bus of its own with an AudioEffectCapture, and the
## actor's shot player to a fifth, so a sound that overlaps another can still be heard on its own voice. For every
## event the actor logged, the capture frame counter is marked at its cue and that voice is searched
## for the sound's onset: it must be there, not before the event, and within the mixer's latency of it.
##
##   --out=<dir>        write mix.wav (the five buses summed, mono), voices.csv (per-event onset and peak) and report.txt
##   --scenario=<name>  reload (default), cancel (a weapon change at 63 % of the reload, 90 ms into the landing), shot (a shot fired on the tick
##                      of the seat)
##   --reduced          reduced motion on
## It cannot say what any of it sounds like; nobody has listened to it.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const ONSET_LEVEL := 0.012      # the first sample above this, on the voice's own bus, is the sound's onset
## How far a sound's onset in the mix may sit from the run's typical offset, in ms. The Dummy driver mixes in chunks of
## about 46 ms (2048 frames at 44.1 kHz) and a sound starts at the next chunk boundary, so which of two sounds
## lands early or late in the mix is decided by where play() fell in a chunk (the same each run, as the events fall
## at the same time: onsets measured at 12 to 18 ms after play() on two voices and 61 to 71 ms on the other two, in
## both runs; the spread over the eight runs made was 103 ms, so the bound is two chunks, 90 ms, either side of the run's
## typical offset). This bound checks each sound is on its voice at its time to that accuracy; it says nothing about the
## latency of a phone's audio output. Capture frame counters, not elapsed wall time, define this clock: the Dummy
## driver sleeps a buffer duration AFTER processing, so processing/scheduling delays otherwise accumulate as false early audio.
const TOLERANCE_MS := 90.0
const SILENT := 0.0008          # below this, a bus is silent
## The cancel scenario's weapon change comes at this fraction of the reload: 90 ms into the landing sound, whose second bounce
## comes 190 ms after it starts, so a build that never stops its voices is heard bouncing 100 ms after the cancel while a
## real cancel (the mixer stops a voice within about 65 ms) is silent by then. The first version cancelled at 0.55, when
## every sound was nearly over, and such a build passed: negative control A6.
const CANCEL_AT := 0.63
const MAX_LATENCY := 0.120      # seconds from the actor's play() to the mixer's clock reading it
var checks := 0
var failures: Array[String] = []
var report: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	report.append("%s %s" % ["ok  " if condition else "FAIL", message])
	if not condition:
		failures.append(message)
		push_error(message)

func _run() -> void:
	var output := ""
	var scenario := "reload"
	var reduced := false
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
		elif argument.begins_with("--scenario="):
			scenario = argument.trim_prefix("--scenario=")
		elif argument == "--reduced":
			reduced = true
	var world := Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	var floor_shape := CollisionShape3D.new()
	var floor_box := BoxShape3D.new()
	floor_box.size = Vector3(80, 1, 80)
	floor_shape.shape = floor_box
	floor_body.add_child(floor_shape)
	floor_body.position = Vector3(0, -0.5, 0)
	world.add_child(floor_body)
	var actor := Actor.new()
	actor.configure(1, 0, "Audio capture", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	actor.credits = 5000
	actor.buy_weapon("rifle")
	actor._equip_blend = 0.0
	actor.reduced_motion = reduced
	actor.ammo = 10
	actor.reserve = 90
	actor.camera.current = true
	var audio: SBReloadAudio = actor._reload_audio
	# One bus and one capture per voice, and one for the shot.
	var captures: Array[AudioEffectCapture] = []
	var names: Array[StringName] = []
	for i in SBReloadAudio.VOICES + 1:
		var bus_name := StringName("capture_%d" % i)
		AudioServer.add_bus()
		var index := AudioServer.bus_count - 1
		AudioServer.set_bus_name(index, bus_name)
		var capture := AudioEffectCapture.new()
		capture.buffer_length = 4.0
		AudioServer.add_bus_effect(index, capture)
		captures.append(capture)
		names.append(bus_name)
		if i < SBReloadAudio.VOICES:
			audio.route(bus_name, i)
		else:
			actor._shot_audio.bus = bus_name
	for i in 4:
		await process_frame
	var rate := AudioServer.get_mix_rate()
	var samples: Array = []
	for i in captures.size():
		samples.append(PackedFloat32Array())
	var seconds := float(Weapons.get_weapon("rifle")["reload"])
	var shot := {"msec": -1, "frame": -1} # a lambda captures a plain variable by value, so the time goes in a Dictionary
	# A cue follows play() on the same main-thread call. Mark the independent mixer frame counter here;
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
	var started := Time.get_ticks_usec()
	var last := started
	var cancel_msec := -1
	var cancel_frames: Array[int] = []
	actor.start_reload()
	var end_at := seconds + 0.9
	while float(Time.get_ticks_usec() - started) / 1e6 < end_at:
		await process_frame
		var now := Time.get_ticks_usec()
		var delta := float(now - last) / 1e6
		last = now
		var elapsed := float(now - started) / 1e6
		if scenario == "cancel" and cancel_msec < 0 and elapsed >= seconds * CANCEL_AT:
			cancel_msec = Time.get_ticks_msec()
			for i in SBReloadAudio.VOICES:
				cancel_frames.append(captures[i].get_pushed_frames() - origin_frames[i])
			actor.credits = 5000
			actor.inventory.append("smg")
			actor.input_state = {"weapon": "smg"}
			actor.tick_authority(delta)
			actor.input_state = {}
		else:
			actor.tick_authority(delta)
		actor.tick_visual(delta)
		for i in captures.size():
			var available := captures[i].get_frames_available()
			if available > 0:
				var frames := captures[i].get_buffer(available)
				var mono := PackedFloat32Array()
				mono.resize(frames.size())
				for k in frames.size():
					mono[k] = (frames[k].x + frames[k].y) * 0.5
				var held: PackedFloat32Array = samples[i]
				held.append_array(mono)
				samples[i] = held
	# The cue marks and captured samples share the AudioEffectCapture frame clock. Under CPU load the
	# Dummy driver's sample count advances more slowly than wall time; that is not early playback.
	for capture in captures:
		check(capture.get_discarded_frames() == 0, "the capture dropped no frames")
	var peaks: Array[float] = []
	for i in captures.size():
		var peak := 0.0
		for s in samples[i]:
			peak = maxf(peak, absf(s))
		peaks.append(peak)
	report.append("captured %d frames per bus at %d Hz; peaks %s" % [(samples[0] as PackedFloat32Array).size(), rate, peaks])
	for i in captures.size():
		var firsts: Array[String] = []
		var buffer_i: PackedFloat32Array = samples[i]
		var quiet := true
		var last_on := -1
		for k in buffer_i.size():
			var loud := absf(buffer_i[k]) > ONSET_LEVEL
			if loud and quiet and (last_on < 0 or k - last_on > int(0.06 * rate)):
				firsts.append("%.0f" % (float(k) * 1000.0 / rate))
			if loud:
				last_on = k
			quiet = not loud
		report.append("bus %d onsets (ms from capture start): %s" % [i, ", ".join(firsts)])
	for entry in audio.log:
		report.append("logged %s at %d ms from origin (voice %d)" % [entry.event, int(entry.msec) - origin_msec, entry.voice])
	var csv: Array[String] = ["event,voice,variant,played_ms,onset_ms,latency_ms,peak"]
	var played_events: Array[String] = []
	for entry in audio.log:
		played_events.append(entry.event)
	var expected: Array[String] = []
	for event in SBReloadPhases.EVENTS:
		expected.append(event[0])
	if scenario == "cancel":
		# Cancelled just after the landing: the unlatch, extract, pouch and land have played; the entry and the seat never do.
		check(played_events == ["unlatch", "extract", "pouch", "land"], "the cancelled reload logged only what came before the cancel (%s)" % [played_events])
	else:
		check(played_events == expected, "the reload logged every event once, in order (%s)" % [played_events])
	# Search around each cue's independently recorded capture-frame mark, retaining the original
	# windows and tolerances. The median compensates chunk phase, not cumulative wall-clock drift.
	var offsets: Array[float] = []
	var found: Array[Dictionary] = []
	for entry in audio.log:
		var voice: int = entry.voice
		var buffer: PackedFloat32Array = samples[voice]
		var start_index := int(event_frames[int(entry.id)])
		var window_from := maxi(0, start_index - int(0.06 * rate))
		var window_to := mini(buffer.size(), start_index + int(0.40 * rate))
		var peak := 0.0
		for k in range(window_from, window_to):
			peak = maxf(peak, absf(buffer[k]))
		var onset := -1
		for k in range(window_from, window_to):
			if absf(buffer[k]) > maxf(0.10 * peak, 0.004):
				onset = k
				break
		var attack := _attack_ms(entry.event, entry.variant)
		var onset_ms := float(onset) * 1000.0 / rate + origin_msec
		var offset := float(onset - start_index) * 1000.0 / rate - attack
		if onset >= 0:
			offsets.append(offset)
		found.append({"entry": entry, "onset_ms": onset_ms, "onset": onset, "peak": peak, "attack": attack, "offset": offset})
	var typical := 0.0
	if not offsets.is_empty():
		offsets.sort()
		typical = offsets[offsets.size() / 2]
	var worst_error := 0.0
	var all_found := true
	for f in found:
		var entry: Dictionary = f.entry
		var error: float = float(f.offset) - typical
		worst_error = maxf(worst_error, absf(error))
		var good: bool = f.onset >= 0 and f.peak > 0.02 and absf(error) <= TOLERANCE_MS
		all_found = all_found and good
		csv.append("%s,%d,%d,%d,%.1f,%.1f,%.3f" % [entry.event, entry.voice, entry.variant, entry.msec, f.onset_ms, f.offset, f.peak])
		check(good, "%s on voice %d: heard at %.0f ms after the cue in capture frames with its %.0f ms attack, %.0f ms from the run's typical offset (peak %.3f)" % [entry.event, entry.voice, float(f.offset) + float(f.attack), f.attack, error, f.peak])
	if scenario != "cancel":
		check(typical > -45.0 and typical < MAX_LATENCY * 1000.0, "the mixer's offset from the cue frame mark is %.0f ms (between -45 and %.0f: playback latency plus the mix chunk)" % [typical, MAX_LATENCY * 1000.0])
	if scenario == "cancel":
		# After the cancel (and the mixer's latency) no reload voice makes a sound.
		var loud_after := 0.0
		for i in SBReloadAudio.VOICES:
			var buffer: PackedFloat32Array = samples[i]
			var from := cancel_frames[i] + int(0.080 * rate)
			for k in range(maxi(from, 0), buffer.size()):
				loud_after = maxf(loud_after, absf(buffer[k]))
		check(loud_after < SILENT, "after the cancel (and 80 ms of mixer latency) every reload voice is silent (peak %.5f)" % loud_after)
	if scenario == "shot":
		var shot_buffer: PackedFloat32Array = samples[SBReloadAudio.VOICES]
		var from := int(shot.frame) - int(0.040 * rate)
		var shot_peak := 0.0
		for k in range(maxi(from, 0), mini(shot_buffer.size(), from + int(0.25 * rate))):
			shot_peak = maxf(shot_peak, absf(shot_buffer[k]))
		var seat_entry: Dictionary = audio.log.back()
		var seat_buffer: PackedFloat32Array = samples[int(seat_entry.voice)]
		var seat_from := int(event_frames[int(seat_entry.id)]) - int(0.040 * rate)
		var seat_peak := 0.0
		for k in range(maxi(seat_from, 0), mini(seat_buffer.size(), seat_from + int(0.25 * rate))):
			seat_peak = maxf(seat_peak, absf(seat_buffer[k]))
		check(shot_peak > ONSET_LEVEL and seat_peak > ONSET_LEVEL, "a shot fired on the tick of the seat and the seat clunk are both in the mix, each on its own bus (shot %.3f, seat %.3f)" % [shot_peak, seat_peak])
	# Before the first event the reload voices are silent (nothing plays early).
	if scenario != "cancel" and audio.log.size() > 0:
		var quiet_until := int(event_frames[int(audio.log[0].id)]) - int(0.060 * rate)
		var early := 0.0
		for i in SBReloadAudio.VOICES:
			for k in range(0, mini(quiet_until, (samples[i] as PackedFloat32Array).size())):
				early = maxf(early, absf((samples[i] as PackedFloat32Array)[k]))
		check(early < SILENT, "nothing is audible on any reload voice before the first event (peak %.5f)" % early)
	if not output.is_empty():
		DirAccess.make_dir_recursive_absolute(output)
		_write_wav(output.path_join("mix_%s.wav" % scenario), samples, rate)
		var file := FileAccess.open(output.path_join("voices_%s.csv" % scenario), FileAccess.WRITE)
		file.store_string("\n".join(csv) + "\n")
		var text := FileAccess.open(output.path_join("report_%s.txt" % scenario), FileAccess.WRITE)
		text.store_string("\n".join(report) + "\n")
	for line in report:
		print(line)
	print("RELOAD_AUDIO_CAPTURE scenario=%s reduced=%s checks=%d failures=%d" % [scenario, reduced, checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)

## Milliseconds into a synthesized sound before it first exceeds a tenth of its own peak.
func _attack_ms(event: String, variant: int) -> float:
	var stream: AudioStreamWAV = (SBReloadAudio._streams[event] as Array)[variant]
	var data := stream.data
	var peak := 0
	for i in range(0, data.size(), 2):
		peak = maxi(peak, absi(data.decode_s16(i)))
	for i in range(0, data.size(), 2):
		if absi(data.decode_s16(i)) > peak / 10:
			return float(i / 2) * 1000.0 / float(stream.mix_rate)
	return 0.0

func _write_wav(path: String, samples: Array, rate: float) -> void:
	var frames := 0
	for s in samples:
		frames = maxi(frames, (s as PackedFloat32Array).size())
	var data := PackedByteArray()
	data.resize(frames * 2)
	for k in frames:
		var sum := 0.0
		for s in samples:
			if k < (s as PackedFloat32Array).size():
				sum += (s as PackedFloat32Array)[k]
		data.encode_s16(k * 2, int(clampf(sum, -1.0, 1.0) * 32767.0))
	var wav := AudioStreamWAV.new()
	wav.format = AudioStreamWAV.FORMAT_16_BITS
	wav.mix_rate = int(rate)
	wav.data = data
	wav.save_to_wav(path)
