"""Bounded documentation publication only. Never imports/runs retained scripts.

Use the approved CPython 3.13 executable with -I. `collect` is create-only and
copies evidence bytes, checks anchors, and binds immutable Git objects. `seal`
checks Git attributes/visibility and writes complete per-directory manifests.
No index, application, test, database, network, or service operation is used.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Publication requires the approved CPython 3.13 interpreter.")

ROUND = Path(__file__).resolve().parent
SOURCE = ROUND.parent / "source-review"
REPO = ROUND.parents[5]
TEMP = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
VERDICT = TEMP / "sol-backend-blind-verdict-20261019T194014Z"
PACKET = TEMP / "blind-trade-read-f12a80a71bbd/packet"
KEY = TEMP / "blind-trade-read-key-4916805315cb/mapping.json"
REVIEW = TEMP / "sol-backend-source-critic-20261019T194154Z"
EVIDENCE_COMMIT = "4a7ba36216bf354d266b508222aea4cfea30bfea"
CANDIDATE = "4a8e9ea73aa8b286d9f1751b0a6b485479737294"
BASELINE = "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd"
PR16 = "d2439acdd5f73df7bae5ada62ee1e3dec2cf30db"
ANCHORS = {
    "verdict": "f76906b5b3ee735d65eedef6bf23998d274a614778fb9e76c196ba39957bfdfa",
    "freeze": "cfeaa74dce6172fb222e6a7cbbefadb7383fd9169332dd51fd94865294908e8a",
    "packet_manifest": "d9a6ea8e0721d573bea5437e84fcc25b899d7b8172f092c4ae7d1415b3c56c36",
    "released_key": "04a96c5d995e755924435b6f48225191f66e6fe0c5832fcc8014db70aecedaf0",
    "source_review": "cf40870f6a894aeddaab51f1fab64a6817e58d2f29385984bed7d45f1dff9899",
    "unexecuted_controls": "cf7fae19e0151694dd76a70e9883e020bab4d0d5f0485852a4161d91f0010d4d",
}
CHECKS = []
COPIES = {"round1": [], "source-review": []}
COMMANDS = []
PHASE = sys.argv[1] if len(sys.argv) == 2 else ""


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def relative(path):
    return path.relative_to(REPO).as_posix()


def write_new(path, data):
    if not (path.is_relative_to(ROUND) or path.is_relative_to(SOURCE)):
        raise ValueError(f"Write outside authorized directories: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data.encode("utf-8") if isinstance(data, str) else data)


def write_json(path, value):
    write_new(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def check(name, condition, **details):
    CHECKS.append({"check": name, "passed": bool(condition), **details})
    return bool(condition)


def strict_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load(data, precise=False):
    return json.loads(data, object_pairs_hook=strict_pairs,
                      parse_float=Decimal if precise else float,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def copy_exact(origin, destination, expected=None):
    if origin.is_symlink():
        raise ValueError(f"Refuse symlink: {origin}")
    data = origin.read_bytes()
    write_new(destination, data)
    group = "round1" if destination.is_relative_to(ROUND) else "source-review"
    root = ROUND if group == "round1" else SOURCE
    actual = sha(data)
    item = {"origin": str(origin), "published": destination.relative_to(root).as_posix(),
            "bytes": len(data), "sha256": actual,
            "exact_byte_copy_verified": destination.read_bytes() == data}
    if expected:
        item["expected_sha256"] = expected
        check(f"pinned hash {group}/{item['published']}", actual == expected,
              expected_sha256=expected, actual_sha256=actual)
    COPIES[group].append(item)
    check(f"exact byte copy {group}/{item['published']}", item["exact_byte_copy_verified"])
    return data


def git(args, stdin=None):
    command = ["git", "--no-pager", *args]
    result = subprocess.run(command, cwd=REPO, input=stdin, capture_output=True,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat"), check=False)
    identifier = f"{PHASE}-{len(COMMANDS) + 1:03d}"
    out = ROUND / f"raw/{identifier}.stdout.bin"
    err = ROUND / f"raw/{identifier}.stderr.log"
    write_new(out, result.stdout)
    write_new(err, result.stderr)
    COMMANDS.append({"utc": now(), "argv": command, "cwd": str(REPO),
                     "returncode": result.returncode,
                     "stdin_sha256": sha(stdin) if stdin is not None else None,
                     "stdin_bytes": len(stdin) if stdin is not None else 0,
                     "stdout_path": out.relative_to(ROUND).as_posix(),
                     "stdout_sha256": sha(result.stdout), "stdout_bytes": len(result.stdout),
                     "stderr_path": err.relative_to(ROUND).as_posix(),
                     "stderr_sha256": sha(result.stderr), "stderr_bytes": len(result.stderr)})
    return result


def oid(spec):
    result = git(["rev-parse", "--verify", spec])
    text = result.stdout.decode("ascii", "replace").strip()
    valid = result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", text) is not None
    check(f"Git object ID {spec}", valid, returncode=result.returncode, stdout=text)
    return text if valid else None


def blob(spec):
    object_id = oid(spec)
    if object_id is None:
        return None, None
    result = git(["cat-file", "blob", object_id])
    valid = result.returncode == 0 and len(result.stdout) > 0
    check(f"nonempty Git blob {spec}", valid, blob=object_id,
          returncode=result.returncode, bytes=len(result.stdout))
    return (object_id, result.stdout) if valid else (object_id, None)


def verify_manifest(root, name="SHA256SUMS.txt"):
    lines = (root / name).read_text(encoding="utf-8-sig").splitlines()
    entries = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        if match is None:
            check(f"manifest syntax {root.name}/{name}", False, line=line)
            continue
        digest, path = match.groups()
        safe = not Path(path).is_absolute() and ".." not in Path(path).parts
        check(f"manifest unique safe path {root.name}/{path}", safe and path not in entries)
        if safe:
            entries[path] = digest.lower()
            file = root / path
            actual = sha(file.read_bytes()) if file.is_file() else None
            check(f"manifest hash {root.name}/{path}", actual == digest.lower(),
                  expected_sha256=digest.lower(), actual_sha256=actual)
    return entries


def rows_tokens(data):
    text = data.decode("utf-8-sig")
    decoder = json.JSONDecoder()
    index = text.index("{") + 1
    raw = None
    while True:
        while text[index].isspace() or text[index] == ",":
            index += 1
        if text[index] == "}":
            break
        key, index = decoder.raw_decode(text, index)
        while text[index].isspace() or text[index] == ":":
            index += 1
        start = index
        _, index = decoder.raw_decode(text, index)
        if key == "rows":
            raw = text[start:index]
    if raw is None:
        raise ValueError("No top-level rows array")
    tokens, quoted, escaped = [], False, False
    for char in raw:
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
    return "".join(tokens).encode("utf-8")


def collect():
    verdict_files = ["audit_packet.ps1", "freeze_artifacts.ps1", "FROZEN.json", "NEUTRAL_VERDICT.md",
                     "per_workload_assessment.json", "SHA256SUMS.txt", "source_hashes.json"]
    packet_files = ["equivalence.json", "METHOD.md", "README.md", "REVIEW_QUESTIONS.md", "SHA256SUMS.txt",
                    "verify_packet.py", "K/measurement.json", "R/measurement.json"]
    review_files = ["ARTIFACT_SHA256.txt", "candidate-app-contract-context.txt", "candidate-app-trade-slice.txt",
                    "candidate-benchmark_trade_reads.py.txt", "candidate-model-contract-context.txt",
                    "candidate-test_trade_reads.py.txt", "collect_review_sources.ps1", "collect_review_sources.py",
                    "COMMANDS.md", "git-commands.json", "isolated_assurance_controls.py", "manifest.json",
                    "pr16-app-trade-slice.txt", "pr16-to-candidate-app.diff", "pr16-to-candidate-authorized.diff",
                    "SOURCE_REVIEW.md", "v2-app-trade-slice.txt"]
    for name in verdict_files:
        expected = ANCHORS["verdict"] if name == "NEUTRAL_VERDICT.md" else ANCHORS["freeze"] if name == "FROZEN.json" else None
        copy_exact(VERDICT / name, ROUND / "verdict" / name, expected)
    for name in packet_files:
        copy_exact(PACKET / name, ROUND / "packet" / name,
                   ANCHORS["packet_manifest"] if name == "SHA256SUMS.txt" else None)
    for name in review_files:
        expected = ANCHORS["source_review"] if name == "SOURCE_REVIEW.md" else ANCHORS["unexecuted_controls"] if name == "isolated_assurance_controls.py" else None
        copy_exact(REVIEW / name, SOURCE / "original" / name, expected)
    key_raw = copy_exact(KEY, ROUND / "released-key/mapping.json", ANCHORS["released_key"])
    key = load(key_raw)
    frozen = load((ROUND / "verdict/FROZEN.json").read_bytes())
    check("original freeze timestamp", frozen["frozen_utc"] == "2026-10-19T19:46:36.4321805Z")
    check("publication is after original freeze", datetime.now(timezone.utc) > datetime.fromisoformat(frozen["frozen_utc"].replace("Z", "+00:00")))
    check("freeze binds packet manifest", frozen["input_packet_manifest_sha256"] == ANCHORS["packet_manifest"])
    check("freeze remains blind and limited", frozen["preferred_label"] == "K"
          and frozen["full_semantic_and_authoritative_safety_bar_independently_established"] is False)
    verify_manifest(ROUND / "verdict")
    verify_manifest(ROUND / "packet")
    verify_manifest(SOURCE / "original", "ARTIFACT_SHA256.txt")
    for artifact in frozen["artifacts"]:
        data = (ROUND / "verdict" / artifact["path"]).read_bytes()
        check(f"FROZEN artifact {artifact['path']}", len(data) == artifact["bytes"] and sha(data) == artifact["sha256"])
    for path, digest in key["packet_files"].items():
        check(f"released-key packet hash {path}", sha((ROUND / "packet" / path).read_bytes()) == digest)
    for item in load((ROUND / "verdict/source_hashes.json").read_bytes())["packet_source_files"]:
        data = (ROUND / "packet" / item["path"]).read_bytes()
        check(f"blind audit input binding {item['path']}", sha(data) == item["sha256"] and len(data) == item["bytes"])
    check("key packet anchor", key["packet_manifest_sha256"] == ANCHORS["packet_manifest"])
    check("key evidence commit", key["source_evidence_commit"] == EVIDENCE_COMMIT)
    kind = git(["cat-file", "-t", EVIDENCE_COMMIT])
    available = kind.returncode == 0 and kind.stdout.strip() == b"commit"
    check("original evidence Git commit available", available, returncode=kind.returncode,
          stdout=kind.stdout.decode("utf-8", "replace"))
    if available:
        manifest_blob, manifest_raw = blob(f"{EVIDENCE_COMMIT}:docs/reports/backend-trade-read-v3/SHA256SUMS.txt")
        if manifest_raw is not None:
            write_new(ROUND / "original-measurements/source-SHA256SUMS.txt", manifest_raw)
            check("original evidence manifest hash", sha(manifest_raw) == key["source_manifest_sha256"],
                  blob=manifest_blob, actual_sha256=sha(manifest_raw), expected_sha256=key["source_manifest_sha256"])
    bindings = []
    review_manifest = load((SOURCE / "original/manifest.json").read_bytes())
    for label, expected_commit, review_label in [("K", CANDIDATE, "candidate"), ("R", BASELINE, "v2")]:
        mapping = key["variants"][label]
        neutral_raw = (ROUND / "packet" / mapping["neutral_file"]).read_bytes()
        neutral = load(neutral_raw)
        check(f"{label} neutral key hash", sha(neutral_raw) == mapping["neutral_sha256"])
        check(f"{label} key identity", mapping["withheld_original_header"]["source"]["commit"] == expected_commit)
        original_blob, original_raw = blob(f"{EVIDENCE_COMMIT}:{mapping['original_git_path']}") if available else (None, None)
        binding = {"label": label, "role": mapping["original_role"], "commit": expected_commit,
                   "original_measurement_blob": original_blob, "original_measurement_available": original_raw is not None,
                   "source_safety": "INSPECTION_ONLY; no current runtime/test or production acceptance"}
        if original_raw is not None:
            write_new(ROUND / "original-measurements" / f"{label}-measurement.json", original_raw)
            check(f"{label} original measurement hash", sha(original_raw) == mapping["original_sha256"],
                  expected_sha256=mapping["original_sha256"], actual_sha256=sha(original_raw))
            original = load(original_raw)
            original_precise, neutral_precise = load(original_raw, True), load(neutral_raw, True)
            row_checks = [left == right for left, right in zip(original_precise["rows"], neutral_precise["rows"])]
            row_equal = len(original_precise["rows"]) == len(neutral_precise["rows"]) == 7 and all(row_checks)
            lexical_equal = rows_tokens(original_raw) == rows_tokens(neutral_raw)
            check(f"{label} exact numeric/string workload row preservation", row_equal, per_row=row_checks)
            check(f"{label} workload JSON tokens preserved except whitespace", lexical_equal)
            header_equal = {name: value for name, value in original.items() if name != "rows"} == mapping["withheld_original_header"]
            check(f"{label} full original header binds released key", header_equal)
            check(f"{label} original source initial/final equal", original["source"] == original["final_source"])
            check(f"{label} original commit binding", original["source"]["commit"] == expected_commit)
            check(f"{label} original source clean flag", original["source"]["backend_dirty"] == "")
            check(f"{label} preserved environment", neutral["environment"] == {name: original[name] for name in ("platform", "python", "packages", "postgresql")})
            check(f"{label} preserved completion flags", all(neutral[name] == original[name] is True for name in ("completed", "database_dropped")))
            binding.update({"original_measurement_sha256": sha(original_raw), "neutral_sha256": sha(neutral_raw),
                            "row_count": len(original["rows"]), "all_rows_preserved_precise_numbers_and_strings": row_equal,
                            "row_json_tokens_sha256": sha(rows_tokens(original_raw)),
                            "row_tokens_preserved_ignoring_only_insignificant_whitespace": lexical_equal,
                            "full_header_key_binding": header_equal})
        reported = mapping["withheld_original_header"]
        backend_tree = oid(f"{expected_commit}:backend")
        check(f"{label} source backend tree", backend_tree == reported["source"]["backend_tree"])
        app_blob, app_raw = blob(f"{expected_commit}:backend/app.py")
        if app_raw is not None:
            recorded_hash = reported["source"]["backend_files"]["backend/app.py"]
            raw_match = sha(app_raw) == recorded_hash
            crlf_match = b"\r" not in app_raw and sha(app_raw.replace(b"\n", b"\r\n")) == recorded_hash
            check(f"{label} app binds exact source review object", app_blob == review_manifest["revisions"][review_label]["app_blob"]
                  and sha(app_raw) == review_manifest["revisions"][review_label]["app_sha256"])
            check(f"{label} recorded app fingerprint binds Git bytes or explicit LF-to-CRLF expansion", raw_match or crlf_match,
                  raw_exact_match=raw_match, explicit_lf_to_crlf_match=crlf_match,
                  git_raw_sha256=sha(app_raw), recorded_file_sha256=recorded_hash)
            binding["app_binding"] = {"blob": app_blob, "git_raw_sha256": sha(app_raw),
                                      "recorded_file_sha256": recorded_hash, "raw_exact_match": raw_match,
                                      "explicit_lf_to_crlf_match": crlf_match,
                                      "qualification": "CRLF match is an explicit byte transformation, not raw Git-byte equality or execution authentication."}
        check(f"{label} actual response/state not retained", neutral["authoritative_state_hashes"] == {"before": None, "after": None, "status": "not_retained"})
        bindings.append(binding)
    for path, hash_name in [("scripts/benchmark_trade_reads.py", "harness_sha256"), ("backend/tests/test_trade_reads.py", "fixture_sha256")]:
        object_id, data = blob(f"{CANDIDATE}:{path}")
        if data is not None:
            matches = all(sha(data) == key["variants"][label]["withheld_original_header"][hash_name] for label in ("K", "R"))
            check(f"common {hash_name} bound to candidate Git blob", matches,
                  blob=object_id, git_raw_sha256=sha(data), path=path)
    check("PR16 and V2 app blobs identical", oid(f"{PR16}:backend/app.py") == review_manifest["revisions"]["v2"]["app_blob"])
    pairs = []
    left = load((ROUND / "packet/K/measurement.json").read_bytes())["rows"]
    right = load((ROUND / "packet/R/measurement.json").read_bytes())["rows"]
    eq_rows = load((ROUND / "packet/equivalence.json").read_bytes())["rows"]
    frozen_pairs = load((ROUND / "verdict/per_workload_assessment.json").read_bytes())["pairs"]
    for index, (a, b, eq, frozen_pair) in enumerate(zip(left, right, eq_rows, frozen_pairs)):
        ka = sorted({sample["statements"] for sample in a["samples"]})
        rb = sorted({sample["statements"] for sample in b["samples"]})
        preserved = len(a["samples"]) == len(b["samples"]) == 10 and len(ka) == len(rb) == 1
        check(f"count observations bind frozen assessment row {index}", preserved
              and ka[0] == frozen_pair["K_statements_every_timed_request"]
              and rb[0] == frozen_pair["R_statements_every_timed_request"])
        check(f"equivalence expected-hash references row {index}", a["response_sha256"] == eq["expected_response_sha256"]["K"]
              and b["response_sha256"] == eq["expected_response_sha256"]["R"])
        pairs.append({"row": index, "trades": a["trades"], "items_per_side": a["items_per_side"],
                      "K_statements_every_retained_sample": ka, "R_statements_every_retained_sample": rb,
                      "samples_per_variant": len(a["samples"]), "count_preference": "K" if ka[0] < rb[0] else "TIE" if ka == rb else "R"})
    write_json(SOURCE / "COPY_LEDGER.json", {"utc": now(), "controls": "UNEXECUTED; copied only", "files": COPIES["source-review"]})
    write_json(ROUND / "COPY_LEDGER.json", {"utc": now(), "frozen_originals_modified": False, "files": COPIES["round1"]})
    write_json(ROUND / "binding/BINDING_VALIDATION.json", {
        "schema": "post-freeze-first-round-source-binding-v1", "created_utc": now(),
        "original_freeze_utc": frozen["frozen_utc"], "original_anchors": ANCHORS,
        "publication_interpreter": {"version": sys.version, "executable": sys.executable},
        "measurement_interpreter_is_not_publication_interpreter": True,
        "evidence_commit": EVIDENCE_COMMIT, "bindings": bindings, "statement_count_pairs": pairs,
        "checks": CHECKS, "failed_checks": [item for item in CHECKS if not item["passed"]],
        "all_recorded_checks_passed": all(item["passed"] for item in CHECKS),
        "limits": ["No actual response bodies/digests or authoritative before/after snapshots were retained in round 1.",
                   "Source review is inspection-only; synthetic controls remain UNEXECUTED.",
                   "No current working-tree runtime/test source or second-round material was inspected.",
                   "Whole reported backend working-tree file inventory is retained, not individually revalidated; Git tree identity and app/harness/fixture binding are checked.",
                   "No trusted timestamp, measurement execution authentication, latency generalization, state/response/production acceptance is supplied."]})
    write_json(ROUND / "raw/collect-commands.json", COMMANDS)
    print(json.dumps({"phase": "collect", "checks": len(CHECKS), "failed_checks": [c for c in CHECKS if not c["passed"]],
                      "exact_copies": {key: len(value) for key, value in COPIES.items()}, "controls": "UNEXECUTED"}, indent=2))


def seal():
    roots = [SOURCE, ROUND]
    files = sorted([file for root in roots for file in root.rglob("*") if file.is_file()])
    if any((root / "PUBLISHED_SHA256SUMS.txt").exists() for root in roots):
        raise RuntimeError("Publication already sealed; do not overwrite old receipts/manifests.")
    attributes = ["text", "filter", "ident", "working-tree-encoding"]
    file_input = b"".join(relative(file).encode() + b"\0" for file in files)
    result = git(["check-attr", "-z", *attributes, "--stdin"], file_input)
    parts = result.stdout.split(b"\0")[:-1]
    attr_rows = [tuple(part.decode() for part in parts[i:i+3]) for i in range(0, len(parts), 3)]
    check("nested exact-byte attributes cover every current payload", result.returncode == 0
          and len(attr_rows) == len(files) * len(attributes)
          and all(row[2] == "unset" for row in attr_rows), returncode=result.returncode,
          attribute_records=len(attr_rows), expected_records=len(files) * len(attributes))
    visible = git(["ls-files", "--others", "--exclude-standard", "-z", "--", relative(ROUND), relative(SOURCE)])
    tracked = git(["ls-files", "--cached", "-z", "--", relative(ROUND), relative(SOURCE)])
    visible_paths = (set(visible.stdout.decode().split("\0")) | set(tracked.stdout.decode().split("\0"))) - {""}
    expected_paths = {relative(file) for file in files}
    check("all publication payloads including raw logs are unignored", visible.returncode == 0
          and tracked.returncode == 0 and expected_paths.issubset(visible_paths),
          missing=sorted(expected_paths - visible_paths),
          untracked_returncode=visible.returncode, tracked_returncode=tracked.returncode)
    if CHECKS[0]["passed"]:
        for file in [ROUND / "verdict/NEUTRAL_VERDICT.md", ROUND / "verdict/FROZEN.json",
                     ROUND / "released-key/mapping.json", SOURCE / "original/SOURCE_REVIEW.md"]:
            data = file.read_bytes()
            expected = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            result = git(["hash-object", f"--path={relative(file)}", "--stdin"], data)
            check(f"Git clean bytes preserved {relative(file)}", result.returncode == 0
                  and result.stdout.decode().strip() == expected, expected_blob=expected,
                  actual_stdout=result.stdout.decode("utf-8", "replace"), returncode=result.returncode)
    write_json(ROUND / "raw/seal-commands.json", COMMANDS)
    collection = load((ROUND / "binding/BINDING_VALIDATION.json").read_bytes())
    receipt = {"schema": "bounded-backend-evidence-publication-receipt-v1", "created_utc": now(),
               "all_collected_binding_checks_passed": collection["all_recorded_checks_passed"],
               "packaging_checks": CHECKS, "packaging_checks_passed": all(item["passed"] for item in CHECKS),
               "controls": "UNEXECUTED; no retained scripts rerun", "source_safety": "INSPECTION_ONLY",
               "freeze_preserved": ANCHORS["freeze"], "neutral_verdict_preserved": ANCHORS["verdict"],
               "checksum_rule": "Each PUBLISHED_SHA256SUMS.txt covers every file in its directory recursively except itself. Manifest anchors are returned outside their own payload.",
               "supersession": "Append-only qualification; no old verdict/evidence file is superseded or rewritten."}
    write_json(ROUND / "PUBLICATION_RECEIPT.json", receipt)
    summaries = []
    for root in roots:
        files = sorted(file for file in root.rglob("*") if file.is_file())
        inventory = [{"path": file.relative_to(root).as_posix(), "bytes": file.stat().st_size,
                      "sha256": sha(file.read_bytes())} for file in files]
        manifest = "".join(f"{item['sha256']}  {item['path']}\n" for item in inventory)
        write_new(root / "PUBLISHED_SHA256SUMS.txt", manifest)
        summaries.append({"directory": relative(root), "manifest_sha256": sha(manifest.encode()),
                          "payload_files": len(files), "payload_bytes": sum(item["bytes"] for item in inventory),
                          "manifest_bytes": len(manifest.encode())})
    print(json.dumps({"phase": "seal", "directories": summaries, "packaging_checks_passed": receipt["packaging_checks_passed"],
                      "binding_checks_passed": receipt["all_collected_binding_checks_passed"]}, indent=2))


try:
    if PHASE == "collect":
        collect()
    elif PHASE == "seal":
        seal()
    else:
        raise SystemExit("Usage: publish_evidence.py collect|seal")
except Exception as error:
    failure = {"utc": now(), "phase": PHASE, "exception": type(error).__name__, "message": str(error),
               "commands": COMMANDS, "checks_so_far": CHECKS, "status": "FAILURE_RETAINED_NOT_A_PASS"}
    target = ROUND / f"raw/{PHASE}-failure.json"
    if not target.exists():
        write_json(target, failure)
    raise
