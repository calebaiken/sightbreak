extends SceneTree
## Common baseline/candidate fixture. Visibility is injected; equip consumption is real.
## Default exit status retains failures on the unchanged baseline.
const DT := 0.12
const SEED := 3841

class VisibilityActor extends "res://scripts/gameplay/actor.gd":
	var visible_enemy := false
	func can_see(other: SBActor) -> bool:
		return visible_enemy and other != null and other.alive

var m: TacticalMatch
var bot: VisibilityActor
var enemy: SBActor
var failures: Array[String] = []
var checks := 0
var cases := 0
var sequence_steps := 0
var shots := 0

func _initialize() -> void:
	_run.call_deferred()

func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)

func _run() -> void:
	print("BOT_DRY_WEAPON_ENGINE " + JSON.stringify(Engine.get_version_info()))
	m = TacticalMatch.new()
	m.configure({"mode": "offline", "difficulty": "normal"})
	root.add_child(m)
	m.set_physics_process(false)
	m.local_id = 0
	m.actors[6].free()
	bot = VisibilityActor.new()
	bot.actor_id = 6
	bot.team = 1
	m.actors[6] = bot
	m.add_child(bot)
	bot.shot_fired.connect(func(_id: int, _origin: Vector3, _direction: Vector3) -> void: shots += 1)
	enemy = m.actors[1]
	for difficulty in ["easy", "normal", "hard"]:
		for primary in ["rifle", "marksman", "smg"]:
			for ammo_case in [
				{"name": "dry", "stored": Vector2i(0, 0), "expected": ""},
				{"name": "clip", "stored": Vector2i(1, 0), "expected": primary},
				{"name": "reserve", "stored": Vector2i(0, 1), "expected": primary},
				{"name": "unknown", "expected": primary}
			]:
				var store := {}
				if ammo_case.has("stored"):
					store[primary] = ammo_case.stored
				_decision(difficulty, primary + "_" + str(ammo_case.name), {
					"inventory": ["sidearm", primary], "store": store,
					"expected_weapon": ammo_case.expected, "expected_reload": false
				})
		_primary_controls(difficulty)
		_combat_controls(difficulty)
		_sequence(difficulty, false)
		_sequence(difficulty, true)
	check(TacticalMatch.PROTOCOL_VERSION == 6, "protocol remains 6")
	check(m._ranked_payload().is_empty(), "offline fixture has no ranked payload")
	m.queue_free()
	await process_frame
	for failure in failures:
		print("BOT_DRY_WEAPON_FAILURE " + failure)
	print("BOT_DRY_WEAPON_RESULT " + JSON.stringify({
		"cases": cases, "sequence_steps": sequence_steps, "checks": checks,
		"failures": failures.size(), "passed": failures.is_empty()
	}))
	quit(0 if failures.is_empty() else 1)

func _primary_controls(difficulty: String) -> void:
	for item in [
		{"name": "unowned_usable", "inventory": ["sidearm"], "store": {"rifle": Vector2i(30, 90)}, "expected_weapon": ""},
		{"name": "skip_dry_first", "inventory": ["sidearm", "smg", "marksman", "rifle"], "store": {"rifle": Vector2i(0, 0), "marksman": Vector2i(1, 0), "smg": Vector2i(1, 0)}, "expected_weapon": "marksman"},
		{"name": "unknown_keeps_priority", "inventory": ["sidearm", "marksman", "rifle"], "store": {"marksman": Vector2i(1, 0)}, "expected_weapon": "rifle"},
		{"name": "all_dry", "inventory": ["sidearm", "rifle", "marksman", "smg"], "store": {"rifle": Vector2i(0, 0), "marksman": Vector2i(0, 0), "smg": Vector2i(0, 0)}, "expected_weapon": ""},
		{"name": "stale_active_dry_cache", "inventory": ["sidearm", "rifle"], "store": {"sidearm": Vector2i(0, 0), "rifle": Vector2i(0, 0)}, "expected_weapon": ""},
		{"name": "stale_active_loaded_cache", "inventory": ["sidearm", "rifle"], "ammo": 0, "reserve": 0, "store": {"sidearm": Vector2i(15, 60), "rifle": Vector2i(0, 0)}, "expected_weapon": "", "expected_reload": true},
		{"name": "active_primary_loaded", "active": "rifle", "inventory": ["sidearm", "rifle"], "ammo": 30, "reserve": 0, "store": {"rifle": Vector2i(0, 0)}, "expected_weapon": ""},
		{"name": "active_primary_empty_reserve", "active": "rifle", "inventory": ["sidearm", "rifle"], "ammo": 0, "reserve": 30, "store": {"rifle": Vector2i(30, 90)}, "expected_weapon": "", "expected_reload": true},
		{"name": "active_primary_fully_dry", "active": "rifle", "inventory": ["sidearm", "rifle"], "ammo": 0, "reserve": 0, "expected_weapon": "", "expected_reload": true},
		{"name": "interacting_return_unchanged", "inventory": ["sidearm", "rifle"], "store": {"rifle": Vector2i(1, 0)}, "interact": true, "expected_weapon": "rifle"}
	]:
		_decision(difficulty, str(item.name), item)

