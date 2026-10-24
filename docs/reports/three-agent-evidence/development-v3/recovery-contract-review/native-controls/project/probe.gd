extends SceneTree
## Harness only. Production functions/module are frozen separately, without aliases.
const JOURNAL = preload("res://transaction_journal.gd")
const PREDICATES = preload("res://receipt_predicates.gd")
var evidence_root: String = ""
var role: String = ""
var journal
var checks: Array = []
var all_passed: bool = true

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--role="):
			role = argument.trim_prefix("--role=")
		if argument.begins_with("--evidence-root="):
			evidence_root = argument.trim_prefix("--evidence-root=").replace("\\", "/")
	call_deferred("_run")

func _check(name: String, actual: Variant, expected: Variant) -> void:
	var passed: bool = actual == expected
	checks.append({"name": name, "actual": actual, "expected": expected, "passed": passed})
	all_passed = all_passed and passed

func _emit(filename: String, data: Dictionary) -> void:
	data["complete"] = true
	data["role"] = role
	data["pid"] = OS.get_process_id()
	data["engine"] = Engine.get_version_info()
	data["checks"] = checks.duplicate(true)
	data["checks_passed"] = all_passed
	var destination: String = evidence_root.path_join("raw").path_join(filename)
	if FileAccess.file_exists(destination):
		push_error("Refusing to overwrite native evidence: " + destination)
		quit(10)
		return
	var text: String = JSON.stringify(data)
	var file: FileAccess = FileAccess.open(destination, FileAccess.WRITE)
	if file == null:
		push_error("Cannot persist native evidence: " + destination)
		quit(11)
		return
	file.store_string(text + "\n")
	file.flush()
	var result: Error = file.get_error()
	file.close()
	if result != OK:
		push_error("Native evidence write failed: " + str(result))
		quit(12)
		return
	print("NATIVE_JSON " + filename + " " + text)

func _wait_for(filename: String) -> bool:
	var start: int = Time.get_ticks_msec()
	while Time.get_ticks_msec() - start < 9000:
		if FileAccess.file_exists(evidence_root.path_join("signals").path_join(filename)):
			return true
		await create_timer(0.025).timeout
	return false

func _run() -> void:
	if role == "A":
		await _run_a()
	elif role == "B":
		await _run_b()
	else:
		push_error("Unknown harness role")
		quit(13)

