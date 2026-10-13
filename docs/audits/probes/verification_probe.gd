extends SceneTree
## Post-fix counterpart to audit_probe.gd's F-HEAD section. The baseline probe hard-codes
## the 0.3 rule (any capsule hit within 0.25 m of head height); this one asks the
## authoritative path (`SBActor.trace_shot`) with the same grid and visible silhouette.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const DT := 1.0 / 60.0

func _initialize() -> void:
	_run.call_deferred()

func _new_actor(world: Node3D, id: int, team: int, at: Vector3) -> SBActor:
	var a := Actor.new()
	a.configure(id, team, "probe-%d" % id, false)
	world.add_child(a)
	a.reset_for_round(at)
	return a

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	await physics_frame
	for crouch in [false, true]:
		var target := _new_actor(world, 43, 1, Vector3(0, 0.05, 6))
		var shooter := _new_actor(world, 44, 0, Vector3(0, 0.05, 0))
		await physics_frame
		for t in range(20):
			target.input_state = {"crouch": crouch, "look": Vector2(PI, 0)}
			target.tick_authority(DT)
			await physics_frame
		var head_hits := 0
		var visual_head := 0
		var head_outside_visual := 0
		var body_hits := 0
		var base_y := target.global_position.y
		var squash := 0.72 if crouch else 1.0
		for iy in range(0, 70):
			var y := 0.9 + iy * 0.01
			for ix in range(-40, 41):
				var lateral := ix * 0.01
				var from := Vector3(lateral, base_y + y, 0.5)
				var hit := shooter.trace_shot(from, Vector3(0, 0, 1), 11.5)
				var counted: bool = hit.actor == target and hit.headshot
				if hit.actor == target and not hit.headshot: body_hits += 1
				var hy := (y - 1.56 * squash) / (0.195 * squash)
				var hx := lateral / 0.16
				var ky := (y - 1.68 * squash) / (0.1175 * squash)
				var kx := lateral / 0.175
				var visible := hx * hx + hy * hy <= 1.0 or kx * kx + ky * ky <= 1.0
				if counted: head_hits += 1
				if visible: visual_head += 1
				if counted and not visible: head_outside_visual += 1
		print("VERIFY headshot_area.%s = counted_cells=%d visible_head_cells=%d counted_outside_visible=%d body_cells=%d (ratio counted/visible=%.2f)" % ["crouched" if crouch else "standing", head_hits, visual_head, head_outside_visual, body_hits, float(head_hits) / maxf(1, visual_head)])
		target.queue_free()
		shooter.queue_free()
		await physics_frame
	world.queue_free()
	await process_frame
	quit()
