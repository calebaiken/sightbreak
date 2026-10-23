#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_dir"
mkdir -p .local/validation
validation_dir="$(mktemp -d "$repo_dir/.local/validation/run-XXXXXX")"
run_godot() {
  local label="$1"
  shift
  timeout "${SIGHTBREAK_TEST_TIMEOUT:-540}" "$repo_dir/scripts/godot.sh" "$@" 2>&1 | tee "$validation_dir/$label.log"
  if rg -q '^SCRIPT ERROR|^ERROR:|Parse Error' "$validation_dir/$label.log"; then return 1; fi
}
run_godot import --headless --editor --import --quit
run_godot actor --headless --script res://tests/actor_test.gd
run_godot world --headless --script res://tests/world_test.gd
run_godot hit-feedback --headless --script res://tests/hit_feedback_test.gd
run_godot weapon-integrity --headless --script res://tests/weapon_integrity_test.gd
run_godot gunplay-rules --headless --audio-driver Dummy --script res://tests/gunplay_rules_probe.gd
run_godot hit-volume --headless --script res://tests/hit_volume_test.gd
run_godot hit-history --headless --script res://tests/hit_history_test.gd
run_godot render-budget --headless --script res://tests/render_budget_test.gd
run_godot smoke-presentation --headless --script res://tests/smoke_presentation_test.gd
run_godot match --headless --script res://tests/match_test.gd
run_godot authority-order --headless --script res://tests/authority_order_test.gd
run_godot state-privacy --headless --script res://tests/state_privacy_test.gd
run_godot snapshot-buffer --headless --script res://tests/snapshot_buffer_test.gd
run_godot input-stream --headless --script res://tests/input_stream_test.gd
run_godot activity-provenance --headless --script res://tests/activity_provenance_test.gd
run_godot movement-replay --headless --script res://tests/movement_prediction_test.gd
run_godot input-lifecycle --headless --script res://tests/input_lifecycle_test.gd
run_godot peer-lifecycle --headless --script res://tests/peer_lifecycle_test.gd
run_godot result-outbox --headless --script res://tests/result_outbox_test.gd
python3 -m unittest discover -s server/tests -v
run_godot reconnect-policy --headless --script res://tests/reconnect_policy_test.gd
run_godot reconnect-independent --headless --script res://tests/independent_reconnect_review_test.gd
run_godot resume-admission --headless --script res://tests/independent_resume_admission_test.gd
run_godot lost-welcome --headless --script res://tests/lost_welcome_test.gd
run_godot resume-alias --headless --script res://tests/independent_resume_alias_test.gd
run_godot resume-auth-loss --headless --script res://tests/resume_auth_loss_test.gd
run_godot bot-ai-regression --headless --script res://tests/bot_ai_regression_test.gd
run_godot bot-dry-weapon --headless --audio-driver Dummy --script res://tests/bot_dry_weapon_test.gd
run_godot bot-squad-symmetry --headless --script res://tests/bot_squad_symmetry_test.gd
run_godot bots --headless --script res://tests/bot_match_test.gd
run_godot bot-lifecycle --headless --script res://tests/bot_lifecycle_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/profile-state" run_godot profile --headless --script res://tests/profile_test.gd
run_godot touch --headless --script res://tests/touch_test.gd
run_godot main --headless --script res://tests/main_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/input-mode-state" run_godot input-mode --headless --script res://tests/input_mode_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/menu-focus-state" run_godot menu-focus --headless --script res://tests/menu_focus_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/offline-diagnostics-state" run_godot offline-diagnostics --headless --script res://tests/offline_diagnostics_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/objective-hud-state" run_godot objective-hud --headless --script res://tests/hud_objective_hint_test.gd
run_godot landscape --headless --script res://tests/landscape_ui_test.gd
run_godot ux-contract --headless --script res://tests/ux_contract_test.gd
run_godot hud-overflow --headless --script res://tests/hud_overflow_test.gd
run_godot economy-ui --headless --script res://tests/economy_ui_test.gd
run_godot armory-ui --headless --script res://tests/armory_ui_test.gd
run_godot armory-state --headless --script res://tests/armory_state_test.gd
run_godot menu-state --headless --script res://tests/menu_state_test.gd
run_godot economy-recovery --headless --script res://tests/economy_recovery_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/transaction-journal-state" run_godot transaction-journal --headless --script res://tests/transaction_journal_test.gd
python3 scripts/test_transaction_restart_oracle.py
run_godot cosmetics --headless --script res://tests/cosmetic_presentation_test.gd
run_godot weapon-art --headless --script res://tests/weapon_art_test.gd
run_godot integration-actor-lifecycle --headless --script res://tests/integration_actor_lifecycle_test.gd
python3 scripts/test_account_network_output.py
python3 scripts/test_account_match_output.py
run_godot reload-sequence --headless --script res://tests/reload_sequence_test.gd
run_godot reload-audio --headless --script res://tests/reload_audio_test.gd
# The real mix of a real-time reload through an AudioEffectCapture on the Dummy driver (it mixes in real time, no speaker).
run_godot reload-audio-capture --headless --audio-driver Dummy --script res://tests/reload_audio_capture.gd -- --scenario=reload
run_godot reload-audio-cancel --headless --audio-driver Dummy --script res://tests/reload_audio_capture.gd -- --scenario=cancel
run_godot reload-audio-shot --headless --audio-driver Dummy --script res://tests/reload_audio_capture.gd -- --scenario=shot
python3 scripts/test_reload_contact.py | tee "$validation_dir/reload-contact.log"
if [[ -n "${DISPLAY:-}" ]]; then
  # Counts the pixels each part of the reload really draws; needs a rendering display (Xvfb is enough).
  run_godot reload-visibility --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_visibility_test.gd -- --step=2
  # The rifle's painted metal keeps its finish through the reload (it turned pale as the reload rolled it): sun, shade, a skin.
  run_godot reload-finish-sunlit --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_discolour_probe.gd -- --assert --conditions=base
  run_godot reload-finish-shade --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_discolour_probe.gd -- --assert --conditions=base --view=shade
  # The parts separate in four lightings (the grip is darker than the receiver, the gloves are not a pale veil beside the sleeve,
  # the rifle does not dissolve in a dark interior): bounds set from this round's measurements, see viewmodel_light_probe.gd.
  run_godot viewmodel-light --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/viewmodel_light_probe.gd -- --assert --poses=ready,grab
  run_godot reload-finish-skin --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_discolour_probe.gd -- --assert --conditions=base --skin
