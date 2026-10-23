extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var out: Array = []
    assert(OS.execute("chmod", ["500", fixture_user_dir], out) == 0)
    finish(1)
