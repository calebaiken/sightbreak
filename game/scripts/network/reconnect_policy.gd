class_name SBReconnectPolicy
extends RefCounted
## A recovery episode has one monotonic deadline, never renewed by callbacks.
const WINDOW_MSEC := 20000
const ATTEMPT_MSEC := 5000
const MAX_ATTEMPTS := 5
var deadline := 0
var attempts := 0
var attempt_started := 0

func begin(now: int) -> void:
	if deadline == 0:
		deadline = now + WINDOW_MSEC

func available(now: int) -> bool:
	return deadline > 0 and now < deadline and attempts < MAX_ATTEMPTS

func take_attempt(now: int) -> bool:
	if not available(now):
		return false
	attempts += 1
	attempt_started = now
	return true

func delay_seconds() -> float:
	return minf(4.0, 2.0 + attempts * 0.5)

func clear() -> void:
	deadline = 0
	attempts = 0
	attempt_started = 0
