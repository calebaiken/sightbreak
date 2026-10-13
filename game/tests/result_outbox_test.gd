extends SceneTree
var failures := 0
var checks := 0
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)
func _initialize() -> void:
	var directory := ProjectSettings.globalize_path("user://outbox-test-%d" % Time.get_ticks_usec())
	var payload := {"match_id": "00000001-0000-4000-8000-000000000000", "mode": "ranked_5v5", "started_at": "2026-01-01T00:00:00Z", "ended_at": "2026-01-01T00:10:00Z", "participants": []}
	for id in range(10):
		payload.participants.append({"player_id": "%08x-0000-4000-8000-000000000000" % (id + 1), "won": id < 5, "active_seconds": 500, "objective_contributions": 0, "abandoned": false})
	var result := SBResultOutbox.stage(payload, directory)
	check(result.get("ok", false) and result.get("queued", false) and not result.has("rewards"), "handoff queued without claiming settlement")
	check(SBResultOutbox.stage(payload, directory).get("ok", false), "identical handoff retry accepted")
	check(DirAccess.get_files_at(directory).size() == 1, "one final file for exact match identity")
	payload.ended_at = "2026-01-01T00:10:01Z"
	check(not SBResultOutbox.stage(payload, directory).get("ok", true), "changed result cannot replace same identity")
	payload.match_id = "../../forged"
	check(not SBResultOutbox.stage(payload, directory).get("ok", true), "path traversal identity refused")
	payload.match_id = "00000002-0000-4000-8000-000000000000"
	check(not SBResultOutbox.stage(payload, "relative").get("ok", true), "ambiguous relative spool refused")
	payload.server_key = "must-not-persist"
	check(not SBResultOutbox.stage(payload, directory).get("ok", true), "top-level secrets refused before persistence")
	payload.erase("server_key")
	payload.participants[0].ticket = "must-not-persist"
	check(not SBResultOutbox.stage(payload, directory).get("ok", true), "nested secrets refused before persistence")
	payload.participants[0].erase("ticket")
	payload.extra = "x".repeat(20000)
	check(not SBResultOutbox.stage(payload, directory).get("ok", true), "oversized record refused")
	for file: String in DirAccess.get_files_at(directory):
		DirAccess.remove_absolute(directory.path_join(file))
	DirAccess.remove_absolute(directory)
	print("RESULT_OUTBOX_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
