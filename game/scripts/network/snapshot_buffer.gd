class_name SBSnapshotBuffer
extends RefCounted
## Ordered transform timeline only: never interpolates health, ammo or damage.
var delay_seconds := 0.10
var max_extrapolation := 0.05
var frames: Array[Dictionary] = []
var last_tick := -1
var clock := 0.0
var epoch := -1
var stale_packets := 0
var resets := 0
var _local_time := 0.0
var _arrival_time := 0.0
var _server_time := 0.0

func clear() -> void:
	frames.clear()
	last_tick = -1
	epoch = -1
	clock = 0
	_local_time = 0
	_arrival_time = 0
	_server_time = 0

func push(tick: int, server_time: float, round_epoch: int, states: Array) -> bool:
	if tick <= last_tick or not is_finite(server_time):
		stale_packets += 1
		return false
	if round_epoch != epoch or (not frames.is_empty() and server_time < float(frames.back().time)):
		frames.clear()
		clock = server_time
		epoch = round_epoch
		resets += 1
	# Clock correction is slewed in advance(), never a backward transform jump.
	_server_time = server_time
	_arrival_time = _local_time
	var poses: Dictionary = {}
	for state: Dictionary in states:
		if bool(state.get("relevant", true)):
			if not frames.is_empty() and frames.back().poses.has(int(state.id)) and (frames.back().poses[int(state.id)].position as Vector3).distance_to(state.position) > 3.0:
				for old: Dictionary in frames:
					old.poses.erase(int(state.id))
			poses[int(state.id)] = {"position": state.position, "velocity": state.get("velocity", Vector3.ZERO), "yaw": state.get("yaw", 0.0), "pitch": state.get("pitch", 0.0)}
		else:
			for old: Dictionary in frames:
				old.poses.erase(int(state.id))
	frames.append({"tick": tick, "time": server_time, "poses": poses})
	while frames.size() > 32:
		frames.pop_front()
	last_tick = tick
	return true

func advance(delta: float) -> void:
	var step := clampf(delta, 0, 0.25)
	_local_time += step
	var target := _server_time + (_local_time - _arrival_time)
	clock += step * clampf(1.0 + (target - clock - step) * 5.0, 0.5, 1.1)
	while frames.size() > 2 and float(frames[1].time) < clock - delay_seconds:
		frames.pop_front()

func sample(id: int) -> Dictionary:
	if frames.is_empty() or not frames.back().poses.has(id):
		return {} # Latest authorization revocation wins immediately.
	var render_time := clock - delay_seconds
	# Ignore frames before this actor became relevant. Holding its first known
	# pose while the buffer warms avoids moving forward then jumping backward.
	var available: Array[Dictionary] = []
	for frame: Dictionary in frames:
		if frame.poses.has(id):
			available.append(frame)
	if available.is_empty():
		return {}
	var left: Dictionary = available.front()
	var right: Dictionary = available.back()
	for frame: Dictionary in available:
		if float(frame.time) <= render_time:
			left = frame
		if float(frame.time) >= render_time:
			right = frame
			break
	var a: Dictionary = left.poses[id]
	var b: Dictionary = right.poses[id]
	if a.position.distance_to(b.position) > 3.0:
		return b.duplicate() # Teleport/reset: never sweep through map geometry.
	var span: float = float(right.time) - float(left.time)
	if span <= 0:
		var result := b.duplicate()
		var extra := clampf(render_time - float(right.time), 0, max_extrapolation)
		result.position += (b.velocity as Vector3) * extra
		return result
	var weight := clampf((render_time - float(left.time)) / span, 0, 1)
	return {"position": (a.position as Vector3).lerp(b.position, weight), "velocity": (a.velocity as Vector3).lerp(b.velocity, weight), "yaw": lerp_angle(float(a.yaw), float(b.yaw), weight), "pitch": lerpf(float(a.pitch), float(b.pitch), weight)}
