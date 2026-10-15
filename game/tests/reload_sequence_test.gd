extends SceneTree
## The reload as a sequence of two magazines, two hands' worth of contact, and the sounds that go
## with it, measured from the actor's real tick_visual loop. Headless. Presentation only: where it
## touches the authoritative reload (ammunition, completion) it checks that nothing changed.
##
## What this can show: that a second magazine node exists and the first never comes back; that each
## magazine slides along its own well; that a click fires on the tick the visible part arrives; that
## reduced motion keeps the staging; that brass lands on the floor; that animation does not change
## ammunition. What it cannot show: that any of it looks like a reload to a person, or that the hand
## looks like a hand. reload_visibility_test.gd (native) measures what is drawn; the frame sequences
## in docs/reports/media/art-v7 are for a human to look at.
const Actor = preload("res://scripts/gameplay/actor.gd")
const Weapons = preload("res://scripts/gameplay/weapons.gd")
const ViewmodelShading = preload("res://scripts/gameplay/viewmodel_shading.gd")
const TICK := 1.0 / 60.0
const DIGITS := ["L_thumb_3", "L_index_3", "L_middle_3", "L_ring_3", "L_pinky_3"]
var checks := 0
var failures: Array[String] = []
var actor: SBActor
var world: Node3D
var reload_seconds := 2.25
var well_axis := Vector3.DOWN
var rest_centre := Vector3.ZERO
var box: AABB

func _initialize() -> void:
	_run.call_deferred()

func check(condition: bool, message: String) -> void:
	checks += 1
	if OS.get_environment("RELOAD_TEST_VERBOSE") != "":
		print("%s %s" % ["ok  " if condition else "FAIL", message])
	if not condition:
		failures.append(message)
		push_error(message)

func _new_actor(id: int) -> SBActor:
	var made := Actor.new()
	made.configure(id, 0, "Reload sequence", true)
	world.add_child(made)
	made.reset_for_round(Vector3.ZERO)
	made.credits = 5000
	made.buy_weapon("rifle")
	made._equip_blend = 0.0
	made.ammo = 10
	made.reserve = 90
	return made

## The rifle's well axis (from the magazine's own geometry, pointing out of the well), as the
## weapon art test finds it, and the seated magazine's centre.
func _measure_well() -> void:
	var rest: Transform3D = actor._magazine_rest_transform
	box = actor._magazine.mesh.get_aabb()
	rest_centre = rest * box.get_center()
	var vertices: PackedVector3Array = actor._magazine.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var top_y := -INF
	var bottom_y := INF
	for vertex in vertices:
		var in_gun: Vector3 = rest * vertex
		top_y = maxf(top_y, in_gun.y)
		bottom_y = minf(bottom_y, in_gun.y)
	var top := Vector3.ZERO
	var top_count := 0
	var bottom := Vector3.ZERO
	var bottom_count := 0
	for vertex in vertices:
		var in_gun: Vector3 = rest * vertex
		if in_gun.y > top_y - 0.01:
			top += in_gun
			top_count += 1
		elif in_gun.y < bottom_y + 0.01:
			bottom += in_gun
			bottom_count += 1
	well_axis = (bottom / bottom_count - top / top_count).normalized()

func _offset(node: MeshInstance3D) -> Vector3:
	return node.transform * box.get_center() - rest_centre

func _travel(node: MeshInstance3D) -> float:
	return _offset(node).dot(well_axis)

func _off_axis(node: MeshInstance3D) -> float:
	var offset := _offset(node)
	return (offset - well_axis * offset.dot(well_axis)).length()

func _progress() -> float:
	return SBReloadPhases.progress(actor._reload_clock, reload_seconds)

## A point as a fraction of the 16:9 frame through the viewmodel projection.
func _screen(point: Vector3) -> Vector2:
	var q := actor.camera.global_transform.affine_inverse() * point
	var t := tan(deg_to_rad(ViewmodelShading.FOV) * 0.5)
	return Vector2(0.5 + 0.5 * (q.x / -q.z) / (t * 16.0 / 9.0), 0.5 - 0.5 * (q.y / -q.z) / t)

static func _area(polygon: PackedVector2Array) -> float:
	var sum := 0.0
	for i in polygon.size():
		var a := polygon[i]
		var b := polygon[(i + 1) % polygon.size()]
		sum += a.x * b.y - b.x * a.y
	return absf(sum) * 0.5

## Share of a magazine's projected hull that lies inside the frame.
func _onscreen_share(node: MeshInstance3D) -> float:
	var vertices: PackedVector3Array = node.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	var points := PackedVector2Array()
	for vertex in vertices:
		points.append(_screen(node.global_transform * vertex))
	var hull := Geometry2D.convex_hull(points)
	var area := _area(hull)
	if area <= 0.0:
		return 0.0
	var inside := 0.0
	for clipped in Geometry2D.intersect_polygons(hull, PackedVector2Array([Vector2.ZERO, Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])):
		inside += _area(clipped)
	return inside / area

func _joint(name: String) -> Vector3:
	var skeleton: Skeleton3D = actor._arms_skeleton
	return skeleton.global_transform * skeleton.get_bone_global_pose(skeleton.find_bone(name)).origin

func _in_frame(p: Vector2, margin := 0.01) -> bool:
	return p.x > margin and p.x < 1.0 - margin and p.y > margin and p.y < 1.0 - margin

