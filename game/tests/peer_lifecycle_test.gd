extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func _initialize() -> void:
	var life := SBPeerLifecycle.new()
	check(life.connected(2, 100), "connected entry created")
	check(not life.connected(2, 200), "repeat connected cannot refresh deadline")
	check(life.expired(20099).is_empty() and life.expired(20100) == [2], "silent compatible peer has fixed join deadline")
	var attempt := life.begin_join(2, 1000)
	check(attempt > 0 and life.begin_join(2, 1000) == -1, "one join attempt per transport")
	life.reject(2, 500)
	life.reject(2, 700)
	check(not life.current(2, attempt, 1000) and life.expired(1000) == [2], "rejection terminal and repeated rejection cannot rearm")
	life.forget(2)
	life.connected(2, 1000)
	check(not life.current(2, attempt, 1000), "reused peer ID cannot accept old HTTP response")
	attempt = life.begin_join(2, 1000)
	check(life.admitted(2, attempt, 1000), "current admission accepted")
	check(life.expired(30999).is_empty() and life.expired(31000) == [2], "joined idle peer deadline")
	life.active(2, 30000)
	check(life.expired(31000).is_empty(), "valid current input renews idle deadline")
	var allowed := 0
	for i in range(1000):
		allowed += int(life.allow_input(2, 30000))
	check(allowed == 90 and life.allow_input(2, 31000), "packet budget before decode and bounded reset")
	for peer in range(3, 12):
		life.connected(peer, 0)
	check(life.peers.size() == 10 and not life.connected(12, 0), "bounded peer table")
	life.forget(2)
	check(not life.allow_input(2, 32000) and life.peers.size() == 9, "disconnect cleanup releases rate and admission state")
	var delayed := SBPeerLifecycle.new()
	delayed.connected(90, 100)
	var old_attempt := delayed.begin_join(90, 100)
	check(not delayed.current(90, old_attempt, 20100) and not delayed.admitted(90, old_attempt, 20100), "late backend completion cannot revive expired admission")
	check(delayed.expired(20100) == [90], "expired entry remains due for cleanup")
	print("PEER_LIFECYCLE_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
