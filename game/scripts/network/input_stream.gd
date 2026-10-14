class_name SBInputStream
extends RefCounted
## Input packets carry redundant ordered commands; one command consumes one
## authority physics step. Neither client timestamps nor packet bursts grant time.
const MAX_BATCH := 12
const MAX_AHEAD := 120
const MAX_BACKLOG := 6
var skipped_commands := 0
var queues: Dictionary = {}
var acknowledged: Dictionary = {}
var rates: Dictionary = {}
var rejected := 0

func accept(peer: int, packet: Dictionary, round_epoch: int, now_msec: int) -> bool:
	var bucket: Dictionary = rates.get(peer, {"start": now_msec, "count": 0})
	if now_msec - int(bucket.start) >= 1000:
		bucket = {"start": now_msec, "count": 0}
	bucket.count += 1
	rates[peer] = bucket
	if bucket.count > 90 or packet.size() > 2 or not packet.get("epoch") is int or packet.epoch != round_epoch or not packet.get("commands") is Array or packet.commands.is_empty() or packet.commands.size() > MAX_BATCH:
		rejected += 1
		return false
	var staged: Dictionary = {}
	var ack: int = acknowledged.get(peer, 0)
	for command: Variant in packet.commands:
		if not command is Dictionary or not command.get("sequence") is int or command.sequence < 1 or command.sequence > ack + MAX_AHEAD:
			rejected += 1
			return false
		var clean := sanitize(command)
		if clean.is_empty():
			rejected += 1
			return false
		if command.sequence > ack:
			staged[command.sequence] = clean
	var queue: Dictionary = queues.get(peer, {})
	# A command identity is immutable after first receipt.
	for sequence: int in staged:
		if not queue.has(sequence):
			queue[sequence] = staged[sequence]
	queues[peer] = queue
	return true

static func sanitize(data: Dictionary) -> Dictionary:
	if not data.get("sequence") is int or data.size() > 12 or not data.get("move") is Vector2 or not data.get("look") is Vector2:
		return {}
	var move: Vector2 = data.move
	var look: Vector2 = data.look
	if not move.is_finite() or not look.is_finite():
		return {}
	var clean := {"sequence": int(data.sequence), "move": move.limit_length(1), "look": Vector2(wrapf(look.x, -PI, PI), clampf(look.y, -1.42, 1.42))}
	for key: String in SBInputGate.BOOLEAN_FIELDS:
		if data.has(key) and not data[key] is bool:
			return {}
		clean[key] = data.get(key, false)
	var weapon: Variant = data.get("weapon", "")
	if not weapon is String or weapon.length() > 24:
		return {}
	clean.weapon = weapon
	return clean

func pop(peer: int) -> Dictionary:
	var queue: Dictionary = queues.get(peer, {})
	if queue.is_empty():
		return {}
	var ordered := queue.keys()
	ordered.sort()
	# A temporary outage must not add permanent command latency. Skip stale
	# intent once backlog exceeds 100 ms, retaining the two newest fixed steps.
	# Never run catch-up combat/physics ticks or grant extra simulation time.
	if ordered.size() > MAX_BACKLOG:
		while ordered.size() > 2:
			queue.erase(ordered.pop_front())
			skipped_commands += 1
	var sequence: int = ordered[0]
	var command: Dictionary = queue[sequence]
	queue.erase(sequence)
	acknowledged[peer] = sequence
	return command

func forget(peer: int) -> void:
	queues.erase(peer)
	acknowledged.erase(peer)
	rates.erase(peer)

func reset_epoch() -> void:
	queues.clear()
	acknowledged.clear()