## One whole reload from a clean start, ticked at 60 Hz the way the game does. `authority` is how
## reload_remaining reaches the actor: "local" (tick_authority every tick, the owner's machine),
## "snapshot" (assigned every third tick, a 20 Hz client) or "jitter" (a snapshot that also leads
## or lags by up to the slack). Records, per tick, everything the checks look at.
func _play(authority: String, reduced := false, hold_after := 0.4) -> Array[Dictionary]:
	var old_node: MeshInstance3D = actor._magazine
	var new_node: MeshInstance3D = actor._magazine_spare
	actor.reduced_motion = reduced
	actor.reload_remaining = 0.0
	actor._reload_clock = 0.0
	actor.tick_visual(TICK)
	actor.ammo = 10
	actor.reserve = 90
	actor.start_reload()
	var cues: Array[Dictionary] = []
	var listener := func(event: String, progress: float): cues.append({"event": event, "progress": progress})
	actor.reload_cue.connect(listener)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var timeline: Array[Dictionary] = []
	var held_remaining := actor.reload_remaining
	var total := int((reload_seconds + hold_after) / TICK)
	var authoritative_end := -1
	for tick in total:
		var sent := false
		match authority:
			"local":
				actor.tick_authority(TICK)
			"snapshot", "jitter", "regress":
				if tick % 3 == 0:
					# "jitter": each snapshot is up to six ticks stale, but the timer never goes back up.
					# "regress": the adversarial case, a timer that jumps up and down by a tenth of a
					# second, which a real server does not send but a bad correction could.
					var sampled := reload_seconds - float(tick) * TICK
					if authority == "jitter":
						sampled = reload_seconds - maxf(float(tick - rng.randi_range(0, 6)) * TICK, 0.0)
						sampled = minf(sampled, held_remaining) if tick > 0 else sampled
					elif authority == "regress":
						sampled += rng.randf_range(-0.1, 0.1)
					held_remaining = clampf(sampled, 0.0, reload_seconds)
					sent = true
				actor.reload_remaining = held_remaining
				if float(tick) * TICK >= reload_seconds:
					actor.reload_remaining = 0.0
		cues.clear()
		actor.tick_visual(TICK)
		if authoritative_end < 0 and actor.reload_remaining <= 0.0 and tick > 0:
			authoritative_end = tick
		timeline.append({
			"tick": tick,
			"progress": _progress() if actor.reload_remaining > 0.0 else 0.0,
			"reloading": actor.reload_remaining > 0.0,
			"cues": cues.duplicate(),
			"old_visible": old_node.visible, "new_visible": new_node.visible,
			"old_travel": _travel(old_node), "new_travel": _travel(new_node),
			"old_offset": _offset(old_node), "new_offset": _offset(new_node),
			"old_off_axis": _off_axis(old_node), "new_off_axis": _off_axis(new_node),
			"old_pos": old_node.transform.origin, "new_pos": new_node.transform.origin,
			"old_basis": old_node.transform.basis, "new_basis": new_node.transform.basis,
			"in_hand": -1 if actor._magazine_in_hand == null else (0 if actor._magazine_in_hand == old_node else 1),
			"gun": actor._gun.transform, "wrist": _joint("L_hand"),
			"seat_sound": actor._mechanical_audio.stream == actor._reload_seat,
			"release_sound": actor._mechanical_audio.stream == actor._reload_release,
			"ammo": actor.ammo, "reserve": actor.reserve, "remaining": actor.reload_remaining,
			"old_share": _onscreen_share(old_node) if old_node.visible else -1.0,
			"new_share": _onscreen_share(new_node) if new_node.visible else -1.0,
			"digits_in_frame": _digits_in_frame(),
			"wrist_overshoot": _overshoot(_screen(_joint("L_hand"))),
			"thumb_in_frame": _in_frame(_screen(_joint("L_thumb_3"))),
		})
	actor.reload_cue.disconnect(listener)
	timeline.append({"nodes": [old_node, new_node]})
	return timeline

## How far a point is outside the frame, as a fraction of the frame (0 when inside it).
func _overshoot(p: Vector2) -> float:
	return maxf(maxf(-p.x, p.x - 1.0), maxf(-p.y, p.y - 1.0)) if not _in_frame(p, 0.0) else 0.0

func _digits_in_frame() -> int:
	var inside := 0
	for name in DIGITS:
		if _in_frame(_screen(_joint(name))):
			inside += 1
	return inside

func _first(timeline: Array[Dictionary], predicate: Callable) -> int:
	for i in timeline.size() - 1:
		if predicate.call(timeline[i]):
			return i
	return -1

func _run() -> void:
	reload_seconds = float(Weapons.get_weapon("rifle")["reload"])
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
	_measure_well()
	await _identity()
	await _paths()
	await _grip()
	await _sync()
	await _reduced_motion()
	await _visibility()
	await _authority()
	await _casings()
	await _edges()
	print("RELOAD_SEQUENCE_TEST checks=%d failures=%d" % [checks, failures.size()])
	quit(1 if not failures.is_empty() else 0)