func _combat_controls(difficulty: String) -> void:
	var fallback := "" if difficulty == "easy" else "sidearm"
	for reserve in [0, 30]:
		_decision(difficulty, "close_empty_clip_reserve_%d" % reserve, {
			"active": "rifle", "ammo": 0, "reserve": reserve, "visible": true,
			"inventory": ["sidearm", "rifle"], "store": {"sidearm": Vector2i(15, 60)},
			"expected_weapon": fallback, "expected_reload": difficulty == "easy"
		})
	for item in [
		{"name": "distance_boundary", "distance": 20.0, "ammo": 0, "expected_reload": true},
		{"name": "loaded_clip", "ammo": 1, "expected_reload": false},
		{"name": "unowned_sidearm", "inventory": ["rifle"], "ammo": 0, "expected_reload": true},
		{"name": "interacting_fallback_unchanged", "ammo": 0, "interact": true, "expected_reload": false}
	]:
		var c: Dictionary = item.duplicate(true)
		c["active"] = "rifle"
		c["visible"] = true
		c["reserve"] = 30
		c["expected_weapon"] = ""
		if not c.has("inventory"):
			c["inventory"] = ["sidearm", "rifle"]
		_decision(difficulty, str(item.name), c)

func _prepare(difficulty: String, c: Dictionary) -> void:
	m.options.difficulty = difficulty
	m.phase = "live"
	m.time_left = 100.0
	m.round_number = 2
	m._elapsed = 20.0
	m._rng.seed = SEED
	m._heard.clear()
	m._team_ai_state = SBBotAI.create_team_state()
	m.objective_state = "planted" if bool(c.get("interact", false)) else "carried"
	m.objective_carrier = 0
	m.objective_position = m.arena.sites[0]
	for other: SBActor in m.actors.values():
		other.alive = false
		other.position = Vector3(100 + other.actor_id * 4, 0, 100)
	bot.inventory.assign(c.get("inventory", ["sidearm", "rifle"]))
	var active := str(c.get("active", "sidearm"))
	if bot.weapon_id != active:
		bot._equip(active)
	bot._ammo_store = c.get("store", {}).duplicate(true)
	bot.ammo = int(c.get("ammo", 15))
	bot.reserve = int(c.get("reserve", 60))
	bot.alive = true
	bot.health = 100
	bot.credits = 800
	bot.grenades = 0
	bot.smokes = 0
	bot.reload_remaining = 0.0
	bot._deploy_remaining = 0.0
	bot._weapon_cooldowns.clear()
	bot.recoil = Vector2.ZERO
	bot.input_state.clear()
	bot.position = m.arena.sites[0] if bool(c.get("interact", false)) else Vector3(-14, 0, -10)
	bot.yaw = -PI / 2.0
	bot.pitch = 0.0
	bot.visible_enemy = bool(c.get("visible", false))
	enemy.alive = true
	enemy.team = 0
	enemy.position = bot.position + Vector3(float(c.get("distance", 6.0)), 0, 0)
	m._reset_bot_state(bot)

func _protected() -> Array:
	return [bot.weapon_id, bot.ammo, bot.reserve, bot.reload_remaining, bot._deploy_remaining,
		bot._weapon_cooldowns.duplicate(true), bot.inventory.duplicate(), bot._ammo_store.duplicate(true),
		bot.credits, bot.health, bot.smokes, bot.grenades]

