"""Run the two existing welcome/alias gates affected by input acceptance.

Run after the matched workload so this host uses one native process at a time.
Requires imported, clean frozen source trees; writes evidence outside them.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time


def identity(root):
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
            "status": subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    report = {"driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "sources": {}, "checks": []}
    error = re.compile(r"SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use", re.I)
    for label, source in (("baseline", args.baseline), ("candidate", args.candidate)):
        initial = identity(source)
        if initial["status"]:
            raise RuntimeError("source must be clean")
        report["sources"][label] = {"before": initial}
        for name in ("independent_resume_alias_test", "lost_welcome_test"):
            cmd = [str(args.godot), "--headless", "--path", str(source / "game"), "--max-fps", "60", "--script", "res://tests/" + name + ".gd"]
            start = time.monotonic()
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
                data, code = result.stdout, result.returncode
            except subprocess.TimeoutExpired as exc:
                data, code = exc.stdout or b"", -1
            log = args.out / (label + "-" + name + ".log")
            log.write_bytes(data)
            report["checks"].append({"source": label, "name": name, "command": cmd, "exit": code, "seconds": time.monotonic() - start,
                "log": log.name, "log_sha256": hashlib.sha256(data).hexdigest(), "native_errors": bool(error.search(data.decode("utf-8", "replace")))})
        report["sources"][label]["after"] = identity(source)
    report["pass"] = all(row["before"] == row["after"] for row in report["sources"].values()) and all(row["exit"] == 0 and not row["native_errors"] for row in report["checks"])
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
