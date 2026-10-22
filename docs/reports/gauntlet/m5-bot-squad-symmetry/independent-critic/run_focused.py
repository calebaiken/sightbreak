#!/usr/bin/env python3
"""Run independent focused M5 checks serially with source/hash stability receipts."""
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
FILES = (
    "game/scripts/gameplay/bot_ai.gd", "game/scripts/gameplay/match.gd",
    "game/scripts/gameplay/actor.gd", "game/scripts/gameplay/arena.gd",
    "game/tests/bot_squad_symmetry_test.gd", "scripts/validate.sh",
)
TESTS = (
    ("import", ("--headless", "--editor", "--import", "--quit")),
    ("symmetry", ("--headless", "--script", "res://tests/bot_squad_symmetry_test.gd")),
    ("bot-ai", ("--headless", "--script", "res://tests/bot_ai_regression_test.gd")),
    ("authority", ("--headless", "--script", "res://tests/authority_order_test.gd")),
    ("match", ("--headless", "--script", "res://tests/match_test.gd")),
    ("actor", ("--headless", "--script", "res://tests/actor_test.gd")),
    ("weapon", ("--headless", "--script", "res://tests/weapon_integrity_test.gd")),
    ("hit-volume", ("--headless", "--script", "res://tests/hit_volume_test.gd")),
    ("privacy", ("--headless", "--script", "res://tests/state_privacy_test.gd")),
)


def source():
    return {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "game_tree": subprocess.check_output(["git", "rev-parse", "HEAD:game"], cwd=ROOT, text=True).strip(),
        "tracked_diff": subprocess.check_output(["git", "diff", "--", "game", "scripts"], cwd=ROOT, text=True),
        "files": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
    }


def main():
    initial = source()
    assert not initial["tracked_diff"]
    receipts = []
    assert not (OUT / "focused-receipts.json").exists(), "Refuse to overwrite prior run"
    for label, arguments in TESTS:
        command = [str(ROOT / "scripts/godot.sh"), *arguments]
        before = source()
        assert before == initial
        start = time.monotonic()
        try:
            run = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, timeout=180)
            code, raw = run.returncode, run.stdout
        except subprocess.TimeoutExpired as error:
            code, raw = "timeout", error.stdout or b""
        log = OUT / (label + ".log")
        log.write_bytes(raw)
        after = source()
        error_lines = [line for line in raw.decode(errors="replace").splitlines()
                       if line.startswith(("ERROR:", "SCRIPT ERROR", "Parse Error"))]
        receipt = {"label": label, "command": command, "returncode": code,
                   "wall_seconds": round(time.monotonic() - start, 3),
                   "log": log.name, "log_sha256": hashlib.sha256(raw).hexdigest(),
                   "source_before": before, "source_after": after,
                   "source_stable": before == after == initial, "error_lines": error_lines,
                   "passed": code == 0 and before == after == initial and not error_lines}
        receipts.append(receipt)
        (OUT / "focused-receipts.json").write_text(json.dumps(receipts, indent=2) + "\n")
        print(json.dumps({k: v for k, v in receipt.items()
                          if k not in ("source_before", "source_after")}), flush=True)
        if not receipt["passed"]:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
