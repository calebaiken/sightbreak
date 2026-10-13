class_name SBPeerLifecycle
extends RefCounted
## Monotonic-wall-clock bounds, independent of round clocks and simulation stalls.
const JOIN_MSEC := 20000
const IDLE_MSEC := 30000
const REJECT_MSEC := 500
const MAX_PEERS := 10
var peers: Dictionary = {}
var generation := 0

func connected(peer: int, now: int) -> bool:
	if peers.has(peer) or peers.size() >= MAX_PEERS:
		return false
	generation += 1
	peers[peer] = {"generation": generation, "deadline": now + JOIN_MSEC, "joined": false, "attempted": false, "rejected": false, "last_input": now, "rate_start": now, "rate_count": 0}
	return true

func begin_join(peer: int, now: int) -> int:
	if not peers.has(peer) or peers[peer].attempted or peers[peer].rejected or now >= int(peers[peer].deadline):
		return -1
	peers[peer].attempted = true
	return int(peers[peer].generation)

func current(peer: int, attempt: int, now: int) -> bool:
	return peers.has(peer) and int(peers[peer].generation) == attempt and not peers[peer].rejected and now < int(peers[peer].deadline)

func admitted(peer: int, attempt: int, now: int) -> bool:
	if not current(peer, attempt, now):
		return false
	peers[peer].joined = true
	peers[peer].last_input = now
	return true

func reject(peer: int, now: int) -> void:
	if peers.has(peer) and not peers[peer].rejected:
		peers[peer].rejected = true
		peers[peer].deadline = now + REJECT_MSEC

func allow_input(peer: int, now: int) -> bool:
	if not peers.has(peer) or not peers[peer].joined or peers[peer].rejected or now - int(peers[peer].last_input) >= IDLE_MSEC:
		return false
	var entry: Dictionary = peers[peer]
	if now - int(entry.rate_start) >= 1000:
		entry.rate_start = now
		entry.rate_count = 0
	entry.rate_count += 1
	return int(entry.rate_count) <= 90

func active(peer: int, now: int) -> void:
	if peers.has(peer) and peers[peer].joined and not peers[peer].rejected and now - int(peers[peer].last_input) < IDLE_MSEC:
		peers[peer].last_input = now

func expired(now: int) -> Array[int]:
	var result: Array[int] = []
	for peer: int in peers:
		var entry: Dictionary = peers[peer]
		if (entry.rejected or not entry.joined) and now >= int(entry.deadline):
			result.append(peer)
		elif entry.joined and now - int(entry.last_input) >= IDLE_MSEC:
			result.append(peer)
	return result

func forget(peer: int) -> void:
	peers.erase(peer)