## A second magazine node, distinct from the first, that the first never replaces in the well.
func _identity() -> void:
	var first: MeshInstance3D = actor._magazine
	var spare: MeshInstance3D = actor._magazine_spare
	check(spare != null and spare != first and spare.get_instance_id() != first.get_instance_id(), "the replacement is a second node, not the first one reused")
	check(spare != null and spare.mesh == first.mesh and spare.get_parent() == first.get_parent() and spare.name != first.name, "it is the same magazine model in the same place under its own name")
	check(spare != null and not spare.visible and first.visible, "at rest only the first magazine is shown")
	var timeline := _play("local")
	var nodes: Array = timeline.pop_back().nodes
	var old_node: MeshInstance3D = nodes[0]
	var new_node: MeshInstance3D = nodes[1]
	# Before the grasp: the old one in its well, the replacement not drawn.
	var before := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.REACH * 0.8)]
	check(before.old_visible and not before.new_visible and (before.old_offset as Vector3).length() < 0.0005, "before the grasp the first magazine is in its well and the second is not drawn")
	# In the hand: the old one, alone, from the grasp to the drop.
	var holding_old := timeline[_first(timeline, func(t): return t.progress >= (SBReloadPhases.GRASP + SBReloadPhases.DROP) * 0.5)]
	check(holding_old.in_hand == 0 and not holding_old.new_visible, "between the grasp and the drop the hand holds the old magazine and the replacement is not drawn")
	# After the drop: the old one falls out of the hand while the hand is empty.
	var fallen := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.DROP + 0.04)]
	check(fallen.old_visible and fallen.in_hand == -1 and (fallen.old_offset as Vector3).length() > 0.10, "after the drop the old magazine is out of the hand and away from its well (%.0f mm)" % ((fallen.old_offset as Vector3).length() * 1000.0))
	# At the acquisition: two magazines exist at once, a hand's reach apart.
	var both := timeline[_first(timeline, func(t): return t.old_visible and t.new_visible)]
	check(both.old_visible and both.new_visible and (both.old_pos as Vector3).distance_to(both.new_pos) > 0.08, "for a moment both magazines are drawn, %.0f mm apart: two separate objects" % (((both.old_pos as Vector3).distance_to(both.new_pos)) * 1000.0))
	var acquired := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.ACQUIRE + 0.01)]
	check(acquired.in_hand == 1 and acquired.new_visible, "from the acquisition the hand holds the replacement")
	# Before that the replacement is drawn only while it rises out of the closing hand, never before.
	var first_drawn := timeline[_first(timeline, func(t): return t.new_visible)]
	check(first_drawn.progress >= SBReloadPhases.ACQUIRE - SBReloadPhases.FETCH - 0.01 and first_drawn.in_hand != 1, "the replacement is first drawn %.2f of the reload before the acquisition, rising out of the hand, not held yet" % (SBReloadPhases.ACQUIRE - first_drawn.progress))
	# The old one never comes back to the well, and is gone before the end.
	var came_back := false
	for t in timeline:
		if t.reloading and t.progress > SBReloadPhases.CLEAR and t.old_visible and (t.old_offset as Vector3).length() < 0.06:
			came_back = true
	check(not came_back, "once it has cleared the well the old magazine is never back at it")
	var gone := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.SEAT)]
	check(not gone.old_visible, "by the seat the old magazine is not drawn")
	# After the seat the replacement is the one in the well.
	var seated := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.SEAT + 0.02)]
	check(seated.new_visible and (seated.new_offset as Vector3).length() < 0.0005, "after the seat the replacement is in the well (%.2f mm)" % ((seated.new_offset as Vector3).length() * 1000.0))
	# When the reload ends the two nodes swap roles: the replacement is now THE magazine.
	check(actor._magazine == new_node and actor._magazine_spare == old_node, "when the reload ends the replacement becomes the magazine in the well and the old one the spare")
	check(new_node.visible and not old_node.visible and (_offset(new_node)).length() < 0.0005, "afterwards one magazine is drawn, seated in the well")
	# The next reload takes the replacement out, not a fresh copy of the first.
	var second := _play("local")
	var second_nodes: Array = second.pop_back().nodes
	check(second_nodes[0] == new_node and second_nodes[1] == old_node, "the next reload extracts the node that was the replacement and fetches the one that fell")
	var extracted := second[_first(second, func(t): return t.progress >= SBReloadPhases.CLEAR)]
	check(extracted.in_hand == 0 and extracted.old_travel > 0.085, "and that node clears the well (%.0f mm)" % (extracted.old_travel * 1000.0))
	# A reload cancelled before the seat leaves the first magazine in the well and swaps nothing.
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	var node_a: MeshInstance3D = actor._magazine
	var node_b: MeshInstance3D = actor._magazine_spare
	actor.ammo = 10
	actor.start_reload()
	for tick in 60:
		actor.reload_remaining = reload_seconds * (1.0 - 0.5) if tick > 0 else reload_seconds
		actor.tick_visual(TICK)
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	check(actor._magazine == node_a and actor._magazine_spare == node_b and node_a.visible and not node_b.visible and _offset(node_a).length() < 0.0005, "a reload cancelled before the seat puts the same magazine back in the well and swaps nothing")

