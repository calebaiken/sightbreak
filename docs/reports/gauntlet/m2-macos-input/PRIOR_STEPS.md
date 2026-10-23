# Earlier ARM workflow state, source inspection

Inspected 2026-10-22 from the full `e38ec3c` source. No local engine workload was
started; this is a prediction checked by the native profile-entry prerequisite,
not a claim that earlier native execution was observed here.

`verify_builds.py:153` runs the native headless smoke, a headless demo with
`--quit-after 120`, and the default graphical smoke. `main.gd:92` loads the
offline profile and applies settings without saving. The smoke branch at line
1324 exits after 15 frames. The short demo uses stock time/rules and cannot
complete the stock match; the initial buy phase alone is 15 seconds. Automatic
profile progression is written only by `on_match_finished` at line 1785.
Other `profile.save()` calls are connected settings/name/touch-edit callbacks,
which these startup commands do not invoke. Earlier default Godot logging can
create or rotate native log/cache files; they are not player-profile files.

`run_native_regressions.py:72` copies the project. Its `configure()` at line 87
sets `config/use_custom_user_dir=true` and a unique
`SIGHTBREAK-native-tests-<uuid>/<suite>` name before each source suite. Its
engine-produced user-directory probe verifies that identity. Those source
fixtures therefore target their own namespaces rather than the canonical
`Godot/app_userdata/SIGHTBREAK` player profile. The source copy and namespaces
have their existing separate cleanup receipts.

This inspection predicts a fresh ARM job reaches the preflight without either
canonical player-profile entry. The preflight checks actual entry presence
twice before export launch. If prior QA or any external actor creates one, it
retains the blocker and does not delete or relabel the existing data as safe.
