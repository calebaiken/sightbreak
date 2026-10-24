class_name SBInputGate
extends RefCounted
## Treat every field sent by a peer as untrusted. The server advances simulation time.
const BOOLEAN_FIELDS := ["fire", "reload", "jump", "crouch", "interact", "grenade", "smoke"]
var last_input: Dictionary = {}
var last_buy: Dictionary = {}
var rejected: int = 0

func validate(peer_id: int, data: Dictionary, now_msec: int) -> Dictionary:
	if now_msec - int(last_input.get(peer_id, -1000)) < 12:
		rejected += 1
		return {}
	last_input[peer_id] = now_msec
	if data.size() > 12 or not data.get("move", null) is Vector2 or not data.get("look", null) is Vector2:
		rejected += 1
		return {}
	var move: Vector2 = data.move
	var look: Vector2 = data.look
	if not move.is_finite() or not look.is_finite():
		rejected += 1
		return {}
	var clean: Dictionary = {"move": move.limit_length(1.0), "look": Vector2(wrapf(look.x, -PI, PI), clampf(look.y, -1.45, 1.45))}
	for field in BOOLEAN_FIELDS:
		clean[field] = data.get(field, false) == true
	var weapon: String = str(data.get("weapon", ""))
	if weapon.length() <= 24:
		clean.weapon = weapon
	return clean

func allow_buy(peer_id: int, now_msec: int) -> bool:
	if now_msec - int(last_buy.get(peer_id, -1000)) < 250:
		return false
	last_buy[peer_id] = now_msec
	return true

func forget(peer_id: int) -> void:
	last_input.erase(peer_id)
	last_buy.erase(peer_id)
