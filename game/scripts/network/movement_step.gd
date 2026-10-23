class_name SBMovementStep
extends RefCounted
## Shared fixed-physics-step movement only. No weapon, damage or economy logic.
const WALK_SPEED := 5.1
const CROUCH_SPEED := 2.5
const GRAVITY := 22.0
const STEP := 1.0 / 60.0

static func advance(actor: CharacterBody3D, controls: Dictionary, delta: float, grounded_override: int = -1) -> void:
	if not actor.alive:
		return
	var look: Vector2 = controls.get("look", Vector2(actor.yaw, actor.pitch))
	if look.is_finite():
		actor.yaw = wrapf(look.x, -PI, PI)
		actor.pitch = clampf(look.y, -1.42, 1.42)
	actor.rotation.y = actor.yaw
	var requested_crouch: bool = controls.get("crouch", false)
	if requested_crouch or not actor._crouching or actor._can_stand():
		actor._crouching = requested_crouch
	actor._collision.shape.height = 1.25 if actor._crouching else 1.8
	actor._collision.position.y = 0.625 if actor._crouching else 0.9
	actor.head_height = 1.13 if actor._crouching else 1.62
	actor._body.scale.y = 0.72 if actor._crouching else 1.0
	var move: Vector2 = controls.get("move", Vector2.ZERO)
	if not move.is_finite():
		move = Vector2.ZERO
	move = move.limit_length(1)
	var direction := actor.global_basis * Vector3(move.x, 0, -move.y)
	var speed := CROUCH_SPEED if actor._crouching else WALK_SPEED
	var grounded: bool = actor.is_on_floor() if grounded_override < 0 else grounded_override == 1
	var acceleration := 28.0 if grounded else 7.0
	actor.velocity.x = move_toward(actor.velocity.x, direction.x * speed, acceleration * delta)
	actor.velocity.z = move_toward(actor.velocity.z, direction.z * speed, acceleration * delta)
	if not grounded:
		actor.velocity.y -= GRAVITY * delta
	var jump: bool = controls.get("jump", false)
	if jump and not actor._jump_previous and grounded and not actor._crouching:
		actor.velocity.y = 6.4
	actor._jump_previous = jump
	actor.move_and_slide()
