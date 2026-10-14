extends SceneTree
## External test driver for the exported executable's embedded game resources.
## This file is outside game/ and is never shipped in client packs.
var game: TacticalMatch
var elapsed := 0.0
var role := "offline"
var output := ""
var finishing := false
var snapshots := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--role="): role = arg.trim_prefix("--role=")
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	_start.call_deferred()

func _start() -> void:
	game = TacticalMatch.new()
	game.configure({"mode":role,"port":29980,"address":"127.0.0.1","name":"Export fixture"})
	root.add_child(game)
	if role != "client":
		game._bot_clock = 1000
		game.phase = "live"
		game.time_left = 1000
		for actor: SBActor in game.actors.values():
			actor.credits = 5000
			actor.buy_weapon("rifle")

func _process(delta: float) -> bool:
	elapsed += delta
	if game == null or finishing: return false
	if role == "client" and game.connection_state == "connected": snapshots += 1
	if role != "server":
		game.set_local_input({"move":Vector2(0,1) if elapsed < 2 else Vector2.ZERO,"look":Vector2(0.35,-0.025),"reload":elapsed > 4,"fire":elapsed > 2 and elapsed < 3})
	if elapsed > (10.0 if role == "server" else 6.0):
		finishing = true
		_finish.call_deferred()
	return false

func _finish() -> void:
	var success := true
	if role != "server":
		var actor: SBActor = game.local_actor()
		success = actor != null and actor.weapon_id == "rifle" and is_instance_valid(actor._arms_skeleton) and actor._arms_skeleton.get_bone_count() == 34 and is_instance_valid(actor._arms_player)
		if role == "client": success = success and game.connection_state == "connected" and snapshots > 10
		if not output.is_empty() and DisplayServer.get_name() != "headless":
			await RenderingServer.frame_post_draw
			success = root.get_texture().get_image().save_png(output) == OK and success
	print("EXPORT_INTEGRATION role=%s passed=%s connected_render_frames=%d protocol=%d" % [role,success,snapshots,TacticalMatch.PROTOCOL_VERSION])
	game.queue_free()
	for i in 5: await process_frame
	quit(0 if success else 1)
