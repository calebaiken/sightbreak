class_name CaseReveal
extends "res://scripts/ui/item_inspector.gd"
## Displays only the server-committed item. No alternate rarity/near-miss outcomes.
signal finished
var committed_item: Dictionary = {}
var reduced_motion := false
var revealed := false
var tween: Tween
var progress := 0.0:
	set(value):
		progress = clampf(value, 0.0, 1.0)
		set_reveal_progress(progress)

func _ready() -> void:
	super._ready()
	custom_minimum_size = Vector2(260, 240)
	prepare_reveal(committed_item)
	if reduced_motion:
		call_deferred("skip")
	else:
		tween = create_tween()
		tween.tween_property(self, "progress", 1.0, 2.8).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
		tween.tween_callback(skip)

func skip() -> void:
	if revealed:
		return
	if tween and tween.is_running():
		tween.kill()
	progress = 1.0
	revealed = true
	finished.emit()

func _gui_input(_event: InputEvent) -> void:
	# Rotation belongs to the explicit inspector after the committed reveal.
	accept_event()
