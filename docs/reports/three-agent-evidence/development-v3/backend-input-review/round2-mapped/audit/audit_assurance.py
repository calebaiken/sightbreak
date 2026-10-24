"""Inspect retained sources/XML/logs and do bounded byte arithmetic, not pytest."""
import ast
from pathlib import Path, PureWindowsPath
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, check, digest, finish, git_bytes, load, save_json, write_new

base = ROOT / "objects/assurance"
entries = {}
for line in (base / "SHA256SUMS.txt").read_text().splitlines():
    expected, path = line.split("  ", 1)
    if path in entries or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError("Unsafe/duplicate manifest entry")
    entries[path] = expected
    file = base / path
    check(f"assurance manifest {path}", file.is_file() and digest(file.read_bytes()) == expected)
actual = {file.relative_to(base).as_posix() for file in base.rglob("*") if file.is_file() and file.name != "SHA256SUMS.txt"}
check("assurance manifest complete payload coverage", actual == set(entries))

shipping = (ROOT / "objects/shipping/backend/app.py").read_bytes()
executed = (ROOT / "objects/r2-executed/backend/app.py").read_bytes()
frozen = (ROOT / "objects/assurance-freeze/backend/app.py").read_bytes()
check("shipping/r2-executed/new-freeze raw app Git bytes identical", shipping == executed == frozen)
for revision in ("8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf", "8dc8e3715dcaeb99fe6e3544243ee591d68c337b", "3e7ce7409322766d07afe504d97f47c5b3614875"):
    _, data = git_bytes(["diff", "--no-ext-diff", "--no-textconv", "--name-only", "4a8e9ea73aa8b286d9f1751b0a6b485479737294", revision,
                         "--", "backend", ":(exclude)backend/tests"])
    check(f"no shipping backend Git changes {revision}", data == b"")

source_files = load((base / "source-files.json").read_bytes())["files"]
for name, evidence_name in [("backend/tests/test_trade_reads.py", "test_trade_reads.py.txt"),
                            ("scripts/benchmark_trade_reads.py", "benchmark_trade_reads.py.txt"),
                            ("scripts/check_trade_read_assurance.py", "check_trade_read_assurance.py.txt")]:
    raw = (base / "frozen-sources" / evidence_name).read_bytes()
    pinned = ROOT / "objects" / ("control-runner" if "check_trade" in name else "assurance-freeze") / name
    check(f"retained frozen source binds pinned executed Git bytes {name}", raw == pinned.read_bytes() and digest(raw) == source_files[name]["sha256"])

test_source = (ROOT / "objects/assurance-freeze/backend/tests/test_trade_reads.py").read_text()
test_ast = ast.parse(test_source)
budget_test = next(node for node in test_ast.body if isinstance(node, ast.FunctionDef) and node.name == "test_trade_read_payload_privacy_and_query_budget")
check("direct bound and old ceiling both present", "parameter_counts.append(len(parameters))" in test_source
      and "assert len(statements) <= budget" in test_source and "assert all(size <= 500 for size in parameter_counts)" in test_source)
old_fixture = ast.parse((ROOT / "objects/shipping/backend/tests/test_trade_reads.py").read_text())
new_fixture = ast.parse(test_source)
for name in ("fixture_id", "seed_workload", "canonical_trades", "database_snapshot"):
    before = next(node for node in old_fixture.body if isinstance(node, ast.FunctionDef) and node.name == name)
    after = next(node for node in new_fixture.body if isinstance(node, ast.FunctionDef) and node.name == name)
    check(f"fixture helper AST unchanged {name}", ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False))

