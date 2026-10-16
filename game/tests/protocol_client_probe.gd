extends SceneTree
## Drives the stock Match client of whichever build it runs in (this tree or an
## archived release) against a running dedicated server, and reports what a player
## would experience. Used by scripts/test_protocol_compat.sh for mixed versions.
## Args: --port=N --seconds=S --name=NAME
const Match = preload("res://scripts/gameplay/match.gd")

func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var port := 27995
	var seconds := 12.0
	var player := "Compat probe"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--port="): port = int(argument.trim_prefix("--port="))
		if argument.begins_with("--seconds="): seconds = float(argument.trim_prefix("--seconds="))
		if argument.begins_with("--name="): player = argument.trim_prefix("--name=")
	var game = Match.new()
	game.configure({"mode": "client", "address": "127.0.0.1", "port": port, "name": player})
	var notices: Array[String] = []
	game.notification.connect(func(text: String) -> void:
		notices.append(text)
		print("PROTOCOL_NOTICE %.2f %s" % [Time.get_ticks_msec() / 1000.0, text]))
	var started := Time.get_ticks_msec()
	# RPCs resolve by node path: mirror main.tscn (/root/Sightbreak/Match).
	var host := Node.new()
	host.name = "Sightbreak"
	root.add_child(host)
	host.add_child(game)
	var states: Array[String] = []
	var joined_at := -1.0
	while (Time.get_ticks_msec() - started) / 1000.0 < seconds:
		await process_frame
		var elapsed := (Time.get_ticks_msec() - started) / 1000.0
		var state := str(game.connection_state)
		if states.is_empty() or states[-1] != state:
			states.append(state)
			print("PROTOCOL_STATE %.2f %s" % [elapsed, state])
		if joined_at < 0.0 and state == "connected" and int(game.local_id) != 0:
			joined_at = elapsed
	var final_state := str(game.connection_state)
	var summary := {"joined": joined_at >= 0.0, "joined_after": snappedf(joined_at, 0.01), "final_state": final_state, "states": states, "notices": notices, "local_id": int(game.local_id), "actors": game.actors.size()}
	print("PROTOCOL_CLIENT " + JSON.stringify(summary))
	game.queue_free()
	await process_frame
	# AudioServer releases transient shot playback on its mixer/update cycles.
	await create_timer(0.5).timeout
	quit()
