#!/usr/bin/env python3
"""Pure source/Git review evidence. Never imports or invokes the game engine."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess

FREEZE = "114150a06c4ae00f38c84e796e5b05054e25ac37"
BASE = "b2e0293a546961230afbd73e5cd2a1a307d69e94"
HERE = Path(__file__).resolve().parent
ROOT = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def frozen(path):
    return subprocess.check_output(["git", "show", f"{FREEZE}:{path}"], cwd=ROOT)


registration = json.loads(frozen("docs/reports/gauntlet/m5-exhausted-primary-benchmark/SOURCE_FREEZE.json"))
hashes = {path: sha256(frozen(path)).hexdigest() for path in registration["sha256"]}
assert hashes == registration["sha256"]
tested_product_files = ["game/scripts/gameplay/bot_ai.gd", "game/scripts/gameplay/actor.gd", "game/scripts/gameplay/weapons.gd"]
assert not git("diff", "--name-only", "8e8d13e", FREEZE, "--", *tested_product_files)
assert git("rev-parse", f"{FREEZE}^") == BASE
changes = git("diff", "--name-status", BASE, FREEZE).splitlines()
assert changes == [
    "A\tdocs/reports/gauntlet/m5-exhausted-primary-benchmark/PREREGISTRATION.md",
    "A\tdocs/reports/gauntlet/m5-exhausted-primary-benchmark/SOURCE_FREEZE.json",
    "A\tgame/tests/bot_exhausted_primary_probe.gd",
]
product_changes = git("diff", "--name-only", BASE, FREEZE, "--", "game/scripts", "scripts", "backend")
assert not product_changes

# Independently enumerate the preregistered Cartesian cells, not game decisions.
difficulties = ("easy", "normal", "hard")
primaries = ("smg", "rifle", "marksman")
targets = ("near", "fallback_boundary", "far", "outside_sidearm", "outside_vision", "no_target")
subset = ("near", "far", "no_target")
cells = []
for difficulty, primary in product(difficulties, primaries):
    for target, active, sidearm in product(targets, ("exhausted", "reloadable"), ("loaded", "dry", "unknown")):
        cells.append(("core", difficulty, primary, active, sidearm, target, "none", False))
    for target in targets:
        cells.append(("loaded_primary", difficulty, primary, "loaded", "loaded", target, "none", False))
    for target in subset:
        for sidearm, group in (("reserve_only", "reserve_only_sidearm"), ("unowned", "unowned_sidearm")):
            cells.append((group, difficulty, primary, "exhausted", sidearm, target, "none", False))
        for active in ("exhausted", "reloadable", "loaded"):
            cells.append(("stale_active_cache", difficulty, primary, active, "loaded", target, "none", True))
        for objective in ("carrier", "defuser"):
            cells.append(("objective_guard", difficulty, primary, "exhausted", "loaded", target, objective, False))
counts = dict(sorted(Counter(cell[0] for cell in cells).items()))
assert len(cells) == len(set(cells)) == 567
assert counts == {"core": 324, "loaded_primary": 54, "objective_guard": 54,
                  "reserve_only_sidearm": 27, "stale_active_cache": 81, "unowned_sidearm": 27}
sequence_count = len(difficulties) * len(primaries) * 8
assert sequence_count == 72
assert sequence_count * 8 == 576
assert registration["fixture_rows"] == {"matrix_cases": 567, "sequences": 72,
    "sequence_steps": 576, "total_decision_action_rows": 1143}

fixture = frozen("game/tests/bot_exhausted_primary_probe.gd").decode()
arena = frozen("game/scripts/gameplay/arena.gd").decode()
for anchor in (
    '{"name": "near", "distance": 6.0, "visible": true}',
    'bot.position = m.arena.sites[0] if s.objective != "none" else Vector3(-14, 0, -10)',
    'bot.pitch = atan2(-0.35, float(s.target.distance))',
    'enemy.reset_for_round(bot.position + Vector3(float(s.target.distance), 0, 0))',
):
    assert anchor in fixture, anchor
for anchor in (
    '_container(Vector3(-7, 0, -11), Color("5d3034"), 9)',
    '_box(at + Vector3(0, 1.55, 0), Vector3(3.0, 3.1, length), color, true, true, "metal")',
    'var node: Node3D = StaticBody3D.new() if solid else Node3D.new()',
):
    assert anchor in arena, anchor

report = {
    "scope": "independent pure source/Git review; no engine/import/UID/native/OCR/services/compile",
    "reviewed_freeze": FREEZE,
    "baseline": BASE,
    "freeze_parent_is_baseline": True,
    "changes": changes,
    "product_changes": [],
    "bot_actor_weapons_match_tested_8e8d13e": True,
    "freeze_hashes_verified": hashes,
    "matrix_group_counts_independently_enumerated": counts,
    "matrix_unique_cells": len(set(cells)),
    "sequences": sequence_count,
    "sequence_steps": sequence_count * 8,
    "decision_action_rows": len(cells) + sequence_count * 8,
    "geometry_witness": {
        "fixture_source_lines": [179, 181, 184],
        "arena_source_lines": [120, 121, 178],
        "shooter_position": [-14, 0, -10],
        "near_target_position": [-8, 0, -10],
        "solid_container_center": [-7, 1.55, -11],
        "solid_container_size": [3, 3.1, 9],
        "solid_container_min": [-8.5, 0, -15.5],
        "solid_container_max": [-5.5, 3.1, -6.5],
        "near_target_foot_position_inside_container": True,
        "center_aim_at_near_container_entry_height": 1.62 - 0.35 * 5.5 / 6,
        "center_aim_enters_container_before_target_body": True,
        "limit": "source geometry proof; actual engine collision query registration has not been observed"
    },
    "verdict": "CHANGES REQUIRED BEFORE BASELINE RUN SUPPORT",
    "runtime_executed": False,
}
output = HERE / "SOURCE_AUDIT.json"
output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps({"output": str(output.relative_to(ROOT)), "freeze": FREEZE,
                  "matrix": len(cells), "rows": len(cells) + sequence_count * 8,
                  "verdict": report["verdict"]}, sort_keys=True))