else
  printf 'reload-visibility skipped: no DISPLAY (needs a native rendering display)\n'
fi
./scripts/test_network.sh
python3 scripts/test_connection_lifecycle.py --out "$validation_dir/connection-lifecycle"
# The armory fixture must be what the backend serves. This needs the backend's Python
# dependencies (uv sync --project backend; point SIGHTBREAK_BACKEND_PYTHON at that interpreter).
backend_python="${SIGHTBREAK_BACKEND_PYTHON:-$repo_dir/.venv/bin/python}"
if [[ -x "$backend_python" ]]; then
  "$backend_python" scripts/export_catalog_fixture.py --check
else
  printf 'SKIPPED catalog fixture drift check: no backend Python at %s\n' "$backend_python"
fi
if [[ "${1:-}" == --backend ]]; then
  backend/dev-db.sh
  test_database="sightbreak_validation_${RANDOM}_test"
  docker exec sightbreak-postgres createdb -U sightbreak "$test_database"
  trap 'docker exec sightbreak-postgres dropdb -U sightbreak "$test_database" >/dev/null' EXIT
  DATABASE_URL="postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/$test_database" \
    PYTHONPATH=backend .venv/bin/pytest backend/tests -q
  .venv/bin/python scripts/test_admission_capacity.py
  .venv/bin/python scripts/test_result_outbox.py
  .venv/bin/python scripts/test_native_economy.py
  .venv/bin/python backend/simulate.py
fi
python3 scripts/test_build_manifest.py
python3 scripts/test_native_observation.py -v
python3 scripts/test_offline_role_guidance.py -v
python3 scripts/test_offline_export_ocr.py -v
python3 scripts/test_offline_capture_fences.py -v
python3 scripts/test_native_focus_fence.py -v
python3 scripts/test_focus_resume_timing.py -v
printf 'Validation completed. Logs: %s\n' "$validation_dir"
