extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    var parent := fixture_user_dir.get_base_dir()
    DirAccess.rename_absolute(parent, parent + ".held")
    DirAccess.make_dir_recursive_absolute(parent + ".target")
    var file := FileAccess.open((parent + ".target").path_join("protected.txt"), FileAccess.WRITE)
    file.store_string("Protected linked parent target must remain unchanged")
    file.close()
    var out: Array = []
    assert(OS.execute("ln", ["-s", parent + ".target", parent], out) == 0)
    finish(1)
