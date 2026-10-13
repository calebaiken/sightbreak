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
run_godot match --headless --script res://tests/match_test.gd
run_godot bots --headless --script res://tests/bot_match_test.gd
run_godot bot-lifecycle --headless --script res://tests/bot_lifecycle_test.gd
SIGHTBREAK_STATE_DIR="$validation_dir/profile-state" run_godot profile --headless --script res://tests/profile_test.gd
run_godot touch --headless --script res://tests/touch_test.gd
run_godot main --headless --script res://tests/main_test.gd
run_godot landscape --headless --script res://tests/landscape_ui_test.gd
run_godot economy-ui --headless --script res://tests/economy_ui_test.gd
run_godot economy-recovery --headless --script res://tests/economy_recovery_test.gd
run_godot cosmetics --headless --script res://tests/cosmetic_presentation_test.gd
./scripts/test_network.sh
if [[ "${1:-}" == --backend ]]; then
  backend/dev-db.sh
  test_database="sightbreak_validation_${RANDOM}_test"
  docker exec sightbreak-postgres createdb -U sightbreak "$test_database"
  trap 'docker exec sightbreak-postgres dropdb -U sightbreak "$test_database" >/dev/null' EXIT
  DATABASE_URL="postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/$test_database" \
    PYTHONPATH=backend .venv/bin/pytest backend/tests -q
  .venv/bin/python scripts/test_native_economy.py
  .venv/bin/python backend/simulate.py
fi
python3 scripts/test_build_manifest.py
printf 'Validation completed. Logs: %s\n' "$validation_dir"