func _predicate_controls() -> Array:
	var predicate = PREDICATES.new()
	# Synthetic legitimate-shape controls, not replayed backend receipts.
	var complete_item: Dictionary = {"id": "legitimate-instance", "definition_id": "obsidian_common", "name": "AR-7 / Graphite", "kind": "weapon_skin", "rarity": "Common", "collection": "Obsidian", "wear": 0.18, "pattern_seed": 44, "variant": "Standard", "reserved": false}
	var cases: Array = [
		{"name": "market_minimal_unrelated_body", "path": "/market/requested-listing/buy", "body": {"item": {"id": "unrelated"}, "credits": 0, "fee": 0}, "expected": true, "kind": "finding"},
		{"name": "case_minimal_partial_body", "path": "/cases/open", "body": {"item": {"id": "partial"}, "roll": 0, "table_version": "anything"}, "expected": true, "kind": "finding"},
		{"name": "market_legitimate_shape", "path": "/market/requested-listing/buy", "body": {"item": complete_item, "credits": 900, "fee": 3}, "expected": true, "kind": "positive"},
		{"name": "case_legitimate_shape", "path": "/cases/open", "body": {"item": complete_item, "roll": 4321, "table_version": "v1"}, "expected": true, "kind": "positive"},
		{"name": "store_legitimate_shape", "path": "/store/buy", "body": {"item": {"id": "supply-instance", "definition_id": "obsidian_case", "kind": "case", "name": "Obsidian Case"}, "credits": 900}, "expected": true, "kind": "positive"},
		{"name": "market_missing_item", "path": "/market/requested-listing/buy", "body": {"credits": 0, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_item_is_array", "path": "/market/requested-listing/buy", "body": {"item": [], "credits": 0, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_empty_id", "path": "/market/requested-listing/buy", "body": {"item": {"id": ""}, "credits": 0, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_numeric_id", "path": "/market/requested-listing/buy", "body": {"item": {"id": 7}, "credits": 0, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_missing_credits", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_negative_credits", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": -1, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_fractional_credits", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": 0.5, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_string_credits", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": "0", "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_boolean_credits", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": true, "fee": 0}, "expected": false, "kind": "negative"},
		{"name": "market_missing_fee", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": 0}, "expected": false, "kind": "negative"},
		{"name": "market_negative_fee", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": 0, "fee": -1}, "expected": false, "kind": "negative"},
		{"name": "market_fee_over_bound", "path": "/market/requested-listing/buy", "body": {"item": {"id": "item"}, "credits": 0, "fee": 10000001}, "expected": false, "kind": "negative"},
		{"name": "case_missing_roll", "path": "/cases/open", "body": {"item": {"id": "item"}, "table_version": "v1"}, "expected": false, "kind": "negative"},
		{"name": "case_roll_over_bound", "path": "/cases/open", "body": {"item": {"id": "item"}, "roll": 10000, "table_version": "v1"}, "expected": false, "kind": "negative"},
		{"name": "case_fractional_roll", "path": "/cases/open", "body": {"item": {"id": "item"}, "roll": 0.5, "table_version": "v1"}, "expected": false, "kind": "negative"},
		{"name": "case_empty_version", "path": "/cases/open", "body": {"item": {"id": "item"}, "roll": 0, "table_version": ""}, "expected": false, "kind": "negative"},
		{"name": "case_numeric_version", "path": "/cases/open", "body": {"item": {"id": "item"}, "roll": 0, "table_version": 1}, "expected": false, "kind": "negative"}
	]
	for fixture in cases:
		var accepted: bool = predicate._valid_receipt_result(fixture.path, fixture.body)
		fixture["actual"] = accepted
		_check("S1/" + fixture.name, accepted, fixture.expected)
	# Direct invocation of the exact second production function, with JSON-safe results.
	_check("S1/integer_whole_float", predicate._receipt_integer(2.0, 0, 9999), true)
	_check("S1/integer_nan_rejected", predicate._receipt_integer(NAN, 0, 9999), false)
	_check("S1/integer_infinity_rejected", predicate._receipt_integer(INF, 0, 9999), false)
	return cases

func _run_a() -> void:
	var cases: Array = _predicate_controls()
	var storage_path: String = evidence_root.path_join("state/pending_transaction.json")
	journal = JOURNAL.new()
	journal.path = storage_path
	_check("S2/A_initially_no_guard", journal.owner_guard == null, true)
	_check("S2/A_initially_no_pending", FileAccess.file_exists(storage_path), false)
	_check("S2/A_initially_no_tmp", FileAccess.file_exists(storage_path + ".tmp"), false)
	var stage_result: Error = journal.stage({})
	var stage_error: String = journal.error
	_check("S2/A_invalid_stage_error", stage_result, ERR_INVALID_DATA)
	_check("S2/A_retains_new_guard", journal.owner_guard != null and journal.owner_guard.is_listening(), true)
	_check("S2/A_invalid_stage_publishes_nothing", FileAccess.file_exists(storage_path), false)
	_check("S2/A_invalid_stage_no_tmp", FileAccess.file_exists(storage_path + ".tmp"), false)
	_check("S2/A_empty_reload", journal.load_pending(), {})
	_emit("native-A-ready.json", {"phase": "invalid_stage_guard_held", "scope_s1": "native predicate-component test only", "s1_cases": cases, "storage_path": storage_path, "stage_result": stage_result, "stage_error": stage_error})
	var released: bool = await _wait_for("release-A.signal")
	_check("S2/A_release_signal_received", released, true)
	_check("S2/A_guard_still_held_until_exit", journal.owner_guard != null and journal.owner_guard.is_listening(), true)
	_check("S2/A_still_no_pending_at_exit", FileAccess.file_exists(storage_path), false)
	_emit("native-A.json", {"phase": "completed_before_process_exit", "scope_s1": "native predicate-component test only", "s1_cases": cases, "storage_path": storage_path, "stage_result": stage_result, "stage_error": stage_error, "guard_release_action": "process exit only; no private release call"})
	quit(0 if all_passed else 1)

func _run_b() -> void:
	var storage_path: String = evidence_root.path_join("state/pending_transaction.json")
	var pending: Dictionary = {"path": "/store/buy", "owner": "independent-control-owner", "server": "http://127.0.0.1:1", "message": "Independent valid-shape control; no request is made.", "method": HTTPClient.METHOD_POST, "payload": {"idempotency_key": "independent-control-key", "definition_id": "obsidian_case"}}
	journal = JOURNAL.new()
	journal.path = storage_path
	_check("S2/B_valid_pending_shape", JOURNAL.valid(pending), true)
	_check("S2/B_no_pending_before_blocked_stage", FileAccess.file_exists(storage_path), false)
	var blocked_result: Error = journal.stage(pending)
	var blocked_error: String = journal.error
	_check("S2/B_blocked_while_A_lives", blocked_result, ERR_ALREADY_IN_USE)
	_check("S2/B_blocked_stage_has_no_guard", journal.owner_guard == null, true)
	_check("S2/B_blocked_stage_publishes_nothing", FileAccess.file_exists(storage_path), false)
	_check("S2/B_blocked_stage_no_tmp", FileAccess.file_exists(storage_path + ".tmp"), false)
	_emit("native-B-blocked.json", {"phase": "valid_stage_blocked_while_A_alive", "storage_path": storage_path, "pending": pending, "stage_result": blocked_result, "stage_error": blocked_error})
	var retry: bool = await _wait_for("retry-B.signal")
	_check("S2/B_retry_signal_received_after_A_exit", retry, true)
	_check("S2/B_no_pending_before_positive_stage", FileAccess.file_exists(storage_path), false)
	var success_result: Error = journal.stage(pending)
	_check("S2/B_valid_stage_after_A_exit", success_result, OK)
	_check("S2/B_positive_guard_listening", journal.owner_guard != null and journal.owner_guard.is_listening(), true)
	_check("S2/B_positive_published_pending", FileAccess.file_exists(storage_path), true)
	_check("S2/B_positive_no_tmp", FileAccess.file_exists(storage_path + ".tmp"), false)
	_check("S2/B_positive_exact_reload", journal.load_pending(), pending)
	_emit("native-B.json", {"phase": "positive_stage_completed_after_A_exit", "storage_path": storage_path, "pending": pending, "blocked_result": blocked_result, "blocked_error": blocked_error, "positive_result": success_result, "published_sha256": FileAccess.get_sha256(storage_path), "published_receipt_preserved": true})
	quit(0 if all_passed else 1)
