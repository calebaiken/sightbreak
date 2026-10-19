extends "res://tests/prediction_timeline_probe.gd"
## Same packet schedule as the retained timeline probe; additive observer only.
var lifecycle: Dictionary = {}
var lifecycle_timeline: Array = []

func snapshot_metrics(predictor: SBMovementPrediction) -> Dictionary:
	var diagnostics: Variant = predictor.get("snapshot_diagnostics")
	if diagnostics == null or diagnostics.samples.is_empty():
		return {"snapshot_observation": null}
	var sample: Dictionary = diagnostics.samples.back().duplicate(true)
	sample.position = vector(sample.position - OFFSET)
	sample.first_snapshot_position = vector(sample.first_snapshot_position - OFFSET)
	return {"snapshot_observation": sample}

func prediction_metrics(predictor: SBMovementPrediction) -> Dictionary:
	var diagnostics: Variant = predictor.get("snapshot_diagnostics")
	var correction_samples := predictor.large_corrections.duplicate(true)
	for sample: Dictionary in correction_samples:
		for field: String in ["previous", "authority", "replayed"]:
			sample[field] = vector(sample[field] - OFFSET)
	return {"snapshot_diagnostic_observations": diagnostics.observations if diagnostics != null else 0,
		"snapshot_diagnostic_repeats": diagnostics.repeats if diagnostics != null else 0,
		"snapshot_diagnostic_retained": diagnostics.samples.size() if diagnostics != null else 0,
		"snapshot_diagnostic_evicted": diagnostics.evicted if diagnostics != null else 0,
		"legacy_error_samples_m": predictor.error_samples.duplicate(),
		"legacy_corrections": predictor.corrections, "legacy_visual_offset": vector(predictor.visual_offset),
		"legacy_large_corrections": correction_samples}

func report_metrics() -> Dictionary:
	return {"diagnostic_lifecycle": lifecycle, "lifecycle_timeline": lifecycle_timeline}

func deliver(predictor: SBMovementPrediction, actor: SBActor, ack: int, position: Vector3, current_epoch: int, enabled: bool = false) -> void:
	var state := actor.snapshot()
	state.move_ack = ack
	state.position = position
	state.grounded = true
	state.jump_held = false
	var previous := actor.global_position
	actor.apply_snapshot(state, 1.0)
	predictor.reconcile(actor, state, current_epoch, previous, enabled)

func shared_lifecycle_timeline() -> void:
	# Execute this identical packet/reset sequence even when the new helper is absent.
	var world := Node3D.new()
	root.add_child(world)
	block(world, Vector3(0, -0.5, 0), Vector3(80, 1, 80))
	var actor := SBActor.new()
	actor.configure(1, 0, "Matched lifecycle", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0.05, 0))
	var predictor := SBMovementPrediction.new()
	var diagnostics: Variant = predictor.get("snapshot_diagnostics")
	var buffer := SBSnapshotBuffer.new()
	var events: Array = [
		["packet", 100, 1, 1, 0.0, true], ["packet", 100, 1, 1, 30.0, false],
		["packet", 99, 1, 1, 29.0, false], ["packet", 103, 1, 1, 0.25, true],
		["packet", 102, 1, 1, 28.0, false], ["packet", 106, 1, 2, 0.5, true],
		["connection_reset", 0, 0, 0, 0.0, false], ["packet", 0, 0, 0, 0.0, true],
		["packet", 3, 0, 0, 0.3, true], ["packet", 6, 1, 0, 10.0, true],
		["packet", 5, 0, 0, 27.0, false], ["packet", 9, 1, 1, 10.1, true],
		["predict_epoch", 10, 2, 0, 0.0, false], ["packet", 12, 2, 0, 20.0, true]]
	await physics_frame
	for event: Array in events:
		var accepted := false
		if event[0] == "connection_reset":
			predictor.reset(true)
			buffer.clear()
		elif event[0] == "predict_epoch":
			predictor.predict(actor, {"move": Vector2(0.2, 0), "look": Vector2.ZERO}, event[2], true)
		else:
			var position := Vector3(float(event[4]), 0.05, 0)
			accepted = buffer.push(event[1], float(event[1]) / 60.0, event[2], [{"id": 1, "position": position}])
			check(accepted == event[5], "matched lifecycle packet acceptance follows outer tick order")
			if accepted:
				deliver(predictor, actor, event[3], position, event[2], true)
			predictor.predict(actor, {"move": Vector2(0.2, 0), "look": Vector2.ZERO}, buffer.epoch, true)
		var observation: Variant = null
		if diagnostics != null:
			observation = {"epoch": diagnostics.epoch, "observations": diagnostics.observations, "sample": null}
			if not diagnostics.samples.is_empty():
				var sample: Dictionary = diagnostics.samples.back().duplicate(true)
				sample.position = vector(sample.position)
				sample.first_snapshot_position = vector(sample.first_snapshot_position)
				observation.sample = sample
		lifecycle_timeline.append({"event": event[0], "tick": event[1], "epoch": event[2], "ack": event[3], "accepted": accepted,
			"received_snapshot_position": vector(Vector3(float(event[4]), 0.05, 0)) if event[0] == "packet" else null,
			"position": vector(actor.global_position), "velocity": vector(actor.velocity), "ammo": actor.ammo,
			"health": actor.health, "jump_held": actor._jump_previous, "crouching": actor._crouching,
			"prediction_epoch": predictor.epoch, "sequence": predictor.sequence,
			"pending_sequences": predictor.pending.map(func(record): return record.command.sequence),
			"legacy_error_samples_m": predictor.error_samples.duplicate(), "corrections": predictor.corrections,
			"hard_corrections": predictor.hard_corrections, "visual_offset": vector(predictor.visual_offset),
			"snapshot_diagnostics": observation})
		await physics_frame
	check(buffer.stale_packets == 4, "matched lifecycle rejects duplicate/reordered packets across reset")
	world.queue_free()
	await process_frame
	await create_timer(0.5).timeout