func _decision(difficulty: String, name: String, c: Dictionary) -> void:
	_prepare(difficulty, c)
	var before := _protected()
	m._bot_input(bot, DT)
	cases += 1
	var label := difficulty + "/" + name
	check(before == _protected(), label + " decision preserves authority state")
	check(str(bot.input_state.weapon) == str(c.expected_weapon), label + " expected weapon " + str(c.expected_weapon))
	check(bool(bot.input_state.reload) == bool(c.get("expected_reload", false)), label + " expected reload")
	check(bool(bot.input_state.interact) == bool(c.get("interact", false)), label + " expected interaction")
	check(int(m._bot_state[6].target) == (1 if bool(c.get("visible", false)) else 0), label + " expected acquired target")
	print("BOT_DRY_WEAPON_CASE " + JSON.stringify({
		"difficulty": difficulty, "name": name, "active": bot.weapon_id,
		"ammo": bot.ammo, "reserve": bot.reserve, "requested": bot.input_state.weapon,
		"reload": bot.input_state.reload, "interact": bot.input_state.interact,
		"target": m._bot_state[6].target, "expected_weapon": c.expected_weapon,
		"expected_reload": c.get("expected_reload", false)
	}))

func _ammo_total() -> int:
	var total := bot.ammo + bot.reserve
	for weapon: String in bot.inventory:
		if weapon != bot.weapon_id:
			var stored: Vector2i = bot._ammo_store[weapon]
			total += stored.x + stored.y
	return total

func _sequence(difficulty: String, alternating: bool) -> void:
	_prepare(difficulty, {"store": {"rifle": Vector2i(0, 0)}})
	var initial_total := _ammo_total()
	var initial_shots := shots
	var switches := 0
	var dry_equips := 0
	var empty_reloads := 0
	var name := "alternating" if alternating else "idle"
	for step in range(8):
		bot.visible_enemy = alternating and step % 2 == 1
		m._elapsed = 20.0 + DT * step
		var before := _protected()
		var prior_weapon := bot.weapon_id
		m._bot_input(bot, DT)
		check(before == _protected(), "%s/%s step %d decision preserves authority" % [difficulty, name, step])
		if bool(bot.input_state.reload) and bot.ammo == 0 and bot.reserve == 0:
			empty_reloads += 1
		var command := bot.input_state.duplicate(true)
		bot.tick_authority_actions(DT)
		if bot.weapon_id != prior_weapon:
			switches += 1
			if bot.ammo == 0 and bot.reserve == 0:
				dry_equips += 1
		check(_ammo_total() == initial_total, "%s/%s step %d conserves ammo" % [difficulty, name, step])
		check(bot.credits == 800 and bot.health == 100 and bot.inventory == ["sidearm", "rifle"], "%s/%s step %d preserves other authority" % [difficulty, name, step])
		sequence_steps += 1
		print("BOT_DRY_WEAPON_STEP " + JSON.stringify({
			"difficulty": difficulty, "sequence": name, "step": step, "visible": bot.visible_enemy,
			"prior_weapon": prior_weapon, "requested": command.weapon, "reload": command.reload,
			"fire": command.fire, "active": bot.weapon_id, "ammo": bot.ammo, "reserve": bot.reserve,
			"reload_remaining": bot.reload_remaining, "deploy_remaining": bot._deploy_remaining,
			"total_ammo": _ammo_total(), "shots": shots - initial_shots
		}))
	check(switches == 0, difficulty + "/" + name + " avoids switches to or from a dry primary")
	check(dry_equips == 0, difficulty + "/" + name + " avoids dry equips")
	check(empty_reloads == 0, difficulty + "/" + name + " avoids repeated dry reload requests")
	check(shots == initial_shots, difficulty + "/" + name + " one-tick sightings do not bypass reaction")
	print("BOT_DRY_WEAPON_SEQUENCE " + JSON.stringify({
		"difficulty": difficulty, "sequence": name, "switches": switches, "dry_equips": dry_equips,
		"empty_reloads": empty_reloads, "shots": shots - initial_shots
	}))
