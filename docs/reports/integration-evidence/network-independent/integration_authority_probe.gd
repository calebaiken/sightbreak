extends SceneTree
var checks := 0
var failures := 0
func _initialize() -> void: run.call_deferred()
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func run() -> void:
	var game := TacticalMatch.new()
	game.configure({"mode":"offline"})
	root.add_child(game)
	game.set_physics_process(false)
	check(not game._prediction_enabled,"normal options leave prediction disabled")
	check(not bool(game.options.get("record_hit_history",false)),"history recording absent by default")
	var actor: SBActor = game.local_actor()
	actor.credits = 5000
	check(actor.buy_weapon("rifle"),"authored rifle purchases through authority")
	check(is_instance_valid(actor._arms_player),"authored animation bound in combined actor")
	actor.ammo = 12
	actor.start_reload()
	var baseline: Dictionary = actor.snapshot().duplicate(true)
	var cooldowns := actor._weapon_cooldowns.duplicate()
	for i in range(240):
		actor.tick_visual([1.0/30,1.0/60,1.0/120][i%3])
		check(actor.snapshot() == baseline,"visual tick cannot mutate replicated authoritative state at step %d" % i)
	check(actor._weapon_cooldowns == cooldowns,"visual tick cannot advance weapon cooldowns")
	check(actor.reload_remaining == baseline.reload and actor.ammo == 12,"animation completion cannot reload ammunition")
	var target: SBActor = game.actors[6]
	target.position = Vector3(0,10,-10)
	actor.position = Vector3(0,10,0)
	await physics_frame
	var before := target.volume_intersection(Vector3(0,11,-5),Vector3.FORWARD,20)
	for i in range(90):
		target.tick_visual(1.0/60)
	check(target.volume_intersection(Vector3(0,11,-5),Vector3.FORWARD,20) == before,"visual animation cannot change body hit registration")
	var packet := game._snapshot(actor.actor_id)
	check(SBSnapshotSchema.valid(packet),"combined snapshot schema accepts authorized packet")
	for state: Dictionary in packet.actors:
		if state.team != actor.team:
			for field in SBStatePrivacy.OWN + SBStatePrivacy.TEAM:
				check(not state.has(field),"enemy private field absent: %s" % field)
		if state.id != actor.actor_id:
			for field in ["move_ack","grounded","jump_held"]:
				check(not state.has(field),"movement reconciliation private to owner: %s" % field)
	check(game._hit_history.frames.is_empty(),"diagnostic history remains empty during ordinary offline game")
	game.queue_free()
	for i in 5: await process_frame
	# Allow AudioServer asynchronous stopped-playback release at shutdown.
	await create_timer(0.2).timeout
	print("INDEPENDENT_INTEGRATION_AUTHORITY checks=%d failures=%d" % [checks,failures])
	quit(1 if failures else 0)