## Each magazine slides along its own well: monotonic, on axis, upright when it enters.
func _paths() -> void:
	var timeline := _play("local")
	timeline.pop_back()
	# Extraction: from the latch to clear of the well, only ever outward.
	var worst_back := 0.0
	var worst_off := 0.0
	var last := -INF
	for t in timeline:
		if t.reloading and t.progress >= SBReloadPhases.UNLATCH and t.progress <= SBReloadPhases.CLEAR:
			if last > -INF:
				worst_back = maxf(worst_back, last - t.old_travel)
			last = t.old_travel
			worst_off = maxf(worst_off, t.old_off_axis)
	check(worst_back < 0.0005 and last > 0.085, "the old magazine only moves outward from the latch to clear (backtrack %.2f mm, %.0f mm out)" % [worst_back * 1000.0, last * 1000.0])
	check(worst_off < 0.004, "and stays on the well's axis while it does (worst %.1f mm off)" % (worst_off * 1000.0))
	# Insertion: from lined up under the well to the stop, only ever inward, on axis, ending seated.
	worst_back = 0.0
	worst_off = 0.0
	last = INF
	var first_travel := -1.0
	for t in timeline:
		if t.reloading and t.progress >= SBReloadPhases.ALIGN and t.progress <= SBReloadPhases.SEAT:
			if first_travel < 0.0:
				first_travel = t.new_travel
			if last < INF:
				worst_back = maxf(worst_back, t.new_travel - last)
			last = t.new_travel
			worst_off = maxf(worst_off, t.new_off_axis)
	check(worst_back < 0.0005 and first_travel > 0.07 and absf(last) < 0.001, "the replacement only moves inward from lined up to the stop (%.0f mm out at the start, %.2f mm at the end, backtrack %.2f mm)" % [first_travel * 1000.0, last * 1000.0, worst_back * 1000.0])
	check(worst_off < 0.004, "and stays on the axis while it does (worst %.1f mm off)" % (worst_off * 1000.0))
	# Upright at the mouth of the well: no more than 4 degrees off its seated orientation when it enters.
	var rest_basis: Basis = actor._magazine_rest_transform.basis
	var entering := timeline[_first(timeline, func(t): return t.progress >= SBReloadPhases.ENTER)]
	var tilt := rad_to_deg((entering.new_basis as Basis).get_rotation_quaternion().angle_to(rest_basis.get_rotation_quaternion()))
	check(tilt < 4.0, "the replacement is square to the well when it enters (%.1f degrees off)" % tilt)
	# The old one is let go at the drop, and then falls; it never goes up.
	var drop_index := _first(timeline, func(t): return t.progress >= SBReloadPhases.DROP + 0.002)
	var height_before := (timeline[drop_index].old_pos as Vector3).y
	var fell := true
	var lowest := height_before
	for i in range(drop_index, mini(drop_index + 24, timeline.size() - 1)):
		if not timeline[i].old_visible:
			break
		var y: float = (timeline[i].old_pos as Vector3).y
		if y > lowest + 0.0005:
			fell = false
		lowest = minf(lowest, y)
	check(fell and lowest < height_before - 0.05, "after the drop the old magazine falls (%.0f mm)" % ((height_before - lowest) * 1000.0))
	# It leaves the picture before it stops being drawn: nothing pops out of existence on screen.
	var last_drawn := -1
	for i in timeline.size() - 1:
		if timeline[i].old_visible and timeline[i].progress > SBReloadPhases.DROP:
			last_drawn = i
	check(last_drawn >= 0 and timeline[last_drawn].old_share < 0.15, "the old magazine is %.0f %% on screen on its last drawn frame (it has fallen out of the frame)" % (maxf(timeline[last_drawn].old_share, 0.0) * 100.0))

## The magazine rides the hand without sliding in it, with a palm-to-base distance that is the
## grip, in both spans.
func _grip() -> void:
	var timeline := _play("local")
	timeline.pop_back()
	var held := [0, 0]
	for t in timeline:
		if t.reloading and t.in_hand >= 0:
			held[t.in_hand] += 1
	check(held[0] >= 20 and held[1] >= 25, "the hand holds the old magazine for %d ticks and the replacement for %d" % held)
	# The grip, as the magazine's pose in the hand bone's frame, measured by posing the clip.
	var player: AnimationPlayer = actor._arms_player
	var worst_move := 0.0
	var worst_turn := 0.0
	var distances: Array[float] = []
	for which in [0, 1]:
		var from: float = SBReloadPhases.GRASP + 0.02 if which == 0 else SBReloadPhases.ACQUIRE + 0.02
		var to: float = SBReloadPhases.DROP - 0.012 if which == 0 else SBReloadPhases.SEAT
		var reference := Transform3D.IDENTITY
		for step in 21:
			var at: float = from + (to - from) * float(step) / 20.0
			actor._magazine_swap_pending = false
			actor.reload_remaining = 0.0
			actor._reload_clock = 0.0
			actor.tick_visual(TICK)
			actor.reload_remaining = reload_seconds * (1.0 - at)
			actor.tick_visual(TICK)
			var in_hand: MeshInstance3D = actor._magazine_in_hand
			if in_hand == null:
				check(false, "a magazine is in the hand at %.2f" % at)
				continue
			var in_hand_frame: Transform3D = actor._hand_in_gun().affine_inverse() * in_hand.transform
			if step == 0:
				reference = in_hand_frame
				distances.append((actor._hand_in_gun().origin - (in_hand.transform * Vector3(box.get_center().x, box.position.y, box.get_center().z))).length())
			worst_move = maxf(worst_move, in_hand_frame.origin.distance_to(reference.origin))
			worst_turn = maxf(worst_turn, in_hand_frame.basis.get_rotation_quaternion().angle_to(reference.basis.get_rotation_quaternion()))
	check(worst_move < 0.0006 and worst_turn < deg_to_rad(0.5), "the magazine does not slide or turn in the hand while it holds it (%.2f mm, %.2f deg)" % [worst_move * 1000.0, rad_to_deg(worst_turn)])
	# The grip itself: the wrist sits a palm's depth from the magazine's base. 80 mm is what the clip's grasp
	# produces (the base cupped in the palm); within 12 mm of it is accepted. A magazine carried well away
	# from the palm, or pushed through it, fails; so does one hand holding the two differently.
	var palm := distances[0]
	check(absf(distances[0] - distances[1]) < 0.002, "both magazines are held the same way (%.1f and %.1f mm from the wrist to the base)" % [distances[0] * 1000.0, distances[1] * 1000.0])
	check(absf(palm - 0.080) < 0.012, "the base of the magazine is in the palm: %.0f mm from the wrist (80 +- 12)" % (palm * 1000.0))

