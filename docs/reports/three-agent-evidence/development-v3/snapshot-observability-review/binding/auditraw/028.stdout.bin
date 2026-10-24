extends SceneTree
## One 121-insertion boundary trace. Identical external fixture for both sources.
const COUNT := 121
const ACK := 1
const EPOCH := 7
const ANCHOR := Vector3(3, 0.0625, -2)
const STEP_M := 0.03125 # Exactly representable: 1/32 metre.
var output := ""
var checks := 0
var failures: Array[String] = []

func _initialize() -> void:
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):
			output = arg.trim_prefix("--output=")
	call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func encode(value: Variant) -> Variant:
	if value is Vector3:
		return [value.x, value.y, value.z]
	if value is Vector2:
		return [value.x, value.y]
	if value is Array:
		return value.map(encode)
	if value is Dictionary:
		var result := {}
		for key: Variant in value:
			result[key] = encode(value[key])
		return result
	return value

func run() -> void:
	var actor := SBActor.new()
	actor.configure(1, 0, "Cache boundary fixture", true)
	root.add_child(actor)
	actor.reset_for_round(ANCHOR + Vector3(0.5, 0, 0))
	await physics_frame
	var predictor := SBMovementPrediction.new()
	# Seed a real pending command so repeated ACKs must preserve a nonzero old error.
	predictor.predict(actor, {"move": Vector2.ZERO, "look": Vector2.ZERO}, EPOCH, false)
	var diagnostics: Variant = predictor.get("snapshot_diagnostics")
	var rows: Array = []
	var state := actor.snapshot()
	state.move_ack = ACK
	state.grounded = true
	state.jump_held = false
	state.velocity = Vector3(0.125, 0, 0)
	for index in range(COUNT):
		var ordinal := index + 1
		state.position = ANCHOR + Vector3(float(index) * STEP_M, 0, 0)
		var previous := actor.global_position
		actor.apply_snapshot(state, 1.0)
		predictor.reconcile(actor, state, EPOCH, previous, true)
		check(actor.global_position == state.position and actor.velocity == state.velocity,
			"insertion %d: received movement state preserved" % ordinal)
		check(predictor.error_samples == [0.5] and predictor.pending.is_empty(),
			"insertion %d: repeat cannot append another command error" % ordinal)
		var observation: Variant = null
		if diagnostics != null:
			observation = {"observed_count": diagnostics.observations, "retained_size": diagnostics.samples.size(),
				"eviction_count": diagnostics.evicted, "repeats": diagnostics.repeats, "ignored": diagnostics.ignored,
				"retained_ordinals": diagnostics.samples.map(func(sample): return sample.observation),
				"oldest_sample": diagnostics.samples.front().duplicate(true),
				"latest_sample": diagnostics.samples.back().duplicate(true)}
			check(diagnostics.observations == ordinal and diagnostics.samples.size() == mini(ordinal, 120)
				and diagnostics.evicted == maxi(ordinal - 120, 0), "insertion %d: window boundary counts" % ordinal)
			check(diagnostics.samples.back().first_snapshot_position == ANCHOR
				and diagnostics.samples.back().first_snapshot_drift_m == float(index) * STEP_M,
				"insertion %d: original observed anchor and exact drift survive eviction" % ordinal)
		rows.append(encode({"insertion": ordinal, "epoch": EPOCH, "ack": ACK, "received_position": state.position,
			"diagnostic": observation, "legacy": {"position": actor.global_position, "velocity": actor.velocity,
				"previous_position": previous, "error_samples_m": predictor.error_samples.duplicate(),
				"pending": predictor.pending.duplicate(true), "epoch": predictor.epoch, "sequence": predictor.sequence,
				"corrections": predictor.corrections, "hard_corrections": predictor.hard_corrections,
				"large_corrections": predictor.large_corrections.duplicate(true), "visual_offset": predictor.visual_offset,
				"jump_held": actor._jump_previous, "crouching": actor._crouching,
				"health": actor.health, "ammo": actor.ammo}}))
	var result := {"scope": "121 direct reconciliations, same ACK; no transport or simulation-time claim",
		"engine": Engine.get_version_info().string, "count": COUNT, "anchor": encode(ANCHOR), "step_m": STEP_M,
		"diagnostic_status": "available" if diagnostics != null else "not_available_not_applicable",
		"checks": checks, "failures": failures, "rows": rows}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file == null:
			push_error("Cannot write cache-boundary trace")
			quit(1)
			return
		file.store_string(JSON.stringify(result, "\t") + "\n")
		file.close()
	actor.queue_free()
	await process_frame
	await create_timer(0.1).timeout
	print("ACK_CACHE_BOUNDARY_PROBE checks=%d failures=%d" % [checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)
