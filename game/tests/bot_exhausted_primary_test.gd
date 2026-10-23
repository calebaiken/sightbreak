extends "res://tests/bot_exhausted_primary_probe.gd"
## Maintained selection assertions and additive controls over the unchanged probe.
var policy_rows := 0
var range_rows := 0
var reserve_rows := 0
var far_loaded_rows: Array[Dictionary] = []

func _expected_weapon(row: Dictionary) -> String:
	var before: Dictionary = row.before
	var acquired: bool = int(row.decision_bot_state.target) != 0
	var enabled: bool = bool(SBBotAI.profile_for(str(row.scenario.difficulty)).sidearm_fallback)
	var distance: float = before.position.distance_to(row.enemy_before.position)
	var interacting: bool = bool(row.command.interact)
	if acquired and enabled and int(before.ammo) == 0 and before.weapon != "sidearm" and before.inventory.has("sidearm") and distance < 20.0 and not interacting:
		return "sidearm"
	var recorded_sidearm: bool = before.ammo_store.has("sidearm")
	var stored: Vector2i = before.ammo_store.get("sidearm", Vector2i.ZERO)
	var known_usable: bool = recorded_sidearm and (stored.x > 0 or stored.y > 0)
	if enabled and ["smg", "rifle", "marksman"].has(str(before.weapon)) and int(before.ammo) == 0 and int(before.reserve) == 0 and before.inventory.has("sidearm") and known_usable and not interacting:
		if not acquired or distance <= float(SBWeapons.get_weapon("sidearm").range):
			return "sidearm"
	if not acquired and before.weapon == "sidearm" and before.inventory.size() > 1:
		for primary in ["rifle", "marksman", "smg"]:
			if before.inventory.has(primary) and before.ammo_store.get(primary, Vector2i(-1, -1)) != Vector2i.ZERO:
				return primary
	return ""

func _observe(label: String, s: Dictionary, step: int, kind: String = "") -> Dictionary:
	var row := super._observe(label, s, step, kind)
	check(str(row.command.weapon) == _expected_weapon(row), label + " selection follows registered exhausted-primary boundary")
	policy_rows += 1
	if label.begins_with("sequence/") and label.ends_with("/far_loaded") and s.difficulty != "easy":
		far_loaded_rows.append(row)
	return row

func _sequence(difficulty: String, primary: String, setting: Dictionary) -> void:
	far_loaded_rows.clear()
	await super._sequence(difficulty, primary, setting)
	if setting.name != "far_loaded" or difficulty == "easy":
		return
	var actual_shots := 0
	var actual_draws := 0
	var impossible_reloads := 0
	for row in far_loaded_rows:
		actual_shots += int(row.shot_delta)
		actual_draws += int(row.switched)
		impossible_reloads += int(row.empty_reload_request)
	check(far_loaded_rows.size() == 8 and actual_draws == 1, difficulty + "/" + primary + " 24m sequence draws exactly once")
	check(actual_shots > 0 and bot.weapon_id == "sidearm" and bot.ammo == 15 - actual_shots and bot.reserve == 0, difficulty + "/" + primary + " 24m sequence consumes genuine sidearm shots")
	check(impossible_reloads == 0, difficulty + "/" + primary + " 24m sequence has no impossible reload repetition")

func _positive_controls() -> void:
	await super._positive_controls()
	emit_row("POLICY_HEADER", {"range_cases_expected": 9, "reserve_steps_expected": 20,
		"total_policy_rows_expected": 1268, "common_fixture_sha256": "540d24dda8e58f4685030e81b55ac3778ccbf31a89f76f9873ac598c32770731"})
	for primary in PRIMARIES:
		for boundary in [{"name": "inside", "distance": 44.9}, {"name": "boundary", "distance": 45.0}, {"name": "outside", "distance": 45.1}]:
			var target := {"name": "range_" + str(boundary.name), "distance": float(boundary.distance), "visible": true}
			var s := _spec("hard", primary, "exhausted", "loaded", target)
			_prepare(s)
			await _settle_pose()
			_observe("policy_range/" + primary + "/" + str(boundary.name), s, -1, "POLICY_RANGE")
			range_rows += 1
	await _reserve_reload_at_24m()
	check(range_rows == 9 and reserve_rows == 20 and policy_rows == 1268, "all maintained policy and supplement rows completed")
	emit_row("POLICY_RESULT", {"policy_rows": policy_rows, "range_rows": range_rows,
		"reserve_rows": reserve_rows, "failures_so_far": failures.duplicate()})

func _reserve_reload_at_24m() -> void:
	var target := {"name": "policy_reserve_24m", "distance": 24.0, "visible": true}
	var s := _spec("normal", "rifle", "exhausted", "reserve_only", target)
	s["control"] = "policy_reserve_24m"
	_prepare(s)
	await _settle_pose()
	var initial_target := _enemy_snapshot()
	var draws := 0
	var starts := 0
	var completions := 0
	var start_step := -1
	var completion_step := -1
	var impossible_reloads := 0
	var summary := {"name": "policy_reserve_24m", "steps": 20, "initial_shooter": _snapshot(),
		"initial_target": initial_target, "visibility_schedule": "visible only on step 0, then hidden"}
	for step in range(20):
		m._elapsed = 20.0 + DT * step
		bot.visible_enemy = step == 0
		var row := _observe("policy_reserve_24m", s, step, "POLICY_RESERVE_STEP")
		var before: Dictionary = row.after_decision
		var after: Dictionary = row.after_action
		draws += int(row.switched)
		impossible_reloads += int(row.empty_reload_request)
		check(int(row.shot_delta) == 0 and row.damage_events.is_empty() and row.elimination_events.is_empty(), "24m reserve-only control emits no shot or damage")
		if before.weapon == after.weapon and float(before.reload) == 0.0 and float(after.reload) > 0.0:
			starts += 1
			start_step = step
			check(after.weapon == "sidearm" and int(after.ammo) == 0 and int(after.reserve) == 15 and is_equal_approx(float(after.reload), float(SBWeapons.get_weapon("sidearm").reload)), "24m reserve-only accepted stock reload has full duration and no premature transfer")
		if before.weapon == after.weapon and float(before.reload) > 0.0 and float(after.reload) == 0.0:
			completions += 1
			completion_step = step
			check(after.weapon == "sidearm" and int(before.ammo) == 0 and int(before.reserve) == 15 and int(after.ammo) == 15 and int(after.reserve) == 0, "24m reserve-only stock completion transfers the reserve")
		reserve_rows += 1
	check(draws == 1 and starts == 1 and completions == 1, "24m reserve-only requires one real draw, reload start and completion")
	check(start_step == 1 and completion_step == 14, "24m reserve-only keeps existing deploy/reload timing")
	check(bot.weapon_id == "sidearm" and bot.ammo == 15 and bot.reserve == 0 and bot.reload_remaining == 0, "24m reserve-only finishes with usable loaded sidearm")
	check(impossible_reloads == 0 and _enemy_snapshot() == initial_target, "24m reserve-only prevents impossible reload repetition and preserves full target state")
	summary.merge({"draws": draws, "reload_starts": starts, "reload_completions": completions,
		"reload_start_step": start_step, "reload_completion_step": completion_step,
		"impossible_reload_requests": impossible_reloads, "final_shooter": _snapshot(), "final_target": _enemy_snapshot()})
	emit_row("POLICY_RESERVE", summary)
