class_name SBDesign
extends RefCounted
## SIGHTBREAK visual language: one source for color, type, spacing, motion and
## component states. Menus, HUD and armory build from these tokens instead of
## defining their own colors. Uses Godot's bundled font (no external font assets).

# Palette — obsidian/graphite surfaces, brushed-steel text, muted metallic gold
# for emphasis and dark crimson reserved for primary actions and danger.
const OBSIDIAN := Color("0a0d12")
const GRAPHITE := Color("141920")
const GRAPHITE_RAISED := Color("1b222b")
const GRAPHITE_HOVER := Color("232c37")
const LINE := Color("2c3540")
const LINE_STRONG := Color("46525f")
const STEEL := Color("8e99a6")
const STEEL_BRIGHT := Color("c3ccd6")
const TEXT := Color("e9ecf0")
const GOLD := Color("c8ab6e")
const GOLD_DIM := Color("8c7647")
const CRIMSON := Color("a32539")
const CRIMSON_BRIGHT := Color("d64a5f")
const SCRIM := Color(0.02, 0.026, 0.036, 0.9)
# Squad colors match the operator shoulder accents in the world.
const ATTACK := Color("c98a52")
const DEFEND := Color("58a8b8")

# Type scale (logical pixels at 720p landscape) and accessible minimums.
const TYPE_DISPLAY := 68
const TYPE_H1 := 32
const TYPE_H2 := 24
const TYPE_H3 := 19
const TYPE_BODY := 16
const TYPE_SMALL := 14
const TYPE_MICRO := 12
# Spacing, radius, touch and motion.
const SPACE_XS := 4
const SPACE_S := 8
const SPACE_M := 12
const SPACE_L := 18
const SPACE_XL := 28
const RADIUS := 3
const TOUCH_MIN := 48
const MOTION_FAST := 0.12
const MOTION_BASE := 0.2
const MOTION_SLOW := 0.35

static var _heading_font: FontVariation

## User-supplied names as one plain line: control, bidi-format and line or
## paragraph separator characters become spaces, runs collapse, length is capped.
static func plain_line(text: String, limit: int = 32) -> String:
	var cleaned := ""
	for index in range(text.length()):
		var code := text.unicode_at(index)
		var hidden := code < 32 or (code >= 127 and code < 160) or code == 0xAD or (code >= 0x200B and code <= 0x200F) or (code >= 0x2028 and code <= 0x202E) or (code >= 0x2060 and code <= 0x206F) or code == 0xFEFF
		cleaned += " " if hidden else text[index]
	while "  " in cleaned:
		cleaned = cleaned.replace("  ", " ")
	return cleaned.strip_edges().left(limit)

static func squad_color(team: int) -> Color:
	return ATTACK if team == 0 else DEFEND

static func squad_name(team: int) -> String:
	return "ATTACK" if team == 0 else "DEFENSE"

static func motion(seconds: float, reduced: bool) -> float:
	return 0.0 if reduced else seconds

## Wide-tracked semibold face for headings and labels.
static func heading_font() -> FontVariation:
	if _heading_font == null:
		_heading_font = FontVariation.new()
		_heading_font.base_font = ThemeDB.fallback_font
		_heading_font.variation_embolden = 0.35
		_heading_font.set_spacing(TextServer.SPACING_GLYPH, 1)
	return _heading_font

static func box(fill: Color, border: Color = Color.TRANSPARENT, border_width: int = 1, padding := Vector2(18, 12)) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width if border.a > 0 else 0)
	style.set_corner_radius_all(RADIUS)
	style.content_margin_left = padding.x
	style.content_margin_right = padding.x
	style.content_margin_top = padding.y
	style.content_margin_bottom = padding.y
	return style

