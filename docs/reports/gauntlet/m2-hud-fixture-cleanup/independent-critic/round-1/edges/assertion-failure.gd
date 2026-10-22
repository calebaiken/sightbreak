extends "res://tests/hud_objective_hint_test.gd"
func run() -> void:
    check(false, "Independent forced assertion failure")
    finish(1)
