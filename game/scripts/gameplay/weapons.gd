class_name SBWeapons
extends RefCounted

# Match currency only. Cosmetic ownership never enters these definitions.
const DATA := {
	"sidearm": {"name": "Kestrel 9", "cost": 0, "damage": 27.0, "head": 3.3, "range": 45.0, "falloff": 0.55, "interval": 0.23, "magazine": 15, "reserve": 60, "reload": 1.45, "spread": 0.003, "recoil": 0.012, "automatic": false, "color": Color("9aabb5")},
	"smg": {"name": "Vectorline", "cost": 1100, "damage": 22.0, "head": 3.1, "range": 35.0, "falloff": 0.5, "interval": 0.085, "magazine": 30, "reserve": 120, "reload": 1.85, "spread": 0.009, "recoil": 0.009, "automatic": true, "color": Color("54b7b1")},
	"rifle": {"name": "Relay AR", "cost": 2400, "damage": 35.0, "head": 3.5, "range": 70.0, "falloff": 0.72, "interval": 0.105, "magazine": 30, "reserve": 90, "reload": 2.25, "spread": 0.002, "recoil": 0.016, "automatic": true, "color": Color("d8ae65")},
	"marksman": {"name": "Longwatch", "cost": 3200, "damage": 74.0, "head": 2.2, "range": 100.0, "falloff": 0.86, "interval": 0.82, "magazine": 8, "reserve": 32, "reload": 2.8, "spread": 0.001, "recoil": 0.045, "automatic": false, "color": Color("ae9aca")}
}

static func get_weapon(id: String) -> Dictionary:
	return DATA.get(id, DATA["sidearm"])
