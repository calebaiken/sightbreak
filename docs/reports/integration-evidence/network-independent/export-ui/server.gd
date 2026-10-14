extends SceneTree
var game: TacticalMatch
var elapsed := 0.0
var joined_id := 0
var shots := 0
var reload_seen := false
var reload_completed := false
var lowest_ammo := 30
var largest_ack := 0
var finishing := false
var ack_reported := false
var last_shot_time := -1.0
var reload_started := false
func _initialize() -> void: start.call_deferred()
func start() -> void:
	var host := Node.new()
	host.name = "Sightbreak"
	root.add_child(host)
	game = TacticalMatch.new()
	game.name = "Match"
	game.configure({"mode":"server","port":27020,"name":"Export UI authority fixture"})
	host.add_child(game)
	game.notification.connect(func(message): print("SERVER_NOTICE "+message))
	game._bot_clock = 1000
	game.phase = "live"
	game.time_left = 1000
	for actor: SBActor in game.actors.values():
		actor.credits = 5000
		actor.buy_weapon("rifle")
		actor.shot_fired.connect(func(id, _origin, _direction):
			if id == joined_id:
				shots += 1
				last_shot_time = elapsed
				print("EXPORT_UI_SHOT actor=%d shots=%d ammo=%d" % [id,shots,game.actors[id].ammo]))
func _process(delta: float) -> bool:
	elapsed += delta
	if game == null or finishing: return false
	if not game._peer_actors.is_empty():
		if joined_id == 0:
			joined_id = game._peer_actors.values()[0]
			print("EXPORT_UI_JOIN actor=%d protocol=%d peers=%d" % [joined_id,TacticalMatch.PROTOCOL_VERSION,game._peer_actors.size()])
			var snapshot := game._snapshot(joined_id)
			print("EXPORT_UI_SCHEMA valid=%s actors=%d phase=%s" % [SBSnapshotSchema.valid(snapshot),snapshot.actors.size(),snapshot.phase])
			var debug_file := FileAccess.open("/workspace/reviews/integration-20261013/network-independent/export-ui/join-snapshot.json",FileAccess.WRITE)
			debug_file.store_string(JSON.stringify(snapshot,"\t"))
			debug_file.close()
		var actor: SBActor = game.actors[joined_id]
		lowest_ammo = mini(lowest_ammo,actor.ammo)
		largest_ack = maxi(largest_ack,int(game._last_input_sequence.get(joined_id,0)))
		if largest_ack > 10 and not ack_reported:
			ack_reported = true
			print("EXPORT_UI_ACK_READY actor=%d ack=%d ammo=%d" % [joined_id,largest_ack,actor.ammo])
		if not reload_started and shots > 0 and elapsed-last_shot_time > 0.6 and not bool(actor.input_state.get("fire",false)):
			reload_started = true
			actor.start_reload()
			print("EXPORT_UI_RELOAD_STARTED trigger=authority_fixture")
		if actor.reload_remaining > 0: reload_seen = true
		if reload_seen and not reload_completed and actor.reload_remaining <= 0 and actor.ammo == 30:
			reload_completed = true
			print("EXPORT_UI_RELOAD_COMPLETED ammo=%d" % actor.ammo)
	if elapsed > 180 or FileAccess.file_exists("/workspace/reviews/integration-20261013/network-independent/export-ui/finish"):
		finishing = true
		finish.call_deferred()
	return false
func finish() -> void:
	var report := {"scope":"source Godot authority fixture; client is actual exported Linux ELF driven through native UI; no rewards","joined_id":joined_id,"shots":shots,"lowest_ammo":lowest_ammo,"largest_ack":largest_ack,"reload_seen":reload_seen,"reload_completed":reload_completed,"reload_trigger":"authority fixture (desktop R-key injection unverified)","prediction_default":game._prediction_enabled,"protocol":TacticalMatch.PROTOCOL_VERSION}
	report.passed = joined_id > 0 and shots > 0 and lowest_ammo < 30 and largest_ack > 10 and reload_seen and reload_completed
	var file := FileAccess.open("/workspace/reviews/integration-20261013/network-independent/export-ui/authority.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("EXPORT_UI_AUTHORITY "+JSON.stringify(report))
	game.queue_free()
	await create_timer(0.2).timeout
	quit(0 if report.passed else 1)
