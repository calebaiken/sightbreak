extends "res://tests/hud_objective_hint_test.gd"
## Read-only critic fixture. Inherits private user-directory ownership and cleanup.
## All actors and snapshots below are declared controls; no gameplay tick runs.

func control(value: bool, label: String, main: Node, game: Node) -> void:
	check(value, "independent: " + label)
	print("INDEPENDENT_PRIORITY_CONTROL " + JSON.stringify({"label": label, "correct": value, "connection": game.connection_state, "notice": game.connection_notice, "status": main.status_label.text, "epoch": game._replica_buffer.epoch, "tick": game._simulation_tick}))

func fixture_snapshot(game: Node, actor: Node, epoch: int, team: int, alive: bool, objective: String, phase: String = "live") -> Dictionary:
	var data: Dictionary = game._snapshot()
	data.epoch = epoch
	data.tick = epoch
	data.elapsed = 0.0
	data.phase = phase
	data.objective = objective
	data.carrier = actor.actor_id
	for state: Dictionary in data.actors:
		if int(state.id) == actor.actor_id:
			state.team = team
			state.alive = alive
			state.health = 100.0 if alive else 0.0
	return data

func notification_priority_benchmark(main: Node, game: Node, actor: Node, touch_enabled: bool) -> void:
	super.notification_priority_benchmark(main, game, actor, touch_enabled)
	game.phase = "live"
	game.objective_state = "planted"
	actor.team = 0
	actor.alive = true
	actor.health = 100
	game._authority = false
	game.connection_state = "connected"
	game.connection_notice = ""
	game.reconnect_token = ""
	game._recovery.clear()
	game._server_disconnected()
	var disconnect_reason: String = game.connection_notice
	main.elapsed = 4000.0
	game._notice_rpc("Version mismatch: this is an ordinary freeform match notice")
	main._process(0.0)
	control(not disconnect_reason.is_empty() and main.status_label.text == disconnect_reason and game.connection_state == "reconnecting", "actual disconnect callback retains typed reason after critical-looking ordinary text touch=%s" % touch_enabled, main, game)
	game._server_disconnected()
	main.elapsed += 20.0
	game._notice_rpc("Echo > Rook")
	main._process(0.0)
	control(main.status_label.text == disconnect_reason, "duplicate disconnect and late ordinary text preserve reason beyond five seconds touch=%s" % touch_enabled, main, game)
	game._rejected_rpc("QA terminal admission reason with a player named Connected")
	var terminal_reason: String = game.connection_notice
	game._connection_failed()
	game._server_disconnected()
	main.elapsed += 20.0
	game._notice_rpc("Relay device armed — defend the site")
	main._process(0.0)
	control(game.connection_state == "failed" and game._recovery.deadline == 0 and main.status_label.text == terminal_reason, "actual terminal callback survives late transport callbacks and ordinary combat touch=%s" % touch_enabled, main, game)
	game._replica_buffer.clear()
	var initial := fixture_snapshot(game, actor, 10, 0, true, "planted")
	game._welcome_rpc(actor.actor_id, "", initial)
	main._process(0.0)
	control(game.connection_state == "connected" and game.connection_notice.is_empty() and main.status_label.text == "DEFEND THE DEVICE", "actual welcome clears terminal presentation and displays accepted snapshot role touch=%s" % touch_enabled, main, game)
	var defender := fixture_snapshot(game, actor, 11, 1, true, "planted")
	game._apply_snapshot(defender)
	game._notice_rpc("Sable > Slate")
	main._process(0.0)
	var defuse := "HOLD %s NEAR THE DEVICE TO DEFUSE" % ("USE" if touch_enabled else "E")
	control(main.status_label.text == defuse and actor.team == 1, "new snapshot epoch immediately selects living defender role under combat touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(initial)
	main._process(0.0)
	control(game._replica_buffer.epoch == 11 and main.status_label.text == defuse and actor.team == 1, "stale attacker epoch cannot restore attacker role touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(fixture_snapshot(game, actor, 12, 0, false, "planted"))
	game._notice_rpc("Ember > Operator")
	main._process(0.0)
	control(not actor.alive and main.status_label.text == "SPECTATING YOUR SQUAD", "new death epoch removes attacker guidance under combat touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(initial)
	main._process(0.0)
	control(not actor.alive and main.status_label.text == "SPECTATING YOUR SQUAD", "stale living epoch cannot revive attacker guidance touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(fixture_snapshot(game, actor, 13, 0, true, "carried"))
	game._notice_rpc("QA isolated unplanted notice")
	main._process(0.0)
	control(main.status_label.text == "QA isolated unplanted notice", "new unplanted epoch preserves ordinary isolated notice touch=%s" % touch_enabled, main, game)
	main.elapsed += 5.001
	main._process(0.0)
	control(main.status_label.text == "HOLD %s AT A SITE TO PLANT" % ("USE" if touch_enabled else "E"), "unplanted notice expires under original five-second policy touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(fixture_snapshot(game, actor, 14, 0, true, "dropped"))
	main._process(0.0)
	control(main.status_label.text == "RECOVER THE RELAY DEVICE", "accepted dropped-device epoch restores recovery role touch=%s" % touch_enabled, main, game)
	game._apply_snapshot(fixture_snapshot(game, actor, 15, 0, true, "planted", "post"))
	main._process(0.0)
	control(main.status_label.text == "ROUND COMPLETE", "accepted post-round epoch removes live planted role touch=%s" % touch_enabled, main, game)
	game._authority = true
	game._replica_buffer.clear()
	game._pending_reconciliation.clear()
	game._recovery.clear()
	game.connection_state = "offline"
	game.connection_notice = ""
	game._elapsed = 0.0
	actor.team = 0
	actor.alive = true
	actor.health = 100