## Button state styles for "primary", "secondary", "ghost" and "tab" variants.
static func button_styles(variant: String = "secondary") -> Dictionary:
	var fill := GRAPHITE_RAISED
	var border := LINE
	var hover_border := GOLD_DIM
	match variant:
		"primary":
			fill = CRIMSON
			border = CRIMSON_BRIGHT.darkened(0.15)
			hover_border = CRIMSON_BRIGHT
		"ghost":
			fill = Color(GRAPHITE, 0.0)
			border = LINE
		"tab":
			fill = GRAPHITE
			border = LINE
	var normal := box(fill, border)
	var hover := box(fill.lightened(0.06) if variant == "primary" else GRAPHITE_HOVER, hover_border)
	var pressed := box(fill.darkened(0.18) if variant == "primary" else GRAPHITE, GOLD)
	var disabled := box(Color(fill, 0.45), Color(border, 0.4))
	var focus := box(Color.TRANSPARENT, GOLD, 2)
	if variant == "primary":
		normal.border_width_bottom = 3
		normal.border_color = CRIMSON_BRIGHT.darkened(0.15)
	return {"normal": normal, "hover": hover, "pressed": pressed, "disabled": disabled, "focus": focus}

## Selected-tab treatment: raised surface with a gold underline.
static func tab_selected_style() -> StyleBoxFlat:
	var style := box(GRAPHITE_HOVER, LINE_STRONG)
	style.border_width_bottom = 3
	style.border_color = GOLD
	return style

static func apply_button(button: Button, variant: String = "secondary") -> void:
	var styles := button_styles(variant)
	for state in styles:
		button.add_theme_stylebox_override(state, styles[state])
	button.add_theme_color_override("font_disabled_color", Color(STEEL, 0.55))
	if variant == "primary":
		button.add_theme_color_override("font_color", Color.WHITE)

static func panel(variant: String = "panel") -> StyleBoxFlat:
	match variant:
		"card": return box(GRAPHITE_RAISED, LINE, 1, Vector2(16, 12))
		"inset": return box(OBSIDIAN, LINE, 1, Vector2(14, 10))
		"overlay": return box(Color(GRAPHITE, 0.96), LINE_STRONG, 1, Vector2(22, 18))
	return box(GRAPHITE, LINE, 1, Vector2(18, 16))

static func label(text: String, size: int = TYPE_BODY, color: Color = TEXT, heading := false) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_size_override("font_size", size)
	node.add_theme_color_override("font_color", color)
	if heading:
		node.add_theme_font_override("font", heading_font())
	return node

## Shared theme. text_scale is the accessibility multiplier for body copy.
static func build_theme(text_scale: float = 1.0) -> Theme:
	var theme := Theme.new()
	var scale := clampf(text_scale, 0.85, 1.4)
	theme.default_font_size = int(round(TYPE_BODY * scale))
	for type in ["Label", "Button", "CheckButton", "OptionButton", "LineEdit"]:
		theme.set_color("font_color", type, TEXT)
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_color("font_pressed_color", "Button", GOLD)
	theme.set_color("font_focus_color", "Button", TEXT)
	theme.set_color("font_disabled_color", "Button", Color(STEEL, 0.55))
	theme.set_color("font_placeholder_color", "LineEdit", Color(STEEL, 0.75))
	theme.set_color("caret_color", "LineEdit", GOLD)
	theme.set_color("selection_color", "LineEdit", Color(GOLD, 0.35))
	var buttons := button_styles("secondary")
	for state in buttons:
		theme.set_stylebox(state, "Button", buttons[state])
		theme.set_stylebox(state, "OptionButton", buttons[state])
	theme.set_stylebox("normal", "LineEdit", box(OBSIDIAN, LINE, 1, Vector2(14, 10)))
	theme.set_stylebox("focus", "LineEdit", box(Color.TRANSPARENT, GOLD, 2))
	theme.set_stylebox("read_only", "LineEdit", box(GRAPHITE, LINE, 1, Vector2(14, 10)))
	theme.set_stylebox("panel", "PanelContainer", panel())
	theme.set_stylebox("panel", "PopupPanel", panel("overlay"))
	var track := box(OBSIDIAN, LINE, 1, Vector2.ZERO)
	var fill := box(GOLD, Color.TRANSPARENT, 0, Vector2.ZERO)
	theme.set_stylebox("background", "ProgressBar", track)
	theme.set_stylebox("fill", "ProgressBar", fill)
	theme.set_constant("separation", "VBoxContainer", SPACE_M)
	theme.set_constant("separation", "HBoxContainer", SPACE_M)
	theme.set_constant("h_separation", "HFlowContainer", SPACE_S)
	theme.set_constant("v_separation", "HFlowContainer", SPACE_S)
	return theme
