class_name SBHitHistory
extends RefCounted
## Server-only diagnostic foundation. Does not award hits or trust client time.
## Reuses the exact live head/body math without moving physics or visual nodes.
const MAX_REWIND_TICKS := 12 # 200 ms at the fixed 60 Hz simulation.
const MAX_FRAMES := MAX_REWIND_TICKS + 2
var frames: Array[Dictionary] = []
var epoch := -1
var serials: Dictionary = {}

static func target_tick(server_tick: int, measured_rtt_ms: float, render_delay_ms := 100.0) -> int:
	# These values must be server-observed/configured, never client supplied.
	if server_tick < 0 or not is_finite(measured_rtt_ms) or measured_rtt_ms < 0 or measured_rtt_ms > 2000 or not is_finite(render_delay_ms) or render_delay_ms < 0 or render_delay_ms > 200:
		return -1
	return maxi(0, server_tick - mini(MAX_REWIND_TICKS, roundi((measured_rtt_ms * 0.5 + render_delay_ms) * 0.06)))

func record(tick: int, generation: int, actors: Dictionary) -> bool:
	if tick < 0 or generation < epoch: return false
	if generation != epoch:
		frames.clear()
		serials.clear()
		epoch = generation
	if not frames.is_empty() and tick <= int(frames.back().tick): return false
	var previous: Dictionary = frames.back().actors if not frames.is_empty() else {}
	var states: Dictionary = {}
	for id: int in actors:
		var actor: SBActor = actors[id]
		var capsule := actor._collision.shape as CapsuleShape3D
		var state := {"transform": actor.global_transform, "squash": maxf(0.05, actor._body.scale.y), "radius": capsule.radius, "height": capsule.height, "center": actor._collision.position.y, "team": actor.team, "alive": actor.alive}
		var discontinuity := not previous.has(id)
		if previous.has(id):
			var old: Dictionary = previous[id]
			discontinuity = old.team != actor.team or old.alive != actor.alive or old.transform.origin.distance_to(actor.global_position) > 3.0
		if discontinuity: serials[id] = int(serials.get(id, 0)) + 1
		state.serial = int(serials[id])
		states[id] = state
	frames.append({"tick": tick, "actors": states})
	while frames.size() > MAX_FRAMES: frames.pop_front()
	return true

func trace(tick: int, generation: int, origin: Vector3, direction: Vector3, world_distance: float, excluded_id: int) -> Dictionary:
	# Caller supplies a CURRENT static-world ray distance. This bound must never
	# be enlarged by rewind. Smoke is visual concealment, not a ballistic wall.
	if generation != epoch or frames.is_empty() or not origin.is_finite() or not direction.is_finite() or absf(direction.length_squared() - 1.0) > 0.001 or not is_finite(world_distance) or world_distance <= 0 or world_distance > 1000: return {}
	var current: Dictionary = frames.back()
	if tick > int(current.tick) or int(current.tick) - tick > MAX_REWIND_TICKS: return {}
	var selected: Dictionary = {}
	for frame: Dictionary in frames:
		if int(frame.tick) == tick:
			selected = frame.actors
			break
	if selected.is_empty(): return {}
	var nearest := world_distance
	var result: Dictionary = {}
	for id: int in selected:
		if id == excluded_id or not current.actors.has(id): continue
		var state: Dictionary = selected[id]
		if not state.alive or not current.actors[id].alive or state.serial != current.actors[id].serial: continue
		var inverse: Transform3D = state.transform.affine_inverse()
		var local_origin := inverse * origin
		var local_direction := inverse.basis * direction
		var body := SBActor._capsule_entry(local_origin - Vector3(0, state.center, 0), local_direction, state.radius, state.height, SBActor.BODY_TOP * float(state.squash) - float(state.center))
		var head_origin := Vector3(local_origin.x, local_origin.y / float(state.squash), local_origin.z)
		var head_direction := Vector3(local_direction.x, local_direction.y / float(state.squash), local_direction.z)
		var distance := nearest
		var hit := false
		var headshot := false
		for volume: Array in SBActor.HEAD_VOLUMES:
			var entry := SBActor._ellipsoid_entry(head_origin, head_direction, volume[0], volume[1])
			if entry >= 0 and entry < distance:
				distance = entry
				hit = true
				headshot = true
		if body >= 0 and body < distance:
			distance = body
			hit = true
			headshot = false
		if hit:
			nearest = distance
			result = {"actor_id": id, "distance": distance, "position": origin + direction * distance, "headshot": headshot}
	return result
