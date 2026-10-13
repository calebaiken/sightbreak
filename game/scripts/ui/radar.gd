class_name SBRadar
extends Control
## North-up tactical radar. Draws only map geometry, objective sites, the local
## operator and living teammates — never opponents — so it adds no information a
## player could not already see. The device appears when planted, or when dropped
## for the carrying squad.
const Design = preload("res://scripts/ui/design_tokens.gd")
const WORLD_HALF := 24.5
var match_game: Node
var _obstacles: Array[AABB] = []

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	custom_minimum_size = Vector2(128, 128)

func bind(game: Node) -> void:
	match_game = game
	_obstacles.clear()
	if game != null and is_instance_valid(game.arena):
		for obstacle: AABB in game.arena._obstacles:
			# Navigation inflates obstacles by 0.55 m; draw their real footprint.
			_obstacles.append(obstacle.grow(-0.55))
	queue_redraw()

func to_radar(world: Vector3) -> Vector2:
	var side := minf(size.x, size.y)
	return Vector2((world.x + WORLD_HALF) / (WORLD_HALF * 2.0), (WORLD_HALF - world.z) / (WORLD_HALF * 2.0)) * side

func _draw() -> void:
	var side := minf(size.x, size.y)
	var frame := Rect2(Vector2.ZERO, Vector2(side, side))
	draw_rect(frame, Color(Design.OBSIDIAN, 0.72))
	draw_rect(frame, Color(Design.LINE_STRONG, 0.9), false, 1.0)
	if match_game == null or not is_instance_valid(match_game):
		return
	for obstacle in _obstacles:
		var a := to_radar(Vector3(obstacle.position.x, 0, obstacle.end.z))
		var b := to_radar(Vector3(obstacle.end.x, 0, obstacle.position.z))
		var rect := Rect2(a, b - a).abs().intersection(frame)
		if rect.has_area():
			draw_rect(rect, Color(Design.STEEL, 0.32))
	var font := Design.heading_font()
	for i in range(match_game.arena.sites.size()):
		var site: Vector3 = match_game.arena.sites[i]
		var center := to_radar(site)
		var radius := 3.8 / (WORLD_HALF * 2.0) * side
		draw_arc(center, radius, 0, TAU, 28, Color(Design.GOLD, 0.7), 1.0)
		draw_string(font, center + Vector2(-4, 4), "A" if i == 0 else "B", HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Design.GOLD)
	for marker in markers():
		var at := to_radar(marker.position)
		match marker.kind:
			"device":
				var pulse := 0.6 + 0.4 * sin(Time.get_ticks_msec() * 0.008)
				draw_rect(Rect2(at - Vector2(4, 4), Vector2(8, 8)), Color(Design.CRIMSON_BRIGHT, pulse))
			"teammate":
				draw_circle(at, 3.2, Design.squad_color(marker.team))
				if marker.carrier:
					draw_arc(at, 5.5, 0, TAU, 16, Design.GOLD, 1.2)
			"self":
				var forward := Vector2(-sin(marker.yaw), cos(marker.yaw))
				var right := Vector2(forward.y, -forward.x)
				draw_colored_polygon(PackedVector2Array([at + forward * 7, at - forward * 4 + right * 4.5, at - forward * 2, at - forward * 4 - right * 4.5]), Design.TEXT)

## Everything the radar shows besides static geometry. Opponents are never listed.
func markers() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	if match_game == null or not is_instance_valid(match_game):
		return result
	var local: SBActor = match_game.local_actor()
	if local == null:
		return result
	if match_game.objective_state == "planted" or (match_game.objective_state == "dropped" and local.team == 0):
		result.append({"kind": "device", "position": match_game.objective_position, "team": -1})
	for actor: SBActor in match_game.actors.values():
		if actor == local or not actor.alive or actor.team != local.team:
			continue
		result.append({"kind": "teammate", "position": actor.global_position, "team": actor.team, "id": actor.actor_id, "carrier": actor.actor_id == match_game.objective_carrier and match_game.objective_state == "carried"})
	if local.alive:
		result.append({"kind": "self", "position": local.global_position, "team": local.team, "yaw": local.yaw})
	return result
