extends "res://tests/authority_order_test.gd"
## Independent critic probe. Stored only in detached review worktrees.
var utility_signals: Array = []
var action_records: Array = []

func _run() -> void:
	print("CRITIC_NEGATIVE engine=%s" % Engine.get_version_info().string)
	match_node = FixtureMatch.new()
	match_node.configure({"mode": "offline"})
	root.add_child(match_node)
	match_node.set_physics_process(false)
	match_node.local_id = 0
	match_node.phase = "live"
	match_node.objective_state = "none"
	match_node.objective_carrier = 0
	var floor_body := StaticBody3D.new()
	var floor_collision := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(200, 0.2, 200)
	floor_collision.shape = box
	floor_body.add_child(floor_collision)
	match_node.add_child(floor_body)
	floor_body.position.y = -0.1
	for id in range(1, 11):
		var actor := match_node._spawn_actor(id, 0 if id <= 5 else 1, "critic-%d" % id)
		actor.shot_fired.connect(func(source: int, _at: Vector3, _dir: Vector3) -> void: shots.append(source))
		actor.eliminated.connect(func(victim: int, killer: int) -> void: eliminations.append([victim, killer]))
		actor.utility_deployed.connect(func(source: int, _at: Vector3, kind: String) -> void: utility_signals.append([source, kind]))
		match_node._peer_actors[100 + id] = id
		match_node._last_peer_input[id] = 0.0
	await physics_frame
	for reverse in [false, true]:
		await _action_contract(reverse)
		await _capped_contacts(reverse)
	await create_timer(0.6).timeout
	match_node.queue_free()
	await process_frame
	print("CRITIC_NEGATIVE checks=%d failures=%d records=%s" % [checks, failures.size(), JSON.stringify(action_records)])
	quit(0 if failures.is_empty() else 1)

func _action_contract(reverse: bool) -> void:
	await process_frame
	_prepare(311, reverse)
	match_node._last_peer_input[1] = 0.0
	var a: SBActor = match_node.actors[1]
	a.position = Vector3(0, 0.01, 40)
	a.input_state = {"look": Vector2.ZERO}
	await _settle()
	a.velocity.x = SBMovementStep.WALK_SPEED
	a.input_state.move = Vector2(1, 0)
	var x_before := a.position.x
	match_node._authority_tick(DT)
	check(absf(a.position.x - x_before - SBMovementStep.WALK_SPEED * DT) < 0.0001, "match moves each actor exactly once reverse=%s" % reverse)
	a.input_state = {"look": Vector2(0, 1.4), "fire": true}
	match_node._authority_tick(DT)
	match_node._authority_tick(DT)
	check(a.ammo == 29 and shots.size() == 1, "match held rifle obeys cooldown reverse=%s" % reverse)
	a.ammo = 0
	a.reserve = 7
	a._weapon_cooldowns.clear()
	match_node._authority_tick(DT)
	check(a.ammo == 0 and a.reload_remaining > 2.2 and shots.size() == 1, "empty held rifle starts reload without shot reverse=%s" % reverse)
	a.reload_remaining = DT * 1.5
	match_node._authority_tick(DT)
	check(a.ammo == 0 and shots.size() == 1, "incomplete reload cannot fire reverse=%s" % reverse)
	match_node._authority_tick(DT)
	check(a.ammo == 6 and a.reserve == 0 and a.reload_remaining == 0 and shots.size() == 2, "reload completes with reserve cap and one shot reverse=%s" % reverse)
	a.input_state = {"look": Vector2(0, 1.4), "weapon": "sidearm", "fire": true}
	match_node._authority_tick(DT)
	check(a.weapon_id == "sidearm" and a.ammo == 15 and a._deploy_remaining > 0, "weapon switch applies deploy delay reverse=%s" % reverse)
	a._deploy_remaining = 0
	a._fire_previous = false
	match_node._authority_tick(DT)
	for tick in range(30): match_node._authority_tick(DT)
	check(a.ammo == 14 and shots.size() == 3, "held semiauto fires once reverse=%s" % reverse)
	# Sustained silence must retain all edge latches, including jump from movement phase.
	a._jump_previous = true
	a._grenade_previous = true
	a._smoke_previous = true
	match_node._elapsed = 1.0
	match_node._authority_tick(DT)
	check(a._fire_previous and a._jump_previous and a._grenade_previous and a._smoke_previous, "stale peer suspension retains four edges reverse=%s" % reverse)
	match_node._last_peer_input[1] = 1.0
	a.input_state = {"look": Vector2(0, 1.4), "fire": true, "grenade": true, "smoke": true}
	match_node._authority_tick(DT)
	check(a.ammo == 14 and a.grenades == 1 and a.smokes == 1, "outage recovery invents no trigger or utility edge reverse=%s" % reverse)
	a.input_state = {"look": Vector2(0, 1.4)}
	match_node._authority_tick(DT)
	a.input_state = {"look": Vector2(0, 1.4), "fire": true, "grenade": true, "smoke": true}
	utility_signals.clear()
	match_node._authority_tick(DT)
	check(a.ammo == 13 and a.grenades == 0 and a.smokes == 0 and utility_signals.size() == 2, "real release rearms fire and utilities once reverse=%s" % reverse)
	a.grenades = 1
	a.smokes = 1
	match_node._authority_tick(DT)
	check(a.grenades == 1 and a.smokes == 1 and utility_signals.size() == 2, "held utilities cannot redeploy after replenish reverse=%s" % reverse)
	action_records.append({"reverse": reverse, "ammo": a.ammo, "shots": shots.size(), "utility_signals": utility_signals.duplicate()})
	for child in match_node.get_children():
		if child is SBUtility: child.queue_free()
	match_node._elapsed = 0.0

func _capped_contacts(reverse: bool) -> void:
	await process_frame
	_prepare(101, reverse)
	var a: SBActor = match_node.actors[1]
	var b: SBActor = match_node.actors[2]
	var front: SBActor = match_node.actors[6]
	a.position = Vector3(-0.4, 0.01, 0)
	b.position = Vector3(0.4, 0.01, 0)
	front.position = Vector3(0, 0.01, -4)
	a.input_state = {"look": Vector2(-atan(0.1), 0)}
	b.input_state = {"look": Vector2(atan(0.1), 0)}
	await _settle()
	front.health = 25
	a.credits = 8950
	b.credits = 8950
	a.input_state.fire = true
	b.input_state.fire = true
	match_node._authority_tick(DT)
	var damage := 0.0
	for amount in match_node._damage_history.get(6, {}).values(): damage += float(amount)
	check(damage == 25 and front.health == 0 and front.deaths == 1 and eliminations.size() == 1, "actual damage and death capped once reverse=%s" % reverse)
	check(a.kills + b.kills == 1 and a.credits + b.credits == 17950 and maxi(a.credits, b.credits) == 9000, "one kill reward obeys credit ceiling reverse=%s" % reverse)
	front.input_state = {"fire": true, "grenade": true, "smoke": true, "move": Vector2.ONE}
	var at := front.position
	match_node._authority_tick(DT)
	check(front.position == at and front.ammo == 30 and front.grenades == 1 and front.smokes == 1 and front.deaths == 1, "dead actor has no movement or action next tick reverse=%s" % reverse)
	action_records.append({"reverse": reverse, "victim_damage": damage, "victim_deaths": front.deaths, "kills": a.kills + b.kills, "credits": a.credits + b.credits})
