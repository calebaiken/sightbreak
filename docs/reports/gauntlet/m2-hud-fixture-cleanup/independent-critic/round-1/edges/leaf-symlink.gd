extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var held := fixture_user_dir + ".held"
    DirAccess.rename_absolute(fixture_user_dir, held)
    var out: Array = []
    assert(OS.execute("ln", ["-s", held, fixture_user_dir], out) == 0)
    finish(0)