## The clicks land on the visible part: measured against the tick the part arrives, under three kinds of
## authority, including a snapshot that leads or lags the visible reload.
func _sync() -> void:
	for authority in ["local", "snapshot", "jitter", "regress"]:
		var timeline := _play(authority)
		var nodes: Array = timeline.pop_back().nodes
		var cue_ticks := {}
		var counts := {"unlatch": 0, "seat": 0}
		for t in timeline:
			for cue in t.cues:
				counts[cue.event] += 1
				cue_ticks[cue.event] = t.tick
		check(counts.unlatch == 1 and counts.seat == 1, "%s authority: each click is cued exactly once (%s)" % [authority, counts])
		check(cue_ticks.get("unlatch", 1 << 30) < cue_ticks.get("seat", -1), "%s authority: the release comes before the seat" % authority)
		# The tick the old magazine first leaves its well (the latch lets go), and the tick the replacement arrives at the stop.
		var left_well := _first(timeline, func(t): return t.reloading and t.old_travel > 0.0005)
		var arrived := _first(timeline, func(t): return t.reloading and t.progress >= SBReloadPhases.ENTER and t.new_travel < 0.001)
		var unlatch_tick: int = cue_ticks.get("unlatch", -100)
		var seat_tick: int = cue_ticks.get("seat", -100)
		if authority == "regress":
			continue # the regressing timer makes the visible reload itself go back; only the once-each rule applies
		check(absi(unlatch_tick - left_well) <= 2, "%s authority: the release click is within two ticks of the magazine leaving its well (click %d, moves %d)" % [authority, unlatch_tick, left_well])
		check(absi(seat_tick - arrived) <= 1, "%s authority: the seat click is within a tick of the replacement reaching its stop (click %d, arrives %d)" % [authority, seat_tick, arrived])
		# Position at the cue, so a click a few ticks early or late is a measurable distance.
		if seat_tick >= 4 and seat_tick < timeline.size():
			var at_cue: float = timeline[seat_tick].new_travel
			var four_before: float = timeline[seat_tick - 4].new_travel
			check(at_cue < 0.0012 and four_before > 0.004, "%s authority: at the seat click the replacement is %.2f mm from its stop and was %.1f mm four ticks before" % [authority, at_cue * 1000.0, four_before * 1000.0])
		if unlatch_tick >= 1 and unlatch_tick + 4 < timeline.size():
			# The clip is keyed every 1/60 of the reload (2.25 ticks), so the part can lead its phase by one clip frame.
			check(timeline[unlatch_tick - 1].old_travel < 0.0025 and timeline[unlatch_tick + 4].old_travel > 0.004, "%s authority: the old magazine is %.1f mm out a tick before the release click and %.1f mm out four ticks after it" % [authority, timeline[unlatch_tick - 1].old_travel * 1000.0, timeline[unlatch_tick + 4].old_travel * 1000.0])
		# The sound that played is the one for the event.
		if seat_tick >= 0 and seat_tick < timeline.size():
			check(timeline[seat_tick].seat_sound, "%s authority: the seat click plays the seat sound" % authority)
		if unlatch_tick >= 0 and unlatch_tick < timeline.size():
			check(timeline[unlatch_tick].release_sound, "%s authority: the release click plays the release sound" % authority)
	# What the old way did, for the record of why the cue is on the visual clock: the authoritative fraction
	# reaches the seat up to a slack before the visible reload does.
	var lead_ticks := int(ceil(actor.RELOAD_VISUAL_SLACK / TICK))
	check(lead_ticks >= 5, "the old authoritative-fraction cue could lead the visible seat by up to %d ticks (the slack is %.2f s)" % [lead_ticks, actor.RELOAD_VISUAL_SLACK])

