"""Extend the original read-only audit; preserve all earlier audit programs/receipts."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
SERIAL = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3-evidence\pre-freeze-tooling-20261019\attempt-20261024T091611731546Z\results.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.source_output.exists():
        raise SystemExit("Refusing to replace an earlier audit")
    spec = importlib.util.spec_from_file_location("original_publication_audit", HERE / "audit.py")
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    audit.PACKETS.update({
        "ci-repair-followup": "SHA256SUMS.txt",
        "retry-tooling-review": "SHA256SUMS.txt",
        "snapshot-observability-review": "SHA256SUMS",
        "ci-attempts/run-39880125007": "SHA256SUMS.txt",
    })
    sys.argv = [str(HERE / "audit.py"), "--output", str(args.output)]
    publication_exit = audit.main()
    serial = json.loads(SERIAL.read_text(encoding="utf-8"))
    failures = []
    if (serial.get("passed") is not True or serial.get("source_unchanged") is not True
            or serial["source_before"] != serial["source_after"]
            or any(row.get("exit") != 0 for row in serial["checks"])):
        failures.append("Serial receipt does not establish unchanged-source successful exits")
    for relative, expected in serial["source_after"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        if actual != expected:
            failures.append({"path": relative, "failure": "Python source changed after serial controls"})
    transfers = {
        "backend/tests/test_trade_reads.py": "8dc8e3715dcaeb99fe6e3544243ee591d68c337b",
        "scripts/benchmark_trade_reads.py": "8dc8e3715dcaeb99fe6e3544243ee591d68c337b",
        "scripts/check_trade_read_assurance.py": "3e7ce7409322766d07afe504d97f47c5b3614875",
        "scripts/verify_trade_read_artifacts.py": "8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf",
        "backend/app.py": "4a8e9ea73aa8b286d9f1751b0a6b485479737294",
        "game/scripts/network/ack_snapshot_diagnostics.gd": "0fbce120d8c17db58596d280f7d8401ab2aa0937",
        "game/scripts/network/movement_prediction.gd": "0fbce120d8c17db58596d280f7d8401ab2aa0937",
    }
    bindings = []
    for path, commit in transfers.items():
        expected = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        staged = subprocess.check_output(["git", "show", f":{path}"], cwd=ROOT)
        matches = expected == staged
        bindings.append({"path": path, "commit": commit, "index_sha256": hashlib.sha256(staged).hexdigest(), "exact_git_bytes": matches})
        if not matches:
            failures.append({"path": path, "failure": "Staged source differs from accepted upstream"})
    result = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Read-only source/index custody; not a new test, native run or acceptance",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "serial_receipt_sha256": hashlib.sha256(SERIAL.read_bytes()).hexdigest(),
        "python_sources_checked": len(serial["source_after"]),
        "upstream_index_bindings": bindings,
        "publication_exit": publication_exit,
        "failures": failures,
        "passed": publication_exit == 0 and not failures,
    }
    args.source_output.parent.mkdir(parents=True, exist_ok=True)
    with args.source_output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
