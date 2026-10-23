extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var held := fixture_user_dir + ".held"
    DirAccess.rename_absolute(fixture_user_dir, held)
    var file := FileAccess.open(fixture_user_dir, FileAccess.WRITE)
    file.store_string("Foreign replacement leaf must remain unchanged")
    file.close()
    finish(0)