## Reduced motion keeps the staging: the gun and the hand are where they are with it off; only the tumble goes.
func _reduced_motion() -> void:
	var normal := _play("local", false)
	normal.pop_back()
	var calm := _play("local", true)
	calm.pop_back()
	var worst_gun := 0.0
	var worst_hand := 0.0
	var worst_turn := 0.0
	for i in mini(normal.size(), calm.size()):
		if normal[i].reloading and calm[i].reloading:
			worst_gun = maxf(worst_gun, ((normal[i].gun as Transform3D).origin).distance_to((calm[i].gun as Transform3D).origin))
			worst_turn = maxf(worst_turn, ((normal[i].gun as Transform3D).basis.get_rotation_quaternion()).angle_to((calm[i].gun as Transform3D).basis.get_rotation_quaternion()))
			worst_hand = maxf(worst_hand, (normal[i].wrist as Vector3).distance_to(calm[i].wrist))
	check(worst_gun < 0.0005 and worst_turn < deg_to_rad(0.3) and worst_hand < 0.0005, "reduced motion does not move the reload staging: the gun is within %.2f mm and %.2f deg and the hand within %.2f mm of where it is without it" % [worst_gun * 1000.0, rad_to_deg(worst_turn), worst_hand * 1000.0])
	# What it does change: the old magazine falls without tumbling.
	var drop := _first(calm, func(t): return t.progress >= SBReloadPhases.DROP + 0.1)
	var drop_normal := _first(normal, func(t): return t.progress >= SBReloadPhases.DROP + 0.1)
	var rest_q: Quaternion = actor._magazine_rest_transform.basis.get_rotation_quaternion()
	var turned_calm := rad_to_deg((calm[drop].old_basis as Basis).get_rotation_quaternion().angle_to(calm[_first(calm, func(t): return t.progress >= SBReloadPhases.DROP)].old_basis.get_rotation_quaternion()))
	var turned_normal := rad_to_deg((normal[drop_normal].old_basis as Basis).get_rotation_quaternion().angle_to(normal[_first(normal, func(t): return t.progress >= SBReloadPhases.DROP)].old_basis.get_rotation_quaternion()))
	check(turned_calm < 2.0 and turned_normal > 20.0, "with reduced motion the discarded magazine falls without tumbling (%.1f degrees against %.0f)" % [turned_calm, turned_normal])
	check(calm[drop].old_visible and (calm[drop].old_pos as Vector3).y < (calm[_first(calm, func(t): return t.progress >= SBReloadPhases.DROP)].old_pos as Vector3).y - 0.02, "and it still falls where it can be seen")
	# Nothing is off screen that was on screen: the same visibility checks as the normal run follow in _visibility.
	var share_normal: float = calm[_first(calm, func(t): return t.progress >= SBReloadPhases.GRASP + 0.02)].old_share
	check(share_normal > 0.85, "the held magazine is %.0f %% on screen with reduced motion on" % (share_normal * 100.0))

## What is in the frame while a hand is doing something: the held magazine, the wrist, the fingertips; in both modes.
func _visibility() -> void:
	for reduced in [false, true]:
		var timeline := _play("local", reduced)
		timeline.pop_back()
		var worst_magazine := 1.0
		var worst_magazine_at := 0.0
		var worst_overshoot := 0.0
		var worst_digits := 5
		var worst_digits_at := 0.0
		var thumb_out := 0
		var frames := 0
		for t in timeline:
			if not t.reloading or t.progress < 0.02 or t.progress > 0.98:
				continue
			frames += 1
			worst_overshoot = maxf(worst_overshoot, t.wrist_overshoot)
			if not t.thumb_in_frame:
				thumb_out += 1
			if t.digits_in_frame < worst_digits:
				worst_digits = t.digits_in_frame
				worst_digits_at = t.progress
			if t.in_hand >= 0:
				var share: float = t.old_share if t.in_hand == 0 else t.new_share
				if share < worst_magazine:
					worst_magazine = share
					worst_magazine_at = t.progress
		var label := "reduced motion" if reduced else "normal motion"
		check(frames > 120, "%s: %d ticks from just after the start to just before the end" % [label, frames])
		# The wrist is a bone under the cuff: it may sit a little below the frame's edge with the hand in
		# view (reload_visibility_test.gd counts the hand's pixels); this bound only stops it going far.
		check(worst_overshoot <= 0.06, "%s: the support wrist is never more than 6 %% of the frame outside it (worst %.1f %%)" % [label, worst_overshoot * 100.0])
		check(thumb_out == 0, "%s: the thumb's tip joint stays inside the frame the whole reload (%d ticks outside)" % [label, thumb_out])
		check(worst_digits >= 3, "%s: at least three of the five fingertip joints stay inside the frame (worst %d at %.2f)" % [label, worst_digits, worst_digits_at])
		check(worst_magazine >= 0.85, "%s: the magazine in the hand is at least 85 %% on screen throughout (worst %.0f %% at %.2f)" % [label, worst_magazine * 100.0, worst_magazine_at])

## Animation never changes what the weapon does: ammunition, the reload timer, completion.
func _authority() -> void:
	var results := {}
	for mode in ["bare", "visual", "visual_reduced"]:
		var subject := _new_actor(20 + results.size())
		subject.global_position = Vector3(6 + results.size() * 3, 0, 0)
		await physics_frame
		subject.reduced_motion = mode == "visual_reduced"
		subject.ammo = 7
		subject.reserve = 53
		subject.start_reload()
		var trace: Array[Vector3] = []
		for tick in int((reload_seconds + 0.5) / TICK):
			subject.tick_authority(TICK)
			if mode != "bare":
				subject.tick_visual(TICK)
			trace.append(Vector3(subject.ammo, subject.reserve, snappedf(subject.reload_remaining, 0.00001)))
		results[mode] = trace
		subject.queue_free()
	var same: bool = results.bare == results.visual and results.bare == results.visual_reduced
	check(same, "ammunition, reserve and the reload timer are the same every tick whether or not the reload is animated, with or without reduced motion")
	var final: Vector3 = (results.bare as Array)[-1]
	check(int(final.x) == 30 and int(final.y) == 30, "the authoritative reload still moves the missing rounds (%d in the magazine, %d in reserve)" % [int(final.x), int(final.y)])
	# The presentation never writes the timer or the ammunition it reads.
	actor.ammo = 11
	actor.reserve = 77
	actor.reload_remaining = 1.1
	var before := Vector3(actor.ammo, actor.reserve, actor.reload_remaining)
	for tick in 30:
		actor.tick_visual(TICK)
	check(Vector3(actor.ammo, actor.reserve, actor.reload_remaining) == before, "tick_visual never writes ammunition, reserve or the timer")

