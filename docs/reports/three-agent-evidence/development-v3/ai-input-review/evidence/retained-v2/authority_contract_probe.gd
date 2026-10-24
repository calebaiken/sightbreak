extends SceneTree

func _initialize() -> void:
	var actor := SBActor.new()
	actor.credits = 0
	actor.weapon_id = "rifle"
	actor.inventory.assign(["sidearm", "rifle"])
	actor.ammo = 2
	actor.reserve = 3
	actor.smokes = 0
	actor.grenades = 0
	var before := resources(actor)
	var purchase: bool = actor.buy_weapon("smg")
	if purchase or resources(actor) != before:
		push_error("Positive control failed: unaffordable player purchase must preserve resources")
		actor.free()
		quit(2)
		return
	SBBotAI.buy_equipment(actor, "normal", 2)
	var after := resources(actor)
	var passed: bool = before == after
	print("EQUIPMENT_AUTHORITY ", JSON.stringify({"before": before, "after": after, "passed": passed}))
	actor.free()
	if not passed:
		push_error("Failed bot purchase granted ammunition or utility outside the round-reset contract")
	quit(0 if passed else 1)

func resources(actor: SBActor) -> Dictionary:
	return {"credits": actor.credits, "weapon": actor.weapon_id, "inventory": actor.inventory.duplicate(), "ammo": actor.ammo, "reserve": actor.reserve, "smokes": actor.smokes, "grenades": actor.grenades}
