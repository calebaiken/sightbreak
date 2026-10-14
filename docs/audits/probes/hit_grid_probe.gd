extends SceneTree
## Codex PR #1 blocker 2: score the same deterministic rays against any SIGHTBREAK
## build. Builds without SBActor.trace_shot (0.3.0) use their own authoritative rule:
## a physics ray against the movement capsule, headshot above head_height - 0.25.
## Usage: godot --headless --path <project>/game --script <this file> -- --out=<file.json>
## Cells: H headshot, B body hit, . no hit on the target. Rays pass through 1 cm cell
## centres, so none lies exactly on a volume boundary where rounding decides.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const DT := 1.0 / 60.0
var world: Node3D

func _initialize() -> void:
	_run.call_deferred()

func _actor(id: int, team: int, at: Vector3) -> SBActor:
	var actor := Actor.new()
	actor.configure(id, team, "grid-%d" % id, false)
	world.add_child(actor)
	actor.reset_for_round(at)
	return actor

func _classify(shooter: SBActor, target: SBActor, from: Vector3, to: Vector3) -> String:
	var direction := (to - from).normalized()
	if shooter.has_method("trace_shot"):
		var shot: Dictionary = shooter.call("trace_shot", from, direction, from.distance_to(to))
		if shot.actor != target:
			return "."
		return "H" if shot.headshot else "B"
	var query := PhysicsRayQueryParameters3D.create(from, to, 3, [shooter.get_rid()])
	var hit := world.get_world_3d().direct_space_state.intersect_ray(query)
	if hit.is_empty() or hit.collider != target:
		return "."
	return "H" if float(hit.position.y) > target.global_position.y + target.head_height - 0.25 else "B"

func _run() -> void:
	var output := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--out="):
			output = argument.trim_prefix("--out=")
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	await physics_frame
	var probe := Actor.new()
	var report := {"build": "trace_shot" if probe.has_method("trace_shot") else "0.3 capsule", "views": {}}
	probe.free()
	for crouch in [false, true]:
		for facing in ["front", "side"]:
			var target := _actor(43, 1, Vector3(0, 0.05, 6))
			var shooter := _actor(44, 0, Vector3(0, 0.05, 0))
			var yaw := PI if facing == "front" else PI * 0.5
			for t in range(30):
				target.input_state = {"crouch": crouch, "look": Vector2(yaw, 0)}
				target.tick_authority(DT)
				await physics_frame
			var feet := target.global_position.y
			var key := "%s_%s" % ["crouched" if crouch else "standing", facing]
			report["target_%s" % key] = [snappedf(target.global_position.x, 0.000001), snappedf(target.global_position.y, 0.000001), snappedf(target.global_position.z, 0.000001)]
			# Horizontal rays on a 1 cm grid across the whole operator.
			var rows: Array[String] = []
			for iy in range(0, 185):
				var row := ""
				for ix in range(-45, 45):
					var at := Vector3((ix + 0.5) * 0.01, feet + (iy + 0.5) * 0.01, 0.5)
					row += _classify(shooter, target, at, at + Vector3(0, 0, 11.5))
				rows.append(row)
			report.views[key] = {"origin": "horizontal z=0.5 -> 12.0", "x_cm": [-44.5, 44.5], "y_cm": [0.5, 184.5], "rows": rows}
			# Plunging rays from 2.5 m up and 4 m out, aimed at the lower body and feet.
			var plunging: Array[String] = []
			var eye := Vector3(0, feet + 2.5, 2.0)
			for iy in range(0, 60):
				var row := ""
				for ix in range(-45, 45):
					var aim := Vector3((ix + 0.5) * 0.01, feet + (iy + 0.5) * 0.01, 6.0)
					row += _classify(shooter, target, eye, eye + (aim - eye).normalized() * 12.0)
				plunging.append(row)
			report.views[key + "_plunging"] = {"origin": "eye (0, 2.5, 2.0) aimed at x,y on the plane z=6", "x_cm": [-44.5, 44.5], "y_cm": [0.5, 59.5], "rows": plunging}
			target.queue_free()
			shooter.queue_free()
			await physics_frame
			await physics_frame
	var counts := {}
	for view: String in report.views:
		var text := "".join(report.views[view].rows)
		counts[view] = {"H": text.count("H"), "B": text.count("B"), ".": text.count(".")}
	report["counts"] = counts
	print("HIT_GRID ", JSON.stringify(counts))
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		file.store_string(JSON.stringify(report))
	world.queue_free()
	await process_frame
	quit()
