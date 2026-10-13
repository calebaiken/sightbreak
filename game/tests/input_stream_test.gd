extends SceneTree
var checks := 0
var failures := 0
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)
func command(sequence: int, move: Vector2 = Vector2(0, 1)) -> Dictionary:
	return {"sequence": sequence, "move": move, "look": Vector2.ZERO}
func _initialize() -> void:
	var stream := SBInputStream.new()
	check(stream.accept(2, {"epoch": 1, "commands": [command(1), command(2)]}, 1, 0), "ordered batch accepted")
	check(stream.pop(2).sequence == 1 and stream.acknowledged[2] == 1, "one command advances ack once")
	check(stream.accept(2, {"epoch": 1, "commands": [command(2, Vector2.LEFT), command(3)]}, 1, 1), "newer input within 12 ms is retained")
	check(stream.pop(2).move == Vector2(0, 1), "repeated command identity cannot be rewritten")
	check(stream.pop(2).sequence == 3 and stream.pop(2).is_empty(), "no extra simulation budget from duplicates")
	check(stream.accept(2, {"epoch": 1, "commands": [command(3), command(4)]}, 1, 2), "redundant resend accepted")
	check(stream.pop(2).sequence == 4, "stale commands not replayed")
	check(not stream.accept(2, {"epoch": 0, "commands": [command(5)]}, 1, 3), "old round commands rejected")
	check(not stream.accept(2, {"epoch": 1, "commands": [command(999999)]}, 1, 4), "unreasonable sequence advance rejected")
	check(not stream.accept(2, {"epoch": 1, "commands": [command(5, Vector2(NAN, 0))]}, 1, 5), "nonfinite movement rejected")
	var malformed := command(5)
	malformed.jump = []
	check(not stream.accept(2, {"epoch": 1, "commands": [malformed]}, 1, 6), "boolean type enforced")
	check(stream.queues[2].is_empty(), "bad packets mutate no queued input")
	for i in range(5, 125):
		stream.accept(2, {"epoch": 1, "commands": [command(i)]}, 1, 1000 + i * 20)
	check(stream.queues[2].size() <= SBInputStream.MAX_AHEAD, "server queue bounded")
	stream.forget(2)
	check(not stream.queues.has(2) and not stream.acknowledged.has(2) and not stream.rates.has(2), "disconnect releases all stream state")
	var recovering := SBInputStream.new()
	for tick in range(1200):
		if tick % 2 == 0 and not (tick >= 300 and tick < 312):
			var batch: Array = []
			for sequence in range(maxi(1, tick - 10), tick + 2):
				batch.append(command(sequence))
			recovering.accept(7, {"epoch": 1, "commands": batch}, 1, tick * 17)
		recovering.pop(7)
		if tick in [600, 1199]:
			check(tick + 1 - int(recovering.acknowledged.get(7, 0)) <= 2, "temporary loss cannot leave permanent command backlog")
	check(recovering.skipped_commands > 0, "stale intent explicitly discarded without extra simulation steps")
	print("INPUT_STREAM_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
