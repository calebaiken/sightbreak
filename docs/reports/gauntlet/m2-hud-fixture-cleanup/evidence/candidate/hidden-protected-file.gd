extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var file := FileAccess.open("user://.protected", FileAccess.WRITE)
    file.store_string("Hidden protected fixture file must remain unchanged")
    file.close()
    finish(0)
