#!/usr/bin/env python3
"""Run the fixed M5 paired observation set serially, retaining every outcome."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def records(text, prefix):
    return [json.loads(line[len(prefix):]) for line in text.splitlines() if line.startswith(prefix)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    # Predeclared seeds, both initial sides, both sources. Never replace a failure.
    for seed in (71, 72):
        for swap in (False, True):
            for label, root in (("baseline", args.baseline), ("candidate", args.candidate)):
                root = root.resolve()
                command = [str(root / "scripts/godot.sh"), "--headless", "--audio-driver", "Dummy", "--script", "res://tests/bot_squad_observation.gd", "--", f"--seed={seed}"]
                if swap:
                    command.append("--swap-start")
                started = time.monotonic()
                try:
                    run = subprocess.run(command, cwd=root, env=os.environ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
                    code, raw = run.returncode, run.stdout
                except subprocess.TimeoutExpired as error:
                    code, raw = "timeout", error.stdout or b""
                filename = f"{label}-{seed}-{'swapped' if swap else 'stock'}.log"
                (args.output / filename).write_bytes(raw)
                text = raw.decode("utf-8", errors="replace")
                row = {"source": label, "seed": seed, "swap_start": swap, "returncode": code, "wall_seconds": round(time.monotonic() - started, 3), "log": filename, "log_sha256": hashlib.sha256(raw).hexdigest(), "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(), "bot_sha256": hashlib.sha256((root / "game/scripts/gameplay/bot_ai.gd").read_bytes()).hexdigest()}
                try:
                    starts = records(text, "BOT_SQUAD_OBSERVATION_START ")
                    rounds = records(text, "BOT_SQUAD_OBSERVATION_ROUND ")
                    matches = records(text, "BOT_SQUAD_OBSERVATION_MATCH ")
                    assert code == 0 and len(starts) == 1 and len(matches) == 1
                    start, match = starts[0], matches[0]
                    assert start["seed"] == seed and start["swap_start"] == swap
                    assert start["actor_order"] == list(range(1, 11)) and start["protocol"] == 6
                    assert start["authority_override"] is False
                    assert match["valid"] and match["phase"] == "match_over" and match["ranked_payload_empty"]
                    assert match["seed"] == seed and match["swap_start"] == swap and match["time_scale"] == 4
                    assert len(rounds) == match["rounds"] and 7 <= len(rounds) <= 12
                    assert [r["round"] for r in rounds] == list(range(1, len(rounds) + 1))
                    assert all(r["winner_ids"] in (list(range(1, 6)), list(range(6, 11))) for r in rounds)
                    assert not any(line.startswith(("SCRIPT ERROR", "ERROR:", "Parse Error")) for line in text.splitlines())
                    low_wins = sum(r["winner_ids"] == list(range(1, 6)) for r in rounds)
                    row.update(valid=True, low_id_round_wins=low_wins, high_id_round_wins=len(rounds) - low_wins, planted_rounds=sum(r["planted"] for r in rounds), match=match)
                except (AssertionError, KeyError, ValueError) as error:
                    row.update(valid=False, validation_error=f"{type(error).__name__}: {error}")
                results.append(row)
                (args.output / "results.json").write_text(json.dumps(results, indent=2) + "\n")
                print(json.dumps(row), flush=True)
    return 0 if all(row["valid"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
