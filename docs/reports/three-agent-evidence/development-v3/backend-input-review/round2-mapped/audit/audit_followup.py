"""Append qualifications without erasing any failed check or original verdict."""
import ast
import difflib
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, check, digest, finish, git_bytes, load, save_json

assurance = ROOT / "objects/assurance"
cases = load((ROOT / "ASSURANCE_CASES.json").read_bytes())
prekey = load((ROOT / "PRE_KEY_FREEZE_VERIFIED.json").read_bytes())
retention = load((ROOT / "RETENTION_BINDING_AUDIT.json").read_bytes())
key = load((ROOT / "second-key-verified.json").read_bytes())

for commit, expected in [("8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf", "4ef756639c2e90037bce79a30e2867aebcc798a7"),
                         ("4a8e9ea73aa8b286d9f1751b0a6b485479737294", "4ef756639c2e90037bce79a30e2867aebcc798a7"),
                         ("701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd", "67027b4fa17674ef067c84401af76eb1524419ac"),
                         ("8dc8e3715dcaeb99fe6e3544243ee591d68c337b", "1dfac444b684ca1a791540e5831fc7d88538abed"),
                         ("3e7ce7409322766d07afe504d97f47c5b3614875", "1dfac444b684ca1a791540e5831fc7d88538abed")]:
    result, raw = git_bytes(["rev-parse", "--verify", commit + ":backend"])
    check(f"backend tree independently binds reported identity {commit}", result["exit"] == 0 and raw.decode().strip() == expected)

attempt1_run = load((assurance / "attempt-1/batch-5000/run.json").read_bytes())
fixture = (ROOT / "objects/assurance-freeze/backend/tests/test_trade_reads.py").read_bytes()
check("first attempt mutant fixture mismatch explained by explicit LF-to-CRLF bytes",
      b"\r" not in fixture and digest(fixture.replace(b"\n", b"\r\n")) == attempt1_run["test_fixture_sha256"],
      recorded_sha256=attempt1_run["test_fixture_sha256"], raw_fixture_sha256=digest(fixture),
      expanded_sha256=digest(fixture.replace(b"\n", b"\r\n")))
old_fixture = (ROOT / "objects/shipping/backend/tests/test_trade_reads.py").read_bytes()
failed_probe = load((assurance / "attempt-1/round1-baseline-posthoc-stdout.json").read_bytes())
check("first attempt historical fixture CRLF mismatch reproduced without running it",
      digest(old_fixture.replace(b"\n", b"\r\n")) == failed_probe["checked_identity"]["sha256"] if "checked_identity" in failed_probe
      else digest(old_fixture.replace(b"\n", b"\r\n")) == failed_probe["actual_sha256"])
status = load((assurance / "attempt-status.json").read_bytes())
check("failed attempt explicitly retained and not merged into completed coverage", status["attempt-1"]["overall_exit"] == 1
      and status["attempt-1"]["later_historical_probes_executed"] is False and status["attempt-2"]["overall_exit"] == 0)

for attempt in ("attempt-1", "attempt-2"):
    restored = (ROOT / f"derived/{attempt}-reversed-app.py.txt").read_bytes()
    mutant = (assurance / attempt / "batch-5000-app.py.txt").read_bytes()
    expected_patch = "".join(difflib.unified_diff(restored.decode().splitlines(True), mutant.decode().splitlines(True),
                                                fromfile="frozen/backend/app.py", tofile="isolated-control/backend/app.py")).encode()
    check(f"{attempt} retained unified patch binds reversible full mutant bytes", expected_patch == (assurance / attempt / "batch-5000.patch").read_bytes())

final = [row for row in cases["cases"] if row["attempt"] == "attempt-2"]
check("completed coverage is exactly two positive and two negative cases", len(final) == 4
      and sum(row["direct_bound_pass"] for row in final) == 2)
for variant in ("candidate", "batch-5000"):
    xml = ET.fromstring((assurance / "attempt-2" / variant / "pytest.xml").read_bytes())
    suites = xml.findall(".//testsuite")
    check(f"{variant} JUnit suite totals match cases", len(suites) == 1
          and suites[0].attrib["tests"] == "2" and suites[0].attrib["errors"] == suites[0].attrib["skipped"] == "0"
          and suites[0].attrib["failures"] == ("0" if variant == "candidate" else "2"))
    log = (assurance / "attempt-2" / variant / "pytest.log").read_text()
    check(f"{variant} retained text log agrees with JUnit", ("2 passed" in log if variant == "candidate" else "2 failed" in log))

db_names = [load((assurance / attempt / variant / "run.json").read_bytes())["database"]
            for attempt in ("attempt-1", "attempt-2") for variant in ("candidate", "batch-5000")]
