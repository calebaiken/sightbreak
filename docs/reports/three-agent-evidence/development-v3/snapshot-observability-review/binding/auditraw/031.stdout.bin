class_name SBMovementPrediction
extends RefCounted
## Bounded movement replay. Server positions/collision and all combat stay final.
const MAX_HISTORY := 120
const AckSnapshotDiagnostics := preload("res://scripts/network/ack_snapshot_diagnostics.gd")
var snapshot_diagnostics := AckSnapshotDiagnostics.new()
var sequence := 0
var _grounded_override := -1
var epoch := -1
var pending: Array[Dictionary] = []
var visual_offset := Vector3.ZERO
var corrections := 0
var hard_corrections := 0
var error_samples: Array[float] = []
var large_corrections: Array[Dictionary] = []

func reset(connection: bool = false) -> void:
	snapshot_diagnostics.clear()
	pending.clear()
	visual_offset = Vector3.ZERO
	epoch = -1
	_grounded_override = -1
	if connection:
		sequence = 0

func predict(actor: CharacterBody3D, controls: Dictionary, current_epoch: int, enabled: bool) -> void:
	if epoch != current_epoch:
		snapshot_diagnostics.begin_epoch(current_epoch)
		pending.clear()
		visual_offset = Vector3.ZERO
		epoch = current_epoch
		sequence = 0
	if pending.size() >= MAX_HISTORY:
		return # Bound stalled connections; no unbounded replay or sequence jump.
	sequence += 1
	var command := controls.duplicate()
	command.sequence = sequence
	command = SBInputStream.sanitize(command)
	if command.is_empty():
		return
	if enabled:
		SBMovementStep.advance(actor, command, SBMovementStep.STEP, _grounded_override)
		_grounded_override = -1
	pending.append({"command": command, "position": actor.global_position})

func packet() -> Dictionary:
	var commands: Array = []
	for index in range(maxi(0, pending.size() - SBInputStream.MAX_BATCH), pending.size()):
		commands.append(pending[index].command)
	return {"epoch": epoch, "commands": commands}

func reconcile(actor: CharacterBody3D, state: Dictionary, current_epoch: int, previous_position: Vector3, enabled: bool) -> void:
	snapshot_diagnostics.observe(state, current_epoch, enabled)
	var ack: int = state.get("move_ack", 0)
	actor._jump_previous = bool(state.get("jump_held", false))
	_grounded_override = 1 if bool(state.get("grounded", false)) else 0
	if epoch != current_epoch:
		pending.clear()
		visual_offset = Vector3.ZERO
		epoch = current_epoch
		sequence = 0
		return
	for record: Dictionary in pending:
		if int(record.command.sequence) == ack:
			error_samples.append((record.position as Vector3).distance_to(state.position))
			if error_samples.size() > 3600:
				error_samples.pop_front()
	while not pending.is_empty() and int(pending.front().command.sequence) <= ack:
		pending.pop_front()
	if not enabled:
		return
	actor._jump_previous = bool(state.get("jump_held", false))
	# Godot collision contacts are not serializable. The next move_and_slide
	# rebuilds them; moving actors and floor transitions can require correction.
	var grounded_override := 1 if bool(state.get("grounded", false)) else 0
	for record: Dictionary in pending:
		SBMovementStep.advance(actor, record.command, SBMovementStep.STEP, grounded_override)
		grounded_override = -1
		record.position = actor.global_position
	_grounded_override = grounded_override
	var error := previous_position - actor.global_position
	if error.length() > 0.01:
		corrections += 1
	if error.length() > 0.3 and large_corrections.size() < 120:
		large_corrections.append({"ack": ack, "error": error.length(), "previous": previous_position, "authority": state.position, "replayed": actor.global_position, "pending": pending.size()})
	if error.length() > 2.0:
		visual_offset = Vector3.ZERO
		hard_corrections += 1
	else:
		visual_offset = (visual_offset + error).limit_length(0.35)

func present(actor: CharacterBody3D, delta: float) -> void:
	visual_offset *= exp(-delta * 20.0)
	var base: Vector3 = actor.global_position + Vector3.UP * actor.head_height
	var desired := base + visual_offset
	var hit := actor.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(base, desired, 1)) if visual_offset.length_squared() > 0.000001 else {}
	if not hit.is_empty():
		desired = hit.position + hit.normal * 0.05
	actor.camera.global_position = desired
