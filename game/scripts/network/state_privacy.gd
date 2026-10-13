class_name SBStatePrivacy
extends RefCounted
## Server-only authorization. Full actor snapshots never leave this boundary.
## Public roster persists when an enemy is hidden; private fields are allowlisted.
const PUBLIC := ["id", "team", "name", "alive", "kills", "deaths", "assists"]
const OBSERVABLE := ["position", "velocity", "yaw", "pitch", "weapon", "crouch"]
const TEAM := ["health", "credits"]
const OWN := ["recoil", "ammo", "reserve", "reload", "grenades", "smokes", "inventory"]
const PEEK_MARGIN := 0.40
const LOOKAHEAD_SECONDS := 0.10
const MAX_LOOKAHEAD := 0.65
var rays: int = 0

static func fields(source: Dictionary, permitted: Array) -> Dictionary:
	var result: Dictionary = {}
	for key: String in permitted:
		if source.has(key):
			result[key] = source[key]
	return result

static func actor_state(source: Dictionary, own: bool, teammate: bool, observable: bool) -> Dictionary:
	var result := fields(source, PUBLIC)
	result.relevant = own or teammate or observable
	if result.relevant:
		result.merge(fields(source, OBSERVABLE))
	if own or teammate:
		result.merge(fields(source, TEAM))
	if own:
		result.merge(fields(source, OWN))
	return result

## A dead player follows the same first living teammate as the spectator camera.
## No surviving teammate means no authorized enemy viewpoint.
static func observer(match_node: Node, recipient_id: int) -> SBActor:
	var owner: SBActor = match_node.actors.get(recipient_id)
	if owner == null:
		return null
	if owner.alive:
		return owner
	for actor: SBActor in match_node.actors.values():
		if actor.team == owner.team and actor.alive:
			return actor
	return null

func clear_segment(world: World3D, from: Vector3, to: Vector3, clouds: Array, smoke: bool = true) -> bool:
	if smoke:
		for cloud: Node3D in clouds:
			if opaque_smoke(cloud, from, to):
				return false
	rays += 1
	return world.direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from, to, 1)).is_empty()

static func opaque_smoke(cloud: SBUtility, from: Vector3, to: Vector3) -> bool:
	# The bot's 3.2 m concealment sphere is larger than opaque rendered smoke.
	# Cull only an inward central ellipsoid, whose circular XZ footprint is
	# rotation-invariant. Outer lobes/rim/growth/fade remain deliberately disclosed.
	if not cloud._detonated or cloud.kind != "smoke" or cloud.dissipation() < 1.0 or cloud._cloud_elapsed < 0.8:
		return false
	var radii: Vector3 = SBUtility.CORE_LOBES[0][1] - Vector3.ONE * (SBUtility.CORE_BILLOW + 0.15)
	var start := (from - cloud.global_position) / radii
	var direction := (to - from) / radii
	var c := start.length_squared() - 1.0
	if c < 0:
		return true
	var a := direction.length_squared()
	if a < 0.000001:
		return false
	var b := 2.0 * start.dot(direction)
	var discriminant := b * b - 4.0 * a * c
	if discriminant <= 0:
		return false
	var t := (-b - sqrt(discriminant)) / (2.0 * a)
	if t < 0 or t > 1:
		return false
	var normal := ((start + direction * t) / radii).normalized()
	# The shader reaches full opacity at facing >= .535 even at zero density.
	return absf(normal.dot((to - from).normalized())) >= 0.65

## No FOV culling or remembered visibility: turning is instant and smoke/cover
## revokes the next snapshot. Small spatial padding prewarms approaching corners.
## Padding intentionally discloses a narrow near-corner band; it is not perfect LOS.
func observable(match_node: Node3D, viewer: SBActor, target: SBActor, eye_override: Variant = null) -> bool:
	if viewer == null or not target.alive:
		return false
	var eye := viewer.global_position + Vector3.UP * viewer.head_height
	if eye_override is Vector3:
		eye = eye_override
	var world := match_node.get_world_3d()
	var clouds := match_node.get_tree().get_nodes_in_group("smoke_clouds")
	var origins: Array[Vector3] = [eye]
	var advance := viewer.velocity * LOOKAHEAD_SECONDS
	advance.y = 0
	advance = advance.limit_length(MAX_LOOKAHEAD)
	if advance.length() > 0.01 and clear_segment(world, eye, eye + advance, clouds):
		origins.append(eye + advance)
	var at := target.global_position
	var offsets: Array[Vector3] = [Vector3.UP * target.head_height, Vector3.UP * 0.85, Vector3.UP * 0.12, Vector3.UP * 0.4,
		Vector3.UP * (target.head_height + 0.17),
		Vector3(-PEEK_MARGIN, 1.0, 0), Vector3(PEEK_MARGIN, 1.0, 0),
		Vector3(0, 1.0, -PEEK_MARGIN), Vector3(0, 1.0, PEEK_MARGIN)]
	for origin: Vector3 in origins:
		for offset: Vector3 in offsets:
			var point := at + offset
			# Do not reach a padded sample through the target's cover.
			if clear_segment(world, at + Vector3.UP * 1.0, point, clouds, false) and clear_segment(world, origin, point, clouds):
				return true
	return false

