"""Final source/exits/receipt consistency checks and external checksum ledger."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, SOURCES, check, digest, filehash, git_blob, load, save_json, utc, write_new

phase_names = ["PRE_KEY_FREEZE_VERIFIED.json", "INPUT_DISCOVERY.json", "SELECTED_OBJECTS.json",
               "ASSURANCE_AUDIT.json", "RETENTION_BINDING_AUDIT.json", "FOLLOWUP_AUDIT.json"]
phases = {name: load((ROOT / name).read_bytes()) for name in phase_names}
prekey = phases["PRE_KEY_FREEZE_VERIFIED.json"]
key = load((ROOT / "second-key-verified.json").read_bytes())
baseline = git_blob("701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd", "backend/app.py")
check("baseline r2 app explicit LF-to-CRLF fingerprint derivation",
      b"\r" not in baseline and digest(baseline.replace(b"\n", b"\r\n")) == key["variants"]["M"]["original_header"]["source"]["backend_files"]["backend/app.py"])


def row_tokens(raw):
    text, decoder = raw.decode("utf-8-sig"), json.JSONDecoder()
    index = text.index("{") + 1
    array = None
    while True:
        while text[index].isspace() or text[index] == ",":
            index += 1
        if text[index] == "}":
            break
        name, index = decoder.raw_decode(text, index)
        while text[index].isspace() or text[index] == ":":
            index += 1
        start = index
        _, index = decoder.raw_decode(text, index)
        if name == "rows":
            array = text[start:index]
    if array is None:
        raise ValueError("No rows array")
    tokens, quoted, escaped = [], False, False
    for char in array:
        if quoted or not char.isspace():
            tokens.append(char)
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
    return "".join(tokens).encode()


for label, role in [("M", "baseline"), ("V", "candidate")]:
    original = (ROOT / "objects/r2" / role / "measurement.json").read_bytes()
    neutral = (ROOT / f"objects/neutral/{label}-measurement.json").read_bytes()
    check(f"{label} original-neutral rows identical JSON tokens ignoring only insignificant whitespace", row_tokens(original) == row_tokens(neutral))

source_index = {}
for phase in phases.values():
    for item in phase["sources"]:
        key_id = (item["kind"], item.get("commit", ""), item["path"], item.get("blob", ""))
        prior = source_index.get(key_id)
        if prior is not None and prior["sha256"] != item["sha256"]:
            raise ValueError("Source identity hash changed across phases")
        source_index[key_id] = item
for item in SOURCES:
    source_index[(item["kind"], item.get("commit", ""), item["path"], item.get("blob", ""))] = item
for item in source_index.values():
    path = ROOT / item["capture"] if item["kind"] == "git" else Path(item["path"])
    check(f"retained source stable {item.get('commit', 'local')}:{item['path']}", path.is_file()
          and path.stat().st_size == item["bytes"] and filehash(path) == item["sha256"])

commands = [load(line) for line in (ROOT / "commands.jsonl").read_text().splitlines()]
for entry in commands:
    for kind in ("stdout", "stderr"):
        path = ROOT / entry[kind]
        check(f"command exit/raw hash record {entry[kind]}", path.stat().st_size == entry[kind + "_bytes"]
              and filehash(path) == entry[kind + "_sha256"])
check("all performed Git commands explicit exit zero", all(entry["exit"] == 0 for entry in commands))

historical = []
for program, receipt in [("verify_freeze_before_key.py", "PRE_KEY_FREEZE_VERIFIED.json"),
                         ("discover_bound_inputs.py", "INPUT_DISCOVERY.json"),
                         ("collect_selected_objects.py", "SELECTED_OBJECTS.json"),
                         ("audit_assurance.py", "ASSURANCE_AUDIT.json")]:
    historical.append({"program": program, "program_sha256": filehash(ROOT / program),
                       "tool_observed_exit": 0, "receipt": receipt,
                       "receipt_sha256": filehash(ROOT / receipt),
                       "note": "Completed direct tool invocation, not rerun for this ledger. Receipt failures are retained independently of process exit."})
for entry in [load(line) for line in (ROOT / "offline-executions.jsonl").read_text().splitlines()]:
    for kind in ("stdout", "stderr"):
        path = ROOT / entry[kind]
        check(f"own audit captured execution {entry[kind]}", path.stat().st_size == entry[kind + "_bytes"] and filehash(path) == entry[kind + "_sha256"])
    check(f"own executed audit source unchanged {Path(entry['argv'][-1]).name}", filehash(Path(entry["argv"][-1])) == entry["program_sha256"])
    historical.append(entry)
save_json("AUDIT_EXECUTIONS.json", {"recorded_utc": utc(), "executions": historical,
                                   "zero_exit_does_not_erase_failed_checks": True,
                                   "target_or_retained_programs_executed": [],
                                   "current_final_seal_command": [sys.executable, "-I", str(Path(__file__).resolve())]})
save_json("SOURCE_HASHES.json", {"created_utc": utc(), "sources": list(source_index.values()),
                               "audit_programs": [{"path": path.name, "sha256": filehash(path), "bytes": path.stat().st_size}
                                                  for path in sorted(ROOT.glob("*.py"))]})
from auditlib import CHECKS
check("final seal has no unresolved integrity check", all(item["passed"] for item in CHECKS))
decision = load((ROOT / "QUALIFIED_DECISION_LEDGER.json").read_bytes())
ledger = {"sealed_utc": utc(), "recommendation": decision["decision"],
          "phase_results": [{"receipt": name, "checks": len(phase["checks"]), "failed_checks": phase["failed_checks"]}
                            for name, phase in phases.items()],
          "two_archived_attempt1_negative_checks_retained": phases["ASSURANCE_AUDIT.json"]["failed_checks"],
          "first_archive_165_pass_1_fail_unchanged": True,
          "final_integrity_checks": CHECKS, "final_integrity_checks_passed": all(item["passed"] for item in CHECKS),
          "original_freeze_anchors": {name: prekey[name] for name in ("freeze_sha256", "report_sha256", "ledger_sha256")},
          "r2_original_app_source_snapshot": "NOT_RETAINED", "historical_actual_import_capture": "NOT_RETAINED",
          "new_r3_reverse_mutant_preimage": "POSTHOC_VERIFIED_9f94_TO_LF_703c; not original capture or retcon",
          "our_backend_DB_pytest_native_service_network_index_source_publication_executions": 0,
          "original_sol_controls": "UNEXECUTED", "primary_repository_changes": [],
          "original_verdicts_or_published_files_superseded": [],
          "checksum_scope": "Every regular file recursively except SHA256SUMS.txt itself and regenerable __pycache__ files. Manifest hash returned outside itself."}
save_json("FINAL_AUDIT_LEDGER.json", ledger)
files = sorted(path for path in ROOT.rglob("*") if path.is_file() and "__pycache__" not in path.parts and path.name != "SHA256SUMS.txt")
# Inner input manifests are themselves payload and must be included, too.
files += sorted(path for path in ROOT.rglob("SHA256SUMS.txt") if path.parent != ROOT and "__pycache__" not in path.parts)
files = sorted(set(files))
manifest = "".join(f"{filehash(path)}  {path.relative_to(ROOT).as_posix()}\n" for path in files)
write_new(ROOT / "SHA256SUMS.txt", manifest)
print(json.dumps({"external_directory": str(ROOT), "payload_files": len(files),
                  "payload_bytes": sum(path.stat().st_size for path in files), "manifest_sha256": digest(manifest.encode()),
                  "final_integrity_checks": len(CHECKS), "final_integrity_checks_passed": ledger["final_integrity_checks_passed"],
                  "prior_audit_negative_checks_retained": 2, "first_archive_failure_retained": True,
                  "recommendation": ledger["recommendation"], "target_executions_by_this_audit": 0}, indent=2))
