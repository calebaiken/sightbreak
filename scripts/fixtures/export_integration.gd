# External source-engine authority fixture for the real exported desktop UI.
# This script is never supplied to an export template via unsupported --script.
# Grants guest practice rifles only; no account tickets, rewards or secrets.
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
var output := ""
var automatic_reload := false
var reload_command_seen := false
var first_reload_observation := "not_observed"
var telemetry: Array[Dictionary] = []
var telemetry_clock := 0.0
var telemetry_signature := ""
var telemetry_wall_start := Time.get_ticks_msec()

# Bounded diagnostics only. These observations never supply actor input or
# modify reload/combat state; the fixture remains guest practice with no rewards.
func observe(reason: String) -> void:
	if not is_instance_valid(game): return
	var sample := {"reason":reason,"wall_unix_msec":int(Time.get_unix_time_from_system()*1000),"wall_elapsed_msec":Time.get_ticks_msec()-telemetry_wall_start,"fixture_elapsed_seconds":elapsed,"authority_elapsed_seconds":game._elapsed,"simulation_tick":game._simulation_tick,"phase":game.phase,"peer_count":game._peer_actors.size(),"joined_id":joined_id}
	if joined_id > 0 and game.actors.has(joined_id):
		var actor: SBActor = game.actors[joined_id]
		sample.merge({"alive":actor.alive,"weapon":actor.weapon_id,"ammo":actor.ammo,"reserve":actor.reserve,"reload_remaining":actor.reload_remaining,"fire_input":bool(actor.input_state.get("fire",false)),"reload_input":bool(actor.input_state.get("reload",false)),"weapon_input":str(actor.input_state.get("weapon","")),"ack":int(game._last_input_sequence.get(joined_id,0)),"peer_bound":game._peer_actors.values().has(joined_id),"shots":shots})
	telemetry.append(sample)
	if telemetry.size() > 128: telemetry.pop_front()
	var file := FileAccess.open(output.path_join("authority-telemetry.json"),FileAccess.WRITE)
	if file != null:
		file.store_string(JSON.stringify({"scope":"bounded read-only authority observations; no gameplay input injection","samples":telemetry},"\t"))
		file.close()
	if reason != "periodic": print("EXPORT_UI_TIMING "+JSON.stringify(sample))

func _initialize() -> void: start.call_deferred()
func start() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg == "--automatic-reload": automatic_reload = true
	if output.is_empty():
		push_error("An external --output directory is required")
		quit(2)
		return
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
				print("EXPORT_UI_SHOT actor=%d shots=%d ammo=%d" % [id,shots,game.actors[id].ammo])
				observe("shot"))
	observe("setup")
func _process(delta: float) -> bool:
	elapsed += delta
	if game == null or finishing: return false
	if not game._peer_actors.is_empty():
		if joined_id == 0:
			joined_id = game._peer_actors.values()[0]
			print("EXPORT_UI_JOIN actor=%d protocol=%d peers=%d" % [joined_id,TacticalMatch.PROTOCOL_VERSION,game._peer_actors.size()])
			var snapshot := game._snapshot(joined_id)
			print("EXPORT_UI_SCHEMA valid=%s actors=%d phase=%s" % [SBSnapshotSchema.valid(snapshot),snapshot.actors.size(),snapshot.phase])
			var debug_file := FileAccess.open(output.path_join("join-snapshot.json"),FileAccess.WRITE)
			debug_file.store_string(JSON.stringify(snapshot,"\t"))
			debug_file.close()
			observe("join")
		var actor: SBActor = game.actors[joined_id]
		lowest_ammo = mini(lowest_ammo,actor.ammo)
		largest_ack = maxi(largest_ack,int(game._last_input_sequence.get(joined_id,0)))
		if largest_ack > 10 and not ack_reported:
			ack_reported = true
			print("EXPORT_UI_ACK_READY actor=%d ack=%d ammo=%d" % [joined_id,largest_ack,actor.ammo])
		if bool(actor.input_state.get("reload",false)) and not reload_command_seen:
			reload_command_seen = true
			print("EXPORT_UI_RELOAD_COMMAND actor=%d" % joined_id)
			observe("native_reload_command")
		if automatic_reload and not reload_started and shots > 0 and elapsed-last_shot_time > 0.6 and not bool(actor.input_state.get("fire",false)):
			reload_started = true
			first_reload_observation = "authority_fixture"
			actor.start_reload()
			print("EXPORT_UI_RELOAD_STARTED trigger=authority_fixture")
			observe("reload_started_by_authority_fixture")
		if actor.reload_remaining > 0:
			reload_seen = true
			if not reload_started:
				reload_started = true
				first_reload_observation = "reload_input_present_at_first_active_sample" if bool(actor.input_state.get("reload",false)) else "no_reload_input_at_first_active_sample"
				print("EXPORT_UI_RELOAD_STARTED trigger=native_client_input")
				observe("reload_started")
		if reload_seen and not reload_completed and actor.reload_remaining <= 0 and actor.ammo == 30:
			reload_completed = true
			print("EXPORT_UI_RELOAD_COMPLETED ammo=%d" % actor.ammo)
			observe("reload_completed")
			write_report()
		var signature := "%s/%s/%s/%s/%s/%s/%s/%s" % [actor.alive,actor.weapon_id,actor.ammo,actor.reserve,actor.reload_remaining>0,bool(actor.input_state.get("fire",false)),bool(actor.input_state.get("reload",false)),game.phase]
		if signature != telemetry_signature:
			telemetry_signature = signature
			observe("state_edge")
	telemetry_clock += delta
	if telemetry_clock >= 0.5:
		telemetry_clock = 0.0
		observe("periodic")
	var diagnostic_request := output.path_join("diagnostic-request")
	if FileAccess.file_exists(diagnostic_request):
		observe("controller_failure_snapshot")
		DirAccess.remove_absolute(diagnostic_request)
	if elapsed > 300 or FileAccess.file_exists(output.path_join("finish")):
		finishing = true
		finish.call_deferred()
	return false
func write_report() -> Dictionary:
	observe("report")
	var report := {"scope":"source Godot authority fixture; client is actual exported desktop binary driven through native UI; no rewards","joined_id":joined_id,"shots":shots,"lowest_ammo":lowest_ammo,"largest_ack":largest_ack,"reload_seen":reload_seen,"reload_completed":reload_completed,"reload_trigger":"authority fixture" if automatic_reload else "native client input", "reload_command_seen":reload_command_seen,"first_reload_observation":first_reload_observation,"prediction_default":game._prediction_enabled,"protocol":TacticalMatch.PROTOCOL_VERSION}
	report.passed = joined_id > 0 and shots > 0 and lowest_ammo < 30 and largest_ack > 10 and reload_seen and reload_completed and (automatic_reload or reload_command_seen)
	var file := FileAccess.open(output.path_join("authority.json"),FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"\t"))
	file.close()
	print("EXPORT_UI_AUTHORITY "+JSON.stringify(report))
	return report
func finish() -> void:
	var report := write_report()
	game.queue_free()
	await create_timer(0.2).timeout
	quit(0 if report.passed else 1)
