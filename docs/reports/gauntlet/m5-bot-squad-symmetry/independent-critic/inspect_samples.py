#!/usr/bin/env python3
"""Independently recompute every paired output from the retained engine logs."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


KINDS = (
    "close", "long", "travel", "stuck", "stuck_low", "stuck_jump", "idle",
    "smoke", "spent_smoke", "empty_smoke", "smoke_near", "smoke_far",
    "carrier_smoke", "carrier", "defuser", "cover",
)
FIELDS = {"move", "look", "fire", "reload", "jump", "crouch", "interact", "weapon", "smoke", "grenade"}


def inspect(path):
    raw = path.read_bytes()
    text = raw.decode()
    rows = [json.loads(line.removeprefix("BOT_SQUAD_SAMPLE "))
            for line in text.splitlines() if line.startswith("BOT_SQUAD_SAMPLE ")]
    assert len(rows) == 960, (path, len(rows))
    indexed = {(r["difficulty"], r["team"], r["kind"], r["id"]): r for r in rows}
    assert len(indexed) == 960
    differences = []
    idle_moving = []
    for difficulty in ("easy", "normal", "hard"):
        for team in (0, 1):
            for kind in KINDS:
                for slot in range(5):
                    a = indexed[difficulty, team, kind, slot + 1]
                    b = indexed[difficulty, team, kind, slot + 6]
                    assert a["slot"] == b["slot"] == slot
                    for row in (a, b):
                        assert set(row["output"]) == {"command", "role", "destination"}
                        assert set(row["output"]["command"]) == FIELDS
                        if kind == "idle" and row["output"]["command"]["move"] != "(0.0, 0.0)":
                            idle_moving.append([difficulty, team, row["id"], row["output"]["command"]["move"]])
                    if a["output"] != b["output"]:
                        differences.append({"difficulty": difficulty, "team": team, "kind": kind,
                                            "slot": slot, "a": a["output"], "b": b["output"]})
    return {
        "log": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
        "samples": len(rows), "pairs": 480, "unequal_pairs": len(differences),
        "unequal_by_kind": dict(Counter(r["kind"] for r in differences)),
        "unequal_by_difficulty": dict(Counter(r["difficulty"] for r in differences)),
        "idle_moving": idle_moving,
        "engine_summary": [line for line in text.splitlines() if line.startswith("BOT_SQUAD_SYMMETRY_RESULT")],
        "failure_lines": sum(line.startswith("BOT_SQUAD_FAILURE ") for line in text.splitlines()),
        "differences": differences,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps([inspect(path) for path in args.logs], indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
