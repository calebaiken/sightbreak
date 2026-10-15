class_name ConfirmSheet
extends Control
## A confirmation that always fits the screen. The terms scroll; the title, the summary and
## both buttons never do, so the player can always read what they are agreeing to and always
## reach the confirming and the cancelling button, whatever the text size or the number of
## items. It is an overlay in the scene tree (not an OS window), laid out inside the safe area.
##
## present() shows it. dialog_text is the full terms as plain text. accepted fires only from
## the confirming button; every other way out (the cancel button, the Escape key) fires
## cancelled. Nothing outside the sheet can be pressed while it is open.
signal accepted
signal cancelled

const DESIGN = preload("res://scripts/ui/design_tokens.gd")
const SAFE_AREA = preload("res://scripts/ui/safe_area.gd")
const SIDE_MARGIN := 16.0
const MAX_WIDTH := 680.0
const PADDING := Vector2(20, 16)
const MIN_TERMS_HEIGHT := 96.0
const SCROLLBAR_ALLOWANCE := 14.0

var dialog_text := ""
var text_scale := 1.0
var panel: PanelContainer
var title_label: Label
var summary_label: Label
var terms: Label
var scroll: ScrollContainer
var hint: Label
var buttons: HFlowContainer
var accept_button: Button
var cancel_button: Button
var settled := false
var _danger := false

func _init() -> void:
	name = "ConfirmSheet"
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var dim := ColorRect.new()
	dim.color = Color(0.0, 0.0, 0.0, 0.74)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	panel = PanelContainer.new()
	panel.name = "ConfirmPanel"
	add_child(panel)
	var stack := VBoxContainer.new()
	stack.add_theme_constant_override("separation", 10)
	panel.add_child(stack)
	title_label = Label.new()
	title_label.name = "ConfirmTitle"
	title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title_label.add_theme_font_override("font", DESIGN.heading_font())
	title_label.add_theme_color_override("font_color", DESIGN.GOLD)
	stack.add_child(title_label)
	summary_label = Label.new()
	summary_label.name = "ConfirmSummary"
	summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(summary_label)
	scroll = ScrollContainer.new()
	scroll.name = "ConfirmTerms"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stack.add_child(scroll)
	terms = Label.new()
	terms.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	scroll.add_child(terms)
	hint = Label.new()
	hint.name = "ConfirmScrollHint"
	hint.text = "▼  Scroll to read every term before you confirm"
	hint.add_theme_color_override("font_color", DESIGN.GOLD)
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stack.add_child(hint)
	buttons = HFlowContainer.new()
	buttons.name = "ConfirmButtons"
	buttons.add_theme_constant_override("h_separation", 12)
	buttons.add_theme_constant_override("v_separation", 8)
	stack.add_child(buttons)
	cancel_button = Button.new()
	cancel_button.name = "ConfirmCancel"
	cancel_button.pressed.connect(_cancel)
	buttons.add_child(cancel_button)
	accept_button = Button.new()
	accept_button.name = "ConfirmAccept"
	accept_button.pressed.connect(_accept)
	buttons.add_child(accept_button)
	resized.connect(_layout)

## Opens the sheet. `summary` is the one line that must be seen even if the terms are not
## scrolled (what is given and received); `danger` marks a one-sided or irreversible act.
func present(title: String, body: String, accept_label: String, summary := "", danger := false, scale := 1.0, cancel_label := "GO BACK") -> void:
	text_scale = scale
	dialog_text = body
	_danger = danger
	settled = false
	title_label.text = title
	terms.text = body
	summary_label.text = summary
	summary_label.visible = not summary.is_empty()
	summary_label.add_theme_color_override("font_color", DESIGN.CRIMSON_BRIGHT if danger else DESIGN.STEEL_BRIGHT)
	cancel_button.text = cancel_label
	accept_button.text = accept_label
	_style()
	panel.modulate.a = 0.0
	show()
	_layout()
	cancel_button.grab_focus()
	# Wrapped text needs its final width before the height can be known: lay out again once
	# the containers have been sorted, then reveal.
	await get_tree().process_frame
	if not is_inside_tree() or not visible:
		return
	_layout()
	await get_tree().process_frame
	if not is_inside_tree() or not visible:
		return
	_layout()
	settled = true
	panel.modulate.a = 1.0

func _style() -> void:
	title_label.add_theme_font_size_override("font_size", DESIGN.scaled_size(DESIGN.TYPE_H2, text_scale))
	for label: Label in [summary_label, terms, hint]:
		label.add_theme_font_size_override("font_size", DESIGN.scaled_size(DESIGN.TYPE_BODY, text_scale))
	hint.add_theme_font_size_override("font_size", DESIGN.scaled_size(DESIGN.TYPE_SMALL, text_scale))
	terms.add_theme_color_override("font_color", DESIGN.TEXT)
	var border := DESIGN.CRIMSON_BRIGHT if _danger else DESIGN.GOLD_DIM
	var box := DESIGN.box(Color(DESIGN.GRAPHITE, 0.99), border, 2 if _danger else 1, PADDING)
	panel.add_theme_stylebox_override("panel", box)
	for button: Button in [cancel_button, accept_button]:
		button.custom_minimum_size = Vector2(0, DESIGN.TOUCH_COMFORT)
		button.add_theme_font_size_override("font_size", DESIGN.scaled_size(DESIGN.TYPE_BODY, text_scale))
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	DESIGN.apply_button(cancel_button, "secondary")
	DESIGN.apply_button(accept_button, "primary")

## Panel width and height from the safe area and the measured terms: as tall as the terms
## need, never taller than the screen, with the terms scrolling in whatever is left.
func _layout() -> void:
	if not visible or panel == null:
		return
	var safe: Rect2 = SAFE_AREA.viewport_rect(size)
	var width := minf(MAX_WIDTH, safe.size.x - 2.0 * SIDE_MARGIN)
	var max_height := safe.size.y - 2.0 * SIDE_MARGIN
	var inner := width - 2.0 * PADDING.x
	for label: Label in [title_label, summary_label, hint]:
		label.custom_minimum_size.x = inner
		label.size.x = inner
	buttons.custom_minimum_size.x = inner
	buttons.size.x = inner
	terms.custom_minimum_size.x = inner - SCROLLBAR_ALLOWANCE
	terms.size.x = inner - SCROLLBAR_ALLOWANCE
	scroll.custom_minimum_size.y = MIN_TERMS_HEIGHT
	hint.show()
	panel.size = Vector2(width, 0)
	var terms_height := terms.get_combined_minimum_size().y
	var chrome := panel.get_combined_minimum_size().y - MIN_TERMS_HEIGHT
	# `chrome` includes the hint. If the terms fit without it, drop it and use the room it held.
	var hint_cost := hint.get_combined_minimum_size().y + 10.0
	if terms_height <= max_height - (chrome - hint_cost):
		hint.hide()
		chrome -= hint_cost
	var height := minf(max_height, chrome + maxf(terms_height, MIN_TERMS_HEIGHT))
	panel.size = Vector2(width, height)
	panel.position = (safe.position + (safe.size - panel.size) * 0.5).round()

func _accept() -> void:
	hide()
	accepted.emit()

func _cancel() -> void:
	hide()
	cancelled.emit()

func _unhandled_input(event: InputEvent) -> void:
	if visible and event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		_cancel()
