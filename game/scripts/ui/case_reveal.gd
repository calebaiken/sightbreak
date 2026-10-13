class_name CaseReveal
extends Control
## Neutral sealed panels move toward a fixed marker. Only the committed reward
## receives a rarity colour; neighbouring panels never imply alternative wins.
signal finished
var committed_item: Dictionary = {}
var reduced_motion := false
var revealed := false
var tween: Tween
var progress := 0.0:
	set(value):
		progress = value
		queue_redraw()
const PANELS := 15
const STEP := 154.0
const CARD_WIDTH := 140.0

func _ready() -> void:
	custom_minimum_size = Vector2(260, 188)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	clip_contents = true
	resized.connect(queue_redraw)
	if reduced_motion:
		call_deferred("skip")
	else:
		tween = create_tween()
		tween.tween_property(self, "progress", 1.0, 2.8).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
		tween.tween_callback(skip)

func skip() -> void:
	if revealed:
		return
	if tween and tween.is_running():
		tween.kill()
	progress = 1.0
	revealed = true
	queue_redraw()
	finished.emit()

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color("0d121a"))
	var font := ThemeDB.fallback_font
	for index in PANELS:
		var x := size.x * 0.5 - CARD_WIDTH * 0.5 + (index - progress * (PANELS - 1)) * STEP
		if x + CARD_WIDTH < 0 or x > size.x:
			continue
		var rect := Rect2(x, 18, CARD_WIDTH, 142)
		var is_reward := revealed and index == PANELS - 1
		var color := Color("394858")
		if is_reward:
			var colors := {"Common": Color("82909a"), "Uncommon": Color("76a896"), "Rare": Color("597eb9"), "Epic": Color("8d69b7"), "Legendary": Color("bba26e"), "Mythic": Color("b6314c")}
			color = colors.get(str(committed_item.get("rarity", "Common")), Color("82909a"))
		draw_style_box(_card_style(color), rect)
		# These represent sealed panels, not potential rewards or a probability reel.
		draw_rect(Rect2(x + 32, 45, 76, 50), Color("242e3a"))
		draw_rect(Rect2(x + 32, 59, 76, 5), color)
		draw_rect(Rect2(x + 64, 62, 12, 15), Color("b7a071") if is_reward else Color("637285"))
		var label := str(committed_item.get("rarity", "" )).to_upper() if is_reward else "SEALED"
		draw_string(font, Vector2(x, 126), label, HORIZONTAL_ALIGNMENT_CENTER, CARD_WIDTH, 15, color.lightened(0.3))
	draw_line(Vector2(size.x * 0.5, 0), Vector2(size.x * 0.5, 16), Color("c8ad76"), 3.0)
	draw_line(Vector2(size.x * 0.5, 162), Vector2(size.x * 0.5, 176), Color("c8ad76"), 3.0)

func _card_style(color: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("19222e")
	style.border_color = color
	style.set_border_width_all(2)
	style.set_corner_radius_all(5)
	return style
