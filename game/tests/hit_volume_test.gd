extends SceneTree
## Codex PR #1 blocker 2: authoritative hit volumes against the 0.3.0 hitbox. The
## movement capsule on collision layer 2 is exactly what 0.3.0 shot at, so every ray
## here is scored both ways in one process: a physics ray against that capsule
## (0.3.0) and SBActor.trace_shot (this build). The body may never hit where 0.3.0
## missed. The only extra area allowed is the drawn crouched helmet where it sticks out
## of the 0.3.0 crouched capsule's rounded top (straight section to 0.94 m, cap to
## 1.25 m); that design conflict is documented in docs/audits/CODEX_REVIEW_RESPONSE.md.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Arena = preload("res://scripts/gameplay/arena.gd")
const DT := 1.0 / 60.0
var failures: Array[String] = []
var checks := 0
var world: Node3D

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if not condition:
		failures.append(message)
		push_error(message)

func _actor(id: int, team: int, at: Vector3) -> SBActor:
	var actor := Actor.new()
	actor.configure(id, team, "volume-%d" % id, false)
	world.add_child(actor)
	actor.reset_for_round(at)
	return actor

func _pose(actor: SBActor, crouch: bool, yaw: float) -> void:
	# Spawn transforms reach the physics server at the next flush; settle after it.
	await physics_frame
	for t in range(30):
		actor.input_state = {"crouch": crouch, "look": Vector2(yaw, 0)}
		actor.tick_authority(DT)
		await physics_frame

func _capsule_hit(shooter: SBActor, target: SBActor, from: Vector3, to: Vector3) -> bool:
	var query := PhysicsRayQueryParameters3D.create(from, to, 2, [shooter.get_rid()])
	var hit := world.get_world_3d().direct_space_state.intersect_ray(query)
	return not hit.is_empty() and hit.collider == target

func _trace(shooter: SBActor, from: Vector3, to: Vector3) -> Dictionary:
	return shooter.trace_shot(from, (to - from).normalized(), from.distance_to(to))