check("all four run receipts identify distinct private test DBs", len(set(db_names)) == 4
      and set(db_names) == set(status["four_unique_test_databases_dropped"]))
runner = (ROOT / "objects/control-runner/scripts/check_trade_read_assurance.py").read_text()
benchmark = (ROOT / "objects/assurance-freeze/scripts/benchmark_trade_reads.py").read_text()
check("driver finally records cleanup only after DROP execution",
      "db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)')" in runner
      and runner.index("db.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)')") < runner.index("receipt['database_dropped'] = True"))
check("probe blocks psycopg.connect before import", runner.index("psycopg.connect = deny_connect") < runner.index("import test_trade_reads as fixture"))
check("fixture identity guard is in the actual benchmark measurement path", "report['imported_fixture'] = fixture_identity(fixture, report['fixture_sha256'])" in benchmark
      and "report['final_imported_fixture'] = fixture_identity(fixture, report['fixture_sha256'])" in benchmark)
check("zero-connect probe not mistaken for zero-connect full benchmark", benchmark.index("connection.execute(sql.SQL('CREATE DATABASE {}')") < benchmark.index("report['imported_fixture'] = fixture_identity"))

runs = load((ROOT / "objects/r2/runs.json").read_bytes())
check("matched r2 command receipts explicit exits and sources", len(runs) == 2
      and all(row["exit"] == 0 and "--runtime-reference" in row["command"] for row in runs)
      and {row["label"] for row in runs} == {"baseline", "candidate"})
for label, role in [("M", "baseline"), ("V", "candidate")]:
    measurement = load((ROOT / "objects/r2" / role / "measurement.json").read_bytes())
    console = (ROOT / "objects/r2" / f"{role}-console.log").read_text()
    row_lines = [load(line) for line in console.splitlines() if line.lstrip().startswith('{"trades"')]
    check(f"{label} retained console grid/counts matches original measurement", len(row_lines) == 7
          and all((left["trades"], left["items_per_side"], left["query_counts"]) == (right["trades"], right["items_per_side"], right["query_counts"])
                  for left, right in zip(row_lines, measurement["rows"])))

derivation = cases["byte_derivations"][1]
check("new R3 attempt-2 posthoc fingerprint preimage binds 9f94 without editing first receipts",
      derivation["reverse_hash_matches"] is True and derivation["CRLF_to_LF_content_matches_shipping"] is True
      and derivation["reconstructed_CRLF"] == 510 and derivation["reconstructed_bare_LF"] == 21)
summary = {"decision": "ACCEPT_WITH_QUALIFICATIONS_FOR_UNCHANGED_TRADE_READ_RUNTIME_INTEGRATION_ONLY",
           "runtime": "4a8e9ea73aa8b286d9f1751b0a6b485479737294",
           "new_test_and_harness_freeze": "8dc8e3715dcaeb99fe6e3544243ee591d68c337b",
           "completed_control_runner": "3e7ce7409322766d07afe504d97f47c5b3614875",
           "retained_evidence_publication": "172c900795c04f9b8706c4e80d72f55927f40da1",
           "first_app_binding_failure": "PRESERVED_165_PASS_1_FAIL; original attempts still failed; cause not inferred from new named newline transform",
           "r2_exact_app_capture": "NOT_RETAINED_OR_INDEPENDENTLY_AUTHENTICATED",
           "r3_app_byte_preimage": "NEW_POSTHOC_REVERSE_MUTANT_MATCH_9f94_NORMALIZES_TO_703c; not original r2 capture",
           "historical_fixture_import": "POSTHOC_ONLY_NOT_ORIGINAL_CAPTURE",
           "completed_targeted_cases": final,
           "bounded_r2_retention": retention["totals"], "freeze_anchors": {key: prekey[key] for key in ("freeze_sha256", "report_sha256", "ledger_sha256")},
           "blockers_to_broader_acceptance": ["No original app byte snapshot or original fixture __file__ capture for r1/r2; new preimage/import evidence is posthoc.",
                                              "Zero-credit fixtures leave eight monetary/history tables empty; no monetary/write/receipt/race proof.",
                                              "Only two new positive and two negative bound cases plus import probes; no new full backend suite or seven-workload run.",
                                              "No memory/unbounded-history/concurrency/production or general-latency acceptance."],
           "our_execution": "Serial approved CPython3.13 stdlib file/hash/JSON/XML/AST arithmetic and read-only Git only; no target imports, pytest, DB/native/services/network/source/index changes."}
save_json("QUALIFIED_DECISION_LEDGER.json", summary)
finish("FOLLOWUP_AUDIT.json", {"qualified_decision": summary["decision"], "prior_negative_checks_preserved": True})
