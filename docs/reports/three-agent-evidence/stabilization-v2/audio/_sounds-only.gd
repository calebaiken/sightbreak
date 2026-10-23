extends SceneTree
## The reload's sounds as the actor schedules and plays them (SBReloadAudio, Actor._fire_reload_cue), driven by the
## actor's real tick_visual loop. Headless. Presentation only.
##
## What this shows: every event of SBReloadPhases.EVENTS plays exactly once per reload and in order, under every kind
## of authority (a local timer, a 20 Hz snapshot, a stale snapshot, a timer that jumps back); a correction that takes
## the clock back over an event does not play it again; sounds that start on the same tick each get a voice and none
## cuts another, and a fifth does not silence the newest; a cancelled reload stops what was playing and plays
## nothing more; a restart starts clean; a weapon change, a round reset and a death leave no sound behind; reduced
## motion does not touch the audio.
## What it cannot show: what any of it SOUNDS like (the sounds are synthesized, nobody has listened to them), or
## that the mixer plays them at the right instant: reload_audio_capture.gd records the mix of a real-time reload
## through an AudioEffectCapture and looks for each sound's onset.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const TICK := 1.0 / 60.0
var checks := 0
var failures: Array[String] = []
var world: Node3D
var actor: SBActor
var seconds := 2.25
var expected: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if OS.get_environment("RELOAD_TEST_VERBOSE") != "":
		print("%s %s" % ["ok  " if condition else "FAIL", message])
	if not condition:
		failures.append(message)
		push_error(message)

func _new_actor(id: int, weapon := "rifle", local := true) -> SBActor:
	var made := Actor.new()
	made.configure(id, 0, "Reload audio", local)
	world.add_child(made)
	made.reset_for_round(Vector3.ZERO)
	made.credits = 5000
	if weapon != "sidearm":
		made.buy_weapon(weapon)
	made._equip_blend = 0.0
	made.ammo = 10
	made.reserve = 90
	return made

## Steps the actor's presentation one tick with the authoritative timer at `remaining`.
func _tick(a: SBActor, remaining: float) -> Array[String]:
	var before: int = a._reload_audio.serial
	a.reload_remaining = remaining
	a.tick_visual(TICK)
	return a._reload_audio.heard_since(before)

## A whole reload, one tick at a time, from a clean start. `authority`: local, snapshot (every third tick), jitter
## (stale by up to six ticks, never going back up) or regress (jumps up and down by a tenth of a second).
func _play(a: SBActor, authority: String, until := 1.0) -> Array[Dictionary]:
	_tick(a, 0.0)
	a.ammo = 10
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	var held := seconds
	var heard: Array[Dictionary] = []
	for tick in int((seconds * until) / TICK) + 1:
		var truth := maxf(seconds - float(tick) * TICK, 0.001)
		var remaining := truth
		if authority != "local":
			if tick % 3 == 0:
				var sampled := truth
				if authority == "jitter":
					sampled = seconds - maxf(float(tick - rng.randi_range(0, 6)) * TICK, 0.0)
					sampled = minf(sampled, held) if tick > 0 else sampled
				elif authority == "regress":
					sampled += rng.randf_range(-0.1, 0.1)
				held = clampf(sampled, 0.001, seconds)
			remaining = held
		for event in _tick(a, remaining):
			heard.append({"event": event, "tick": tick, "progress": SBReloadPhases.progress(a._reload_clock, seconds)})
	return heard

func _run() -> void:
	seconds = float(Weapons.get_weapon("rifle")["reload"])
	for event in SBReloadPhases.EVENTS:
		expected.append(event[0])
	world = Node3D.new()
	root.add_child(world)
	var floor_body := StaticBody3D.new()
	floor_body.collision_layer = 1
	var floor_shape := CollisionShape3D.new()
	var floor_box := BoxShape3D.new()
	floor_box.size = Vector3(80, 1, 80)
	floor_shape.shape = floor_box
	floor_body.add_child(floor_shape)
	floor_body.position = Vector3(0, -0.5, 0)
	world.add_child(floor_body)
	actor = _new_actor(1)
	await physics_frame
	await physics_frame
	_sounds()
	# excluded _once_in_order
	# excluded _corrections
	# excluded _simultaneous
	# excluded _cancel
	# excluded _restart_and_reset
	# excluded _other_weapons
	print("RELOAD_AUDIO_TEST checks=%d failures=%d" % [checks, failures.size()])
	# Release test-owned actors while the audio mixer is still running.
	world.queue_free()
	await process_frame
	await create_timer(0.15).timeout
	quit(1 if not failures.is_empty() else 0)

