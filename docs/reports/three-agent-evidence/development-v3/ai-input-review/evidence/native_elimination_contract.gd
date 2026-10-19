extends SceneTree

# Exactly the dictionary overload used by frozen V2 TacticalMatch._eliminated.
# No actor aliases are introduced; all three actors are the shipped SBActor.
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var victim := SBActor.new()
	victim.configure(6, 1, "Victim")
	root.add_child(victim)
	victim.reset_for_round(Vector3(-14, 0.05, 2))
	victim.alive = false
	var ally := SBActor.new()
	ally.configure(7, 1, "LivingAlly")
	root.add_child(ally)
	ally.reset_for_round(Vector3(-14, 0.05, 4))
	var killer := SBActor.new()
	killer.configure(1, 0, "Killer")
	root.add_child(killer)
	killer.reset_for_round(Vector3(-14, 0.05, -10))
	var actors: Dictionary = {6: victim, 7: ally, 1: killer}
	var states: Dictionary = {6: SBBotAI.create_state(victim), 7: SBBotAI.create_state(ally), 1: SBBotAI.create_state(killer)}
	var team_state: Dictionary = SBBotAI.create_team_state()
	print("NATIVE_ELIMINATION_BEGIN exact_v2_dictionary_callback")
	SBBotAI.record_elimination(team_state, states, actors, 6, 100.0)
	print("NATIVE_ELIMINATION ", JSON.stringify({"ally_heard_at": states[7].heard_at, "ally_alert_recorded": states[7].heard_at == 100.0, "team_state": team_state}))
	victim.queue_free()
	ally.queue_free()
	killer.queue_free()
	await process_frame
	await process_frame
	print("NATIVE_ELIMINATION_COMPLETE errors_in_stderr_are_failures_not_a_pass")
	quit(0)
