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
run_godot hit-volume --headless --script res://tests/hit_volume_test.gd
run_godot hit-history --headless --script res://tests/hit_history_test.gd
run_godot render-budget --headless --script res://tests/render_budget_test.gd
run_godot smoke-presentation --headless --script res://tests/smoke_presentation_test.gd
run_godot match --headless --script res://tests/match_test.gd
run_godot state-privacy --headless --script res://tests/state_privacy_test.gd
run_godot snapshot-buffer --headless --script res://tests/snapshot_buffer_test.gd
run_godot input-stream --headless --script res://tests/input_stream_test.gd
run_godot movement-replay --headless --script res://tests/movement_prediction_test.gd
run_godot input-lifecycle --headless --script res://tests/input_lifecycle_test.gd
run_godot peer-lifecycle --headless --script res://tests/peer_lifecycle_test.gd
run_godot result-outbox --headless --script res://tests/result_outbox_test.gd
python3 -m unittest discover -s server/tests -v
run_godot bots --headless --script res://tests/bot_match_test.gd
run_godot bot-lifecycle --headless --script res://tests/bot_lifecycle_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/profile-state" run_godot profile --headless --script res://tests/profile_test.gd
run_godot touch --headless --script res://tests/touch_test.gd
run_godot main --headless --script res://tests/main_test.gd
run_godot landscape --headless --script res://tests/landscape_ui_test.gd
run_godot ux-contract --headless --script res://tests/ux_contract_test.gd
run_godot hud-overflow --headless --script res://tests/hud_overflow_test.gd
run_godot economy-ui --headless --script res://tests/economy_ui_test.gd
run_godot armory-ui --headless --script res://tests/armory_ui_test.gd
run_godot economy-recovery --headless --script res://tests/economy_recovery_test.gd
run_godot cosmetics --headless --script res://tests/cosmetic_presentation_test.gd
run_godot weapon-art --headless --script res://tests/weapon_art_test.gd
run_godot integration-actor-lifecycle --headless --script res://tests/integration_actor_lifecycle_test.gd
./scripts/test_network.sh
python3 scripts/test_connection_lifecycle.py --out "$validation_dir/connection-lifecycle"
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
printf 'Validation completed. Logs: %s\n' "$validation_dir"