## The sounds themselves: one per event, two different variants of each, and no two events alike.
func _sounds() -> void:
	var audio: SBReloadAudio = actor._reload_audio
	check(audio.get_child_count() == SBReloadAudio.VOICES and SBReloadAudio.VOICES >= 4, "the reload has %d voices of its own (separate from the shot, hurt and footstep players)" % audio.get_child_count())
	var seen := {}
	var all_distinct := true
	var variants_differ := true
	var every_event := true
	var healthy := true
	var report := ""
	for event in expected:
		var variants: Array = SBReloadAudio._streams.get(event, [])
		every_event = every_event and variants.size() >= 2
		if variants.size() < 2:
			continue
		variants_differ = variants_differ and (variants[0] as AudioStreamWAV).data != (variants[1] as AudioStreamWAV).data
		for variant in variants:
			var data: PackedByteArray = (variant as AudioStreamWAV).data
			all_distinct = all_distinct and not seen.has(data.hex_encode().sha256_text())
			seen[data.hex_encode().sha256_text()] = event
			var peak := 0
			var energy := 0.0
			for i in range(0, data.size(), 2):
				var s := data.decode_s16(i)
				peak = maxi(peak, absi(s))
				energy += float(s) * float(s)
			var rms := sqrt(energy / (data.size() / 2.0)) / 32767.0
			var length := float(data.size() / 2) / SBReloadAudio.MIX_RATE
			healthy = healthy and peak > 25000 and peak < 32767 and rms > 0.02 and length > 0.05 and length < 0.5
			report += "%s %.2fs peak %d rms %.3f; " % [event, length, peak, rms]
	check(every_event, "every reload event has a sound, in two variants")
	check(all_distinct and variants_differ, "no two sounds are the same recording (%d distinct)" % seen.size())
	check(healthy, "each sound is audible and unclipped: peak 25000 to 32766 of 32767, rms over 0.02, 0.05 to 0.5 s (%s)" % report)

## Every event plays exactly once and in order, in step with the visible progress, under every authority.
func _once_in_order() -> void:
	var reference: Array[Dictionary] = []
	for authority in ["local", "snapshot", "jitter", "regress"]:
		var played := _play(actor, authority)
		var names: Array[String] = []
		for entry in played:
			names.append(entry.event)
		check(names == expected, "%s authority: every event sounds once, in the authored order (%s)" % [authority, names])
		var on_time := true
		var worst := 0.0
		for entry in played:
			var phase := 0.0
			for event in SBReloadPhases.EVENTS:
				if event[0] == entry.event:
					phase = float(event[1])
			var late: float = float(entry.progress) - phase
			worst = maxf(worst, absf(late) if authority != "regress" else 0.0)
			on_time = on_time and late > -0.0001 and (late < 0.03 or authority == "regress")
		check(on_time, "%s authority: each sound lands on the tick the clock reaches its phase, within 0.03 of the reload (worst %.3f)" % [authority, worst])
		if authority == "local":
			reference = played
		elif authority != "regress":
			var worst_gap := 0
			for i in mini(played.size(), reference.size()):
				worst_gap = maxi(worst_gap, absi(int(played[i].tick) - int(reference[i].tick)))
			check(worst_gap <= 8, "%s authority sounds within %d ticks of the local timer's (the stale snapshot's lag) for every event" % [authority, worst_gap])
		_tick(actor, 0.0)
	# Offline and networked clients sound the same list. A reduced-motion player hears the same reload.
	actor.reduced_motion = true
	var calm := _play(actor, "local")
	actor.reduced_motion = false
	var calm_names: Array[String] = []
	for entry in calm:
		calm_names.append(entry.event)
	check(calm_names == expected, "reduced motion changes no sound (%s)" % [calm_names])
	_tick(actor, 0.0)

## A correction that takes the presentation clock back over an event does not play it twice.
func _corrections() -> void:
	_tick(actor, 0.0)
	var heard: Array[String] = []
	# Forward to just past the seat, a correction back to the pouch, forward again, to the end.
	for remaining in [seconds, seconds * 0.7, seconds * 0.45, seconds * 0.15]:
		for tick in 6:
			heard.append_array(_tick(actor, remaining - float(tick) * TICK * 0.5))
	var back_remaining := seconds * 0.55 # jump the authoritative timer UP: the clock follows at once
	for tick in 4:
		heard.append_array(_tick(actor, back_remaining))
	for step in 60:
		heard.append_array(_tick(actor, maxf(back_remaining - float(step) * TICK, 0.001)))
	var counts := {}
	for event in heard:
		counts[event] = int(counts.get(event, 0)) + 1
	var worst := 0
	for key in counts:
		worst = maxi(worst, int(counts[key]))
	check(worst == 1, "a timer correction that goes back over events plays none twice (%s)" % [counts])
	_tick(actor, 0.0)

## Sounds that start on the same tick: each has a voice and all are sounding.
func _simultaneous() -> void:
	var audio: SBReloadAudio = actor._reload_audio
	audio.stop_all()
	var voices: Array[int] = []
	for event in ["seat", "pouch", "land", "extract"]:
		voices.append(audio.play(event, 0.5, 1.62))
	var unique := {}
	for v in voices:
		unique[v] = true
	check(unique.size() == 4 and audio.playing_count() == 4, "four sounds on one tick use four different voices, and all four are playing (%s, %d playing)" % [voices, audio.playing_count()])
	var fifth := audio.play("unlatch", 0.5, 1.62)
	check(fifth >= 0 and audio.voice_playing(fifth) and audio.playing_count() == 4, "a fifth takes a voice (voice %d) and is itself playing, rather than being dropped" % fifth)
	# The shot is its own player: it sounds together with a reload event, and neither stops the other.
	actor._shot_audio.stop()
	var seat_voice := audio.play("seat", 0.8, 1.62)
	actor._shot_audio.play()
	check(actor._shot_audio.playing and audio.voice_playing(seat_voice), "a shot and the seat clunk on the same tick are both playing")
	actor._shot_audio.stop()
	audio.stop_all()

