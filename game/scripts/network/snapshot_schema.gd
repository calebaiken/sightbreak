class_name SBSnapshotSchema
extends RefCounted
## Validate the entire packet before mutating client state. Never deserialize objects.
static func number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

static func vector(value: Variant) -> bool:
	return value is Vector3 and value.is_finite() and value.length() < 1024

static func valid(data: Dictionary) -> bool:
	if data.size() > 24 or not data.get("actors") is Array or data.actors.size() != 10:
		return false
	for field: String in ["tick", "epoch"]:
		if not data.get(field) is int or data[field] < 0:
			return false
	if not data.get("phase") in ["waiting", "buy", "live", "post", "match_over"] or not data.get("objective") in ["unknown", "carried", "dropped", "planted", "defused", "detonated"]:
		return false
	for field: String in ["round", "attack", "defend", "time", "objective_timer", "carrier", "elapsed"]:
		if not number(data.get(field)) or float(data[field]) < 0:
			return false
	if not vector(data.get("objective_position")) or not data.get("interactions") is Dictionary or data.interactions.size() > 10:
		return false
	for id: Variant in data.interactions:
		if not id is int or id < 1 or id > 10 or not number(data.interactions[id]):
			return false
	if not data.get("humans", []) is Array or data.get("humans", []).size() > 10 or not data.get("contributions", {}) is Dictionary:
		return false
	for id: Variant in data.get("humans", []):
		if not id is int or id < 1 or id > 10:
			return false
	for id: Variant in data.get("contributions", {}):
		if not id is int or id < 1 or id > 10 or not number(data.contributions[id]):
			return false
	var ids: Dictionary = {}
	for state: Variant in data.actors:
		if not state is Dictionary or state.size() > 30 or not state.get("id") is int or state.id < 1 or state.id > 10 or ids.has(state.id):
			return false
		ids[state.id] = true
		for field: String in ["kills", "deaths", "assists"]:
			if not number(state.get(field)):
				return false
		if not state.get("team") in [0, 1] or not state.get("alive") is bool or not state.get("name") is String or state.name.length() > 24:
			return false
		if state.has("relevant") and not state.relevant is bool:
			return false
		if state.has("crouch") and not state.crouch is bool:
			return false
		if bool(state.get("relevant", true)) and not vector(state.get("position")):
			return false
		for field: String in ["position", "velocity"]:
			if state.has(field) and not vector(state[field]):
				return false
		for field: String in ["yaw", "pitch", "health", "kills", "deaths", "assists", "credits", "ammo", "reserve", "reload", "grenades", "smokes"]:
			if state.has(field) and not number(state[field]):
				return false
		if state.has("recoil") and (not state.recoil is Vector2 or not state.recoil.is_finite()):
			return false
		if state.has("weapon") and (not state.weapon is String or not SBWeapons.DATA.has(state.weapon)):
			return false
		if state.has("inventory"):
			if not state.inventory is Array or state.inventory.size() > 8:
				return false
			for weapon: Variant in state.inventory:
				if not weapon is String or not SBWeapons.DATA.has(weapon):
					return false
	if not data.get("utilities", []) is Array or data.get("utilities", []).size() > 64:
		return false
	for utility: Variant in data.get("utilities", []):
		if not utility is Dictionary or not utility.get("id") is int or not utility.get("kind") in ["smoke", "grenade"] or not vector(utility.get("position")) or not utility.get("detonated") is bool or not number(utility.get("life")):
			return false
	return true