func _run() -> void:
	world = Node3D.new()
	root.add_child(world)
	world.add_child(Arena.new())
	await physics_frame
	await _parity()
	await _specific_rays()
	await _pass_through_and_ordering()
	_tangent_rays()
	_long_range_rays()
	world.queue_free()
	await process_frame
	print("HIT_VOLUME_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

## 2 cm grids, horizontal and plunging, standing and crouched, front and side. Rays
## sit a quarter cell off the grid lines so none lands exactly on the 0.31 m radius,
## where float rounding alone decides between the two shapes.
func _parity() -> void:
	for crouch in [false, true]:
		for yaw in [PI, PI * 0.5]:
			var target := _actor(43, 1, Vector3(0, 0.05, 6))
			var shooter := _actor(44, 0, Vector3(0, 0.05, 0))
			await _pose(target, crouch, yaw)
			var feet := target.global_position.y
			var squash := 0.72 if crouch else 1.0
			var capsule_top := 1.25 if crouch else 1.8
			var torso_top := Actor.BODY_TOP * squash
			var label := "%s %s" % ["crouched" if crouch else "standing", "front" if yaw == PI else "side"]
			var extra_body := 0
			var extra_head_elsewhere := 0
			var helmet_outside_capsule := 0
			var missing_torso := 0
			var rays: Array = []
			for iy in range(0, 93):
				for ix in range(-22, 22):
					var at := Vector3((ix + 0.25) * 0.02, feet + (iy + 0.25) * 0.02, 0.5)
					rays.append([at, at + Vector3(0, 0, 11.5), (iy + 0.25) * 0.02])
			var eye := Vector3(0, feet + 2.5, 2.0)
			for iy in range(0, 30):
				for ix in range(-22, 22):
					var aim := Vector3((ix + 0.25) * 0.02, feet + (iy + 0.25) * 0.02, 6.0)
					rays.append([eye, eye + (aim - eye).normalized() * 12.0, (iy + 0.25) * 0.02])
			for ray: Array in rays:
				var old_hit := _capsule_hit(shooter, target, ray[0], ray[1])
				var shot := _trace(shooter, ray[0], ray[1])
				var new_hit: bool = shot.actor == target
				var height: float = float(shot.position.y) - feet if new_hit else 0.0
				if new_hit and not old_hit:
					if not shot.headshot:
						extra_body += 1
					elif crouch and height > capsule_top - 0.31:
						helmet_outside_capsule += 1
					else:
						extra_head_elsewhere += 1
				# Aimed below the drawn torso top, the old capsule and the new volumes agree.
				if old_hit and not new_hit and float(ray[2]) < torso_top - 0.02:
					missing_torso += 1
			check(extra_body == 0, "%s: no body hit where 0.3.0 missed (%d rays)" % [label, extra_body])
			check(extra_head_elsewhere == 0, "%s: extra headshot area is only the drawn crouched helmet above the capsule's straight section (%d other rays)" % [label, extra_head_elsewhere])
			check(helmet_outside_capsule == 0 if not crouch else helmet_outside_capsule < 60, "%s: drawn crouched helmet outside the 0.3.0 capsule stays small (%d rays)" % [label, helmet_outside_capsule])
			check(missing_torso == 0, "%s: every 0.3.0 hit below the torso top still hits (%d misses)" % [label, missing_torso])
			target.queue_free()
			shooter.queue_free()
			await physics_frame

func _specific_rays() -> void:
	var target := _actor(45, 1, Vector3(0, 0.05, 6))
	var shooter := _actor(46, 0, Vector3(0, 0.05, 0))
	await _pose(target, false, PI)
	var feet := target.global_position.y
	var cases := [
		# [x, height above feet, expected: "B" body, "H" head, "." miss, description]
		[0.0, 0.03, "B", "foot level, centre line"],
		[0.25, 0.03, ".", "foot level outside the rounded capsule bottom (0.3.0 missed; the reviewed PR hit)"],
		[0.29, 0.10, ".", "shin-level corner outside the capsule bottom"],
		[0.20, 0.20, "B", "lower leg inside the capsule bottom"],
		[0.0, 0.9, "B", "torso centre"],
		[0.30, 0.9, "B", "torso, 1 cm inside the 0.31 m edge"],
		[0.32, 0.9, ".", "torso, 1 cm outside the 0.31 m edge"],
		[0.0, 1.56, "H", "drawn head centre"],
		[0.25, 1.56, ".", "air beside the drawn head (0.3.0 headshot area, removed by H-2)"],
	]
	for case: Array in cases:
		var from := Vector3(case[0], feet + case[1], 0.5)
		var shot := _trace(shooter, from, from + Vector3(0, 0, 11.5))
		var got := "." if shot.actor != target else ("H" if shot.headshot else "B")
		check(got == case[2], "standing %s: expected %s, got %s" % [case[3], case[2], got])
	await _pose(target, true, PI)
	feet = target.global_position.y
	var crouched := [
		[0.0, 0.03, "B", "crouched foot level"],
		[0.25, 0.03, ".", "crouched foot corner outside the capsule bottom"],
		[0.0, 0.6, "B", "crouched torso"],
		[0.0, 1.56 * 0.72, "H", "crouched drawn head centre"],
		[0.0, 1.30, ".", "above the drawn crouched helmet"],
	]
	for case: Array in crouched:
		var from := Vector3(case[0], feet + case[1], 0.5)
		var shot := _trace(shooter, from, from + Vector3(0, 0, 11.5))
		var got := "." if shot.actor != target else ("H" if shot.headshot else "B")
		check(got == case[2], "%s: expected %s, got %s" % [case[3], case[2], got])
	target.queue_free()
	shooter.queue_free()
	await physics_frame

## Rays through empty volume space reach whatever is behind; geometry still blocks.
func _pass_through_and_ordering() -> void:
	# The x = 2 m lane has no arena geometry between z = 0.5 and 14 at any height used.
	var front := _actor(47, 1, Vector3(2, 0.05, 6))
	var behind := _actor(48, 1, Vector3(2.27, 0.05, 8))
	var shooter := _actor(49, 0, Vector3(2, 0.05, 0))
	await _pose(front, false, PI)
	await _pose(behind, false, PI)
	var feet := front.global_position.y
	# At 12 cm the rounded capsule bottom is 0.245 m wide: 0.27 m out clears the front
	# operator and runs through the centre line of the one behind.
	var corner := Vector3(behind.global_position.x, feet + 0.12, 0.5)
	var shot := _trace(shooter, corner, corner + Vector3(0, 0, 11.5))
	check(shot.actor == behind and not shot.headshot, "a ray past the front operator's rounded feet hits the operator behind (got %s at %s)" % [shot.actor.display_name if shot.actor else "nothing", shot.position])
	var centre := Vector3(2.0, feet + 0.9, 0.5)
	shot = _trace(shooter, centre, centre + Vector3(0, 0, 11.5))
	check(shot.actor == front and absf(float(shot.distance) - (6.0 - 0.31 - 0.5)) < 0.01, "the nearer operator takes the hit at its surface (%.3f m)" % float(shot.distance))
	var wall := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2, 3, 0.2)
	shape.shape = box
	wall.add_child(shape)
	world.add_child(wall)
	wall.global_position = Vector3(2, 1.5, 4.0)
	await physics_frame
	await physics_frame
	shot = _trace(shooter, centre, centre + Vector3(0, 0, 11.5))
	check(shot.actor == null and shot.hit and absf(float(shot.distance) - 3.4) < 0.01, "a wall in front of the operator stops the shot (%.3f m)" % float(shot.distance))
	wall.queue_free()
	front.queue_free()
	behind.queue_free()
	shooter.queue_free()
	await physics_frame

