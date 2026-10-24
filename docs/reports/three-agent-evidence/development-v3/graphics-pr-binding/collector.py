"""Retain a new, narrowly scoped PR binding without rewriting the blind packet."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/graphics-pr-binding"
BASE = "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd"
CANDIDATE = "79a9591350854373076e62a4707ec84edc803756"
PR = "bb5212dd596571653bd37eb85a4594a72bfd1abc"
OUT.mkdir()
commands = []


def git(*args):
    argv = ["git", "--no-optional-locks", *args]
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=30)
    index = len(commands)
    stem = f"command-{index:02d}"
    for suffix, data in [("stdout", result.stdout), ("stderr", result.stderr)]:
        (OUT / f"{stem}.{suffix}.txt").write_bytes(data)
    commands.append({"argv": argv, "cwd": str(ROOT), "exit": result.returncode,
                     "stdout": f"{stem}.stdout.txt", "stderr": f"{stem}.stderr.txt"})
    if result.returncode:
        raise RuntimeError(f"Git failed: {argv!r}: {result.stderr!r}")
    return result.stdout.decode("utf-8").strip()


for commit in [BASE, CANDIDATE, PR]:
    if git("rev-parse", "--verify", commit + "^{commit}") != commit:
        raise RuntimeError("Unexpected resolved commit")
paths = git("diff", "--name-only", BASE, CANDIDATE, "--", "game").splitlines()
paths.append("tools/art/arms_build.py")
if len(paths) != 11 or len(set(paths)) != 11:
    raise RuntimeError(f"Unexpected comparison scope: {paths!r}")
rows = []
for path in paths:
    candidate_blob = git("rev-parse", f"{CANDIDATE}:{path}")
    pr_blob = git("rev-parse", f"{PR}:{path}")
    rows.append({"path": path, "candidate_blob": candidate_blob,
                 "pr_blob": pr_blob, "equal": candidate_blob == pr_blob})
full_game_diff = git("diff", "--name-status", CANDIDATE, PR, "--", "game")
receipt = {"created_utc": datetime.now(timezone.utc).isoformat(),
           "baseline": BASE, "captured_candidate": CANDIDATE,
           "github_pr2_head_observed": PR,
           "prior_invalid_token": "2" + PR,
           "prior_packet_unchanged": True,
           "scope": "Only baseline-to-candidate game delta plus arms builder; not whole-game equality",
           "all_11_scoped_blobs_equal": all(row["equal"] for row in rows),
           "whole_game_equal": not full_game_diff, "rows": rows,
           "whole_game_diff": full_game_diff.splitlines(), "commands": commands}
(OUT / "binding.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
(OUT / "collector.py").write_bytes(Path(__file__).read_bytes())
entries = []
for path in sorted(OUT.iterdir()):
    entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
(OUT / "SHA256SUMS.txt").write_text("\n".join(entries) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUT), "rows": len(rows),
                  "all_equal": receipt["all_11_scoped_blobs_equal"],
                  "whole_game_equal": receipt["whole_game_equal"]}, indent=2))
