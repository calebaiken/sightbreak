"""Serial launcher for OUR named offline audits, never retained target programs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ALLOWED = {"audit_retention_bindings.py", "audit_followup.py", "seal_audit.py"}
if sys.version_info[:2] != (3, 13) or len(sys.argv) != 2 or sys.argv[1] not in ALLOWED:
    raise SystemExit("Approved CPython 3.13 and a named own offline audit required")
name = sys.argv[1]
program = ROOT / name
out = ROOT / (name + ".stdout.log")
err = ROOT / (name + ".stderr.log")
argv = [sys.executable, "-I", str(program)]
with out.open("xb") as stdout, err.open("xb") as stderr:
    result = subprocess.run(argv, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
record = {"utc": datetime.now(timezone.utc).isoformat(), "argv": argv, "exit": result.returncode,
          "program_sha256": hashlib.sha256(program.read_bytes()).hexdigest(),
          "stdout": out.name, "stdout_bytes": out.stat().st_size,
          "stdout_sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
          "stderr": err.name, "stderr_bytes": err.stat().st_size,
          "stderr_sha256": hashlib.sha256(err.read_bytes()).hexdigest(),
          "scope": "Our file/JSON/hash/AST audit only. Exit zero is not a substitute for checking audit failures."}
with (ROOT / "offline-executions.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
    stream.write(json.dumps(record) + "\n")
print(json.dumps(record, indent=2))
print(out.read_text(encoding="utf-8"))
if result.returncode:
    print(err.read_text(encoding="utf-8"), file=sys.stderr)
raise SystemExit(result.returncode)