func lifecycle_controls() -> void:
	var predictor := SBMovementPrediction.new()
	var diagnostics: Variant = predictor.get("snapshot_diagnostics")
	if diagnostics == null:
		lifecycle = {"available": false, "checks": 0, "scope": "absent diagnostic; coverage gate evaluated separately"}
		return
	var before_checks := checks
	var world := Node3D.new()
	root.add_child(world)
	var actor := SBActor.new()
	actor.configure(1, 0, "Diagnostic controls", true)
	world.add_child(actor)
	actor.reset_for_round(Vector3.ZERO)
	await physics_frame
	check(diagnostics.samples.is_empty() and diagnostics.epoch == -1, "diagnostic starts empty")
	deliver(predictor, actor, 9, Vector3(1, 0, 0), 7)
	check(diagnostics.observations == 1 and diagnostics.samples.size() == 1, "first epoch snapshot is observed before replay's epoch return")
	check(diagnostics.samples.back().anchor_kind == "first_observed_snapshot_not_consumption", "anchor explicitly excludes consumption-time inference")
	check(not diagnostics.samples.back().repeated_ack and diagnostics.samples.back().previous_snapshot_delta_m == null, "first observation has no invented prior-snapshot delta")
	# Give the old ACK metric one real pending record; repeat must not append again.
	predictor.pending.append({"command": {"sequence": 10}, "position": Vector3(1.8, 0, 0)})
	deliver(predictor, actor, 10, Vector3(1.5, 0, 0), 7)
	var legacy := predictor.error_samples.duplicate()
	deliver(predictor, actor, 10, Vector3(1.9, 0, 0), 7)
	var repeat: Dictionary = diagnostics.samples.back()
	check(repeat.repeated_ack and is_equal_approx(repeat.previous_snapshot_delta_m, 0.4), "repeat measures snapshot-to-snapshot delta")
	check(is_equal_approx(repeat.first_snapshot_drift_m, 0.4), "repeat is anchored to first observed snapshot")
	check(predictor.error_samples == legacy and legacy.size() == 1 and is_equal_approx(legacy[0], 0.3), "repeat leaves consumed-command error series unchanged")
	deliver(predictor, actor, 10, Vector3(1.9, 0, 0), 7)
	check(diagnostics.samples.back().previous_snapshot_delta_m == 0.0, "identical repeated snapshot has zero measured delta")
	var accepted: int = diagnostics.observations
	var ignored: int = diagnostics.ignored
	diagnostics.observe({"move_ack": 8, "position": Vector3(50, 0, 0)}, 7, false)
	diagnostics.observe({"move_ack": 10, "position": Vector3(50, 0, 0)}, 6, false)
	check(diagnostics.observations == accepted and diagnostics.ignored == ignored + 2, "regressed ACK and stale epoch do not pollute diagnostic anchors")
	for invalid: Dictionary in [{}, {"move_ack": -1, "position": Vector3.ZERO}, {"move_ack": 10.0, "position": Vector3.ZERO},
		{"move_ack": 10, "position": Vector3(NAN, 0, 0)}, {"move_ack": 10, "position": Vector3.INF}, {"move_ack": 10, "position": Vector3(1024, 0, 0)}]:
		diagnostics.observe(invalid, 8, false)
	check(diagnostics.observations == accepted and diagnostics.epoch == 7, "invalid future-epoch data cannot erase current diagnostic history")
	# Upstream tick ordering is the existing snapshot buffer, not inferred by ACK.
	var buffer := SBSnapshotBuffer.new()
	var delivery_trace: Array = []
	for row: Array in [[20, 8, 1, 0.0], [20, 8, 1, 20.0], [19, 8, 1, 19.0], [21, 8, 1, 0.25], [23, 8, 1, 0.5], [22, 8, 1, 22.0], [24, 9, 1, 30.0], [23, 8, 1, 23.0]]:
		var position := Vector3(float(row[3]), 0, 0)
		var allowed := buffer.push(row[0], float(row[0]) / 60.0, row[1], [{"id": 1, "position": position}])
		if allowed:
			deliver(predictor, actor, row[2], position, row[1])
		delivery_trace.append({"tick": row[0], "epoch": row[1], "accepted": allowed,
			"observations": diagnostics.observations, "drift": diagnostics.samples.back().first_snapshot_drift_m})
	check(buffer.stale_packets == 4, "duplicate and reordered outer ticks are rejected before reconciliation")
	check(delivery_trace[4].observations == 3 and is_equal_approx(delivery_trace[4].drift, 0.5), "accepted repeated ACK order has correct first-snapshot drift")
	check(diagnostics.epoch == 9 and diagnostics.observations == 1 and diagnostics.samples.back().first_snapshot_drift_m == 0.0, "round transition never compares to previous epoch's pose")
	predictor.predict(actor, {"move": Vector2.ZERO, "look": Vector2.ZERO}, 10, false)
	check(diagnostics.epoch == 10 and diagnostics.samples.is_empty() and diagnostics.observations == 0, "predict-side epoch change clears diagnostic samples")
	deliver(predictor, actor, 0, Vector3.ZERO, 10)
	check(diagnostics.observations == 1 and not diagnostics.samples.back().repeated_ack, "ACK zero is an explicit first observation after round reset")
	# Store only allowlisted values, never references to combat/private state.
	var state := {"move_ack": 1, "position": Vector3(2, 0, 0), "ammo": 9, "health": 42, "inventory": ["rifle"], "name": "PRIVATE"}
	diagnostics.observe(state, 10, false)
	state.position = Vector3(90, 0, 0)
	state.inventory.append("sidearm")
	var stored: Dictionary = diagnostics.samples.back()
	check(stored.position == Vector3(2, 0, 0), "observation owns copied value rather than caller state")
	check(stored.size() == 10 and not stored.has("ammo") and not stored.has("health") and not stored.has("inventory") and not stored.has("name"), "diagnostics retain only allowlisted movement metadata")
	diagnostics.clear()
	for index in range(481):
		diagnostics.observe({"move_ack": 25, "position": Vector3(float(index) / 1000, 0, 0)}, 11, index % 2 == 0)
	check(diagnostics.samples.size() == 120 and diagnostics.observations == 481 and diagnostics.evicted == 361, "long stream retains exactly bounded sample window")
	check(diagnostics.samples.front().observation == 362 and diagnostics.samples.back().observation == 481, "eviction keeps the newest observations")
	check(is_equal_approx(diagnostics.samples.back().first_snapshot_drift_m, 0.480), "single ACK anchor survives sample-window eviction")
	var bounded_receipt := {"observations": diagnostics.observations, "retained": diagnostics.samples.size(), "evicted": diagnostics.evicted,
		"first_snapshot_drift_m": diagnostics.samples.back().first_snapshot_drift_m}
	var other := SBMovementPrediction.new()
	check(other.get("snapshot_diagnostics").samples.is_empty(), "predictors do not share diagnostic state")
	predictor.reset(false)
	check(diagnostics.samples.is_empty() and diagnostics.epoch == -1 and diagnostics.repeats == 0 and diagnostics.ignored == 0, "reset clears samples, anchors and counters")
	deliver(predictor, actor, 25, Vector3(50, 0, 0), 1)
	check(diagnostics.observations == 1 and diagnostics.samples.back().first_snapshot_drift_m == 0.0, "new connection can restart epoch space without old-anchor drift")
	predictor.reset(true)
	check(diagnostics.samples.is_empty() and diagnostics.observations == 0 and predictor.sequence == 0, "connection reset clears diagnostics and preserves existing sequence reset")
	check(actor.ammo == 15 and actor.health == 100 and actor.reload_remaining == 0, "diagnostic controls grant no combat state")
	lifecycle = {"available": true, "checks": checks - before_checks, "ordered_delivery": delivery_trace,
		"bounded_cache": bounded_receipt, "legacy_error_samples_m": legacy}
	world.queue_free()
	await process_frame
	await create_timer(0.5).timeout

func run() -> void:
	await shared_lifecycle_timeline()
	await lifecycle_controls()
	await super.run()
