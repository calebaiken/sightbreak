extends SceneTree

class PerceptionActor extends SBActor:
	var visible_enemy: bool = true
	func can_see(_other: SBActor) -> bool:
		return visible_enemy

var checks: int = 0
var failures: int = 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, description: String) -> void:
	checks += 1
	if not condition:
		failures += 1
		push_error("FAIL: " + description)

func _run() -> void:
	var match_node := TacticalMatch.new()
	match_node.configure({"mode": "offline", "name": "QA"})
	root.add_child(match_node)
	match_node.set_physics_process(false)
	await physics_frame
	check(match_node.actors.size() == 10, "5v5 roster")
	check(match_node.local_actor() != null, "local controllable actor")
	check(match_node.phase == "buy" and match_node.round_number == 1, "initial preparation")
	check(match_node.objective_carrier == 1, "local attacker carries objective")
	match_node.phase = "live"
	match_node.local_actor().position = match_node.arena.sites[0]
	match_node.local_actor().input_state = {"interact": true}
	match_node._objective_tick(1.0)
	check(match_node.interaction_progress > 0 and match_node.objective_state == "carried", "plant requires hold")
	match_node.local_actor().input_state = {"interact": false}
	match_node._objective_tick(0.1)
	check(match_node.interaction_progress == 0, "released hold resets planting")
	match_node.local_actor().input_state = {"interact": true}
	match_node._objective_tick(3.1)
	check(match_node.objective_state == "planted", "plant succeeds at site")
	check(match_node.objective_timer == TacticalMatch.DEVICE_SECONDS, "device countdown starts")
	check(int(match_node.objective_contributions[1]) == 1, "plant records objective contribution")
	var defender: SBActor = match_node.actors[6]
	defender.position = match_node.objective_position
	defender.input_state = {"interact": true}
	match_node._objective_tick(5.1)
	check(match_node.objective_state == "defused" and match_node.defend_score == 1, "defuse awards defender win")
	check(match_node.phase == "post", "round transition")
	check(int(match_node.objective_contributions[6]) == 1, "defuse records objective contribution")
	match_node._begin_round()
	match_node.phase = "live"
	match_node.local_actor().position = match_node.arena.sites[1]
	match_node.local_actor().input_state = {"interact": true}
	match_node._objective_tick(3.1)
	match_node._objective_tick(35.1)
	check(match_node.attack_score == 1 and match_node.phase == "post", "detonation awards attacker win")
	match_node._begin_round()
	match_node.phase = "live"
	for actor: SBActor in match_node.actors.values():
		if actor.team == 0:
			actor.alive = false
	match_node._check_elimination()
	check(match_node.defend_score == 2, "elimination wins unplanted round")
	match_node.round_number = 6
	var old_team: int = match_node.local_actor().team
	match_node._begin_round()
	check(match_node.local_actor().team != old_team and match_node.round_number == 7, "halftime swaps sides")
	check(int(match_node.objective_contributions[1]) == 2, "objective contributions persist through halftime")
	check(match_node.attack_score == 2 and match_node.defend_score == 1, "scores follow squads at halftime")
	match_node.phase = "live"
	match_node.attack_score = 6
	var reports: Array = []
	match_node.match_finished.connect(func(report: Dictionary) -> void: reports.append(report))
	match_node.local_actor().deaths = 3
	match_node._end_round(0, "QA")
	check(match_node.phase == "match_over" and reports.size() == 1, "seventh win finishes match once")
	check(int(reports[0].deaths) == 3 and int(reports[0].objectives) == 2, "result reports deaths and objective contributions")
	match_node._emit_results()
	check(reports.size() == 1, "result publication is idempotent")
	var gate := SBInputGate.new()
	var valid: Dictionary = gate.validate(2, {"move": Vector2(100, 100), "look": Vector2(90, 90)}, 100)
	check(valid.move.length() <= 1.001 and absf(valid.look.y) <= 1.451, "server clamps movement and pitch")
	check(gate.validate(2, {"move": Vector2.ZERO, "look": Vector2.ZERO}, 101).is_empty(), "input flood rejected")
	check(gate.validate(2, {"move": Vector2(NAN, 0), "look": Vector2.ZERO}, 120).is_empty(), "NaN movement rejected")
	check(gate.validate(2, {"move": "teleport", "look": Vector2.ZERO}, 140).is_empty(), "malformed input rejected")
	check(gate.allow_buy(2, 500) and not gate.allow_buy(2, 501), "buy command rate bounded")
	# A complete seven-round squad sweep must survive the halftime side switch.
	var complete := TacticalMatch.new()
	complete.configure({"mode": "offline", "name": "Full match QA"})
	root.add_child(complete)
	complete.set_physics_process(false)
	var complete_reports: Array = []
	complete.match_finished.connect(func(report: Dictionary) -> void: complete_reports.append(report))
	for number in range(1, 8):
		check(complete.round_number == number, "full match advances round %d" % number)
		complete.phase = "live"
		complete._end_round(complete.local_actor().team, "QA squad win")
		if number < 7:
			check(complete.phase == "post", "match continues before seventh squad win")
			complete._begin_round()
	check(complete.phase == "match_over" and complete.attack_score == 0 and complete.defend_score == 7, "full sweep preserves squad score after halftime")
	check(complete_reports.size() == 1 and bool(complete_reports[0].won), "local result recognizes halftime squad winner")
	# Results arriving through client snapshots carry the same stats and emit only once.
	var replica := TacticalMatch.new()
	replica.configure({"mode": "offline"})
	root.add_child(replica)
	replica.set_physics_process(false)
	replica._authority = false
	var replica_reports: Array = []
	replica.match_finished.connect(func(report: Dictionary) -> void: replica_reports.append(report))
	complete.local_actor().deaths = 2
	complete.objective_contributions[1] = 4
	replica._apply_snapshot(complete._snapshot())
	replica._apply_snapshot(complete._snapshot())
	check(replica_reports.size() == 1 and int(replica_reports[0].deaths) == 2 and int(replica_reports[0].objectives) == 4, "client final snapshot produces complete single result")
	# Alternating squad wins must produce a 6–6 draw at regulation end.
	var draw_match := TacticalMatch.new()
	draw_match.configure({"mode": "offline"})
	root.add_child(draw_match)
	draw_match.set_physics_process(false)
	var draw_reports: Array = []
	draw_match.match_finished.connect(func(report: Dictionary) -> void: draw_reports.append(report))
	for number in range(1, 13):
		draw_match.phase = "live"
		var winning_side: int = draw_match.local_actor().team if number % 2 == 1 else 1 - draw_match.local_actor().team
		draw_match._end_round(winning_side, "Draw QA")
		if number < 12:
			draw_match._begin_round()
	check(draw_match.round_number == 12 and draw_match.attack_score == 6 and draw_match.defend_score == 6, "regulation draw reaches twelve rounds")
	check(draw_reports.size() == 1 and bool(draw_reports[0].draw) and not bool(draw_reports[0].won), "draw result is explicit")
	# These are reward-policy fixtures, not a claim of a played ranked match.
	complete._ranked_eligible = true
	complete._elapsed = 400
	complete._match_started_elapsed = 0
	complete._match_id = "fixture"
	for id: int in complete.actors:
		complete._account_ids[id] = "account-%d" % id
		complete._peer_actors[id + 100] = id
		complete._activity_seconds[id] = 350
	var reward_payload: Dictionary = complete._ranked_payload()
	check(reward_payload.participants.size() == 10, "eligible payload contains ten authenticated participants")
	var winners: int = 0
	for participant: Dictionary in reward_payload.participants:
		if participant.won:
			winners += 1
	check(winners == 5, "authoritative results identify five squad winners")
	complete._activity_seconds[1] = 100
	check(complete._ranked_payload().is_empty(), "low activity prevents online reward submission")
	complete._activity_seconds[1] = 350
	complete._ranked_eligible = false
	check(complete._ranked_payload().is_empty(), "bot replacement permanently disqualifies account match")
	complete._account_ids[77] = "expired-account"
	complete._reservations["expired"] = {"id": 77, "expires": 1.0}
	complete._expire_reservations()
	check(not complete._account_ids.has(77), "expired reservation releases stale account identity")
	check(SBEconomyBridge.valid_origin("http://127.0.0.1:8080") and SBEconomyBridge.valid_origin("https://economy.example.org"), "bridge accepts local HTTP and authenticated HTTPS origins")
	for dangerous: String in ["http://127.0.0.1:8080@public.example", "http://public.example", "https://safe.example@evil.example", "https://safe.example?key=1", "https://safe.example#fragment", "http://localhost:99999"]:
		check(not SBEconomyBridge.valid_origin(dangerous), "bridge rejects ambiguous or insecure origin " + dangerous)
	var bridge := SBEconomyBridge.new()
	var request: HTTPRequest = bridge.make_request()
	check(request.max_redirects == 0 and request.body_size_limit == 65536, "privileged HTTP never follows redirects and bounds replies")
	# Server lifecycle reset is exercised without binding sockets in this rule test.
	complete._peer_actors.clear()
	complete.options.mode = "server"
	complete.options.require_accounts = true
	complete.reward_status = "committed"
	complete._reset_server_match()
	check(complete.phase == "waiting" and complete.round_number == 0 and complete._account_ids.is_empty() and complete._reservations.is_empty(), "account server returns to clean waiting lobby")
	check(complete.actors.size() == 10 and complete.attack_score == 0 and complete.local_actor() == null, "lobby reset recreates ten fresh server actors")
	complete.options.require_accounts = false
	complete._reset_server_match()
	check(complete.phase == "buy" and complete.round_number == 1 and complete.reward_status == "unranked", "guest server starts fresh bot match")
	complete.objective_state = "dropped"
	complete.phase = "live"
	complete.objective_position = Vector3(3, 0, 4)
	complete._update_device_visual(0.1)
	check(complete._device.visible and complete._device.position == complete.objective_position, "dropped objective has a visible world device")
	# Bot perception is per round, preventing immediate inherited locks after respawn.
	complete._bot_state[6].target = 1
	complete._bot_state[6].reaction = 3.0
	complete._bot_state[6].seen_at = complete._elapsed
	complete._begin_round()
	check(complete._bot_state[6].target == 0 and complete._bot_state[6].reaction == 0 and complete._bot_state[6].seen_at == -100.0, "round reset clears bot target and memory")
	complete.phase = "live"
	complete.objective_state = "planted"
	complete.objective_position = Vector3(15, 0, 10)
	for actor: SBActor in complete.actors.values():
		actor.alive = actor.team == 1
		actor.input_state.clear()
		actor.position = complete.objective_position + Vector3(actor.actor_id - 5, 0, 0)
	var defuser_id: int = complete._nearest_defender()
	check(defuser_id != 0, "planted objective chooses a living defender")
	for actor: SBActor in complete.actors.values():
		complete._bot_input(actor, 0.12)
	var interacting: int = 0
	for actor: SBActor in complete.actors.values():
		if bool(actor.input_state.get("interact", false)):
			interacting += 1
	check(interacting == 1, "only nearest bot defuses while teammates cover")
	complete.actors[defuser_id].alive = false
	check(complete._nearest_defender() != defuser_id, "another living bot replaces fallen defuser")
	complete.local_id = 7
	complete.actors[7].alive = true
	complete.actors[7].position = complete.objective_position
	complete.actors[7].input_state = {"interact": true}
	check(complete._nearest_defender() == 7, "human holding interaction has defuse priority")
	complete.local_id = 0
	complete.objective_state = "carried"
	var reloader: SBActor = complete.actors[7]
	reloader.ammo = 1
	complete._bot_input(reloader, 0.12)
	check(bool(reloader.input_state.reload) and not bool(reloader.input_state.fire), "safe bot tops up depleted magazine without firing at unseen foes")
	# Exercise timer-driven transitions, including the post-round window and final freeze.
	var timed := TacticalMatch.new()
	timed.configure({"mode": "offline"})
	root.add_child(timed)
	timed.set_physics_process(false)
	timed.time_left = 0.001
	timed._authority_tick(0.01)
	check(timed.phase == "live" and timed.time_left == TacticalMatch.ROUND_SECONDS, "buy timer opens live play")
	timed.time_left = 0.001
	timed._authority_tick(0.01)
	check(timed.phase == "post" and timed.defend_score == 1, "unplanted round timer awards defense")
	timed.time_left = 0.001
	timed._authority_tick(0.01)
	check(timed.phase == "buy" and timed.round_number == 2, "post timer starts fresh round")
	timed.phase = "live"
	timed.objective_state = "planted"
	timed.objective_timer = 1.0
	timed.time_left = 0.001
	timed._authority_tick(0.01)
	check(timed.phase == "live" and timed.objective_timer > 0, "planted objective outlives round timer")
	timed.objective_timer = 0.001
	timed._authority_tick(0.01)
	check(timed.phase == "post" and timed.attack_score == 1, "device timer finishes planted round")
	timed.phase = "live"
	timed.attack_score = 6
	timed._end_round(0, "Timer QA finish")
	timed._authority_tick(10.0)
	check(timed.phase == "match_over" and timed.attack_score == 7, "completed offline match never auto-restarts")
	# Deterministic perception fixture isolates aim policy from map ray geometry.
	var old_bot: SBActor = timed.actors[6]
	var aiming_bot := PerceptionActor.new()
	aiming_bot.configure(6, 1, "Aim fixture", false)
	timed.add_child(aiming_bot)
	timed.actors[6] = aiming_bot
	old_bot.queue_free()
	timed.phase = "live"
	timed.objective_state = "carried"
	for actor: SBActor in timed.actors.values():
		actor.alive = actor.actor_id == 1 or actor.actor_id == 6
	aiming_bot.position = Vector3.ZERO
	aiming_bot.yaw = 0
	timed.actors[1].position = Vector3(5, 0, 0)
	timed._bot_state[6].target = 1
	timed._bot_state[6].reaction = 1.0
	timed._bot_input(aiming_bot, 0.12)
	check(not bool(aiming_bot.input_state.fire) and absf(aiming_bot.input_state.look.x) <= 0.61, "bot turn rate and alignment prevent snap shooting")
	aiming_bot.yaw = -PI / 2
	timed._bot_input(aiming_bot, 0.12)
	check(bool(aiming_bot.input_state.fire), "aligned visible enemy permits fire after reaction time")
	var last_visible: Vector3 = timed._bot_state[6].last_seen
	aiming_bot.visible_enemy = false
	timed.actors[1].position = Vector3(20, 0, 10)
	timed._bot_input(aiming_bot, 0.12)
	check(not bool(aiming_bot.input_state.fire) and timed._bot_state[6].last_seen == last_visible, "occluded enemy cannot be tracked or shot through geometry")
	timed.queue_free()
	request.free()
	bridge.free()
	draw_match.queue_free()
	complete.queue_free()
	replica.queue_free()
	print("MATCH_TEST: %d/%d passed" % [checks - failures, checks])
	match_node.queue_free()
	await process_frame
	quit(1 if failures else 0)