func _tangent_rays() -> void:
	# Rays that only touch the 0.31 x 1.8 m capsule miss it, as against the physics
	# capsule, whatever the float32 rounding of the discriminant.
	var misses := [
		[Vector3(0.31, 2.0, 0.0), Vector3.DOWN, "vertical ray on the radius"],
		[Vector3(-1.0, -0.9, 0.0), Vector3.RIGHT, "ray under the rounded bottom"],
		[Vector3(-1.0, 0.0, 0.31), Vector3.RIGHT, "ray along the side"],
	]
	for case in misses:
		check(Actor._capsule_entry(case[0], case[1], 0.31, 1.8, 0.48) < 0.0, "tangent %s misses" % case[2])
	var hits := [
		[Vector3(0.3099, 2.0, 0.0), Vector3.DOWN, "vertical ray 0.1 mm inside"],
		[Vector3(-1.0, -0.899, 0.0), Vector3.RIGHT, "ray 1 mm into the rounded bottom"],
		[Vector3(0.3097, 0.9976, -0.0698), Vector3(0, -0.9976, 0.0698).normalized(), "steep 86-degree ray 0.3 mm inside the wall"],
	]
	for case in hits:
		check(Actor._capsule_entry(case[0], case[1], 0.31, 1.8, 0.48) >= 0.0, "%s hits" % case[2])


## Exact distance (64-bit) between the ray's line and the capsule's axis segment.
static func _axis_distance(o: Vector3, d: Vector3, half: float) -> float:
	var dd := d.x * d.x + d.y * d.y + d.z * d.z
	var k := -(o.x * d.x + o.y * d.y + o.z * d.z) / dd
	var wx := -o.x - k * d.x
	var wy := -o.y - k * d.y
	var wz := -o.z - k * d.z
	var m := d.y / dd
	var ex := -m * d.x
	var ey := 1.0 - m * d.y
	var ez := -m * d.z
	var ee := ex * ex + ey * ey + ez * ez
	var u := 0.0 if ee < 0.000000000000000001 else clampf(-(wx * ex + wy * ey + wz * ez) / ee, -half, half)
	var fx := wx + u * ex
	var fy := wy + u * ey
	var fz := wz + u * ez
	return sqrt(fx * fx + fy * fy + fz * fz)

func _long_range_rays() -> void:
	# Marksman and rifle distances: rays aimed within 1.5 cm of the lower body's
	# surface must agree with exact geometry wherever it is more than 0.05 mm away.
	var rng := RandomNumberGenerator.new()
	rng.seed = 3093
	var radius := 0.31
	var height := 1.8
	var top := 0.48
	var half := height * 0.5 - radius
	var decided := 0
	var extra := 0
	var lost := 0
	for i in range(4000):
		var distance := rng.randf_range(40.0, 140.0)
		var bearing := rng.randf_range(-PI, PI)
		var around := rng.randf_range(-PI, PI)
		var aim_radius := radius + rng.randf_range(-0.015, 0.015)
		var aim := Vector3(cos(around) * aim_radius, rng.randf_range(-0.9, top - 0.06), sin(around) * aim_radius)
		var origin := Vector3(cos(bearing) * distance, rng.randf_range(0.4, 1.0), sin(bearing) * distance)
		var direction := (aim - origin).normalized()
		var exact := _axis_distance(origin, direction, half)
		if absf(exact - radius) < 0.00005:
			continue
		decided += 1
		var hit: bool = Actor._capsule_entry(origin, direction, radius, height, top) >= 0.0
		if hit and exact > radius:
			extra += 1
		elif not hit and exact < radius:
			lost += 1
	check(decided > 3000 and extra == 0 and lost == 0, "40-140 m rays match exact capsule geometry (%d extra, %d lost of %d)" % [extra, lost, decided])
