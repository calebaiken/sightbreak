extends SceneTree
## Synthetic rule fixtures, separate from the actual RPC pair and account play.
class RuleMatch extends TacticalMatch:
	func _ready() -> void:
		set_physics_process(false)
		set_process(false)
	func _objective_tick(_delta: float) -> void: pass
	func _check_elimination() -> void: pass
	func _is_bot(_id: int) -> bool: return false

var checks := 0
var failures := 0
var games: Array[RuleMatch] = []

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func make_match() -> RuleMatch:
	var game := RuleMatch.new()
	game.phase = "live"
	game.time_left = 10000
	game.local_id = 0
	game._elapsed = 100
	game._snapshot_generation = 1
	game._ranked_started = true
	root.add_child(game)
	var actor := SBActor.new()
	actor.configure(1, 0, "Activity rule fixture", false)
	game.add_child(actor)
	actor.position = Vector3(100 + games.size() * 10, 100, 0)
	actor.input_state = {"move": Vector2.ZERO, "look": Vector2.ZERO}
	actor._deploy_remaining = 0
	actor.shot_fired.connect(game._shot)
	game.actors[1] = actor
	game._peer_actors[99] = 1
	game._last_peer_input[1] = 100
	games.append(game)
	return game

func command(sequence: int, look := Vector2.ZERO, move := Vector2.ZERO, interact := false) -> Dictionary:
	return {"sequence": sequence, "look": look, "move": move, "interact": interact}

func accept(game: RuleMatch, commands: Array, epoch := 1) -> bool:
	return game._input_stream.accept(99, {"epoch": epoch, "commands": commands}, game._snapshot_generation, int(game._elapsed * 1000))

func tick(game: RuleMatch, delta := 1.0 / 60.0) -> void:
	game._elapsed += delta
	game._authority_tick(delta)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var aim := make_match()
	check(accept(aim, [command(1, Vector2(0.08, 0))]), "real aim input accepted")
	check(not aim._last_activity.has(1), "unconsumed input cannot grant activity")
	tick(aim)
	check(aim._last_activity.get(1) == aim._elapsed and is_equal_approx(aim.actors[1].yaw, 0.08), "consumed real aim grants activity")
	check(is_equal_approx(aim._activity_seconds.get(1, 0), 1.0 / 60), "one authority step grants one delta")
	var last: float = aim._last_activity[1]
	check(accept(aim, [command(2, Vector2(0.081, 0))]), "subthreshold aim accepted")
	tick(aim)
	check(aim._last_activity[1] == last, "subthreshold look does not renew activity")
	var neutral := make_match()
	check(accept(neutral, [command(1)]), "neutral command accepted")
	tick(neutral)
	check(not neutral._last_activity.has(1) and neutral._activity_seconds.get(1, 0) == 0, "neutral consumption stays idle")
	check(accept(neutral, [command(2), command(1, Vector2(0.08, 0))]), "fresh neutral plus stale look accepted")
	tick(neutral)
	check(not neutral._last_activity.has(1) and neutral.actors[1].yaw == 0, "discarded stale look cannot count")
	check(accept(neutral, [command(3)]), "new immutable queued neutral accepted")
	check(accept(neutral, [command(3, Vector2(0.08, 0))]), "queued duplicate remains accepted")
	tick(neutral)
	check(not neutral._last_activity.has(1) and neutral.actors[1].yaw == 0, "mutated duplicate cannot count")
	var backlog: Array = []
	for sequence in range(4, 16):
		backlog.append(command(sequence, Vector2(0.08, 0) if sequence < 14 else Vector2.ZERO))
	check(accept(neutral, backlog), "bounded backlog accepted")
	tick(neutral)
	tick(neutral)
	check(not neutral._last_activity.has(1) and neutral._input_stream.skipped_commands == 10, "dropped backlog intent cannot count")
	check(not accept(neutral, [command(16, Vector2(0.08, 0))], 0), "old epoch rejected")
	check(not accept(neutral, [command(16, Vector2(NAN, 0))]), "nonfinite look rejected")
	tick(neutral)
	check(not neutral._last_activity.has(1), "rejected packets cannot grant activity")
	for state in ["buy", "post", "dead"]:
		var spectator := make_match()
		if state == "dead": spectator.actors[1].alive = false
		else: spectator.phase = state
		accept(spectator, [command(1, Vector2(0.08, 0))])
		tick(spectator)
		check(spectator._last_activity.get(1) == spectator._elapsed, "consumed %s aim retains input-activity policy" % state)
	var moving := make_match()
	moving.actors[1].velocity = Vector3(1, 0, 0)
	accept(moving, [command(1, Vector2.ZERO, Vector2.RIGHT)])
	tick(moving)
	check(moving._last_activity.get(1) == moving._elapsed, "consumed moving input retains observed-velocity activity")
	var hold := make_match()
	hold._interactions[1] = 0.5
	accept(hold, [command(1, Vector2.ZERO, Vector2.ZERO, true)])
	tick(hold)
	check(hold._last_activity.get(1) == hold._elapsed, "existing stationary objective hold remains activity")
	var idle_hold := make_match()
	accept(idle_hold, [command(1, Vector2.ZERO, Vector2.ZERO, true)])
	tick(idle_hold)
	check(not idle_hold._last_activity.has(1), "ineffective interact request alone cannot count")
	var shot := make_match()
	var firing := command(1)
	firing.fire = true
	accept(shot, [firing])
	tick(shot)
	check(shot._last_activity.get(1) == shot._elapsed and shot.actors[1].ammo == 14, "real emitted shot retains activity")
	var dry := make_match()
	dry.actors[1].ammo = 0
	accept(dry, [firing])
	tick(dry)
	check(not dry._last_activity.has(1), "dry fire request alone cannot count")
	var window := make_match()
	window._last_activity[1] = 90.0
	window._authority_tick(0.25)
	check(window._activity_seconds.get(1, 0) == 0.25, "ten-second boundary remains inclusive")
	window._elapsed = 100.001
	window._authority_tick(0.25)
	check(window._activity_seconds.get(1, 0) == 0.25, "activity window expires after ten seconds")
	window.phase = "match_over"
	window._last_activity[1] = window._elapsed
	window._authority_tick(0.25)
	check(window._activity_seconds.get(1, 0) == 0.25, "terminal phase grants no activity")
	var epoch := make_match()
	accept(epoch, [command(1)])
	tick(epoch)
	epoch._input_stream.reset_epoch()
	epoch._snapshot_generation = 2
	check(not accept(epoch, [command(2, Vector2(0.08, 0))]), "prior-epoch queued look rejected")
	check(accept(epoch, [command(1, Vector2(0.08, 0))], 2), "new epoch aim accepted")
	tick(epoch)
	check(epoch._last_activity.get(1) == epoch._elapsed, "new epoch consumption renews activity")
	for game in games: game.queue_free()
	await process_frame
	await create_timer(0.7).timeout
	print("ACTIVITY_PROVENANCE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
