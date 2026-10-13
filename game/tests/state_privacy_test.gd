extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func _initialize() -> void:
	call_deferred("run")
func state(packet: Dictionary, id: int) -> Dictionary:
	for entry: Dictionary in packet.actors:
		if entry.id == id:
			return entry
	return {}
func run() -> void:
	var game := TacticalMatch.new()
	game.configure({"mode": "offline"})
	root.add_child(game)
	game.set_physics_process(false)
	for actor: SBActor in game.actors.values():
		actor.position = Vector3(30 + actor.actor_id, 10, 0)
	game.actors[1].position = Vector3(0, 10, 0)
	game.actors[6].position = Vector3(0, 10, -10)
	game.actors[6].credits = 4567
	game.actors[6].ammo = 13
	game.objective_carrier = 1
	game._interactions = {1: 1.3, 6: 0.7}
	await physics_frame
	var open := game._snapshot(1)
	check(SBSnapshotSchema.valid(open), "authorized snapshot conforms to schema")
	check(state(open, 6).relevant and state(open, 6).position == game.actors[6].position, "visible enemy synchronized")
	for field: String in ["credits", "health", "ammo", "reserve", "inventory", "recoil", "reload", "grenades", "smokes"]:
		check(not state(open, 6).has(field), "enemy private field removed: " + field)
	check(state(open, 1).has("inventory") and state(open, 2).has("health") and not state(open, 2).has("inventory"), "own and teammate permissions explicit")
	check(open.interactions == {1: 1.3}, "interaction progress only for recipient")
	var defender := game._snapshot(6)
	check(defender.carrier == 0 and defender.objective == "unknown" and defender.objective_position == Vector3.ZERO, "hidden carrier and location absent")
	check(game._snapshot(0).actors.size() == 10 and game._snapshot(99).is_empty(), "no arbitrary spectator entitlement")
	var wall := StaticBody3D.new()
	wall.collision_layer = 1
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(20, 6, 1)
	shape.shape = box
	wall.add_child(shape)
	game.add_child(wall)
	wall.position = Vector3(0, 11, -5)
	await physics_frame
	await physics_frame
	var hidden := game._snapshot(1)
	check(not state(hidden, 6).relevant, "wall hides enemy")
	for field: String in SBStatePrivacy.OBSERVABLE + SBStatePrivacy.TEAM + SBStatePrivacy.OWN:
		check(not state(hidden, 6).has(field), "hidden field absent on wire: " + field)
	check(state(hidden, 6).name == game.actors[6].display_name and state(hidden, 6).has("kills"), "public roster retained")
	game.actors[6].position.x += 0.5
	check(state(game._snapshot(1), 6) == state(hidden, 6), "hidden movement produces no changing enemy data")
	check(not game._privacy.point_visible(game, game.actors[1], game.actors[6].position), "hidden impacts suppressed")
	game.actors[1].velocity = Vector3(0, 0, -6)
	game.actors[1].position.z = -4.3
	check(not state(game._snapshot(1), 6).relevant, "lookahead cannot pass through solid wall")
	game.actors[1].position = Vector3(10.5, 10, -4.3)
	game.actors[6].position = Vector3(10.5, 10, -6.0)
	check(state(game._snapshot(1), 6).relevant, "corner peek receives enemy immediately")
	wall.queue_free()
	game.actors[1].position = Vector3(0, 10, 0)
	game.actors[1].velocity = Vector3.ZERO
	game.actors[6].position = Vector3(0, 10, -10)
	await physics_frame
	var smoke := SBUtility.new()
	smoke.kind = "smoke"
	game.add_child(smoke)
	smoke.set_physics_process(false)
	smoke._detonate()
	smoke.position = Vector3(0, 11, -5)
	check(state(game._snapshot(1), 6).relevant, "growing uncertain smoke preserves enemy visibility")
	smoke._cloud_elapsed = 1.0
	check(not state(game._snapshot(1), 6).relevant, "opaque smoke core revokes spatial state")
	game.actors[1].position.x = 2.6
	game.actors[6].position.x = 2.6
	check(state(game._snapshot(1), 6).relevant, "translucent smoke rim cannot erase visible enemy")
	game.actors[1].position.x = 0
	game.actors[6].position.x = 0
	smoke._lifetime = 0
	check(state(game._snapshot(1), 6).relevant, "smoke dissipation restores visibility")
	game.actors[1].alive = false
	check(SBStatePrivacy.observer(game, 1).actor_id == 2, "dead player follows living teammate only")
	for id in range(2, 6):
		game.actors[id].alive = false
	check(SBStatePrivacy.observer(game, 1) == null and not state(game._snapshot(1), 6).relevant, "eliminated team has no enemy viewpoint")
	game.actors[1].alive = true
	game.actors[1].team = 1
	check(state(game._snapshot(1), 6).has("health") and not state(game._snapshot(1), 2).has("health"), "team switch recalculates authorization")
	game.actors[1].team = 0
	check(not state(game._snapshot(1), 6).has("health"), "reconnect/team change does not retain permission")
	var replica := TacticalMatch.new()
	replica.configure({"mode": "offline"})
	root.add_child(replica)
	replica.set_physics_process(false)
	replica._apply_snapshot(open)
	replica._apply_snapshot(hidden)
	check(not replica.actors[6].visible and replica.actors[6].collision_layer == 0 and replica.actors[6].position == Vector3.ZERO, "client revokes geometry collision and cached position")
	replica._apply_snapshot(open)
	check(replica.actors[6].visible and replica.actors[6].collision_layer == 2, "visible enemy returns correctly")
	check(replica.actors[6].position == state(open, 6).position, "relevance restoration snaps to the authorized position")
	for mutation: Dictionary in [{"actors": []}, {"phase": []}, {"objective_position": Vector3(NAN, 0, 0)}, {"interactions": {1: "bad"}}, {"utilities": [false]}]:
		var bad := open.duplicate(true)
		bad.merge(mutation, true)
		check(not SBSnapshotSchema.valid(bad), "malformed packet rejected atomically " + str(mutation.keys()))
		replica._apply_snapshot(bad)
	var bad_actor := open.duplicate(true)
	bad_actor.actors[0].position = "teleport"
	check(not SBSnapshotSchema.valid(bad_actor), "malformed actor rejected")
	bad_actor = open.duplicate(true)
	bad_actor.actors[0].crouch = []
	check(not SBSnapshotSchema.valid(bad_actor), "malformed boolean rejected before any mutation")
	var cloud_state := {"id": 123, "kind": "smoke", "position": Vector3(0, 10, 0), "detonated": true, "life": 12.0}
	replica._sync_utility_visuals([cloud_state])
	cloud_state.life = 10.0
	replica._sync_utility_visuals([cloud_state])
	await process_frame
	check(replica._remote_utilities[123]._cloud_puffs[0].scale == Vector3.ONE, "newer smoke age cannot be overwritten by a birth tween")
	print("STATE_PRIVACY_TEST checks=%d failures=%d" % [checks, failures])
	game.queue_free()
	replica.queue_free()
	await process_frame
	await process_frame
	quit(1 if failures else 0)
