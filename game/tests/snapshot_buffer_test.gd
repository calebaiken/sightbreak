extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func pose(x: float, yaw: float = 0, relevant: bool = true) -> Array:
	return [{"id": 1, "position": Vector3(x, 0, 0), "velocity": Vector3(2, 0, 0), "yaw": yaw, "pitch": 0.0, "relevant": relevant}]
func _initialize() -> void:
	var buffer := SBSnapshotBuffer.new()
	check(buffer.sample(1).is_empty(), "empty buffer")
	check(buffer.push(1, 0.0, 1, pose(0)), "first snapshot")
	buffer.push(4, 0.05, 1, pose(0.1))
	buffer.advance(0.05)
	buffer.push(7, 0.10, 1, pose(0.2))
	buffer.advance(0.05)
	buffer.push(10, 0.15, 1, pose(0.3))
	buffer.clock = 0.15
	buffer.advance(0.025)
	check(is_equal_approx(buffer.sample(1).position.x, 0.15), "continuous interpolation between 20 Hz positions")
	check(not buffer.push(7, 0.10, 1, pose(999)), "out of order rejected")
	check(not buffer.push(10, 0.15, 1, pose(999)), "duplicate rejected")
	buffer.advance(0.25)
	check(is_equal_approx(buffer.sample(1).position.x, 0.4), "extrapolation bounded to 50 ms")
	buffer.push(13, 0.30, 1, pose(1, 0, false))
	check(buffer.sample(1).is_empty(), "relevance revoked immediately despite delay")
	buffer.push(16, 0.35, 1, pose(1))
	check(is_equal_approx(buffer.sample(1).position.x, 1), "relevance return never reuses pre-occlusion pose")
	buffer.push(19, 0.4, 2, pose(40))
	check(is_equal_approx(buffer.sample(1).position.x, 40), "round reset never sweeps across map")
	buffer.push(22, 0.45, 2, pose(40.1, deg_to_rad(179)))
	buffer.push(25, 0.50, 2, pose(40.2, deg_to_rad(-179)))
	buffer.clock = 0.575
	check(absf(absf(buffer.sample(1).yaw) - PI) < 0.01, "yaw takes shortest path through wrap")
	for i in range(26, 100):
		buffer.push(i, i / 60.0, 2, pose(40.2))
	check(buffer.frames.size() <= 32, "history bounded")
	buffer.clear()
	check(buffer.push(1, 0, 0, pose(5)), "reconnection clears stale tick threshold")
	buffer.push(4, 0.05, 0, pose(5.1))
	check(buffer.sample(1).position.x == 5.0, "warmup holds first pose instead of latest")
	buffer.clear()
	var prior := -INF
	var backwards := 0
	for tick in range(240):
		var t := tick / 60.0
		if tick % 3 == 0:
			buffer.push(tick, t, 1, pose(t * 2, 0, t >= 1.0))
		buffer.advance(1.0 / 60.0)
		var value := buffer.sample(1)
		if not value.is_empty():
			if value.position.x < prior - 0.000001:
				backwards += 1
			prior = value.position.x
	check(backwards == 0, "revealed moving actor never steps backwards while buffer warms")
	buffer.clear()
	var holds := 0
	var moves := 0
	prior = -INF
	for tick in range(420):
		var t := tick / 60.0
		var latency := 0.25 if t >= 2.0 else 0.0
		if tick % 3 == 0 and (latency == 0 or t >= 2.25):
			buffer.push(int((t - latency) * 60), t - latency, 1, pose((t - latency) * 2))
		buffer.advance(1.0 / 60.0)
		var x: float = buffer.sample(1).position.x
		if t >= 5:
			if absf(x - prior) < 0.000001: holds += 1
			else: moves += 1
		prior = x
	check(holds == 0 and moves > 100, "clock slewing restores continuous interpolation after latency increases")
	print("SNAPSHOT_BUFFER_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
