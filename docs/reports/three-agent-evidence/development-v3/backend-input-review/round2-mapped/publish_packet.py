"""Create-only compact publication of a completed audit, never a target runner.

Only stdlib file/hash collection and read-only Git metadata commands are used.
Do not import/run copied programs. Writes are restricted to this NEW directory.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required")
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[5]
AUDIT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-mapped-assurance-20261023T005138Z")
VERDICT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-retention-blind-verdict-20261019T200657Z")
MANIFEST_SHA = "048276d1fcb0fe2dc52485b9d730e109669e5902ffca5f79c38cb089d7068750"
FREEZE_SHA = "185d7b4cd1dacde52d8d9cc48bc35b43fde9b1453ef98a362d798e9bb9ab0f9e"
REPORT_SHA = "1248f66b7b80e2acbf69595ef084b164957547497f7c40c2e56c4489847fcf3e"
LEDGER_SHA = "f34dec97780638ddba68a38dbf50d967000b8181eb00ad410e3060084612bc20"
KEY_SHA = "28f0de31229e531e7164ce3905ae88cedcbd07ce89e62f046983000ebdecf93a"
CAP = 6 * 1024 * 1024
CHECKS, COMMANDS = [], []
MODE = sys.argv[1] if len(sys.argv) == 2 else ""


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def filehash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check(name, condition, **details):
    CHECKS.append({"check": name, "passed": bool(condition), **details})
    return bool(condition)


def require(name, condition, **details):
    if not check(name, condition, **details):
        raise ValueError(name)


def write_new(path, data):
    if not path.is_relative_to(ROOT):
        raise ValueError("Publication writes outside exclusive directory forbidden")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data.encode("utf-8") if isinstance(data, str) else data)
        stream.flush()
        os.fsync(stream.fileno())


def save(name, value):
    # Publication metadata is compact; copied original evidence bytes are never encoded here.
    write_new(ROOT / name, json.dumps(value, separators=(",", ":"), ensure_ascii=False) + "\n")


def load(path):
    return json.loads(path.read_bytes())


def freeze_first():
    require("second frozen report exact anchor", filehash(VERDICT / "NEUTRAL_RETENTION_VERDICT.md") == REPORT_SHA)
    require("second FROZEN exact anchor", filehash(VERDICT / "FROZEN.json") == FREEZE_SHA)
    require("second frozen ledger exact anchor", filehash(VERDICT / "SHA256SUMS.txt") == LEDGER_SHA)
    frozen = load(VERDICT / "FROZEN.json")
    for item in frozen["artifacts"]:
        path = VERDICT / item["path"]
        require(f"frozen artifact {item['path']}", path.stat().st_size == item["bytes"] and filehash(path) == item["sha256"])
    return {"verified_before_key_collection": True, "verified_utc": utc(), "frozen_utc": frozen["frozen_utc"],
            "report_sha256": REPORT_SHA, "freeze_sha256": FREEZE_SHA, "ledger_sha256": LEDGER_SHA,
            "scope": "Publication anchor check, not a new blind verdict or trusted chronology attestation"}


def inventory():
    manifest = AUDIT / "SHA256SUMS.txt"
    require("full completed 611-file external manifest anchor", filehash(manifest) == MANIFEST_SHA)
    entries = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require("valid external manifest entry", match is not None)
        digest, name = match.groups()
        require(f"safe unique external name {name}", name not in entries and not Path(name).is_absolute() and ".." not in Path(name).parts)
        path = AUDIT / name
        require(f"external bytes {name}", path.is_file() and not path.is_symlink() and filehash(path) == digest)
        entries[name] = {"path": name, "bytes": path.stat().st_size, "sha256": digest}
    actual = {p.relative_to(AUDIT).as_posix() for p in AUDIT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p != manifest}
    require("external manifest covers exactly all 611 payload files", len(entries) == 611 and actual == set(entries))
    return entries


def plan():
    frozen = freeze_first()
    entries = inventory()
    source_index = load(AUDIT / "SOURCE_HASHES.json")
    selected = {name for name in entries if "/" not in name or name.startswith(("objects/", "derived/"))
                or name.startswith("raw/") and entries[name]["bytes"] <= 1024}
    representative = []
    for source in source_index["sources"]:
        if source["kind"] == "git" and "/retention-r2/" in source["path"] and "/workloads/" in source["path"]:
            copied = "/workloads/05-40-20/" in source["path"]
            if copied:
                selected.add(source["capture"])
            representative.append({"git_commit": source["commit"], "git_path": source["path"],
                                   "git_blob": source["blob"], "bytes": source["bytes"], "sha256": source["sha256"],
                                   "external_capture": source["capture"], "representative_case": copied})
    frozen_files = [{"path": p.name, "bytes": p.stat().st_size, "sha256": filehash(p)}
                    for p in sorted(VERDICT.iterdir()) if p.is_file()]
    selected_bytes = sum(entries[name]["bytes"] for name in selected)
    estimated = selected_bytes + sum(item["bytes"] for item in frozen_files) + (AUDIT / "SHA256SUMS.txt").stat().st_size
    require("selection leaves room for publication ledgers below 6 MiB", estimated < CAP - 512 * 1024,
            selected_input_bytes=estimated, cap=CAP)
    value = {"created_utc": utc(), "audit_root": str(AUDIT), "audit_manifest_sha256": MANIFEST_SHA,
             "frozen_verdict_root": str(VERDICT), "freeze_precheck": frozen, "external_payload_files": 611,
             "external_payload_bytes": sum(item["bytes"] for item in entries.values()),
             "selected_audit_files": len(selected), "selected_audit_bytes": selected_bytes,
             "selected_input_bytes_including_full_frozen_verdict_and_external_manifest": estimated,
             "representative_policy": "All indexed raw received/canonical/expected bodies and all 12 before/after state tables for (40,20), both roles, deduplicated by original immutable blob capture. Other cases remain fully indexed/external.",
             "inventory": [{**item, "selected": name in selected} for name, item in sorted(entries.items())],
             "representatives": representative, "frozen_files": frozen_files}
    save("COLLECTION_PLAN.json", value)
    save("PLAN_VALIDATION.json", {"checks": CHECKS, "all_checks_passed": all(c["passed"] for c in CHECKS), "targets_executed": []})
    print(json.dumps({key: value[key] for key in ("external_payload_files", "external_payload_bytes", "selected_audit_files", "selected_audit_bytes", "selected_input_bytes_including_full_frozen_verdict_and_external_manifest")}, indent=2))


def copy_exact(origin, destination, expected):
    require(f"copy origin hash {origin}", filehash(origin) == expected)
    data = origin.read_bytes()
    existing = destination.exists()
    if existing:
        require("resume may only retain matching existing bytes", MODE.startswith("resume") and destination.read_bytes() == data,
                published=destination.relative_to(ROOT).as_posix())
    else:
        write_new(destination, data)
    require(f"exact copied bytes {destination.relative_to(ROOT)}", destination.read_bytes() == data and filehash(destination) == expected)
    return {"origin": str(origin), "published": destination.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": expected,
            "copy_method": "Existing interrupted copy verified without overwrite" if existing else "read_bytes/write_bytes; no decoding, transformations or source execution"}


def refine():
    original = load(ROOT / "COLLECTION_PLAN.json")
    entries = {item["path"]: item for item in original["inventory"]}
    selected = {name for name, item in entries.items() if "/" not in name or name.startswith(("objects/", "derived/"))
                or name.startswith("raw/") and item["bytes"] <= 1024}
    for item in original["representatives"]:
        bounded = "/workloads/02-1-2/" in item["git_path"]
        heavy_state = "/workloads/05-40-20/state/" in item["git_path"]
        item["representative_case"] = bounded or heavy_state
        if bounded or heavy_state:
            selected.add(item["external_capture"])
    original["inventory"] = [{**item, "selected": name in selected} for name, item in sorted(entries.items())]
    original["selected_audit_files"] = len(selected)
    original["selected_audit_bytes"] = sum(entries[name]["bytes"] for name in selected)
    original["selected_input_bytes_including_full_frozen_verdict_and_external_manifest"] = original["selected_audit_bytes"] + sum(item["bytes"] for item in original["frozen_files"]) + (AUDIT / "SHA256SUMS.txt").stat().st_size
    original["representative_policy"] = "Complete received/canonical/expected bodies and before/after states for bounded (1,2), plus all 12 before/after item-heavy (40,20) state arrays, both roles. Full response/state index and full 611-file external manifest retained. Some other tiny/shared artifacts are also present. Large (40,20) bodies remain external rather than duplicated."
    original["refinement"] = "Initial COLLECTION_PLAN.json is preserved as planning history; this smaller active plan reserves space for complete publication ledgers. No original audit file is changed."
    require("refined selection reserves at least 1 MiB for publication metadata", original["selected_input_bytes_including_full_frozen_verdict_and_external_manifest"] < CAP - 1024 * 1024)
    save("COMPACT_COLLECTION_PLAN.json", original)
    save("REFINEMENT_VALIDATION.json", {"checks": CHECKS, "all_checks_passed": True})
    print(json.dumps({key: original[key] for key in ("selected_audit_files", "selected_audit_bytes", "selected_input_bytes_including_full_frozen_verdict_and_external_manifest", "representative_policy")}, indent=2))


def git(args, stdin=None):
    command = ["git", "--no-pager", *args]
    result = subprocess.run(command, cwd=REPO, input=stdin, capture_output=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat"), check=False)
    ident = f"{MODE}-{len(COMMANDS) + 1:03d}"
    out, err = ROOT / f"publication-raw/{ident}.stdout.bin", ROOT / f"publication-raw/{ident}.stderr.log"
    write_new(out, result.stdout)
    write_new(err, result.stderr)
    COMMANDS.append({"utc": utc(), "argv": command, "exit": result.returncode,
                     "stdin_sha256": sha(stdin) if stdin is not None else None,
                     "stdout": out.relative_to(ROOT).as_posix(), "stdout_bytes": len(result.stdout), "stdout_sha256": sha(result.stdout),
                     "stderr": err.relative_to(ROOT).as_posix(), "stderr_bytes": len(result.stderr), "stderr_sha256": sha(result.stderr)})
    require(f"explicit Git exit {ident}", result.returncode == 0, returncode=result.returncode)
    return result.stdout


def recover_interrupted_copy():
    partial = ROOT / "audit/SOURCE_HASHES.json"
    data = partial.read_bytes()
    require("known interrupted copy is exactly the observed all-zero allocation", len(data) == 316257
            and data == b"\0" * 316257 and sha(data) == "f175044a72317f9be0889591b1d0cf9f9f303063ddda43f848ae51c34be4db09")
    require("original source-hash index remains frozen", filehash(AUDIT / "SOURCE_HASHES.json") == "42c75c2db266b9e945e40bfaf298838ab4400cbc74f051355f9a5c21daac27da")
    preserved = ROOT / "publication-raw/interrupted-SOURCE_HASHES.zero-filled.bin"
    require("recovery does not replace existing failure evidence", not preserved.exists())
    partial.rename(preserved)
    require("exact interrupted bytes preserved after scoped rename", preserved.read_bytes() == data)
    save("publication-raw/INTERRUPTED_COPY_RECOVERY.json", {"utc": utc(), "original_published_path": "audit/SOURCE_HASHES.json",
                                                          "preserved_failure_path": preserved.relative_to(ROOT).as_posix(),
                                                          "bytes": len(data), "sha256": sha(data), "all_zero": True,
                                                          "original_audit_unchanged": True,
                                                          "next_action": "Create fresh verified copy at audit/SOURCE_HASHES.json; preserve every earlier failed receipt", "checks": CHECKS})
    print(json.dumps({"preserved_failure_bytes": len(data), "original_verified": True}))


def recover_remaining_zero_copies():
    plan = load(ROOT / "COMPACT_COLLECTION_PLAN.json")
    damaged = []
    for item in plan["inventory"]:
        path = ROOT / "audit" / item["path"]
        if not item["selected"] or not path.exists() or filehash(path) == item["sha256"]:
            continue
        data = path.read_bytes()
        require("bulk recovery is restricted to known all-zero interrupted copies", len(data) == item["bytes"]
                and bool(data) and not any(data), published=path.relative_to(ROOT).as_posix())
        require("original source remains frozen for damaged copy", filehash(AUDIT / item["path"]) == item["sha256"])
        damaged.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "damaged_sha256": sha(data),
                        "original_sha256": item["sha256"]})
    require("observed damaged-copy inventory retained", len(damaged) == 122 and sum(item["bytes"] for item in damaged) == 1355473)
    archive = ROOT / "publication-raw/interrupted-zero-copies.zip"
    with archive.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for item in damaged:
                bundle.writestr(item["path"], (ROOT / item["path"]).read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    with zipfile.ZipFile(archive) as bundle:
        require("failure archive contains every damaged copy", set(bundle.namelist()) == {item["path"] for item in damaged})
        for item in damaged:
            data = bundle.read(item["path"])
            require("failure bytes losslessly retained before removing bad copy", sha(data) == item["damaged_sha256"]
                    and data == (ROOT / item["path"]).read_bytes(), published=item["path"])
    save("publication-raw/BULK_INTERRUPTED_COPY_RECOVERY.json", {"utc": utc(), "scope": "Damaged publication copies only; originals unchanged",
                                                                "archive": archive.relative_to(ROOT).as_posix(), "archive_sha256": filehash(archive),
                                                                "archived_files": len(damaged), "uncompressed_bytes": sum(item["bytes"] for item in damaged),
                                                                "damaged_copies": damaged, "checks": CHECKS,
                                                                "original_evidence_not_compressed_or_transformed": True})
    for item in damaged:
        # Exact known corrupt copies only, after verifying the lossless archive.
        path = ROOT / item["path"]
        require("bad copy unchanged immediately before scoped removal", filehash(path) == item["damaged_sha256"])
        path.unlink()
    print(json.dumps({"archived_damaged_files": len(damaged), "uncompressed_failure_bytes": sum(item["bytes"] for item in damaged),
                      "archive_bytes": archive.stat().st_size, "originals_unchanged": True}))


def archive_publication_history():
    names = ["COLLECTION_PLAN.json", "PLAN_VALIDATION.json", "publication-raw/interrupted-SOURCE_HASHES.zero-filled.bin"]
    require("initial plan is publication metadata for the same external bundle", load(ROOT / names[0])["audit_manifest_sha256"] == MANIFEST_SHA)
    require("initial plan validation remains a recorded pass", load(ROOT / names[1])["all_checks_passed"] is True)
    require("only the known interrupted zero file is packed", filehash(ROOT / names[2]) == "f175044a72317f9be0889591b1d0cf9f9f303063ddda43f848ae51c34be4db09")
    records = [{"original_publication_path": name, "bytes": (ROOT / name).stat().st_size, "sha256": filehash(ROOT / name)} for name in names]
    archive = ROOT / "publication-raw/planning-and-restart-history.zip"
    with archive.open("xb") as stream:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
            for name in names:
                bundle.writestr(name, (ROOT / name).read_bytes())
        stream.flush()
        os.fsync(stream.fileno())
    with zipfile.ZipFile(archive) as bundle:
        require("temporary publication history retained losslessly", set(bundle.namelist()) == set(names))
        for item in records:
            data = bundle.read(item["original_publication_path"])
            require("archived publication-history bytes exact", sha(data) == item["sha256"]
                    and data == (ROOT / item["original_publication_path"]).read_bytes())
    save("publication-raw/PUBLICATION_HISTORY_INDEX.json", {"utc": utc(), "archive": archive.relative_to(ROOT).as_posix(),
                                                            "archive_sha256": filehash(archive), "entries": records,
                                                            "scope": "Only initial planning metadata and damaged publication-copy bytes; no completed-audit/verdict/source evidence is compressed or transformed.",
                                                            "restore": "ZIP entries preserve the original publication-relative filenames and exact bytes. Active plan is COMPACT_COLLECTION_PLAN.json.",
                                                            "checks": CHECKS})
    for item in records:
        path = ROOT / item["original_publication_path"]
        require("history unchanged before removing redundant unpacked copy", filehash(path) == item["sha256"])
        path.unlink()
    print(json.dumps({"losslessly_archived_history_files": len(records), "uncompressed_history_bytes": sum(item["bytes"] for item in records),
                      "archive_bytes": archive.stat().st_size, "directory_bytes": sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())}))


def collect():
    plan = load(ROOT / "COMPACT_COLLECTION_PLAN.json")
    frozen = freeze_first()
    require("completed external manifest stable since plan", filehash(AUDIT / "SHA256SUMS.txt") == MANIFEST_SHA)
    if MODE.startswith("resume"):
        verified = 0
        for item in plan["inventory"]:
            source = AUDIT / item["path"]
            actual = filehash(source)
            if actual != item["sha256"] or source.stat().st_size != item["bytes"]:
                require("post-restart original audit bytes unchanged", False, path=item["path"], actual_sha256=actual, expected_sha256=item["sha256"])
            verified += 1
        require("all 611 original audit payloads reverified after restart", verified == 611)
        receipt_name = "RESTART_REVALIDATION.json" if not (ROOT / "RESTART_REVALIDATION.json").exists() else f"RESTART_REVALIDATION-{MODE}.json"
        save(receipt_name, {"utc": utc(), "original_payloads_verified": verified,
                                           "full_manifest_sha256": MANIFEST_SHA,
                                           "existing_copies": "Only matching bytes retained; no preexisting file overwritten",
                                           "target_runs": []})
    copies = []
    # Copy/verify the freeze before copying the already-released identity key.
    for item in plan["frozen_files"]:
        copies.append(copy_exact(VERDICT / item["path"], ROOT / "frozen-second" / item["path"], item["sha256"]))
    require("released key exact completed-audit bytes", filehash(AUDIT / "second-key-verified.json") == KEY_SHA)
    for item in plan["inventory"]:
        if item["selected"]:
            copies.append(copy_exact(AUDIT / item["path"], ROOT / "audit" / item["path"], item["sha256"]))
    copies.append(copy_exact(AUDIT / "SHA256SUMS.txt", ROOT / "audit/SHA256SUMS.txt", MANIFEST_SHA))

    sources = load(AUDIT / "SOURCE_HASHES.json")["sources"]
    grouped = {}
    for item in sources:
        if item["kind"] == "git":
            grouped.setdefault(item["commit"], []).append(item)
    bindings = []
    for commit, items in sorted(grouped.items()):
        resolved = git(["rev-parse", "--verify", commit + "^{commit}"]).decode("ascii").strip()
        require(f"actual commit resolves nonempty {commit}", re.fullmatch(r"[0-9a-f]{40}", resolved) is not None and resolved.startswith(commit))
        if commit == "866e2e1f38461fa245557c9015b6c1a1a97ad745":
            paths = ["docs/reports/backend-trade-read-v3/retention-r2", "docs/reports/backend-trade-read-v3/identity-release-r2"]
        elif commit == "172c900795c04f9b8706c4e80d72f55927f40da1":
            paths = ["docs/reports/backend-trade-read-v3/assurance-r3"]
        else:
            paths = sorted({item["path"] for item in items})
        tree_data = git(["ls-tree", "-r", "-z", resolved, "--", *paths])
        require(f"nonempty pinned Git tree output {commit}", len(tree_data) > 0)
        tree = {}
        for record in tree_data.split(b"\0"):
            if record:
                header, path = record.split(b"\t", 1)
                mode, kind, oid = header.decode().split()
                tree[path.decode()] = (mode, kind, oid)
        for item in items:
            data = (AUDIT / item["capture"]).read_bytes()
            actual_oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            entry = tree.get(item["path"])
            valid = entry is not None and entry[0] in ("100644", "100755") and entry[1:] == ("blob", item["blob"]) and actual_oid == item["blob"] and sha(data) == item["sha256"] and len(data) == item["bytes"]
            require(f"actual pinned Git source binding {commit}:{item['path']}", valid)
            bindings.append({"commit": resolved, "path": item["path"], "git_mode": entry[0], "blob": actual_oid, "sha256": sha(data),
                             "bytes": len(data), "external_capture": item["capture"], "verified": valid})

    integration = git(["rev-parse", "--verify", "88bfc51^{commit}"]).decode().strip()
    require("local integration commit resolves", re.fullmatch(r"[0-9a-f]{40}", integration) is not None and integration.startswith("88bfc51"))
    tree = git(["ls-tree", integration, "--", "backend/app.py"]).decode().strip()
    require("local 88bfc51 app matches original 4a8 blob", tree == "100644 blob 16f33c94da490c77a8ab930b88d8fc0662f3fa4c\tbackend/app.py")
    message = git(["show", "-s", "--format=%B", integration]).decode()
    require("local integration records -x source commit", "(cherry picked from commit 4a8e9ea73aa8b286d9f1751b0a6b485479737294)" in message)

    old = load(ROOT / "audit/objects/first-round/BINDING_VALIDATION.json")
    require("first-round original 165/1 failure history unchanged", len(old["checks"]) == 166 and len(old["failed_checks"]) == 1 and old["all_recorded_checks_passed"] is False)
    initial_assurance = load(ROOT / "audit/ASSURANCE_AUDIT.json")
    require("two archived attempt-1 negative audit checks retained", len(initial_assurance["failed_checks"]) == 2)
    preimage = (ROOT / "audit/derived/attempt-2-reversed-app.py.txt").read_bytes()
    shipping = (ROOT / "audit/objects/shipping/backend/app.py").read_bytes()
    require("new posthoc preimage copied without promotion to original capture", sha(preimage) == "9f94a55f1b19858eec3ac54036601b5c26a330749454a6cb89650d51e298f020"
            and sha(shipping) == "703c20b298d734395f292d4a8c5e415e55e6f35109e9a51dcb36fbcb62647441" and preimage.replace(b"\r\n", b"\n") == shipping)
    qualified = load(ROOT / "audit/QUALIFIED_DECISION_LEDGER.json")
    require("R2 missing original app/import capture still explicit", qualified["r2_exact_app_capture"] == "NOT_RETAINED_OR_INDEPENDENTLY_AUTHENTICATED"
            and qualified["historical_fixture_import"] == "POSTHOC_ONLY_NOT_ORIGINAL_CAPTURE")
    aliases = {}
    for item in copies:
        aliases.setdefault(item["sha256"], []).append(item["published"])
    omitted = [{**item, "external_path": str(AUDIT / item["path"]),
                "published_same_hash_aliases": aliases.get(item["sha256"], [])}
               for item in plan["inventory"] if not item["selected"]]
    save("COPY_LEDGER.json", {"created_utc": utc(), "copies": copies, "source_execution": "NONE; copied completed evidence only"})
    save("OMISSIONS.json", {"external_root": str(AUDIT), "full_external_manifest_sha256": MANIFEST_SHA,
                            "external_payload_files": 611, "selected_external_payload_files": plan["selected_audit_files"],
                            "omitted_external_files": len(omitted), "omitted_external_bytes": sum(item["bytes"] for item in omitted),
                            "omissions": omitted, "full_bundle_unmodified": True,
                            "rule": "Only the compact selected subset is published. Same-hash aliases do not claim all original paths are present. Full manifest and source/hash index remain available.",
                            "never_published_or_executed_here": ["Original unexecuted Sol source controls", "New target/pytest/PG/native/service run", "Original r1/r2 app-byte or actual-import captures that were never retained"]})
    indexed = []
    for item in plan["representatives"]:
        published = "audit/" + item["external_capture"] if any(x["path"] == item["external_capture"] and x["selected"] for x in plan["inventory"]) else None
        indexed.append({**item, "published_capture": published,
                        "exact_git_reference": item["git_commit"] + ":" + item["git_path"]})
    save("RESPONSE_STATE_INDEX.json", {"scope": "All indexed original raw response/canonical/expected and state-array artifact files from 14 r2 workload records; bounded (1,2) bodies/states and item-heavy (40,20) full states, both roles.",
                                      "manifest_anchor": MANIFEST_SHA, "artifacts": indexed,
                                      "all_other_cases_refer_to": "audit/RETENTION_WORKLOAD_LEDGER.json and audit/SOURCE_HASHES.json plus the complete external bundle/Git references"})
    save("GIT_BINDINGS.json", {"created_utc": utc(), "bindings": bindings,
                              "local_integration_commit": integration, "local_integration_app_blob": "16f33c94da490c77a8ab930b88d8fc0662f3fa4c",
                              "scope": "Immutable pinned Git tree linkage + independently computed blob SHA1/SHA256; not original historical execution attestation or current working-tree inspection"})
    save("PUBLICATION_VALIDATION.json", {"created_utc": utc(), "freeze_first": frozen, "checks": CHECKS,
                                        "failed_checks": [c for c in CHECKS if not c["passed"]],
                                        "all_publication_checks_passed": all(c["passed"] for c in CHECKS),
                                        "historical_failed_checks_not_reclassified": True, "old_published_files_superseded": [],
                                        "target_executions": [], "primary_write_scope": ROOT.relative_to(REPO).as_posix()})
    save("COLLECTION_COMMANDS.json", COMMANDS)
    print(json.dumps({"copied_files": len(copies), "copied_bytes": sum(item["bytes"] for item in copies),
                      "omitted_external_files": len(omitted), "omitted_external_bytes": sum(item["bytes"] for item in omitted),
                      "verified_git_bindings": len(bindings), "publication_checks": len(CHECKS),
                      "current_directory_bytes": sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())}, indent=2))


def seal():
    require("publication collection is a pass", load(ROOT / "PUBLICATION_VALIDATION.json")["all_publication_checks_passed"] is True)
    for item in load(ROOT / "COPY_LEDGER.json")["copies"]:
        path = ROOT / item["published"]
        require(f"final copied bytes {item['published']}", path.stat().st_size == item["bytes"] and filehash(path) == item["sha256"])
    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    stdin = b"".join(p.relative_to(ROOT).as_posix().encode() + b"\0" for p in files)
    attrs = git(["-C", str(ROOT), "check-attr", "-z", "text", "filter", "ident", "working-tree-encoding", "--stdin"], stdin).split(b"\0")[:-1]
    require("all copied bytes protected by nested attributes", len(attrs) == len(files) * 4 * 3 and all(attrs[i] == b"unset" for i in range(2, len(attrs), 3)))
    visible = set((git(["-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "-z", "--", "."]) + git(["-C", str(ROOT), "ls-files", "--cached", "-z", "--", "."])).decode().split("\0")) - {""}
    require("all raw logs and payloads Git-visible", all(p.relative_to(ROOT).as_posix() in visible for p in files))
    for p in [ROOT / "frozen-second/FROZEN.json", ROOT / "frozen-second/NEUTRAL_RETENTION_VERDICT.md", ROOT / "audit/second-key-verified.json", ROOT / "audit/MAPPED_ASSURANCE_REPORT.md"]:
        data = p.read_bytes()
        expected = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        actual = git(["hash-object", "--path=" + p.relative_to(REPO).as_posix(), "--stdin"], data).decode().strip()
        require(f"Git clean bytes preserved {p.relative_to(ROOT)}", actual == expected and re.fullmatch(r"[0-9a-f]{40}", actual) is not None)
    save("SEAL_COMMANDS.json", COMMANDS)
    save("PUBLICATION_RECEIPT.json", {"sealed_utc": utc(), "checks": CHECKS, "all_packaging_checks_passed": all(c["passed"] for c in CHECKS),
                                      "source_safety": "QUALIFIED_NARROW_INTEGRATION_ONLY", "original_source_controls": "UNEXECUTED",
                                      "first_archive_165_pass_1_fail": "PRESERVED", "R2_original_app_import_capture": "NOT_RETAINED",
                                      "R3_reverse_mutant": "NEW_POSTHOC_PREIMAGE_ONLY", "old_files_superseded": [], "target_runs": [],
                                      "checksum_rule": "Root PUBLISHED_SHA256SUMS.txt covers every file recursively except itself; copied audit/SHA256SUMS.txt is the FULL EXTERNAL 611-file index, not this compact subset's ledger."})
    files = sorted(p for p in ROOT.rglob("*") if p.is_file())
    manifest = "".join(f"{filehash(p)}  {p.relative_to(ROOT).as_posix()}\n" for p in files)
    total = sum(p.stat().st_size for p in files) + len(manifest.encode())
    require("whole published packet <=6 MiB including ledger", total <= CAP, bytes=total, cap=CAP)
    write_new(ROOT / "PUBLISHED_SHA256SUMS.txt", manifest)
    print(json.dumps({"payload_files": len(files), "total_files_including_ledger": len(files) + 1,
                      "bytes_including_ledger": total, "manifest_sha256": sha(manifest.encode()),
                      "checks_passed": all(c["passed"] for c in CHECKS), "target_executions": 0}, indent=2))


try:
    if MODE == "plan":
        plan()
    elif MODE == "refine":
        refine()
    elif MODE == "recover-copy":
        recover_interrupted_copy()
    elif MODE == "recover-zero-copies":
        recover_remaining_zero_copies()
    elif MODE == "archive-publication-history":
        archive_publication_history()
    elif MODE == "collect" or MODE.startswith("resume"):
        collect()
    elif MODE == "seal":
        seal()
    else:
        raise SystemExit("Usage: publish_packet.py plan|refine|collect|resumeN|recover-copy|recover-zero-copies|archive-publication-history|seal")
except Exception as error:
    failure = ROOT / f"{MODE}-failure.json"
    if not failure.exists():
        save(failure.name, {"utc": utc(), "error": type(error).__name__, "message": str(error), "checks": CHECKS, "commands": COMMANDS,
                            "status": "FAILURE_RETAINED_NOT_A_PASS"})
    raise
