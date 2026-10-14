class_name SBWeaponGlyph
extends Control
## Flat side-profile glyph of a weapon class for menus (muzzle to the right). Original
## shapes on a 100 x 40 grid, scaled to fit the control; drawn, not textured, so it
## costs no assets and stays sharp at any text or screen size. Presentation only.

const SHAPES := {
	"sidearm": [
		[Vector2(14, 10), Vector2(78, 10), Vector2(80, 12), Vector2(80, 19), Vector2(14, 19)],
		[Vector2(16, 19), Vector2(70, 19), Vector2(70, 24), Vector2(16, 24)],
		[Vector2(16, 23), Vector2(33, 23), Vector2(29, 39), Vector2(13, 39)],
		[Vector2(38, 24), Vector2(52, 24), Vector2(52, 27), Vector2(41, 31), Vector2(38, 27)],
	],
	"smg": [
		[Vector2(4, 13), Vector2(22, 13), Vector2(22, 18), Vector2(4, 18)],
		[Vector2(20, 9), Vector2(72, 9), Vector2(72, 22), Vector2(20, 22)],
		[Vector2(72, 11), Vector2(98, 11), Vector2(98, 20), Vector2(72, 20)],
		[Vector2(44, 22), Vector2(53, 22), Vector2(53, 39), Vector2(44, 39)],
		[Vector2(25, 22), Vector2(34, 22), Vector2(31, 36), Vector2(22, 36)],
	],
	"rifle": [
		[Vector2(1, 11), Vector2(19, 9), Vector2(19, 22), Vector2(3, 25)],
		[Vector2(19, 8), Vector2(60, 8), Vector2(60, 22), Vector2(19, 22)],
		[Vector2(60, 10), Vector2(86, 10), Vector2(86, 19), Vector2(60, 19)],
		[Vector2(86, 13), Vector2(99, 13), Vector2(99, 16), Vector2(86, 16)],
		[Vector2(39, 2), Vector2(53, 2), Vector2(53, 8), Vector2(39, 8)],
		[Vector2(45, 22), Vector2(54, 22), Vector2(57, 38), Vector2(49, 39)],
		[Vector2(28, 22), Vector2(36, 22), Vector2(33, 36), Vector2(25, 36)],
	],
	"marksman": [
		[Vector2(0, 12), Vector2(18, 10), Vector2(18, 22), Vector2(2, 26)],
		[Vector2(18, 9), Vector2(56, 9), Vector2(56, 21), Vector2(18, 21)],
		[Vector2(56, 13), Vector2(100, 13), Vector2(100, 16), Vector2(56, 16)],
		[Vector2(28, 1), Vector2(56, 1), Vector2(56, 7), Vector2(28, 7)],
		[Vector2(40, 21), Vector2(48, 21), Vector2(48, 31), Vector2(40, 31)],
		[Vector2(26, 21), Vector2(33, 21), Vector2(30, 35), Vector2(23, 35)],
	],
}

var weapon_id := "rifle":
	set(value):
		weapon_id = value
		queue_redraw()
var tint := Color.WHITE:
	set(value):
		tint = value
		queue_redraw()

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _draw() -> void:
	var scale_factor := minf(size.x / 100.0, size.y / 40.0)
	var offset := (size - Vector2(100, 40) * scale_factor) * 0.5
	for shape: Array in SHAPES.get(weapon_id, SHAPES["rifle"]):
		var points := PackedVector2Array()
		for point: Vector2 in shape:
			points.append(offset + point * scale_factor)
		draw_colored_polygon(points, tint)
