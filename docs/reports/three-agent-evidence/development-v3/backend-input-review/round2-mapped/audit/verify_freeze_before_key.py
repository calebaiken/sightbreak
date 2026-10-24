"""Must pass before any second identity mapping bytes are opened."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, check, digest, finish, git_blob, load, local

COMMIT = "866e2e1f38461fa245557c9015b6c1a1a97ad745"
GIT_ROOT = "docs/reports/backend-trade-read-v3/identity-release-r2/sol"
ORIGINAL = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-retention-blind-verdict-20261019T200657Z")
REPORT_SHA = "1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e"

freeze_raw = git_blob(COMMIT, GIT_ROOT + "/FROZEN.json")
report_raw = git_blob(COMMIT, GIT_ROOT + "/NEUTRAL_RETENTION_VERDICT.md")
check("archived freeze supplied prefix", digest(freeze_raw).startswith("185d7b"), actual_sha256=digest(freeze_raw))
check("archived report full freeze-bound SHA", digest(report_raw) == REPORT_SHA, actual_sha256=digest(report_raw))
check("archived freeze equals external original", freeze_raw == local(ORIGINAL / "FROZEN.json"))
check("archived report equals external original", report_raw == local(ORIGINAL / "NEUTRAL_RETENTION_VERDICT.md"))
ledger_raw = local(ORIGINAL / "SHA256SUMS.txt")
check("external freeze ledger supplied prefix", digest(ledger_raw).startswith("f34dec"), actual_sha256=digest(ledger_raw))
entries = {}
for line in ledger_raw.decode("utf-8-sig").splitlines():
    sha, name = line.split("  ", 1)
    if name in entries or Path(name).is_absolute() or ".." in Path(name).parts:
        raise ValueError("Unsafe/duplicate freeze ledger path")
    entries[name] = sha
    data = local(ORIGINAL / name)
    check(f"external freeze ledger hash {name}", digest(data) == sha, bytes=len(data))
freeze = load(freeze_raw)
check("ledger binds full archived freeze", entries["FROZEN.json"] == digest(freeze_raw))
check("ledger binds full archived report", entries["NEUTRAL_RETENTION_VERDICT.md"] == REPORT_SHA)
for artifact in freeze["artifacts"]:
    data = local(ORIGINAL / artifact["path"])
    check(f"FROZEN bytes/hash {artifact['path']}", len(data) == artifact["bytes"] and digest(data) == artifact["sha256"])
check("freeze explicitly blind before identity", "identity key/source/repository/owner reports not inspected" in freeze["blind_status"])
check("first frozen report preserved in second freeze", freeze["preserved_first_verdict"]["sha256"] == "f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa")
result = finish("PRE_KEY_FREEZE_VERIFIED.json", {"key_opened_in_this_program": False,
                  "frozen_utc": freeze["frozen_utc"], "freeze_sha256": digest(freeze_raw),
                  "report_sha256": digest(report_raw), "ledger_sha256": digest(ledger_raw),
                  "packet_manifest_sha256": freeze["packet_manifest_sha256"],
                  "original_verdict_directory": str(ORIGINAL), "packet_root": freeze["packet_root"]})
if not result["all_checks_passed"]:
    raise SystemExit(2)
