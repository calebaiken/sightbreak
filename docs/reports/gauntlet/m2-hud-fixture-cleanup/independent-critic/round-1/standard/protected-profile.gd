extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var file := FileAccess.open("user://offline_training.json", FileAccess.WRITE)
    file.store_string("Protected fixture save must remain unchanged")
    file.close()
    await super.run()
