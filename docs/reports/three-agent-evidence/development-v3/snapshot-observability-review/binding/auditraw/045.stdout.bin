extends RefCounted
## Local observation only. ACKs identify commands, not authority simulation time.
## A first observed snapshot may already include held-input steps after consumption.
const MAX_SAMPLES := 120
const ANCHOR_KIND := "first_observed_snapshot_not_consumption"
var epoch := -1
var observations := 0
var repeats := 0
var ignored := 0
var evicted := 0
var samples: Array[Dictionary] = []
var _ack := -1
var _first_position := Vector3.ZERO
var _previous_position := Vector3.ZERO

func clear() -> void:
	epoch = -1
	observations = 0
	repeats = 0
	ignored = 0
	evicted = 0
	samples.clear()
	_ack = -1
	_first_position = Vector3.ZERO
	_previous_position = Vector3.ZERO

func begin_epoch(current_epoch: int) -> bool:
	if current_epoch < 0 or current_epoch < epoch:
		ignored += 1
		return false
	if current_epoch != epoch:
		clear()
		epoch = current_epoch
	return true

func observe(state: Dictionary, current_epoch: int, prediction_enabled: bool) -> void:
	# Never retain a caller's dictionary, private combat fields, or invalid position.
	if not state.get("move_ack") is int or int(state.move_ack) < 0 or not state.get("position") is Vector3 or not (state.position as Vector3).is_finite() or (state.position as Vector3).length() >= 1024:
		ignored += 1
		return
	if not begin_epoch(current_epoch):
		return
	var ack: int = state.move_ack
	if ack < _ack:
		ignored += 1
		return
	var position: Vector3 = state.position
	var repeated := ack == _ack
	if not repeated:
		_first_position = position
	observations += 1
	if repeated:
		repeats += 1
	samples.append({"epoch": epoch, "observation": observations, "ack": ack,
		"prediction_enabled": prediction_enabled, "repeated_ack": repeated,
		"anchor_kind": ANCHOR_KIND, "position": position,
		"first_snapshot_position": _first_position,
		"previous_snapshot_delta_m": position.distance_to(_previous_position) if repeated else null,
		"first_snapshot_drift_m": position.distance_to(_first_position)})
	if samples.size() > MAX_SAMPLES:
		samples.pop_front()
		evicted += 1
	_ack = ack
	_previous_position = position
