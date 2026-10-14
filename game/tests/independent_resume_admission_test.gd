extends SceneTree
## Independent native-ENet review: separate SceneMultiplayer roots in one process.
## Spy account bridge deliberately tests calls, not PostgreSQL semantics.
class SpyBridge extends SBEconomyBridge:
	var inspected := 0
	var consumed := 0
	func inspect_ticket(_ticket: String) -> Dictionary:
		inspected += 1
		return {"ok": true, "data": {"player_id": "review-account", "display_name": "Review account"}}
	func consume_ticket(_ticket: String) -> Dictionary:
		consumed += 1
		return {"ok": true, "data": {"player_id": "review-account"}}

var checks := 0
var failures := 0
var branches: Array[Node] = []
var port := 33540
var server: TacticalMatch
var original: TacticalMatch
var spy: SpyBridge
func check(ok: bool, label: String) -> void:
	checks += 1
	print("REVIEW_ADMISSION %s %s" % ["PASS" if ok else "FAIL", label])
	if not ok: failures += 1
func _initialize() -> void:
	call_deferred("run")
func create_match(label: String, settings: Dictionary) -> TacticalMatch:
	var branch := Node.new()
	branch.name = label
	root.add_child(branch)
	var api := SceneMultiplayer.new()
	set_multiplayer(api, branch.get_path())
	branches.append(branch)
	var game := TacticalMatch.new()
	game.configure(settings)
	branch.add_child(game)
	return game
func wait_state(game: TacticalMatch, states: Array[String], seconds := 4.0) -> bool:
	var deadline := Time.get_ticks_msec() + int(seconds * 1000)
	while not game.connection_state in states and Time.get_ticks_msec() < deadline:
		await process_frame
	return game.connection_state in states
func dispose(game: TacticalMatch) -> void:
	var branch := game.get_parent()
	game.queue_free()
	await process_frame
	await process_frame
	set_multiplayer(null, branch.get_path())
	branches.erase(branch)
	branch.queue_free()
	await process_frame
func challenge(label: String, token: String) -> TacticalMatch:
	return create_match(label, {"mode": "client", "address": "127.0.0.1", "port": port, "reconnect_token": token, "join_ticket": "review-ticket-never-consumed".repeat(2)})
func run() -> void:
	server = create_match("Authority", {"mode": "server", "port": port})
	server.phase = "waiting"
	server._bot_clock = 1000
	original = challenge("Original", "")
	check(await wait_state(original, ["connected"]), "original client admitted over native ENet")
	if original.connection_state != "connected":
		await cleanup()
		quit(1)
		return
	var original_id := original.local_id
	var old_peer: int = server._peer_actors.find_key(original_id)
	spy = SpyBridge.new()
	server.add_child(spy)
	server._bridge = spy
	server.options.require_accounts = true
	server._account_ids[original_id] = "review-account"
	var challenger := challenge("BusyToken", original.reconnect_token)
	check(await wait_state(challenger, ["reconnecting", "failed"]), "valid occupied resume receives explicit response")
	check(challenger.connection_state == "reconnecting", "valid occupied reservation is transient")
	check(spy.inspected == 0 and spy.consumed == 0, "busy current credential bypasses ticket inspection and consumption")
	check(server._peer_actors.size() == 1 and server._peer_actors.get(old_peer) == original_id and original.connection_state == "connected", "live actor owner retains sole authority")
	check(server._join_slots.is_empty() and server._join_accounts.is_empty(), "busy retry has no provisional identity or slot claim")
	await dispose(challenger)
	challenger = challenge("DuplicateAccount", "")
	check(await wait_state(challenger, ["failed"]), "fresh duplicate account is terminal")
	check(spy.inspected == 1 and spy.consumed == 0 and server._peer_actors.size() == 1, "fresh duplicate cannot consume ticket or evict current owner")
	await dispose(challenger)
	server.options.require_accounts = false
	challenger = challenge("WrongGuestToken", "f".repeat(64))
	check(await wait_state(challenger, ["failed"]), "wrong guest resume token is terminal")
	check(server._peer_actors.size() == 1 and challenger.local_id == 0, "wrong guest token cannot acquire unrelated free actor")
	await dispose(challenger)
	server._reservations["e".repeat(64)] = {"id": 2, "expires": server._elapsed - 1.0}
	challenger = challenge("ExpiredGuestToken", "e".repeat(64))
	check(await wait_state(challenger, ["failed"]), "expired guest resume token is terminal")
	check(server._peer_actors.size() == 1 and challenger.local_id == 0 and not server._reservations.has("e".repeat(64)), "expired reservation cannot acquire actor and is retired")
	await dispose(challenger)
	check(server._peer_lifecycle.peers.size() <= 10 and server._peer_actors.size() == 1, "negative probes did not expand authority capacity")
	await cleanup()
	print("INDEPENDENT_RESUME_ADMISSION checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
func cleanup() -> void:
	if is_instance_valid(original): await dispose(original)
	if is_instance_valid(server): await dispose(server)
	await process_frame
	await process_frame
