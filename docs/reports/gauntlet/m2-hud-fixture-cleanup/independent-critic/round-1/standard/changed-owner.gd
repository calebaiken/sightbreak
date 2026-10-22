extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var file := FileAccess.open("user://hud-fixture-owner.txt", FileAccess.WRITE)
    file.store_string("Changed ownership marker must remain unchanged")
    file.close()
    finish(0)
