## Journal-only native component probe. The Python driver keeps A alive while B
## stages, then retries in that same B after A exits. No UI or HTTP is exercised.
extends SceneTree
const JOURNAL = preload("res://scripts/ui/transaction_journal.gd")
var config: Dictionary

class FaultJournal extends "res://scripts/ui/transaction_journal.gd":
	var fault := ""
	var control := ""
	var injected := false
	var injection_ok := true
	var verified_temporary_sha256 := ""
	var published_sha256 := ""

	func _matches_bytes(file_path: String, expected: String) -> bool:
		var temporary := file_path.ends_with(".tmp")
		if not injected and ((temporary and fault in ["temp_truncated", "temp_missing", "temp_canonical", "rename_locked", "rename_missing_source", "rename_published"]) or (not temporary and fault in ["postpublish_truncated", "postpublish_missing"])):
			injected = true
			if not temporary:
				published_sha256 = FileAccess.get_sha256(file_path)
			# These are explicit filesystem fault injections, not a disk-full test.
			match fault:
				"temp_truncated", "postpublish_truncated":
					var file := FileAccess.open(file_path, FileAccess.WRITE)
					injection_ok = file != null
					if file != null:
						injection_ok = file.store_string("{truncated")
						file.close()
				"temp_missing", "postpublish_missing":
					injection_ok = DirAccess.remove_absolute(file_path) == OK
				"temp_canonical":
					var file := FileAccess.open(path, FileAccess.WRITE)
					injection_ok = file != null
					if file != null:
						injection_ok = file.store_string("{unexpected canonical evidence")
						file.close()
					return false
				"rename_locked", "rename_missing_source", "rename_published":
					injection_ok = super._matches_bytes(file_path, expected)
					if not injection_ok:
						return false
					verified_temporary_sha256 = FileAccess.get_sha256(file_path)
					if fault == "rename_missing_source":
						injection_ok = DirAccess.remove_absolute(file_path) == OK
					elif fault == "rename_published":
						injection_ok = DirAccess.rename_absolute(file_path, path) == OK
						published_sha256 = FileAccess.get_sha256(path)
					else:
						# The driver takes a real Windows no-delete sharing handle
						# before allowing production DirAccess.rename_absolute to run.
						var ready := FileAccess.open(control + "/rename_ready", FileAccess.WRITE)
						injection_ok = ready != null
						if ready != null:
							ready.store_string(str(OS.get_process_id()))
							ready.close()
						var deadline := Time.get_ticks_msec() + 15000
						while not FileAccess.file_exists(control + "/rename_go") and Time.get_ticks_msec() < deadline:
							OS.delay_msec(10)
						injection_ok = injection_ok and FileAccess.file_exists(control + "/rename_go")
					return injection_ok
		return super._matches_bytes(file_path, expected)

func _initialize() -> void:
	config = JSON.parse_string(FileAccess.get_file_as_string(OS.get_cmdline_user_args()[0]))
	call_deferred("run")

func publish(name: String, state: Dictionary) -> void:
	state.pid = OS.get_process_id()
	state.source_sha256 = FileAccess.get_sha256("res://scripts/ui/transaction_journal.gd")
	state.event = name
	var text := JSON.stringify(state)
	var target := str(config.control) + "/" + name + ".json"
	var file := FileAccess.open(target + ".tmp", FileAccess.WRITE)
	file.store_string(text)
	file.close()
	DirAccess.rename_absolute(target + ".tmp", target)
	print("JOURNAL_STAGE_STATE " + text)

func snapshot(journal: RefCounted, result: int, pending: Dictionary) -> Dictionary:
	var stage_error: String = journal.error
	var loaded: Dictionary = journal.load_pending()
	return {"result": result, "guard": journal.owner_guard != null and journal.owner_guard.is_listening(),
		"path": journal.path, "canonical_exists": FileAccess.file_exists(journal.path),
		"canonical_sha256": FileAccess.get_sha256(journal.path) if FileAccess.file_exists(journal.path) else "",
		"temporary_exists": FileAccess.file_exists(journal.path + ".tmp"),
		"temporary_sha256": FileAccess.get_sha256(journal.path + ".tmp") if FileAccess.file_exists(journal.path + ".tmp") else "",
		"stage_error": stage_error, "load_error": journal.error, "loaded": loaded,
		"input": pending, "loaded_exact_input": loaded == pending}

func wait_for(name: String) -> bool:
	var deadline := Time.get_ticks_msec() + 25000
	while not FileAccess.file_exists(str(config.control) + "/" + name):
		if Time.get_ticks_msec() >= deadline:
			push_error("Timed out waiting for " + name)
			return false
		await create_timer(0.02).timeout
	return true

func run() -> void:
	var pending: Dictionary = config.pending
	pending.method = int(pending.method)
	if config.role == "contender":
		var journal := JOURNAL.new()
		journal.path = config.journal
		publish("contender_first", snapshot(journal, journal.stage(pending), pending))
		if not await wait_for("retry_go"):
			quit(2)
			return
		publish("contender_retry", snapshot(journal, journal.stage(pending), pending))
		quit(0)
		return
	var journal := FaultJournal.new()
	journal.path = config.journal
	journal.fault = str(config.get("fault", ""))
	journal.control = config.control
	var setup_result := OK
	if config.case in ["existing_pending", "existing_damaged"]:
		var file := FileAccess.open(journal.path, FileAccess.WRITE)
		if file == null:
			quit(3)
			return
		var text := JSON.stringify({"schema": 1, "transaction": pending}) if config.case == "existing_pending" else "{damaged"
		setup_result = OK if file.store_string(text) else ERR_FILE_CANT_WRITE
		file.close()
	if str(config.case).begins_with("already_owned_"):
		setup_result = journal.acquire()
	if config.case in ["invalid", "already_owned_invalid"]:
		pending = {}
	elif config.case == "oversized":
		pending.message = "x".repeat(JOURNAL.MAX_BYTES)
	var before := snapshot(journal, setup_result, pending)
	var result := journal.stage(pending)
	var state := snapshot(journal, result, pending)
	state.before = before
	state.setup_result = setup_result
	state.injected = journal.injected
	state.injection_ok = journal.injection_ok
	state.verified_temporary_sha256 = journal.verified_temporary_sha256
	state.published_sha256 = journal.published_sha256
	var original_path: String = journal.path
	journal.path = original_path + ".retargeted"
	state.retarget_blocked = journal.path == original_path
	journal.path = original_path
	publish("owner", state)
	if not await wait_for("owner_exit"):
		quit(2)
		return
	quit(0)
