class_name OfflineProfile
extends RefCounted

const PATH := "user://offline_training.json"
const DEFAULTS := {
	"schema": 1, "scope": "offline_training", "display_name": "Operator",
	"xp": 0, "level": 1, "credits": 0, "matches": 0, "wins": 0,
	"kills": 0, "deaths": 0, "last_daily": "", "history": [],
	"settings": {"sensitivity": 0.0028, "touch_sensitivity": 0.004, "fov": 78.0,
		"volume": 0.65, "difficulty": 1, "gyro": false, "gyro_sensitivity": 1.2,
		"touch_visible": false, "reduced_motion": false, "crosshair_color": "d9eac6",
		"crosshair_size": 5.0, "fps_limit": 60, "graphics_quality": 1, "hud_scale": 1.0, "hud_positions": {}}
}
var data: Dictionary = DEFAULTS.duplicate(true)

func load_profile() -> void:
	if not FileAccess.file_exists(PATH):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	if parsed is Dictionary and parsed.get("scope") == "offline_training" and parsed.get("schema") == 1:
		for key in DEFAULTS:
			if key == "settings" or not parsed.has(key):
				continue
			if typeof(DEFAULTS[key]) == TYPE_INT and (parsed[key] is int or parsed[key] is float):
				if is_finite(float(parsed[key])):
					data[key] = maxi(0, int(parsed[key]))
			elif typeof(parsed[key]) == typeof(DEFAULTS[key]):
				data[key] = parsed[key]
		if parsed.get("settings") is Dictionary:
			for key in DEFAULTS.settings:
				if not parsed.settings.has(key):
					continue
				var candidate: Variant = parsed.settings[key]
				var expected: Variant = DEFAULTS.settings[key]
				if (expected is int or expected is float) and (candidate is int or candidate is float):
					if is_finite(float(candidate)): data.settings[key] = candidate
				elif typeof(candidate) == typeof(expected):
					data.settings[key] = candidate
		data.xp = maxi(0, int(data.xp))
		data.level = level_for_xp(int(data.xp))
		data.credits = maxi(0, int(data.credits))
		data.settings.sensitivity = clampf(float(data.settings.sensitivity), 0.0005, 0.008)
		data.settings.touch_sensitivity = clampf(float(data.settings.touch_sensitivity), 0.001, 0.012)
		data.settings.fov = clampf(float(data.settings.fov), 60.0, 100.0)
		data.settings.volume = clampf(float(data.settings.volume), 0.0, 1.0)

func save() -> Error:
	var file := FileAccess.open(PATH + ".tmp", FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	return DirAccess.rename_absolute(PATH + ".tmp", PATH)

static func level_for_xp(xp: int) -> int:
	return 1 + int(sqrt(float(maxi(xp, 0)) / 150.0))

func record_match(summary: Dictionary) -> Dictionary:
	# Only local training progress. Never serialized into economy API requests.
	var victory := bool(summary.get("won", false))
	var earned := 100 + (75 if victory else 0)
	var today := Time.get_date_string_from_system(true)
	if data.last_daily != today:
		earned += 150
		data.last_daily = today
	var xp := 120 + int(summary.get("kills", 0)) * 15 + int(summary.get("objectives", 0)) * 50
	var old_level: int = data.level
	data.xp += xp
	data.level = level_for_xp(data.xp)
	earned += (data.level - old_level) * 250
	data.credits += earned
	data.matches += 1
	data.wins += int(victory)
	data.kills += int(summary.get("kills", 0))
	data.deaths += int(summary.get("deaths", 0))
	var entry := summary.duplicate(true)
	entry["time"] = Time.get_datetime_string_from_system(true)
	entry["credits_earned"] = earned
	data.history.push_front(entry)
	data.history = data.history.slice(0, 30)
	var error := save()
	return {"credits": earned, "xp": xp, "level": data.level, "save_error": error}
