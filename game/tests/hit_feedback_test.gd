extends SceneTree
var checks := 0
var failures := 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var game = load("res://scripts/gameplay/match.gd").new()
	game.configure({"mode": "offline", "name": "Feedback QA"})
	root.add_child(game)
	game.set_physics_process(false)
	var actor = game.local_actor()
	check(actor.hit_confirmed.is_connected(game._confirmed_hit), "Authority actor confirmation connected to match transport")
	var before: Dictionary = actor.snapshot().duplicate(true)
	actor.hit_feedback_remaining = 0.0
	game._hit_feedback_rpc(actor.actor_id, true, true)
	check(actor.hit_feedback_remaining == 0, "Authority refuses incoming client-style feedback")
	game._authority = false
	game._hit_feedback_rpc(actor.actor_id + 1, true, true)
	check(actor.hit_feedback_remaining == 0, "Recipient refuses another operator's feedback")
	game._hit_feedback_rpc(actor.actor_id, true, false)
	check(actor.hit_feedback_remaining > 0 and actor.hit_feedback_headshot and not actor.hit_feedback_lethal, "Confirmed local headshot shows nonlethal feedback")
	game._hit_feedback_rpc(actor.actor_id, false, true)
	check(actor.hit_feedback_lethal and not actor.hit_feedback_headshot, "Confirmed elimination has explicit feedback")
	var after: Dictionary = actor.snapshot()
	check(before.health == after.health and before.ammo == after.ammo and before.credits == after.credits and before.kills == after.kills, "Feedback cannot mutate gameplay or wallet state")
	actor.tick_visual(0.2)
	check(actor.hit_feedback_remaining == 0, "Feedback clears within bounded visual duration")
	game._impact_rpc(Vector3.INF, Vector3.UP, false)
	game._impact_rpc(Vector3.ZERO, Vector3.ZERO, false)
	game._impact_rpc(Vector3(999, 0, 0), Vector3.UP, false)
	check(game.get_node_or_null("CombatEffects") == null, "Malformed/out-of-bounds impact events cannot allocate effects")
	game._impact_rpc(Vector3.ZERO, Vector3.UP, false)
	var effects = game.get_node_or_null("CombatEffects")
	check(effects != null and effects._pools.sparks.slots.size() == 40, "Valid server impact uses fixed-capacity client visual pool")
	check(actor.snapshot().health == before.health and actor.snapshot().ammo == before.ammo, "Network effects cannot apply damage or consume ammunition")
	game.queue_free()
	await process_frame
	await process_frame
	print("HIT_FEEDBACK_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
