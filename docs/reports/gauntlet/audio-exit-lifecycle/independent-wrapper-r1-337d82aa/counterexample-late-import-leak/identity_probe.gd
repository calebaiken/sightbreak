extends SceneTree
func _initialize() -> void:
    var destination := ""
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--receipt="): destination = argument.trim_prefix("--receipt=")
    var data := {"project_path":ProjectSettings.globalize_path("res://"), "data_dir":OS.get_data_dir(),
        "user_data_dir":OS.get_user_data_dir(), "driver":AudioServer.get_driver_name(),
        "uses_custom_user_dir":ProjectSettings.get_setting("application/config/use_custom_user_dir"),
        "custom_user_dir":ProjectSettings.get_setting("application/config/custom_user_dir_name"),
        "profile_exists":FileAccess.file_exists("user://offline_training.json"),
        "diagnostics_exist":DirAccess.dir_exists_absolute(ProjectSettings.globalize_path("user://offline-diagnostics-unit"))}
    var file := FileAccess.open(destination, FileAccess.WRITE)
    if file == null:
        push_error("Cannot write owned native identity receipt")
        quit(2)
        return
    file.store_string(JSON.stringify(data))
    file.close()
    quit(0)
