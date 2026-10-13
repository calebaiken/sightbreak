extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)
func _initialize() -> void: _run.call_deferred()
func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var actor := SBActor.new()
	actor.configure(1, 1, "history", false)
	world.add_child(actor)
	actor.reset_for_round(Vector3(0, 0, 6))
	await physics_frame
	var history := SBHitHistory.new()
	var actors := {1: actor}
	check(history.record(100, 1, actors), "first frame recorded")
	check(not history.record(100, 1, actors), "duplicate frame rejected")
	for stance in [false, true]:
		actor._body.scale.y = 0.72 if stance else 1.0
		actor._collision.shape.height = 1.25 if stance else 1.8
		actor._collision.position.y = actor._collision.shape.height * 0.5
		var tick := 101 if not stance else 102
		history.record(tick, 1, actors)
		for y in range(1, 185, 3):
			for x in [-0.4, -0.2, 0.0, 0.2, 0.4]:
				var origin := Vector3(x, float(y) / 100.0, 0)
				var live := actor.volume_intersection(origin, Vector3.BACK, 20)
				var old := history.trace(tick, 1, origin, Vector3.BACK, 20, 0)
				check(live.is_empty() == old.is_empty() and (live.is_empty() or (live.headshot == old.headshot and absf(float(live.distance) - float(old.distance)) < 0.00001)), "historical volume equals live standing/crouched volume")
	actor.global_position.x = 1.0
	history.record(103, 1, actors)
	check(not history.trace(102, 1, Vector3(0, 0.5, 0), Vector3.BACK, 20, 0).is_empty(), "moving target historical hit")
	check(history.trace(103, 1, Vector3(0, 0.5, 0), Vector3.BACK, 20, 0).is_empty(), "current target misses previous line")
	check(history.trace(102, 1, Vector3(0, 0.5, 0), Vector3.BACK, 4, 0).is_empty(), "current world obstruction bounds rewind")
	check(history.trace(102, 1, Vector3(0, 0.5, 0), Vector3.BACK, 20, 1).is_empty(), "shooter excluded")
	check(history.trace(104, 1, Vector3.ZERO, Vector3.BACK, 20, 0).is_empty(), "future rejected")
	check(history.trace(102, 2, Vector3.ZERO, Vector3.BACK, 20, 0).is_empty(), "wrong epoch rejected")
	actor.team = 0
	history.record(104, 1, actors)
	check(history.trace(102, 1, Vector3(0, 0.5, 0), Vector3.BACK, 20, 0).is_empty(), "team switch invalidates history")
	actor.global_position.x = 10
	history.record(105, 1, actors)
	check(history.trace(104, 1, Vector3(1, 0.5, 0), Vector3.BACK, 20, 0).is_empty(), "teleport invalidates history")
	actor.alive = false
	history.record(106, 1, actors)
	check(history.trace(105, 1, Vector3(10, 0.5, 0), Vector3.BACK, 20, 0).is_empty(), "dead target cannot be hit again")
	for tick in range(107, 140): history.record(tick, 1, actors)
	check(history.frames.size() == SBHitHistory.MAX_FRAMES, "history storage bounded")
	check(history.trace(100, 1, Vector3.ZERO, Vector3.BACK, 20, 0).is_empty(), "expired history rejected")
	check(SBHitHistory.target_tick(100, 0) == 94, "configured render delay counted")
	check(SBHitHistory.target_tick(100, 200) == 88, "rewind capped at 200ms")
	check(SBHitHistory.target_tick(100, 1500) == 88, "high RTT cannot exceed cap")
	check(SBHitHistory.target_tick(100, NAN) == -1 and SBHitHistory.target_tick(100, -1) == -1 and SBHitHistory.target_tick(100, 3000) == -1, "unreasonable timing rejected")
	history.record(140, 2, actors)
	check(history.frames.size() == 1 and not history.record(141, 1, actors), "reset clears old epoch and rejects regressions")
	world.queue_free()
	await process_frame
	print("HIT_HISTORY_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
