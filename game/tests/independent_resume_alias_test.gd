extends SceneTree
## Native ENet alias safety, one process with isolated SceneMultiplayer roots.
## Expiry boundary uses an explicitly injected deadline; no twenty-second latency claim.
class UnconfirmedMatch extends TacticalMatch:
	var discarded := false
	var hold := false
	@rpc("authority", "call_remote", "reliable")
	func _welcome_rpc(_id: int, _token: String, _data: Dictionary) -> void:
		discarded = true
		if not hold:
			connection_state = "failed"
			multiplayer.multiplayer_peer.close()
var server: TacticalMatch
var checks := 0
var failures := 0
var port := 33543
func check(ok: bool, label: String) -> void:
	checks += 1
	print("REVIEW_ALIAS %s %s" % ["PASS" if ok else "FAIL", label])
	if not ok: failures += 1
func _initialize() -> void: call_deferred("run")
func setup(label: String, token := "", suppress := false, hold := false, authority := false) -> TacticalMatch:
	var branch := Node.new()
	branch.name = label
	root.add_child(branch)
	set_multiplayer(SceneMultiplayer.new(), branch.get_path())
	var game: TacticalMatch = UnconfirmedMatch.new() if suppress else TacticalMatch.new()
	if suppress: (game as UnconfirmedMatch).hold = hold
	game.configure({"mode": "server" if authority else "client", "port": port, "reconnect_token": token})
	branch.add_child(game)
	return game
func wait_until(test: Callable, seconds := 4.0) -> bool:
	var limit := Time.get_ticks_msec() + int(seconds * 1000)
	while not test.call() and Time.get_ticks_msec() < limit: await process_frame
	return test.call()
func dispose(game: TacticalMatch) -> void:
	var branch := game.get_parent()
	game.queue_free()
	await process_frame
	await process_frame
	set_multiplayer(null, branch.get_path())
	branch.queue_free()
	await process_frame
func run() -> void:
	server = setup("Authority", "", false, false, true)
	server.phase = "waiting"
	server._bot_clock = 1000
	var original := setup("Original")
	check(await wait_until(func(): return original.connection_state == "connected"), "original admission")
	var credential := original.reconnect_token
	var actor := original.local_id
	await dispose(original)
	check(await wait_until(func(): return server._peer_actors.is_empty()), "original owner retired")
	var unconfirmed := setup("UnconfirmedLive", credential, true, true) as UnconfirmedMatch
	check(await wait_until(func(): return unconfirmed.discarded), "first resume committed but welcome application suppressed")
	if not server._resume_aliases.has(actor):
		check(false, "pending alias exists")
		await dispose(unconfirmed)
		await dispose(server)
		quit(1)
		return
	var first: Dictionary = server._resume_aliases[actor].duplicate()
	var owner: int = server._peer_actors.find_key(actor)
	check(int(first.expires) > Time.get_ticks_msec() and int(first.expires) <= Time.get_ticks_msec() + SBReconnectPolicy.WINDOW_MSEC, "alias lifetime is at most twenty seconds from grant")
	check(str(first.token) == credential and str(first.current_token) != credential and int(first.peer) == owner, "alias is tied to original credential and replacement owner")
	var challenger := setup("AliasAgainstLiveOwner", credential)
	check(await wait_until(func(): return challenger.connection_state in ["reconnecting", "failed"]), "live-alias challenge receives response")
	check(challenger.connection_state == "reconnecting" and server._peer_actors.size() == 1 and server._peer_actors.get(owner) == actor, "previous alias cannot evict unconfirmed live owner")
	check(int(server._resume_aliases[actor].expires) == int(first.expires), "busy alias request does not renew grace")
	await dispose(challenger)
	await dispose(unconfirmed)
	check(await wait_until(func(): return server._peer_actors.is_empty()), "unconfirmed owner retired before alias reclamation")
	unconfirmed = setup("SecondLostWelcome", credential, true, false) as UnconfirmedMatch
	check(await wait_until(func(): return unconfirmed.discarded), "same previous credential recovers after lost welcome")
	await dispose(unconfirmed)
	check(await wait_until(func(): return server._peer_actors.is_empty()), "second unconfirmed generation retired")
	check(server._resume_aliases.size() == 1 and str(server._resume_aliases[actor].token) == credential and int(server._resume_aliases[actor].expires) == int(first.expires), "repeated lost welcome preserves single alias and original deadline")
	check(str(server._resume_aliases[actor].current_token) != str(first.current_token), "replacement generation rotates current credential")
	var confirmed := setup("Confirmed", credential)
	check(await wait_until(func(): return confirmed.connection_state == "connected"), "old alias recovers original actor before deadline")
	var confirmed_owner: int = server._peer_actors.find_key(actor)
	check(confirmed.local_id == actor and await wait_until(func(): return int(server._input_stream.acknowledged.get(confirmed_owner, 0)) > 0 and not server._resume_aliases.has(actor)), "first accepted input revokes previous credential for matching generation")
	challenger = setup("OldAliasAfterConfirmation", credential)
	check(await wait_until(func(): return challenger.connection_state == "failed"), "confirmed-session old alias is terminally invalid")
	check(server._peer_actors.size() == 1 and server._peer_actors.get(confirmed_owner) == actor, "old alias cannot displace confirmed authority")
	await dispose(challenger)
	credential = confirmed.reconnect_token
	await dispose(confirmed)
	check(await wait_until(func(): return server._peer_actors.is_empty()), "confirmed owner retired")
	unconfirmed = setup("ExpiryFixture", credential, true, false) as UnconfirmedMatch
	check(await wait_until(func(): return unconfirmed.discarded), "new pending alias created for expiry boundary")
	await dispose(unconfirmed)
	check(await wait_until(func(): return server._peer_actors.is_empty()), "expiry fixture owner retired")
	server._resume_aliases[actor].expires = Time.get_ticks_msec() - 1
	challenger = setup("ExpiredAlias", credential)
	check(await wait_until(func(): return challenger.connection_state == "failed"), "elapsed alias deadline rejects original token")
	check(server._peer_actors.is_empty() and not server._resume_aliases.has(actor), "expired alias has no actor authority and is removed")
	await dispose(challenger)
	check(server._resume_aliases.size() <= 10 and server._reservations.size() <= 10, "credential tables remain bounded by actor count")
	await dispose(server)
	await process_frame
	print("INDEPENDENT_RESUME_ALIAS checks=%d failures=%d" % [checks, failures])
	quit(0 if failures == 0 else 1)
