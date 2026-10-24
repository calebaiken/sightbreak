extends SceneTree
const JOURNAL = preload("res://scripts/ui/transaction_journal.gd")

func _initialize() -> void:
	var journal := JOURNAL.new()
	journal.path = OS.get_cmdline_user_args()[0]
	var original := FileAccess.get_file_as_bytes(journal.path)
	var pending := journal.load_pending()
	var claim_result := journal.claim(pending)
	var clear_result := journal.clear(pending)
	var other := pending.duplicate(true)
	other.payload.idempotency_key = "competing-process"
	var stage_result := journal.stage(other)
	var blocked := claim_result != OK and clear_result != OK and stage_result != OK and FileAccess.get_file_as_bytes(journal.path) == original
	print("OWNER_BLOCKED " + JSON.stringify({"pid": OS.get_process_id(), "claim": claim_result, "clear": clear_result, "stage": stage_result, "unchanged": blocked}))
	quit(0 if blocked else 1)
