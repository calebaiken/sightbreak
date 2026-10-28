extends SceneTree
## Evidence tool: how many attacker-spawn -> defender-spawn pairs have a clear line of sight? Same ray as SBActor.can_see
## (head height 1.62 m, mask 3). Prints SPAWN_LOS clear=N of 25 pairs.
## usage: godot --headless --audio-driver Dummy --script <this file>
func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var m := TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.local_id = 0
	await physics_frame
	await physics_frame
	await physics_frame
	var space := m.get_world_3d().direct_space_state
	var clear := 0
	var total := 0
	var rows: Array = []
	for a: Vector3 in m.arena.attack_spawns:
		for d: Vector3 in m.arena.defend_spawns:
			total += 1
			var from := a + Vector3.UP * 1.62
			var to := d + Vector3.UP * 1.62
			var q := PhysicsRayQueryParameters3D.create(from, to, 3)
			var hit := space.intersect_ray(q)
			var blocked := not hit.is_empty() and not (hit.get("collider") is SBActor)
			if not blocked: clear += 1
			rows.append("%s -> %s dist=%.1f blocked=%s by=%s" % [str(a), str(d), a.distance_to(d), blocked, str(hit.get("collider"))])
	print("SPAWN_LOS clear=%d of %d pairs" % [clear, total])
	for r in rows.slice(0, 8): print("  ", r)
	# what blocks the centre line, and how long are the longest uninterrupted corridors from the attacker spawn?
	var forward := 0.0
	var q2 := PhysicsRayQueryParameters3D.create(Vector3(0, 1.62, -21), Vector3(0, 1.62, 21), 3)
	var h2 := space.intersect_ray(q2)
	print("CENTRE_LINE hit=", str(h2.get("position", "none")), " collider=", str(h2.get("collider")))
	var obstacle_count: int = m.arena._obstacles.size()
	print("OBSTACLES ", obstacle_count, " WAYPOINTS ", m.arena.waypoints.size())
	m.queue_free()
	await create_timer(0.2).timeout
	quit(0)
