from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, check, digest, finish, git_blob, git_bytes, load, local, write_new

archive = "866e2e1f38461fa245557c9015b6c1a1a97ad745"
assurance = "172c900795c04f9b8706c4e80d72f55927f40da1"
key = load((ROOT / "second-key-verified.json").read_bytes())
raw_root = key["raw_git_path"]
for name in (ROOT / "r2-raw-paths.txt").read_text().splitlines():
    relative = name.removeprefix(raw_root + "/")
    if "/workloads/" in relative:
        continue
    data = git_blob(archive, name)
    write_new(ROOT / "objects/r2" / relative, data)
    check(f"r2 key raw hash {relative}", digest(data) == key["raw_files"][relative])

assurance_root = "docs/reports/backend-trade-read-v3/assurance-r3"
_, tree = git_bytes(["ls-tree", "-r", "--name-only", assurance, "--", assurance_root])
for name in tree.decode().splitlines():
    relative = name.removeprefix(assurance_root + "/")
    data = git_blob(assurance, name)
    write_new(ROOT / "objects/assurance" / relative, data)
    if relative == "SHA256SUMS.txt":
        check("new assurance supplied raw manifest anchor", digest(data) == "38a72cbab4948e9144040626c3793e6310e74d0d73758ab8c83b6e18867c4f8c", actual_sha256=digest(data))

for label, commit, paths in [
    ("shipping", "4a8e9ea73aa8b286d9f1751b0a6b485479737294", ["backend/app.py", "backend/tests/test_trade_reads.py", "scripts/benchmark_trade_reads.py"]),
    ("r2-executed", "8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf", ["backend/app.py", "scripts/benchmark_trade_reads.py", "scripts/verify_trade_read_artifacts.py", "backend/tests/test_trade_reads.py"]),
    ("assurance-freeze", "8dc8e3715dcaeb99fe6e3544243ee591d68c337b", ["backend/app.py", "backend/tests/test_trade_reads.py", "scripts/benchmark_trade_reads.py", "scripts/check_trade_read_assurance.py"]),
    ("control-runner", "3e7ce7409322766d07afe504d97f47c5b3614875", ["scripts/check_trade_read_assurance.py"]),
]:
    for name in paths:
        data = git_blob(commit, name)
        write_new(ROOT / "objects" / label / name, data)

for label in ("M", "V"):
    path = Path(key["packet_path"]) / label / "measurement.json"
    data = local(path)
    check(f"{label} frozen neutral measurement key hash", digest(data) == key["variants"][label]["neutral_measurement_sha256"])
    write_new(ROOT / f"objects/neutral/{label}-measurement.json", data)

first_root = "docs/reports/three-agent-evidence/development-v3/backend-input-review/round1/binding"
for name in ("BINDING_VALIDATION.json", "LINE_ENDING_QUALIFICATION.json", "QUALIFIED_RECEIPT.json"):
    data = git_blob("7b6a71a", first_root + "/" + name)
    write_new(ROOT / "objects/first-round" / name, data)
finish("SELECTED_OBJECTS.json")
