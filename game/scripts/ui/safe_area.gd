class_name DeviceSafeArea
extends RefCounted

static func scaled_rect(viewport_size: Vector2, window_size: Vector2, screen_safe: Rect2) -> Rect2:
	if window_size.x <= 0 or window_size.y <= 0: return Rect2(Vector2.ZERO, viewport_size)
	var scale := viewport_size / window_size
	var bounds := Rect2(Vector2.ZERO, viewport_size)
	return Rect2(screen_safe.position * scale, screen_safe.size * scale).intersection(bounds)

static func viewport_rect(viewport_size: Vector2) -> Rect2:
	if OS.get_name() not in ["Android", "iOS"]:
		return Rect2(Vector2.ZERO, viewport_size)
	var safe := Rect2(DisplayServer.get_display_safe_area())
	if safe.size.x <= 0 or safe.size.y <= 0:
		return Rect2(Vector2.ZERO, viewport_size)
	return scaled_rect(viewport_size, Vector2(DisplayServer.window_get_size()), safe)
