extends SceneTree
const Profile = preload("res://scripts/profile.gd")
var checks := 0
var failures := 0
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(message)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	if FileAccess.file_exists(Profile.PATH):
		push_error("Profile test requires an empty isolated SIGHTBREAK_STATE_DIR; refusing to replace existing local progress.")
		quit(2)
		return
	var profile = Profile.new()
	var reward: Dictionary = profile.record_match({"won": true, "kills": 12, "deaths": 3, "objectives": 2})
	check(reward.save_error == OK, "Atomic profile save succeeds")
	check(profile.data.xp == 400, "Kills and objectives contribute training XP")
	check(profile.data.credits == 575, "First match, win, daily and level rewards calculated")
	var loaded = Profile.new()
	loaded.load_profile()
	check(loaded.data.xp == 400 and loaded.data.credits == 575, "JSON numeric progress survives reopening")
	check(loaded.data.matches == 1 and loaded.data.deaths == 3 and loaded.data.kills == 12, "Career numeric fields survive reopening")
	check(loaded.data.history.size() == 1 and loaded.data.history[0].objectives == 2, "Recent match results persist")
	loaded.record_match({"won": false, "kills": 0, "deaths": 1, "objectives": 0})
	check(loaded.data.credits == 675, "Daily first-match reward is not repeated")
	check(loaded.data.scope == "offline_training", "Local profile remains explicitly offline")
	check(Profile.level_for_xp(-100) == 1 and Profile.level_for_xp(600) == 3, "Level curve boundary checks")
	loaded.data.settings.sensitivity = "corrupted-value"
	loaded.data.settings.hud_positions = "corrupted-value"
	loaded.save()
	var recovered = Profile.new()
	recovered.load_profile()
	check(recovered.data.settings.sensitivity == Profile.DEFAULTS.settings.sensitivity and recovered.data.settings.hud_positions is Dictionary, "Corrupt setting types fall back to safe defaults")
	DirAccess.remove_absolute(Profile.PATH)
	print("PROFILE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