## Brass bounces on the floor under the port, not at the shooter's feet.
func _casings() -> void:
	var effects := SBCombatEffects.for_world(world)
	var shooter := _new_actor(40)
	shooter.global_position = Vector3(0, 2.0, 5)
	shooter.velocity = Vector3.ZERO
	await physics_frame
	await physics_frame
	var port: Vector3 = shooter._gun.global_transform * shooter._ejection_point
	var ground: float = shooter._cosmetic_floor(shooter._viewmodel_to_world(port) if shooter._viewmodel else port)
	check(absf(ground) < 0.01, "from %.1f m up the floor under the ejection port is found at %.3f m (the shooter's feet are at %.1f)" % [shooter.global_position.y, ground, shooter.global_position.y])
	var before: int = effects._next["casings"]
	shooter.play_shot_effect()
	var slot: Dictionary = effects._pools["casings"].slots[before]
	check(is_equal_approx(float(slot.ground), ground) and absf(float(slot.ground) - shooter.global_position.y) > 1.0, "the casing is given that floor (%.3f), not the shooter's feet (%.1f)" % [float(slot.ground), shooter.global_position.y])
	var lowest_y := INF
	for step in 112:
		effects._process(0.016)
		lowest_y = minf(lowest_y, (slot.at as Vector3).y)
		if slot.resting:
			break
	check(lowest_y < 0.02 and lowest_y > -0.01, "the casing reaches the floor and no lower (lowest %.3f m)" % lowest_y)
	check(int(slot.bounces) >= 1 and (slot.at as Vector3).y < 0.25, "it has bounced on it %d time(s) and is still down at the floor, not up at the shooter (%.3f m)" % [slot.bounces, (slot.at as Vector3).y])
	# With no floor within reach of the probe the brass does not claim one.
	shooter.global_position = Vector3(0, 30.0, 5)
	await physics_frame
	await physics_frame
	var none: float = shooter._cosmetic_floor(shooter.global_position + Vector3(0, 1.5, 0))
	check(is_inf(none) and none < 0.0, "with no floor in reach the probe says so (%s)" % none)
	var before_air: int = effects._next["casings"]
	shooter.play_shot_effect()
	var air_slot: Dictionary = effects._pools["casings"].slots[before_air]
	check(not is_finite(float(air_slot.ground)), "a casing thrown over open air is given no floor to bounce on")
	# The shooter's own body is not a floor: a ray from above the head must pass through it.
	shooter.global_position = Vector3(0, 0.0, 9)
	await physics_frame
	await physics_frame
	var through: float = shooter._cosmetic_floor(shooter.global_position + Vector3(0, 1.6, 0))
	check(absf(through) < 0.01, "the shooter's own capsule is not the floor under the port (%.3f)" % through)

