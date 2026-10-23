"""Read only the authorized pinned Git objects; never import the application."""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

assert sys.version_info[:2] == (3, 13), sys.version
ROOT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
REVISIONS = {
    "candidate": "4a8e9ea73aa8b286d9f1751b0a6b485479737294",
    "pr16": "d2439acdd5f73df7bae5ada62ee1e3dec2cf30db",
    "v2": "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd",
}
LOG = ROOT / "git-commands.jsonl"
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat")


def git(*args: str) -> bytes:
    command = ["git", "--no-pager", *args]
    result = subprocess.run(command, cwd=REPO, env=ENV, capture_output=True, check=False)
    entry = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "argv": command,
        "cwd": str(REPO),
        "returncode": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
        "stdout_bytes": len(result.stdout),
        "stderr": result.stderr.decode("utf-8", "replace"),
    }
    with LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry) + "\n")
    if result.returncode:
        raise RuntimeError(entry)
    return result.stdout


def write_new(name: str, data: str | bytes) -> None:
    mode = "xb" if isinstance(data, bytes) else "x"
    options = {} if isinstance(data, bytes) else {"encoding": "utf-8", "newline": "\n"}
    with (ROOT / name).open(mode, **options) as handle:
        handle.write(data)


def selected(source: str, wanted: set[str]) -> str:
    lines = source.splitlines()
    sections = []
    for node in ast.parse(source).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in wanted:
            start = min([node.lineno, *[d.lineno for d in getattr(node, "decorator_list", [])]])
            sections.append("\n".join(f"{i}: {lines[i - 1]}" for i in range(start, node.end_lineno + 1)))
    return "\n\n".join(sections) + "\n"


manifest = {"python": sys.version, "executable": sys.executable, "repository": str(REPO), "revisions": {}}
trade_slices = {}
for label, revision in REVISIONS.items():
    commit = git("show", "-s", "--format=%H%n%P%n%s", revision).decode("utf-8")
    raw = git("show", f"{revision}:backend/app.py")
    source = raw.decode("utf-8")
    trade_slice = selected(source, {"trade_json", "trades"})
    trade_slices[label] = trade_slice
    write_new(f"{label}-app-trade-slice.txt", trade_slice)
    manifest["revisions"][label] = {
        "commit": commit,
        "app_blob": git("rev-parse", f"{revision}:backend/app.py").decode().strip(),
        "app_sha256": hashlib.sha256(raw).hexdigest(),
        "trade_slice_sha256": hashlib.sha256(trade_slice.encode()).hexdigest(),
    }
    if label == "candidate":
        imports = "\n".join(ast.get_source_segment(source, node) for node in ast.parse(source).body
                            if isinstance(node, (ast.Import, ast.ImportFrom))) + "\n"
        write_new("candidate-app-imports.txt", imports)
        write_new("candidate-app-contract-context.txt", selected(source, {
            "authenticated", "item_json", "get_trade", "new_trade", "offer", "confirm", "cancel_trade",
            "market_buy", "transaction", "owned", "inventory",
        }))

paths = ["backend/app.py", "backend/tests/test_trade_reads.py", "scripts/benchmark_trade_reads.py"]
patch = git("diff", "--no-ext-diff", "--no-textconv", "--no-renames", "--unified=3",
            REVISIONS["pr16"], REVISIONS["candidate"], "--", *paths)
write_new("pr16-to-candidate-authorized.diff", patch)
manifest["authorized_diff_sha256"] = hashlib.sha256(patch).hexdigest()
for label in ("pr16", "v2"):
    comparison = "".join(difflib.unified_diff(trade_slices[label].splitlines(keepends=True),
                                            trade_slices["candidate"].splitlines(keepends=True),
                                            fromfile=label + ":backend/app.py:selected",
                                            tofile="candidate:backend/app.py:selected"))
    write_new(f"{label}-to-candidate-trade-slice.diff", comparison)
    manifest[f"{label}_slice_diff_sha256"] = hashlib.sha256(comparison.encode()).hexdigest()

for path, name in [("backend/tests/test_trade_reads.py", "candidate-test_trade_reads.py.txt"),
                   ("scripts/benchmark_trade_reads.py", "candidate-benchmark_trade_reads.py.txt")]:
    raw = git("show", f"{REVISIONS['candidate']}:{path}")
    source = raw.decode("utf-8")
    write_new(name, "\n".join(f"{i}: {line}" for i, line in enumerate(source.splitlines(), 1)) + "\n")
    manifest[path] = {"blob": git("rev-parse", f"{REVISIONS['candidate']}:{path}").decode().strip(),
                      "sha256": hashlib.sha256(raw).hexdigest()}

models_raw = git("show", f"{REVISIONS['candidate']}:backend/models.py")
write_new("candidate-model-contract-context.txt", selected(models_raw.decode(), {"Player", "Session", "Item", "Trade"}))
manifest["model_blob"] = git("rev-parse", f"{REVISIONS['candidate']}:backend/models.py").decode().strip()
write_new("manifest.json", json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