static func spectator_position(world: World3D, viewer: SBActor) -> Vector3:
	var eye := viewer.global_position + Vector3.UP * viewer.head_height
	var desired := viewer.global_position + Vector3(sin(viewer.yaw) * 3, 2.8, cos(viewer.yaw) * 3)
	var hit := world.direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(eye, desired, 1))
	return desired if hit.is_empty() else (hit.position as Vector3) + (hit.normal as Vector3) * 0.1

static func viewpoint(match_node: Node3D, recipient_id: int) -> Vector3:
	var viewer := observer(match_node, recipient_id)
	if viewer == null:
		return Vector3.ZERO
	return viewer.global_position + Vector3.UP * viewer.head_height if match_node.actors[recipient_id].alive else spectator_position(match_node.get_world_3d(), viewer)

func point_visible(match_node: Node3D, viewer: SBActor, point: Vector3, eye_override: Variant = null) -> bool:
	if viewer == null:
		return false
	var eye: Vector3 = eye_override if eye_override is Vector3 else viewer.global_position + Vector3.UP * viewer.head_height
	return clear_segment(match_node.get_world_3d(), eye, point, match_node.get_tree().get_nodes_in_group("smoke_clouds"))

func utility_relevant(match_node: Node3D, viewer: SBActor, eye: Vector3, utility: SBUtility) -> bool:
	if viewer == null:
		return false
	if utility._detonated and utility.kind == "grenade":
		return eye.distance_to(utility.position) <= 65 # Existing explosion audio range.
	if utility._detonated and utility.kind == "smoke":
		# Smoke is silent. Send only when its conservative visible volume intersects
		# an unobstructed view, including a camera within the volume. Ignore smoke
		# concealment when checking the cloud itself, otherwise it hides itself.
		var radius := 3.8 * utility.dissipation()
		if eye.distance_to(utility.position) <= radius:
			return true
		for offset: Vector3 in [Vector3.ZERO, Vector3.LEFT, Vector3.RIGHT, Vector3.UP, Vector3.DOWN, Vector3.FORWARD, Vector3.BACK]:
			if clear_segment(match_node.get_world_3d(), eye, utility.position + offset * radius, [], false):
				return true
		return false
	return point_visible(match_node, viewer, utility.position, eye)

func snapshot(match_node: Node3D, recipient_id: int) -> Dictionary:
	var owner: SBActor = match_node.actors.get(recipient_id)
	if owner == null:
		return {}
	var viewer := observer(match_node, recipient_id)
	var eye := viewpoint(match_node, recipient_id)
	var states: Array = []
	for actor: SBActor in match_node.actors.values():
		var same_team := actor.team == owner.team
		states.append(actor_state(actor.snapshot(), actor.actor_id == recipient_id, same_team,
			false if same_team else observable(match_node, viewer, actor, eye)))
	var objective: String = match_node.objective_state
	var objective_known: bool = owner.team == 0 or objective == "planted" or (objective == "dropped" and point_visible(match_node, viewer, match_node.objective_position + Vector3.UP * 0.15, eye))
	var interactions: Dictionary = {}
	if match_node._interactions.has(recipient_id):
		interactions[recipient_id] = match_node._interactions[recipient_id]
	var utilities: Array = []
	for child: Node in match_node.get_children():
		if child is SBUtility and utility_relevant(match_node, viewer, eye, child):
			# No owner attribution or private inventory count.
			utilities.append({"id": child.get_instance_id(), "kind": child.kind, "position": child.position, "detonated": child._detonated, "life": child._lifetime})
	return {"actors": states, "utilities": utilities, "humans": match_node._peer_actors.values(),
		"contributions": match_node.objective_contributions.duplicate(), "reward_status": match_node.reward_status,
		"phase": match_node.phase, "round": match_node.round_number, "attack": match_node.attack_score,
		"defend": match_node.defend_score, "time": match_node.time_left,
		"objective": objective if objective_known else "unknown", "objective_timer": match_node.objective_timer if objective == "planted" else 0.0,
		"objective_position": match_node.objective_position if objective_known and objective != "carried" else Vector3.ZERO,
		"carrier": match_node.objective_carrier if owner.team == 0 else 0,
		"interactions": interactions, "elapsed": match_node._elapsed}
