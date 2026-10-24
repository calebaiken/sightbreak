"""Append blocked/source-only evidence. Does not launch or simulate Godot."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("controls_driver_definitions_only", ROOT / "driver.py")
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)

preflight_error = None
try:
    driver.preflight("blocked-no-native")
except RuntimeError as error:
    preflight_error = str(error)

sources = []
for source_path, destination in (
    ("game/scripts/ui/economy_ui.gd", ROOT / "source/economy_ui.gd"),
    ("game/scripts/ui/transaction_journal.gd", ROOT / "project/transaction_journal.gd"),
):
    specifier = driver.COMMIT + ":" + source_path
    exact = driver.git("show", specifier)
    if exact != destination.read_bytes():
        raise RuntimeError("Frozen source differs from exact Git commit")
    sources.append({"source_path": source_path, "git_blob_oid": driver.git("rev-parse", specifier).decode().strip(),
                    "byte_equal_to_git": True, **driver.digest(destination)})

source_bytes = (ROOT / "source/economy_ui.gd").read_bytes().splitlines(keepends=True)
fragment = b"".join(source_bytes[596:608])
if (ROOT / "project/receipt_predicates.gd").read_bytes() != b"extends RefCounted\n\n" + fragment:
    raise RuntimeError("Predicate extraction differs from production")

timeline = json.loads((ROOT / "raw/timeline.json").read_text(encoding="utf-8"))
result = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
native_artifacts = [str(path) for path in (ROOT / "raw").glob("native-*")]
engine_artifacts = [str(path) for path in (ROOT / "raw").glob("engine-*")]
if timeline or native_artifacts or engine_artifacts or driver.ENGINE.exists():
    raise RuntimeError("Blocked evidence differs from expected no-native state")

driver.save(ROOT / "blocked-source-manifest.json", {
    "utc": driver.utc(), "commit": driver.COMMIT,
    "status": "BLOCKED_BEFORE_ANY_NATIVE_LAUNCH", "native_process_count": 0,
    "runtime_claims_verified": False, "original_failure_preserved": result,
    "engine": {"requested_path": str(driver.ENGINE), "exists": False, "sha256": None},
    "pre_import_manifest_created": (ROOT / "pre-import-manifest.json").exists(),
    "scope": "Post-failure source-only binding verification, not native evidence",
    "source": sources, "predicate_region_byte_equal": True,
    "python": {**driver.digest(driver.PYTHON), "version": driver.sys.version},
    "prepared_inputs": [driver.digest(ROOT / name) for name in (
        "driver.py", "project/probe.gd", "project/project.godot", "project/receipt_predicates.gd",
        "harness/matrix_process.py", "commands.json", "record_blocked.py")],
    "control_status": {"S1_finding_shapes": "NOT_RUN", "S1_positives_and_negatives": "NOT_RUN",
                       "S2_A_invalid_stage": "NOT_RUN", "S2_B_blocked_stage": "NOT_RUN",
                       "S2_B_positive_after_A_exit": "NOT_RUN"},
    "network_count": "not independently measured", "post_failure_preflight_error": preflight_error,
    "local_searches": ["No Godot executable found in user profile, including hidden files",
                       "No 4.7.2 matching path found under approved OpenCode temporary root",
                       "No Godot command on PATH"],
    "fresh_attempt_required": "Existing failure/result/signal files must not be overwritten or reused"})
driver.save(ROOT / "blocked-final-sha256.json", [driver.digest(path) for path in sorted(ROOT.rglob("*")) if path.is_file()])
print(json.dumps({"root": str(ROOT), "status": "BLOCKED_BEFORE_ANY_NATIVE_LAUNCH", "native_process_count": 0,
                  "sources": sources, "summary": driver.digest(ROOT / "BLOCKED.md"),
                  "manifest": driver.digest(ROOT / "blocked-source-manifest.json"),
                  "hash_index": driver.digest(ROOT / "blocked-final-sha256.json")}, indent=2))