## A cancelled reload stops what was sounding and plays nothing more.
func _cancel() -> void:
	var audio: SBReloadAudio = actor._reload_audio
	# Mid-reload, by a weapon change.
	_tick(actor, 0.0)
	actor.ammo = 10
	var progress_ticks := int(seconds * 0.55 / TICK)
	for tick in progress_ticks:
		_tick(actor, seconds - float(tick) * TICK)
	var before := audio.serial
	check(before > 0 and audio.count_logged("extract") >= 1, "the reload got as far as the extraction before it was cancelled")
	actor.credits = 5000
	actor.inventory.append("smg")
	actor.input_state = {"weapon": "smg"}
	actor.tick_authority(TICK)
	actor.input_state = {}
	actor.tick_visual(TICK)
	check(audio.playing_count() == 0, "a weapon change stops every reload sound that was playing (%d still playing)" % audio.playing_count())
	for tick in 200:
		_tick(actor, 0.0)
	check(audio.serial == before, "and the cancelled reload plays nothing more (%d new sounds)" % (audio.serial - before))
	actor.input_state = {"weapon": "rifle"}
	actor.tick_authority(TICK)
	actor.input_state = {}
	actor.tick_visual(TICK)
	# By the timer going to zero before the seat (a death, a rewind).
	actor.ammo = 10
	for tick in int(seconds * 0.45 / TICK):
		_tick(actor, seconds - float(tick) * TICK)
	var mark := audio.serial
	_tick(actor, 0.0)
	check(audio.playing_count() == 0, "a reload cut short before the seat stops its sounds (%d playing)" % audio.playing_count())
	for tick in 120:
		_tick(actor, 0.0)
	check(audio.serial == mark, "and plays no later event (the landing, the entry, the seat)")
	# By a death: the actor stops everything.
	actor.ammo = 10
	for tick in int(seconds * 0.45 / TICK):
		_tick(actor, seconds - float(tick) * TICK)
	actor.reset_for_round(Vector3.ZERO)
	check(audio.playing_count() == 0, "a round reset mid-reload leaves no reload sound playing")
	# After the seat, ending the reload does not cut the clunk short.
	actor.ammo = 10
	for tick in int(seconds * 0.82 / TICK):
		_tick(actor, seconds - float(tick) * TICK)
	var seat_logged := audio.count_logged("seat") >= 1
	_tick(actor, 0.0)
	check(seat_logged and audio.playing_count() >= 1, "a reload that ends after the seat lets the seat clunk ring out")
	audio.stop_all()
	_tick(actor, 0.0)

## A restart starts clean; the next reload plays everything again, once.
func _restart_and_reset() -> void:
	var audio: SBReloadAudio = actor._reload_audio
	_tick(actor, 0.0)
	actor.ammo = 10
	for tick in int(seconds * 0.6 / TICK):
		_tick(actor, seconds - float(tick) * TICK)
	# The timer is full again with no idle frame: a new reload.
	var heard: Array[String] = []
	for tick in int(seconds / TICK) + 2:
		heard.append_array(_tick(actor, maxf(seconds - float(tick) * TICK, 0.001)))
	check(heard == expected, "a reload restarted with no idle frame plays the whole list once (%s)" % [heard])
	_tick(actor, 0.0)
	# Variants alternate from one reload to the next.
	var first := _play(actor, "local")
	var first_variant: int = audio.log.back().variant
	_tick(actor, 0.0)
	var second := _play(actor, "local")
	var second_variant: int = audio.log.back().variant
	check(first.size() == expected.size() and second.size() == expected.size() and first_variant != second_variant, "two reloads in a row both play the whole list, and use the other variant of each sound (%d, then %d)" % [first_variant, second_variant])
	_tick(actor, 0.0)

## The other weapons: the SMG's magazine has only a release at the start and a seat.
func _other_weapons() -> void:
	var smg := _new_actor(2, "smg")
	var heard: Array[String] = []
	var smg_seconds := float(Weapons.get_weapon("smg")["reload"])
	smg.ammo = 5
	for tick in int(smg_seconds / TICK) + 2:
		var before: int = smg._reload_audio.serial
		smg.reload_remaining = maxf(smg_seconds - float(tick) * TICK, 0.001)
		smg.tick_visual(TICK)
		heard.append_array(smg._reload_audio.heard_since(before))
	check(heard == ["unlatch", "seat"], "the SMG's reload sounds a release and a seat, once each (%s)" % [heard])
	smg.queue_free()
