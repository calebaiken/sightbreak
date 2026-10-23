extends SceneTree
var match_node: TacticalMatch
var elapsed: float = 0
var planted: bool = false
var kills: int = 0
var finished: bool = false

func _initialize() -> void:
	call_deferred("_start")

func _start() -> void:
	match_node = TacticalMatch.new()
	match_node.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(match_node)
	# Exercise all 10 actors as bots, including device carrier.
	match_node.local_id = 0
	match_node.phase = "live"
	match_node.time_left = 100
	Engine.time_scale = 4.0

func _process(delta: float) -> bool:
	if match_node == null or finished:
		return false
	elapsed += delta
	planted = planted or match_node.objective_state == "planted"
	if elapsed > 100 or match_node.phase == "post":
		for actor: SBActor in match_node.actors.values():
			kills += actor.kills
		print("BOT_MATCH_OBSERVATION elapsed=%0.1f kills=%d planted=%s score=%d:%d" % [elapsed, kills, planted, match_node.attack_score, match_node.defend_score])
		for actor: SBActor in match_node.actors.values():
			print("BOT %s alive=%s position=%s" % [actor.display_name,actor.alive,actor.position])
		var success: bool = kills > 0 and (match_node.phase == "post" or planted)
		finished = true
		_finish.call_deferred(success)
	return false

func _finish(success: bool) -> void:
	Engine.time_scale = 1.0
	match_node.queue_free()
	await create_timer(0.6).timeout
	await process_frame
	await process_frame
	quit(0 if success else 1)