all_cases = []
byte_results = []
for attempt in ("attempt-1", "attempt-2"):
    folder = base / attempt
    mutation = load((folder / "mutation.json").read_bytes())
    mutant = (folder / "batch-5000-app.py.txt").read_bytes()
    check(f"{attempt} retained mutant file exact hash", digest(mutant) == mutation["mutant_app_sha256"])
    text = mutant.decode("utf-8")
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "trades")
    constants = [n for n in ast.walk(node) if isinstance(n, ast.Constant) and n.value == 5000]
    check(f"{attempt} only four 5000 trade constants", len(constants) == 4)
    lines = mutant.splitlines(keepends=True)
    segment = b"".join(lines[node.lineno - 1:node.end_lineno])
    check(f"{attempt} exact reversible four constant byte edits", segment.count(b"5000") == 4)
    restored = b"".join(lines[:node.lineno - 1]) + segment.replace(b"5000", b"500") + b"".join(lines[node.end_lineno:])
    raw_sha_match = digest(restored) == mutation["frozen_app_sha256"]
    normalized_match = restored.replace(b"\r\n", b"\n") == shipping.replace(b"\r\n", b"\n")
    check(f"{attempt} reverse mutant reconstructs recorded original working app SHA", raw_sha_match,
          reconstructed_sha256=digest(restored), recorded_sha256=mutation["frozen_app_sha256"])
    check(f"{attempt} reconstructed app content binds shipping after CRLF-to-LF only", normalized_match)
    # The attempted derivation is retained regardless of success, never silently fixed.
    write_new(ROOT / f"derived/{attempt}-reversed-app.py.txt", restored)
    byte_results.append({"attempt": attempt, "mutant_sha256": digest(mutant), "reverse_sha256": digest(restored),
                         "recorded_frozen_sha256": mutation["frozen_app_sha256"], "reverse_hash_matches": raw_sha_match,
                         "CRLF_to_LF_content_matches_shipping": normalized_match,
                         "reconstructed_CRLF": restored.count(b"\r\n"), "reconstructed_bare_LF": restored.count(b"\n") - restored.count(b"\r\n"),
                         "scope": "NEW posthoc R3 reverse-mutant derivation, not R2 retained app capture and not a rewrite of first-round failed tests"})
    for label in ("candidate", "batch-5000"):
        run = load((folder / label / "run.json").read_bytes())
        xml = ET.fromstring((folder / label / "pytest.xml").read_bytes())
        cases = xml.findall(".//testcase")
        check(f"{attempt}/{label} exactly two retained targeted cases", len(cases) == 2)
        check(f"{attempt}/{label} explicit expected exit", run["exit"] == run["expected_exit"] == (0 if label == "candidate" else 1))
        check(f"{attempt}/{label} unique *_test DB dropped receipt", run["database"].endswith("_test") and run["database_dropped"] is True)
        check(f"{attempt}/{label} testcase source hash bound", run["test_fixture_sha256"] == source_files["backend/tests/test_trade_reads.py"]["sha256"])
        if label == "batch-5000":
            check(f"{attempt}/mutant executed app hash binds retained mutant", run["app_sha256"] == digest(mutant))
        for case in cases:
            props = {prop.attrib["name"]: prop.attrib["value"] for prop in case.findall("./properties/property")}
            counts = ast.literal_eval(props["query_parameter_counts"])
            query_count, budget = int(props["query_count"]), int(props["query_budget"])
            expected_max = 500 if label == "candidate" else 1600 if "[40-20]" in case.attrib["name"] else 502
            failure = case.find("failure")
            check(f"{attempt}/{label}/{case.attrib['name']} old query ceiling still passes", query_count <= budget and query_count == len(counts))
            check(f"{attempt}/{label}/{case.attrib['name']} actual bound counts", max(counts) == expected_max)
            check(f"{attempt}/{label}/{case.attrib['name']} no errors/skips", case.find("error") is None and case.find("skipped") is None)
            check(f"{attempt}/{label}/{case.attrib['name']} expected direct-bound outcome", (failure is None) == (label == "candidate"))
            if failure is not None:
                check(f"{attempt}/{label}/{case.attrib['name']} only direct-bound assertion failed",
                      "assert all(size <= 500" in (failure.text or "") and "test_trade_reads.py:111" in (failure.text or ""))
            all_cases.append({"attempt": attempt, "variant": label, "test": case.attrib["name"],
                              "query_count": query_count, "old_budget": budget, "actual_parameter_counts": counts,
                              "direct_bound_pass": failure is None, "database": run["database"]})

probes = load((base / "attempt-2/fixture-probes.json").read_bytes())
check("completed attempt retains all six import probes", len(probes) == 6)
for probe in probes:
    name, actual = probe["name"], probe["actual"]
    stdout = load((base / "attempt-2" / f"{name}-stdout.json").read_bytes())
    stderr = (base / "attempt-2" / f"{name}-stderr.log").read_text()
    check(f"{name} exact stdout receipt binding", stdout == actual)
    check(f"{name} explicit subprocess exit", probe["exit"] == probe["expected_exit"] == (1 if name == "fixture-mismatch" else 0))
    check(f"{name} driver connect calls zero", actual["database_connect_calls"] == 0)
    check(f"{name} actual module path inside expected source or fallback",
          PureWindowsPath(actual["actual_module_file"]).name == "test_trade_reads.py"
          and str(PureWindowsPath(actual["actual_module_file"])).startswith(str(PureWindowsPath(actual["source_path"])))
          if "baseline-posthoc" not in name else str(PureWindowsPath(actual["actual_module_file"])).startswith(str(PureWindowsPath(actual["fixture_root"]))))
    if name == "fixture-mismatch":
        fixture = (ROOT / "objects/assurance-freeze/backend/tests/test_trade_reads.py").read_bytes()
        check("negative imported fixture materialized byte change binds hash",
              digest(fixture + b'\n# Isolated provenance-negative byte change.\n') == actual["actual_sha256"])
        check("negative fixture hash rejection has explicit stderr", actual["actual_sha256"] != actual["expected_sha256"]
              and actual["mismatch_rejected"] is True and "Imported fixture byte mismatch" in stderr)
    else:
        checked = actual["checked_identity"]
        check(f"{name} actual __file__/resolved path/hash accepted", actual["actual_sha256"] == actual["expected_sha256"] == checked["sha256"]
              and checked["module_file"] == checked["resolved_path"] == actual["actual_module_file"] and actual["mismatch_rejected"] is False)
    if "posthoc" in name:
        check(f"{name} clearly not original capture", probe["kind"] == "posthoc_import_replay_not_original_capture")

first = load((ROOT / "objects/first-round/BINDING_VALIDATION.json").read_bytes())
check("first 165/1 failure history preserved", len(first["checks"]) == 166 and len(first["failed_checks"]) == 1 and first["all_recorded_checks_passed"] is False)
save_json("ASSURANCE_CASES.json", {"cases": all_cases, "byte_derivations": byte_results,
          "historical_fixture_probes_are_posthoc": True, "our_DB_pytest_native_executions": 0})
finish("ASSURANCE_AUDIT.json", {"case_count_including_retained_failed_first_attempt": len(all_cases), "byte_derivations": byte_results,
                               "do_not_double_count_first_attempt": True, "historical_fixture_provenance": "POSTHOC_NOT_ORIGINAL_CAPTURE"})
