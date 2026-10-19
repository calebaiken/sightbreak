extends SceneTree

var failures: Array[String] = []

func _initialize() -> void:
	_run.call_deferred()

func resources(a: SBActor) -> Dictionary:
	return {"credits": a.credits, "weapon": a.weapon_id, "inventory": a.inventory.duplicate(), "ammo": a.ammo, "reserve": a.reserve, "smokes": a.smokes, "grenades": a.grenades}

func check(label: String, ok: bool, before: Dictionary, after: Dictionary) -> void:
	print("NATIVE_EQUIPMENT ", JSON.stringify({"case": label, "passed": ok, "before": before, "after": after}))
	if not ok:
		failures.append(label)

func _run() -> void:
	var a := SBActor.new()
	a.configure(2, 0, "RealEquipmentActor")
	root.add_child(a)
	a.reset_for_round(Vector3(0, 0.05, 0))
	a.credits = 5000
	a.buy_weapon("rifle")
	a.ammo = 2
	a.reserve = 3
	a.smokes = 0
	a.grenades = 0
	a.credits = 0
	var before: Dictionary = resources(a)
	SBBotAI.buy_equipment(a, "normal", 2)
	check("failed_purchase_grants_nothing", before == resources(a), before, resources(a))
	a.reset_loadout()
	a.credits = 5000
	a.ammo = 2
	a.reserve = 3
	before = resources(a)
	SBBotAI.buy_equipment(a, "normal", 2)
	check("successful_purchase_uses_real_actor_price_and_ammo", a.weapon_id == "rifle" and a.credits == 5000 - int(SBWeapons.DATA.rifle.cost) and a.ammo == 30 and a.reserve == 90 and a.smokes == 0 and a.grenades == 0, before, resources(a))
	a.credits = 5000
	a.ammo = 2
	a.reserve = 3
	before = resources(a)
	SBBotAI.buy_equipment(a, "normal", 2)
	check("duplicate_purchase_grants_nothing", before == resources(a), before, resources(a))
	a.reset_loadout()
	a.credits = 5000
	a.alive = false
	before = resources(a)
	SBBotAI.buy_equipment(a, "normal", 2)
	check("dead_actor_purchase_grants_nothing", before == resources(a), before, resources(a))
	a.reset_for_round(Vector3(0, 0.05, 0))
	before = resources(a)
	check("round_reset_is_the_resource_owner", a.alive and a.weapon_id == "sidearm" and a.ammo == 15 and a.reserve == 60 and a.smokes == 1 and a.grenades == 1, before, resources(a))
	a.queue_free()
	await process_frame
	await process_frame
	print("NATIVE_EQUIPMENT_COMPLETE ", JSON.stringify({"failures": failures}))
	quit(0 if failures.is_empty() else 1)
