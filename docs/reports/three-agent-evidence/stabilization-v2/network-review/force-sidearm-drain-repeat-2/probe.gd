extends SceneTree
## Drives the stock Match client of whichever build it runs in (this tree or an
## archived release) against a running dedicated server, and reports what a player
## would experience. Used by scripts/test_protocol_compat.sh for mixed versions.
## Args: --port=N --seconds=S --name=NAME
const Actor = preload("res://scripts/gameplay/actor.gd")
const ReloadAudio = preload("res://scripts/gameplay/reload_audio.gd")
const Match = preload("res://scripts/gameplay/match.gd")

var _review_playbacks: Array[AudioStreamPlayback] = []

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
	await _review_before_free(game)
	game.queue_free()
	await process_frame
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--review-drain="):
			await create_timer(float(argument.trim_prefix("--review-drain="))).timeout
	if "--review-track" in OS.get_cmdline_user_args():
		var drain_started := Time.get_ticks_usec()
		for step in 30:
			var counts: Array[int] = []
			for playback in _review_playbacks:
				counts.append(playback.get_reference_count())
			print("REVIEW_PLAYBACK_REFS elapsed_us=%s counts=%s" % [Time.get_ticks_usec() - drain_started, counts])
			if counts.all(func(count): return count <= 2):
				break
			await process_frame
		_review_playbacks.clear()
	print("REVIEW_AFTER_FREE game_valid=%s peer=%s" % [is_instance_valid(game), root.multiplayer.multiplayer_peer])
	quit()

func _review_before_free(game) -> void:
	for argument in OS.get_cmdline_user_args():
		if argument == "--review-force-shot":
			game.local_actor()._shot_audio.play()
		if argument == "--review-force-sidearm":
			game._audible_shot_rpc(Vector3(0, 1, 0), "sidearm")
		if argument == "--review-force-transient":
			game._audible_shot_rpc(Vector3(0, 1, 0), "rifle")
		if argument == "--review-close":
			game._close_client()
	if "--review-force-shot" in OS.get_cmdline_user_args() or "--review-force-transient" in OS.get_cmdline_user_args() or "--review-force-sidearm" in OS.get_cmdline_user_args():
		await create_timer(0.04).timeout
	print("REVIEW_OWNED peer=%s id=%s auth=%s" % [root.multiplayer.multiplayer_peer, root.multiplayer.multiplayer_peer.get_instance_id(), (root.multiplayer as SceneMultiplayer).auth_callback])
	for weapon in Actor._shot_streams:
		print("REVIEW_CACHE shot.%s stream=%s" % [weapon, Actor._shot_streams[weapon].get_instance_id()])
	print("REVIEW_CACHE hurt stream=%s" % Actor._hurt_stream.get_instance_id())
	for event in ReloadAudio._streams:
		for i in (ReloadAudio._streams[event] as Array).size():
			print("REVIEW_CACHE reload.%s.%s stream=%s" % [event, i, ReloadAudio._streams[event][i].get_instance_id()])
	_review_audio_nodes(game)

func _review_audio_nodes(node: Node) -> void:
	if node is AudioStreamPlayer3D:
		var voice := node as AudioStreamPlayer3D
		var stream_id := voice.stream.get_instance_id() if voice.stream != null else 0
		var playback_id := voice.get_stream_playback().get_instance_id() if voice.has_stream_playback() else 0
		if "--review-track" in OS.get_cmdline_user_args() and voice.is_in_group("network_shot_audio") and voice.has_stream_playback():
			_review_playbacks.append(voice.get_stream_playback())
		print("REVIEW_AUDIO path=%s node=%s playing=%s stream=%s playback=%s" % [voice.get_path(), voice.get_instance_id(), voice.playing, stream_id, playback_id])
		if "--review-stop" in OS.get_cmdline_user_args():
			voice.stop()
			if "--review-stop-only" not in OS.get_cmdline_user_args():
				voice.stream = null
	for child in node.get_children():
		_review_audio_nodes(child)
