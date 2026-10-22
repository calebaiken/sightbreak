extends SceneTree
## Independent synthetic authority checks. The RPC result is evaluated separately.
class IsolatedMatch extends TacticalMatch:
	func _ready() -> void:
		set_physics_process(false)
		set_process(false)
	func _objective_tick(_delta: float) -> void: pass
	func _check_elimination() -> void: pass
	func _is_bot(_id: int) -> bool: return false

var games: Array[IsolatedMatch] = []
var observations: Array[Dictionary] = []
var failures := 0

func setup() -> IsolatedMatch:
	var game := IsolatedMatch.new()
	game.phase = "live"
	game.local_id = 0
	game._elapsed = 100
	game.time_left = 10000
	game._snapshot_generation = 1
	game._ranked_started = true
	game._ranked_eligible = true
	root.add_child(game)
	var actor := SBActor.new()
	actor.configure(1, 0, "Independent provenance fixture", false)
	game.add_child(actor)
	actor.position = Vector3(100 + games.size() * 10, 100, 0)
	actor.input_state = {"look": Vector2.ZERO, "move": Vector2.ZERO}
	actor._deploy_remaining = 0
	actor.shot_fired.connect(game._shot)
	game.actors[1] = actor
	game._peer_actors[99] = 1
	game._last_peer_input[1] = game._elapsed
	games.append(game)
	return game

func cmd(sequence: int, yaw := 0.0, pitch := 0.0) -> Dictionary:
	return {"sequence": sequence, "look": Vector2(yaw, pitch), "move": Vector2.ZERO}

func accept(game: IsolatedMatch, commands: Array, epoch := 1, peer := 99) -> bool:
	return game._input_stream.accept(peer, {"epoch": epoch, "commands": commands}, game._snapshot_generation, int(game._elapsed * 1000))

func tick(game: IsolatedMatch) -> void:
	game._elapsed += 1.0 / 60
	game._authority_tick(1.0 / 60)

func record(label: String, game: IsolatedMatch, ok: bool) -> void:
	var actor: SBActor = game.actors[1]
	observations.append({"label": label, "pass": ok, "elapsed": game._elapsed, "last_activity": game._last_activity.get(1, -100), "active_seconds": game._activity_seconds.get(1, 0), "yaw": actor.yaw, "pitch": actor.pitch, "input_look": str(actor.input_state.get("look")), "ack": game._last_input_sequence.get(1, 0), "queued": str(game._input_stream.queues), "rejected": game._input_stream.rejected, "skipped": game._input_stream.skipped_commands, "ranked_eligible": game._ranked_eligible})
	if not ok: failures += 1

func _initialize() -> void: call_deferred("run")

