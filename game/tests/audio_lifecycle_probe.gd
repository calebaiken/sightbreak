extends RefCounted
## Opt-in read-only observation. Never retain an audio object beyond one call.
## Latest playback only: public Godot APIs cannot enumerate polyphonic voices
## or acknowledge AudioServer's asynchronous deletion/drain state.
var _tree: WeakRef
var _players := {}
var _objects := {}
var _sequence := 0
var _stage := "attach"

func attach(tree: SceneTree) -> void:
	_tree = weakref(tree)
	tree.node_added.connect(_node_added)
	tree.node_removed.connect(_node_removed)
	_emit({"kind":"header", "driver":AudioServer.get_driver_name(), "mix_rate":AudioServer.get_mix_rate(), "scope":"read_only_latest_playback_not_server_drain"})
	_visit(tree.root)

func _visit(node: Node) -> void:
	_node_added(node)
	for child in node.get_children():
		_visit(child)

func _id(object: Object) -> String:
	# JSON numbers lose 64-bit ObjectID precision. The analyzer converts this
	# signed decimal string to the unsigned form printed by engine leak output.
	return str(object.get_instance_id())

func _emit(row: Dictionary) -> void:
	row.schema = 1
	row.sequence = _sequence
	row.stage = _stage
	row.process_frame = Engine.get_process_frames()
	row.physics_frame = Engine.get_physics_frames()
	row.usec = Time.get_ticks_usec()
	_sequence += 1
	print("AUDIO_LIFECYCLE " + JSON.stringify(row))

func _track(object: Object) -> String:
	var id := _id(object)
	if not _objects.has(id):
		_objects[id] = {"weak":weakref(object), "alive":true}
		var row := {"kind":"object", "id":id, "class":object.get_class()}
		if object is AudioStreamWAV:
			var wav := object as AudioStreamWAV
			var digest := HashingContext.new()
			digest.start(HashingContext.HASH_SHA256)
			digest.update(wav.data)
			row.wav = {"format":wav.format, "mix_rate":wav.mix_rate, "stereo":wav.stereo, "bytes":wav.data.size(), "sha256":digest.finish().hex_encode()}
		_emit(row)
	return id

func _owner(player: AudioStreamPlayer3D) -> Dictionary:
	var owner := player.get_parent()
	while owner != null:
		var script = owner.get_script()
		var path: String = script.resource_path if script != null else ""
		var role := ""
		if path == "res://scripts/gameplay/actor.gd":
			if owner.get("_shot_audio") == player: role = "actor_shot"
			elif owner.get("_hurt_audio") == player: role = "actor_hurt"
		elif path == "res://scripts/gameplay/reload_audio.gd": role = "reload_voice"
		elif path == "res://scripts/gameplay/utility.gd": role = "utility"
		elif path == "res://scripts/gameplay/match.gd":
			if owner.get("_device_audio") == player: role = "match_device"
			elif player.is_in_group("network_shot_audio"): role = "network_shot"
		if not role.is_empty():
			return {"role":role, "id":_id(owner), "path":str(owner.get_path()) if owner.is_inside_tree() else "", "script":path}
		owner = owner.get_parent()
	return {"role":"unknown", "id":"", "path":"", "script":""}

func _node_added(node: Node) -> void:
	if node is AudioStreamPlayer3D:
		var id := _track(node)
		_players[id] = {"weak":weakref(node), "last":{}}
		_sample(node, "node_added", true)

func _node_removed(node: Node) -> void:
	if node is AudioStreamPlayer3D:
		# SceneTree emits this after native EXIT_TREE. The owning actor's
		# _exit_tree may not yet have run, because children exit first.
		_sample(node, "node_removed_after_native_exit", true)

func _sample(player: AudioStreamPlayer3D, event: String, force: bool) -> void:
	var id := _id(player)
	var stream: AudioStream = player.stream
	var latest: AudioStreamPlayback
	if player.has_stream_playback(): latest = player.get_stream_playback()
	var state := {"path":str(player.get_path()) if player.is_inside_tree() else "", "owner":_owner(player), "inside_tree":player.is_inside_tree(), "queued_for_deletion":player.is_queued_for_deletion(), "playing":player.playing, "stream_paused":player.stream_paused, "has_stream_playback":player.has_stream_playback(), "stream_id":_track(stream) if stream != null else "", "latest_playback_id":_track(latest) if latest != null else "", "latest_playing":latest.is_playing() if latest != null else null}
	if force or state != _players[id].last:
		_emit({"kind":"player", "event":event, "id":id, "state":state})
		_players[id].last = state

func snapshot(stage: String, force := false) -> void:
	_stage = stage
	for id in _players:
		var player = _players[id].weak.get_ref()
		if player != null: _sample(player, "snapshot", force)
	for id in _objects:
		var object = _objects[id].weak.get_ref()
		var alive := object != null
		if force or alive != _objects[id].alive:
			_emit({"kind":"weak", "id":id, "alive":alive})
			_objects[id].alive = alive
	# These readings expose driver timing, not a mix counter or drain receipt.
	_emit({"kind":"checkpoint", "time_since_last_mix":AudioServer.get_time_since_last_mix(), "time_to_next_mix":AudioServer.get_time_to_next_mix()})

func finish() -> void:
	snapshot("final_pre_quit", true)
	var tree = _tree.get_ref()
	if tree != null:
		tree.node_added.disconnect(_node_added)
		tree.node_removed.disconnect(_node_removed)
