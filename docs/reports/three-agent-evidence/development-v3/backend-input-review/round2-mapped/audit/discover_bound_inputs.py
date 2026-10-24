from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, check, digest, finish, git_blob, git_bytes, load, local, save_json, write_new

prekey = load((ROOT / "PRE_KEY_FREEZE_VERIFIED.json").read_bytes())
if not prekey["all_checks_passed"] or prekey["key_opened_in_this_program"]:
    raise SystemExit("Pre-key freeze verification required")
archive = "866e2e1f38461fa245557c9015b6c1a1a97ad745"
key_path = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\blind-trade-retention-r2-key-6eb0d1093bd6\mapping.json")
external = local(key_path)
archived = git_blob(archive, "docs/reports/backend-trade-read-v3/identity-release-r2/mapping.json")
expected = "28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a"
check("released second key supplied full hash", digest(external) == expected)
check("released second key exact Git archive bytes", external == archived)
write_new(ROOT / "second-key-verified.json", archived)
key = load(archived)
check("second key binds frozen packet", key["packet_manifest_sha256"] == prekey["packet_manifest_sha256"])
summary = {"variants": key["variants"], "raw_git_path": key["raw_git_path"],
           "raw_manifest_sha256": key["raw_manifest_sha256"], "raw_file_count": len(key["raw_files"]),
           "packet_file_count": len(key["packet_files"]), "key_sha256": digest(archived)}
save_json("SECOND_KEY_SUMMARY.json", summary)
for commit, label in [("172c900795c04f9b8706c4e80d72f55927f40da1", "assurance-publication"),
                      ("8dc8e3715dcaeb99fe6e3544243ee591d68c337b", "assurance-source-freeze"),
                      ("3e7ce7409322766d07afe504d97f47c5b3614875", "control-runner")]:
    _, names = git_bytes(["diff-tree", "--no-commit-id", "--name-status", "-r", commit])
    write_new(ROOT / f"{label}-paths.txt", names)
_, paths = git_bytes(["ls-tree", "-r", "--name-only", archive, "--", key["raw_git_path"]])
write_new(ROOT / "r2-raw-paths.txt", paths)
finish("INPUT_DISCOVERY.json", {"mapping_read_only_after_verified_freeze": True,
                               "key_sha256": digest(archived), "raw_git_path": key["raw_git_path"]})
