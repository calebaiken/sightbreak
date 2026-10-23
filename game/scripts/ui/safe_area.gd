class_name DeviceSafeArea
extends RefCounted

static func scaled_rect(viewport_size: Vector2, window_size: Vector2, screen_safe: Rect2) -> Rect2:
	if window_size.x <= 0 or window_size.y <= 0: return Rect2(Vector2.ZERO, viewport_size)
	var scale := viewport_size / window_size
	var bounds := Rect2(Vector2.ZERO, viewport_size)
	var mapped := Rect2(screen_safe.position * scale, screen_safe.size * scale).intersection(bounds)
	# Devices may return an empty/stale safe area during orientation changes.
	return mapped if mapped.has_area() else bounds

## Tests and design captures only: pretend the device reserves this much on each side
## (left, top, right, bottom, in viewport pixels). Zero on a real device.
static var simulated_insets := Vector4.ZERO

static func viewport_rect(viewport_size: Vector2) -> Rect2:
	if simulated_insets != Vector4.ZERO:
		var inset := Rect2(simulated_insets.x, simulated_insets.y, viewport_size.x - simulated_insets.x - simulated_insets.z, viewport_size.y - simulated_insets.y - simulated_insets.w)
		return inset if inset.has_area() else Rect2(Vector2.ZERO, viewport_size)
	if OS.get_name() not in ["Android", "iOS"]:
		return Rect2(Vector2.ZERO, viewport_size)
	var safe := Rect2(DisplayServer.get_display_safe_area())
	if safe.size.x <= 0 or safe.size.y <= 0:
		return Rect2(Vector2.ZERO, viewport_size)
	return scaled_rect(viewport_size, Vector2(DisplayServer.window_get_size()), safe)