func run() -> void:
	var immutable := setup()
	accept(immutable, [cmd(1, 0.08)])
	accept(immutable, [cmd(1)])
	record("queued actual aim grants no time before consumption", immutable, not immutable._last_activity.has(1))
	tick(immutable)
	record("later neutral duplicate cannot erase immutable actual aim", immutable, is_equal_approx(immutable.actors[1].yaw, 0.08) and immutable._last_activity[1] == immutable._elapsed)
	var last: float = immutable._last_activity[1]
	accept(immutable, [cmd(2, 0.08), cmd(1, -1.0)])
	tick(immutable)
	record("discarded stale opposite aim cannot renew unchanged consumed look", immutable, immutable._last_activity[1] == last and is_equal_approx(immutable.actors[1].yaw, 0.08))
	accept(immutable, [cmd(3), cmd(1, 0.08)])
	tick(immutable)
	record("return to zero remains real consumed aim after nonzero look", immutable, immutable._last_activity[1] == immutable._elapsed and immutable.actors[1].yaw == 0)
	var ordered := setup()
	accept(ordered, [cmd(2, 0.08)])
	accept(ordered, [cmd(1)])
	tick(ordered)
	record("earlier neutral consumed before queued actual aim", ordered, not ordered._last_activity.has(1) and ordered._last_input_sequence[1] == 1)
	tick(ordered)
	record("queued actual aim qualifies on its consumption step", ordered, ordered._last_activity[1] == ordered._elapsed and is_equal_approx(ordered.actors[1].yaw, 0.08))
	var duplicate := setup()
	accept(duplicate, [cmd(1, 0.04), cmd(1, 0.08)])
	tick(duplicate)
	record("same-packet last duplicate retains existing stream semantics", duplicate, duplicate._last_activity[1] == duplicate._elapsed and is_equal_approx(duplicate.actors[1].yaw, 0.08))
	var epoch := setup()
	accept(epoch, [cmd(1, 0.08)])
	epoch._input_stream.reset_epoch()
	epoch._snapshot_generation = 2
	var rejected := not accept(epoch, [cmd(2, 0.16)])
	accept(epoch, [cmd(1)], 2)
	tick(epoch)
	record("old epoch queued aim and replay erased before current neutral", epoch, rejected and not epoch._last_activity.has(1) and epoch.actors[1].yaw == 0)
	var invalid := setup()
	var invalid_rejected := not accept(invalid, [cmd(1), cmd(2, NAN)])
	tick(invalid)
	record("malformed tail rejects whole staged packet without activity", invalid, invalid_rejected and not invalid._last_activity.has(1) and invalid._input_stream.queues.is_empty())
	var backlog := setup()
	var batch: Array = []
	for sequence in range(1, 13): batch.append(cmd(sequence, 0.08 if sequence < 11 else 0.0))
	accept(backlog, batch)
	tick(backlog)
	tick(backlog)
	record("discarded ten-command aim backlog never grants activity", backlog, not backlog._last_activity.has(1) and backlog._input_stream.skipped_commands == 10 and backlog._last_input_sequence[1] == 12)
	var rebound := setup()
	accept(rebound, [cmd(1, 0.08)])
	rebound._peer_disconnected(99)
	rebound._peer_actors[100] = 1
	accept(rebound, [cmd(1)], 1, 100)
	tick(rebound)
	record("disconnect forgets queued aim and new peer neutral stays idle", rebound, not rebound._last_activity.has(1) and not rebound._input_stream.queues.has(99) and rebound.actors[1].yaw == 0 and not rebound._ranked_eligible)
	var normalized := setup()
	accept(normalized, [cmd(1, 0.08, 50.0)])
	tick(normalized)
	record("finite raw pitch is clamped before consumed activity", normalized, is_equal_approx(normalized.actors[1].pitch, 1.42) and normalized._last_activity[1] == normalized._elapsed)
	last = normalized._last_activity[1]
	accept(normalized, [cmd(2, TAU + 0.08, 100.0)])
	tick(normalized)
	record("wrapped equivalent yaw and clamped pitch do not renew", normalized, normalized._last_activity[1] == last and is_equal_approx(normalized.actors[1].yaw, 0.08))
	accept(normalized, [cmd(3, TAU + 0.09, 100.0)])
	tick(normalized)
	record("actual finite aim after normalization continues to qualify", normalized, normalized._last_activity[1] == normalized._elapsed and is_equal_approx(normalized.actors[1].yaw, 0.09))
	for state in ["waiting", "buy", "post", "dead"]:
		var game := setup()
		if state == "dead": game.actors[1].alive = false
		else: game.phase = state
		accept(game, [cmd(1, 0.08)])
		tick(game)
		record("consumed aim preserves existing " + state + " activity eligibility", game, game._last_activity.get(1) == game._elapsed)
	var output := ""
	for arg: String in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	var file := FileAccess.open(output, FileAccess.WRITE)
	file.store_string(JSON.stringify({"fixture": "independent synthetic authority state; not account play", "observations": observations, "failures": failures}, "  "))
	file.close()
	for game in games: game.queue_free()
	await process_frame
	await create_timer(0.7).timeout
	print("INDEPENDENT_ACTIVITY_PROVENANCE failures=%d" % failures)
	quit(1 if failures else 0)
