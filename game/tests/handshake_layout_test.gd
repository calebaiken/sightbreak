extends SceneTree
## The version handshake compares the Relay Yard layout as well as the protocol number: the layout is the collision
## world every authoritative move and shot resolves in. Pure checks of the parsing and the decision; the real
## server and client processes are covered by scripts/test_handshake_hardening.sh and scripts/test_protocol_compat.sh.

## SHA-256 of the yard's collision solids for each revision, from _layout_fingerprint. A peer on another revision resolves hits
## and movement in a different world, so a change to the solids must come with a new RelayYard.LAYOUT_REVISION (the handshake
## refuses mixed layouts) and a new entry here.
const LAYOUT_FINGERPRINTS := {2: "f15066b6469df3ff02458df978db860374be78d4a85b8297c817af34af877d5e"}
var checks := 0
var failures := 0

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(label)

func _hello(protocol: Variant, layout: Variant = RelayYard.LAYOUT_REVISION, accepted: bool = true) -> Dictionary:
	var hello := {"game": "sightbreak", "protocol": protocol, "build": "test", "accepted": accepted, "reason": ""}
	if layout != null:
		hello["layout"] = layout
	return hello

## Every collision solid, to the millimetre and in a fixed order, hashed.
static func _layout_fingerprint() -> String:
	var arena := RelayYard.new()
	arena._build()
	var rows: Array[String] = []
	for box: AABB in arena._obstacles:
		rows.append("%.3f,%.3f,%.3f,%.3f,%.3f,%.3f" % [box.position.x, box.position.y, box.position.z, box.size.x, box.size.y, box.size.z])
	arena.free()
	rows.sort()
	return "\n".join(rows).sha256_text()

func _initialize() -> void:
	var current: int = RelayYard.LAYOUT_REVISION
	check(current > TacticalMatch.LEGACY_LAYOUT, "this build's yard is newer than the open pad that predates the field")
	check(TacticalMatch.PROTOCOL_VERSION == 6, "the layout field is additive: protocol 6 is preserved")

	check(LAYOUT_FINGERPRINTS.has(current) and _layout_fingerprint() == LAYOUT_FINGERPRINTS.get(current, ""), "the collision solids changed without a new RelayYard.LAYOUT_REVISION and fingerprint (see LAYOUT_FINGERPRINTS)")

	# Parsing: a missing field is the open pad; only whole, bounded numbers are readable.
	check(TacticalMatch._hello_layout({}) == TacticalMatch.LEGACY_LAYOUT, "a hello without the field is the legacy layout")
	check(TacticalMatch._hello_layout({"layout": 2}) == 2 and TacticalMatch._hello_layout({"layout": 2.0}) == 2, "whole numbers are read")
	for unreadable in [2.5, "2", "two", true, null, -1, 1e400, 1000000, [2], {"layout": 2}]:
		check(TacticalMatch._hello_layout({"layout": unreadable}) == -1, "unreadable layout %s is refused rather than rounded" % str(unreadable))

	# What this build puts on the wire is what it accepts back.
	var game := TacticalMatch.new()
	var own: Dictionary = TacticalMatch._read_hello(game._hello(true, ""))
	game.free()
	check(own.get("layout") == current and TacticalMatch._hello_protocol(own) == 6, "the hello announces protocol and layout")
	check(TacticalMatch._hello_mismatch(own, "server", "client").is_empty(), "a hello from this very build is admitted")

	# Decision.
	var mismatch := func(protocol: Variant, layout: Variant) -> String: return TacticalMatch._hello_mismatch(_hello(protocol, layout), "server", "client")
	check(mismatch.call(6, current).is_empty(), "matching protocol and layout are admitted")
	check(mismatch.call(6, null) != "" and "layout 1" in mismatch.call(6, null), "a build without the layout field is refused as layout 1")
	check("Relay Yard layout %d" % current in mismatch.call(6, null), "the reason names this build's layout")
	check("layout %d" % (current + 1) in mismatch.call(6, current + 1), "a newer layout is refused with its number")
	check("no readable layout" in mismatch.call(6, 2.5) and "no readable layout" in mismatch.call(6, "two"), "an unreadable layout says so")
	check("network protocol 6" in mismatch.call(7, current) and "protocol 7" in mismatch.call(7, current), "a protocol mismatch is reported first and unchanged")
	check("no readable protocol" in mismatch.call(2.9, current), "an unreadable protocol still says so")
	check("layout" not in mismatch.call(7, null), "a protocol mismatch does not blame the layout")

	# The same decision, from the other end, names the sides the right way round.
	var from_client: String = TacticalMatch._hello_mismatch(_hello(6, null), "client", "server")
	check(from_client.begins_with("This client uses Relay Yard layout") and "this server sent layout 1" in from_client, "the client names itself and the server correctly")
	print("HANDSHAKE_LAYOUT_TEST checks=%d failures=%d" % [checks, failures])
	quit(1 if failures else 0)
