extends SceneTree
func _initialize() -> void:
    push_error("Intentional native cleanup control failure")
    quit(9)
