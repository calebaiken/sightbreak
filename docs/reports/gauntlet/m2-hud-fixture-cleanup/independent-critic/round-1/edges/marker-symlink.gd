extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var marker := fixture_user_dir.path_join("hud-fixture-owner.txt")
    var target := fixture_user_dir + ".marker-target"
    DirAccess.rename_absolute(marker, target)
    var out: Array = []
    assert(OS.execute("ln", ["-s", target, marker], out) == 0)
    finish(0)