## The paths a match actually takes besides a clean reload: cancelled before and after the seat, with the
## replacement in hand, a round reset, a weapon swap, a restart with no idle frame between, a remote actor,
## and the procedural weapons (which keep their older click timing and 20 % reduced-motion dip).
func _edges() -> void:
	var shown := func(a: SBActor) -> int:
		var n := 0
		for node in [a._magazine, a._magazine_spare]:
			if node != null and node.visible:
				n += 1
		return n
	# Cancel with the replacement in the hand: the first magazine goes back in the well, nothing swaps.
	_drive(actor, 0.65)
	var first: MeshInstance3D = actor._magazine
	var second: MeshInstance3D = actor._magazine_spare
	check(actor._magazine_in_hand == second, "mid-reload with the replacement in hand")
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	check(actor._magazine == first and actor._magazine_spare == second and shown.call(actor) == 1 and first.visible and _offset(first).length() < 0.0005, "a reload cancelled with the replacement in the hand puts the first magazine back and swaps nothing")
	# Cancel after the seat: the replacement is what sits in the well, once.
	_drive(actor, SBReloadPhases.SEAT + 0.03)
	var before_first: MeshInstance3D = actor._magazine
	var before_second: MeshInstance3D = actor._magazine_spare
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	check(actor._magazine == before_second and actor._magazine_spare == before_first and shown.call(actor) == 1 and _offset(actor._magazine).length() < 0.0005, "a reload cancelled after the seat leaves the replacement seated in the well, one magazine drawn")
	# A round reset mid-reload: one magazine, and the next reload clicks again.
	_drive(actor, 0.5)
	actor.reset_for_round(Vector3.ZERO)
	actor.tick_visual(TICK)
	check(shown.call(actor) == 1 and actor._magazine.visible and actor._magazine_in_hand == null and not actor._magazine_swap_pending, "a round reset mid-reload leaves one magazine in the well and no pending swap")
	actor.ammo = 10
	actor.reserve = 90
	var cues: Array[String] = []
	var listener := func(event: String, _p: float): cues.append(event)
	actor.reload_cue.connect(listener)
	_drive(actor, 0.95)
	actor.reload_cue.disconnect(listener)
	check(cues == ["unlatch", "seat"], "and the reload after it clicks both times (%s)" % [cues])
	# Back to back with no idle frame between: the second reload clicks again and swaps once.
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	var node_a: MeshInstance3D = actor._magazine
	var node_b: MeshInstance3D = actor._magazine_spare
	var again: Array[String] = []
	var listener2 := func(event: String, _p: float): again.append(event)
	actor.reload_cue.connect(listener2)
	_drive(actor, 0.9, false)  # first reload to its end, reload_remaining still above zero
	actor.reload_remaining = reload_seconds  # the timer restarts (a new reload) with no zero frame
	for tick in int(reload_seconds / TICK) + 3:
		actor.reload_remaining = maxf(0.001, reload_seconds - float(tick) * TICK)
		actor.tick_visual(TICK)
	actor.reload_cue.disconnect(listener2)
	check(again.count("unlatch") == 2 and again.count("seat") == 2, "a reload restarted with no idle frame between clicks both times again (%s)" % [again])
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	check(shown.call(actor) == 1 and (actor._magazine == node_a or actor._magazine == node_b), "and ends with one magazine drawn")
	# A weapon swap mid-reload and back: no stale state, one magazine each time.
	actor.ammo = 10
	_drive(actor, 0.6)
	actor.input_state = {"weapon": "sidearm"}
	actor.tick_authority(TICK)
	actor.input_state = {}
	actor.tick_visual(TICK)
	check(actor.weapon_id == "sidearm" and actor._magazine_in_hand == null and not actor._magazine_swap_pending and (actor._magazine == null or actor._magazine.visible), "swapping weapons mid-reload clears the reload's presentation state (weapon %s, in hand %s, pending %s)" % [actor.weapon_id, actor._magazine_in_hand, actor._magazine_swap_pending])
	actor.input_state = {"weapon": "rifle"}
	actor.tick_authority(TICK)
	actor.input_state = {}
	actor.reload_remaining = 0.0
	actor.tick_visual(TICK)
	check(actor.weapon_id == "rifle" and shown.call(actor) == 1, "and swapping back leaves one magazine drawn")
	# A remote actor (no camera, never drawn in first person) is not touched by any of it.
	var remote := Actor.new()
	remote.configure(61, 1, "Remote", false)
	world.add_child(remote)
	remote.reset_for_round(Vector3(9, 0, 9))
	remote.credits = 5000
	remote.buy_weapon("rifle")
	remote.ammo = 10
	remote.reserve = 90
	remote.start_reload()
	for tick in int((reload_seconds + 0.3) / TICK):
		remote.tick_authority(TICK)
		remote.tick_visual(TICK)
	check(remote.ammo == 30 and remote.reserve == 70 and remote.reload_remaining == 0.0, "a remote actor completes its authoritative reload unchanged (%d/%d)" % [remote.ammo, remote.reserve])
	remote.queue_free()
	# The procedural weapons keep their click timing (the release at the start, the seat at 0.80) and their calmed dip.
	var procedural := _new_actor(62)
	procedural.global_position = Vector3(-8, 0, 3)
	procedural.buy_weapon("smg")
	procedural.ammo = 5
	procedural.reserve = 40
	await physics_frame
	check(not is_instance_valid(procedural._arms_player), "the SMG has no rigged hands")
	var smg_seconds := float(Weapons.get_weapon("smg")["reload"])
	var smg_cues: Array = []
	var smg_listener := func(event: String, p: float): smg_cues.append([event, p])
	procedural.reload_cue.connect(smg_listener)
	var normal_dip := 0.0
	var calm_dip := 0.0
	for pass_index in 2:
		procedural.reduced_motion = pass_index == 1
		procedural.reload_remaining = 0.0
		procedural.tick_visual(TICK)
		var rest_position: Vector3 = procedural._gun.position
		smg_cues.clear()
		var peak := 0.0
		for tick in int(smg_seconds / TICK) + 2:
			procedural.reload_remaining = maxf(0.001, smg_seconds - float(tick) * TICK)
			procedural.tick_visual(TICK)
			peak = maxf(peak, procedural._gun.position.distance_to(rest_position))
		if pass_index == 0:
			normal_dip = peak
			check(smg_cues.size() == 2 and smg_cues[0][0] == "unlatch" and float(smg_cues[0][1]) < 0.05 and smg_cues[1][0] == "seat" and absf(float(smg_cues[1][1]) - SBReloadPhases.SEAT) < 0.02, "the SMG's release click is at the start and its seat click at the seat, once each (%s)" % [smg_cues])
		else:
			calm_dip = peak
	procedural.reload_cue.disconnect(smg_listener)
	check(normal_dip > 0.05 and calm_dip < normal_dip * 0.3 and calm_dip > normal_dip * 0.1, "with reduced motion the SMG's reload dip is about a fifth of the normal one (%.0f mm against %.0f mm)" % [calm_dip * 1000.0, normal_dip * 1000.0])

## Drives the actor's reload from a clean start to `progress` at 60 Hz with the authoritative timer assigned as a
## client would; `finish` false leaves the reload still running.
func _drive(a: SBActor, progress: float, _finish := true) -> void:
	a.reload_remaining = 0.0
	a.tick_visual(TICK)
	a.ammo = 10
	var steps := int(progress * reload_seconds / TICK) + 1
	for tick in steps:
		a.reload_remaining = maxf(0.001, reload_seconds - float(tick) * TICK)
		a.tick_visual(TICK)
