extends SceneTree
## Read-only reproduction probe for CLAUDE_AUDIT_0.3. Runs against unmodified source.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const Utility = preload("res://scripts/gameplay/utility.gd")
const Match = preload("res://scripts/gameplay/match.gd")
const WeaponModel = preload("res://scripts/gameplay/weapon_model.gd")
const CosmeticMaterial = preload("res://scripts/ui/cosmetic_material.gd")
const Gate = preload("res://scripts/network/input_gate.gd")
const DT := 1.0 / 60.0

func _initialize() -> void:
	_run.call_deferred()

func out(key: String, value) -> void:
	print("AUDIT ", key, " = ", value)

func _new_actor(world: Node3D, id: int, team: int, at: Vector3) -> SBActor:
	var a := Actor.new()
	a.configure(id, team, "probe-%d" % id, false)
	world.add_child(a)
	a.reset_for_round(at)
	return a

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var arena := Arena.new()
	world.add_child(arena)
	await physics_frame

	# F-FIRE: effective fire interval at the 60 Hz authoritative tick.
	var x := -18.0
	for weapon in ["smg", "rifle", "sidearm", "marksman"]:
		var a := _new_actor(world, 40, 0, Vector3(x, 0.05, -20))
		x += 3.0
		if weapon != "sidearm":
			a.credits = 99999
			a.buy_weapon(weapon)
		a.ammo = 100000
		var ticks: Array[int] = []
		a.shot_fired.connect(func(_id, _o, _d): ticks.append(-1))
		var shot_ticks: Array[int] = []
		var automatic: bool = Weapons.get_weapon(weapon).automatic
		for t in range(1200):
			var before := ticks.size()
			a.input_state = {"look": Vector2(0, 1.4), "fire": true if automatic else (t % 2 == 0), "weapon": weapon}
			a.tick_authority(DT)
			if ticks.size() > before:
				shot_ticks.append(t)
		var span := float(shot_ticks[-1] - shot_ticks[0]) * DT
		var effective := span / float(shot_ticks.size() - 1)
		var designed: float = Weapons.get_weapon(weapon).interval
		out("fire_interval.%s" % weapon, "designed=%.4fs effective=%.4fs rate_designed=%.2f/s rate_effective=%.2f/s delta=%.1f%%" % [designed, effective, 1.0 / designed, 1.0 / effective, (1.0 / effective - 1.0 / designed) / (1.0 / designed) * 100.0])
		a.queue_free()
	await physics_frame

	# F-SWITCH: marksman quick-switch bypasses its 0.82 s fire interval.
	for use_switch in [false, true]:
		var m := _new_actor(world, 41, 0, Vector3(0, 0.05, -20))
		m.credits = 99999
		m.buy_weapon("marksman")
		m.ammo = 100
		var fired: Array[int] = []
		var tick := [0]
		m.shot_fired.connect(func(_id, _o, _d): fired.append(tick[0]))
		for t in range(200):
			tick[0] = t
			var state := {"look": Vector2(0, 1.4), "weapon": "marksman", "fire": t % 2 == 0}
			if use_switch and fired.size() == 1 and t == fired[0] + 1:
				state = {"look": Vector2(0, 1.4), "weapon": "sidearm", "fire": false}
			m.input_state = state
			m.tick_authority(DT)
			if fired.size() >= 2:
				break
		out("marksman_second_shot.%s" % ("quickswitch" if use_switch else "normal"), "%.3fs after first (designed interval %.2fs)" % [float(fired[1] - fired[0]) * DT, Weapons.get_weapon("marksman").interval])
		m.queue_free()
	await physics_frame

	# F-SPREAD: spread is a pure function of (actor_id, shots fired).
	var sequences: Array = []
	for trial in range(3):
		var id := 7 if trial < 2 else 8
		var s := _new_actor(world, id, 0, Vector3(-10 + trial * 4, 0.05, 18))
		s.credits = 99999
		s.buy_weapon("rifle")
		s.ammo = 1000
		var dirs: Array = []
		s.shot_fired.connect(func(_id, _o, d: Vector3): dirs.append(d))
		# Trial 1 waits between rounds (different elapsed time / round) before shooting.
		s.reset_for_round(Vector3(-10 + trial * 4, 0.05, 18))
		var settle := 30 + (97 if trial == 1 else 0)
		for t in range(settle):
			s.input_state = {"look": Vector2(0.3, 0.2), "weapon": "rifle"}
			s.tick_authority(DT)
			await physics_frame
		if trial == 1:
			s.reset_for_round(Vector3(-6, 0.05, 18))
			for t in range(30):
				s.input_state = {"look": Vector2(0.3, 0.2), "weapon": "rifle"}
				s.tick_authority(DT)
				await physics_frame
		s.ammo = 1000
		for t in range(60):
			s.input_state = {"look": Vector2(0.3, 0.2), "fire": true, "weapon": "rifle"}
			s.tick_authority(DT)
		out("spread_shots_sampled.trial%d" % trial, dirs.size())
		sequences.append(dirs)
		out("spread_seed.actor%d" % id, s._rng.seed)
		s.queue_free()
	var same: bool = sequences[0].size() == sequences[1].size()
	for i in range(mini(sequences[0].size(), sequences[1].size())):
		same = same and sequences[0][i].is_equal_approx(sequences[1][i])
	var differs := false
	for i in range(mini(sequences[0].size(), sequences[2].size())):
		differs = differs or not sequences[0][i].is_equal_approx(sequences[2][i])
	out("spread_identical_for_same_actor_id_after_round_reset", same)
	out("spread_differs_for_other_actor_id", differs)
	await physics_frame

	# F-RECOIL: horizontal spray pattern continues across bursts (shot index not reset).
	var r := _new_actor(world, 42, 0, Vector3(10, 0.05, 18))
	r.credits = 99999
	r.buy_weapon("rifle")
	r.ammo = 1000
	var patterns: Array = [[], []]
	for t in range(30):
		r.input_state = {"look": Vector2(0, 0), "weapon": "rifle"}
		r.tick_authority(DT)
	for burst in range(2):
		var shots := 0
		while shots < 8:
			var before := r.ammo
			r.input_state = {"look": Vector2(0, 0), "fire": true, "weapon": "rifle"}
			r.tick_authority(DT)
			if r.ammo < before:
				shots += 1
				patterns[burst].append(snappedf(r.recoil.x, 0.0001))
		for t in range(240):
			r.input_state = {"look": Vector2(0, 0)}
			r.tick_authority(DT)
		out("recoil_after_recovery.burst%d" % burst, r.recoil)
	out("recoil_x_pattern.burst0", patterns[0])
	out("recoil_x_pattern.burst1", patterns[1])
	r.queue_free()
	await physics_frame

	# F-HEAD: headshot region vs. the visible head/helmet silhouette (front view).
	for crouch in [false, true]:
		var target := _new_actor(world, 43, 1, Vector3(0, 0.05, 6))
		var shooter := _new_actor(world, 44, 0, Vector3(0, 0.05, 0))
		for t in range(20):
			target.input_state = {"crouch": crouch, "look": Vector2(PI, 0)}
			target.tick_authority(DT)
			await physics_frame
		var head_hits := 0
		var visual_head := 0
		var head_outside_visual := 0
		var base_y := target.global_position.y
		var squash := 0.72 if crouch else 1.0
		var space := world.get_world_3d().direct_space_state
		for iy in range(0, 70):
			var y := 0.9 + iy * 0.01
			for ix in range(-40, 41):
				var lateral := ix * 0.01
				var from := Vector3(lateral, base_y + y, 0.5)
				var to := Vector3(lateral, base_y + y, 12)
				var q := PhysicsRayQueryParameters3D.create(from, to, 2)
				var hit := space.intersect_ray(q)
				var counted: bool = not hit.is_empty() and hit.collider == target and hit.position.y > target.global_position.y + target.head_height - 0.25
				# Visible head ellipsoid + helmet ellipsoid projected on the XY plane.
				var hy := (y - 1.56 * squash) / (0.195 * squash)
				var hx := lateral / 0.16
				var ky := (y - 1.68 * squash) / (0.1175 * squash)
				var kx := lateral / 0.175
				var visible := hx * hx + hy * hy <= 1.0 or kx * kx + ky * ky <= 1.0
				if counted: head_hits += 1
				if visible: visual_head += 1
				if counted and not visible: head_outside_visual += 1
		out("headshot_area.%s" % ("crouched" if crouch else "standing"), "counted_cells=%d visible_head_cells=%d counted_outside_visible=%d (ratio counted/visible=%.2f)" % [head_hits, visual_head, head_outside_visual, float(head_hits) / maxf(1, visual_head)])
		target.queue_free()
		shooter.queue_free()
		await physics_frame
	await physics_frame

	# F-SMOKE: a smoke resting on a container roof is snapped to absolute y = 1.6.
	var smoke := Utility.new()
	smoke.kind = "smoke"
	world.add_child(smoke)
	smoke.global_position = Vector3(-7, 3.4, -11)
	smoke.velocity = Vector3.ZERO
	for t in range(130):
		smoke._physics_process(DT)
		if smoke._detonated:
			break
	var container := AABB(Vector3(-8.5, 0, -15.5), Vector3(3, 3.1, 9))
	out("smoke_on_container.cloud_center", smoke.global_position)
	out("smoke_on_container.center_inside_container_volume", container.has_point(smoke.global_position))
	smoke.queue_free()

	# F-INV: purchased weapons survive death and the halftime funds reset.
	var game := Match.new()
	game.configure({"mode": "offline", "difficulty": "easy"})
	world.add_child(game)
	await physics_frame
	var me: SBActor = game.local_actor()
	me.credits = 5000
	game.phase = "buy"
	game._buy(me.actor_id, "rifle")
	out("inventory.after_purchase", me.inventory)
	me.apply_damage(500, 6)
	game.round_number = 2
	game._begin_round()
	out("inventory.after_death_next_round", me.inventory)
	game.round_number = 6
	game._begin_round()
	out("inventory.after_halftime", "%s credits=%d team=%d weapon=%s" % [me.inventory, me.credits, me.team, me.weapon_id])

	for bot: SBActor in game.actors.values():
		bot.credits = 5000
		bot.inventory.assign(["sidearm"])
	var round_started := Time.get_ticks_usec()
	game.round_number = 2
	game._begin_round()
	out("round_start_cost", "%.1f ms for _begin_round() with 9 bot purchases" % (float(Time.get_ticks_usec() - round_started) / 1000.0))

	# F-SNAPSHOT: payload size of the 20 Hz snapshot (10 actors).
	var raw := var_to_bytes(game._snapshot())
	var packed := raw.compress(FileAccess.COMPRESSION_DEFLATE)
	out("snapshot_bytes", "raw=%d deflate=%d per_second_per_client=%d" % [raw.size(), packed.size(), packed.size() * 20])
	out("snapshot_exposes_enemy_positions_and_carrier", game._snapshot().has("carrier") and game._snapshot().actors[0].has("position"))
	game.queue_free()
	await physics_frame

	# F-NAV: GDScript bot navigation cost (10 bots re-plan every 0.12 s).
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var pairs: Array = []
	for i in range(400):
		pairs.append([Vector3(rng.randf_range(-21, 21), 0, rng.randf_range(-21, 21)), Vector3(rng.randf_range(-21, 21), 0, rng.randf_range(-21, 21))])
	var started := Time.get_ticks_usec()
	for pair in pairs:
		arena.bot_navigation(pair[0], pair[1])
	var per_call := float(Time.get_ticks_usec() - started) / pairs.size()
	out("bot_navigation", "%.1f us/call, waypoints=%d obstacles=%d, 10 bots @ 8.33 Hz = %.1f ms per second of play" % [per_call, arena.waypoints.size(), arena._obstacles.size(), per_call * 10 * (1.0 / 0.12) / 1000.0])

	# F-MODEL: per-equip weapon model construction cost and resource sharing.
	var holder := Node3D.new()
	world.add_child(holder)
	started = Time.get_ticks_usec()
	var first_mesh: Mesh
	var second_mesh: Mesh
	for i in range(20):
		var node := Node3D.new()
		holder.add_child(node)
		var built: Dictionary = WeaponModel.build(node, "rifle", true)
		for child in node.get_children():
			if child is MeshInstance3D:
				if i == 0 and first_mesh == null: first_mesh = child.mesh
				if i == 1 and second_mesh == null: second_mesh = child.mesh
	out("weapon_model_build", "%.2f ms per first-person rifle build; meshes shared between builds=%s" % [float(Time.get_ticks_usec() - started) / 20000.0, first_mesh == second_mesh])
	var actor_started := Time.get_ticks_usec()
	var spawned := _new_actor(world, 45, 0, Vector3(5, 0.05, 5))
	out("actor_construction", "%.2f ms per actor (body batching + first-person gun)" % (float(Time.get_ticks_usec() - actor_started) / 1000.0))
	spawned.queue_free()

	# F-SHADER: cosmetic finish allocates a new Shader resource per call.
	var a1 := CosmeticMaterial.finish({})
	var a2 := CosmeticMaterial.finish({})
	out("cosmetic_shader_shared_between_calls", a1.shader == a2.shader)

	# F-ARENA: static batches, shadow casters and thin details.
	var batches := 0
	var instances := 0
	var thin := 0
	var flat_ground_details := 0
	var shadowed_batches := 0
	for child in arena.get_children():
		if child is MultiMeshInstance3D:
			batches += 1
			if child.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF: shadowed_batches += 1
			var mm: MultiMesh = child.multimesh
			instances += mm.instance_count
			for i in range(mm.instance_count):
				var tr: Transform3D = mm.get_instance_transform(i)
				var size := Vector3(tr.basis.x.length(), tr.basis.y.length(), tr.basis.z.length())
				if minf(size.x, minf(size.y, size.z)) < 0.05: thin += 1
				if size.y < 0.03 and tr.origin.y < 0.05: flat_ground_details += 1
	var labels := arena.find_children("*", "Label3D", true, false).size()
	var raw_arena := Arena.new()
	raw_arena._build()
	for visual in raw_arena._box_visuals:
		var size: Vector3 = (visual.mesh as BoxMesh).size
		var origin: Vector3 = visual.get_parent().position
		if minf(size.x, minf(size.y, size.z)) < 0.05: thin += 1
		if size.y < 0.03 and origin.y < 0.05: flat_ground_details += 1
	out("arena_unbatched_boxes", raw_arena._box_visuals.size())
	raw_arena.free()
	out("arena_batches", "multimesh_batches=%d shadow_casting_batches=%d instances=%d instances_thinner_than_5cm=%d ground_decal_boxes=%d label3d=%d" % [batches, shadowed_batches, instances, thin, flat_ground_details, labels])

	# F-GATE: two legitimate 30 Hz inputs bunched by jitter (<12 ms apart).
	var gate := Gate.new()
	var first := gate.validate(5, {"move": Vector2.ZERO, "look": Vector2.ZERO}, 1000)
	var second := gate.validate(5, {"move": Vector2(0, 1), "look": Vector2.ZERO, "fire": true}, 1008)
	out("input_gate_drops_newer_bunched_packet", not first.is_empty() and second.is_empty())

	await physics_frame
	quit(0)
