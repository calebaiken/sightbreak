"""UNEXECUTED here: pure CPython 3.13 controls, no app/DB/native/network imports.

This checks two assurance gaps, not backend or database performance. Git reads
are pinned. Only tiny temporary fixtures below this external review directory
are created. No repository source, environment, service, or shared data is changed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
from importlib.machinery import PathFinder
import json
from math import ceil
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Controls require CPython 3.13; no alternative interpreter is allowed.")

ROOT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
CANDIDATE = "4a8e9ea73aa8b286d9f1751b0a6b485479737294"


def source(path: str) -> str:
    result = subprocess.run(
        ["git", "--no-pager", "show", f"{CANDIDATE}:{path}"],
        cwd=REPO,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"),
        capture_output=True,
        check=True,
    )
    return result.stdout.decode("utf-8")


tests = ast.parse(source("backend/tests/test_trade_reads.py"))
runtime = ast.parse(source("backend/app.py"))
harness = ast.parse(source("scripts/benchmark_trade_reads.py"))
test_function = next(node for node in tests.body if isinstance(node, ast.FunctionDef)
                     and node.name == "test_trade_read_payload_privacy_and_query_budget")
cases = ast.literal_eval(test_function.decorator_list[0].args[1])
budget_statement = next(node for node in test_function.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == "budget"
                                for target in node.targets))
statement_assertions = [node for node in test_function.body if isinstance(node, ast.Assert)
                        and any(isinstance(part, ast.Name) and part.id == "statements"
                                for part in ast.walk(node.test))]
assert len(statement_assertions) == 2
budget_control = compile(ast.fix_missing_locations(ast.Module(
    body=[copy.deepcopy(budget_statement), *copy.deepcopy(statement_assertions)], type_ignores=[]
)), "<pinned query-budget and SELECT-only predicates>", "exec")

route = next(node for node in runtime.body if isinstance(node, ast.FunctionDef) and node.name == "trades")
batches = [node for node in route.body[0].body if isinstance(node, ast.For)]
assert len(batches) == 2
assert all(isinstance(node.iter, ast.Call) and node.iter.func.id == "range"
           and ast.literal_eval(node.iter.args[-1]) == 500 for node in batches)
batch_slices = [node for batch in batches for node in ast.walk(batch) if isinstance(node, ast.Slice)]
assert len(batch_slices) == 2
assert all(isinstance(node.upper, ast.BinOp) and ast.literal_eval(node.upper.right) == 500
           for node in batch_slices)

rows = []
for count, per_side in cases:
    item_count = count * per_side * 2
    player_count = count + 1 if count else 0
    # Fixture cardinalities are from the pinned seed_workload: unique items and
    # one new partner per trade. Two auth queries and one trade query are fixed.
    bounded_count = 3 + ceil(item_count / 500) + ceil(player_count / 500)
    oversized_count = 3 + ceil(item_count / 5000) + ceil(player_count / 5000)
    local = {"count": count, "per_side": per_side, "ceil": ceil,
             "statements": ["SELECT synthetic_control"] * oversized_count}
    exec(budget_control, local)
    assert bounded_count == local["budget"]
    rows.append({"trades": count, "per_side": per_side, "budget": local["budget"],
                 "5000_id_batch_query_count": oversized_count,
                 "pinned_statement_predicates_accept_oversized_batches": True})

# Check the actual harness source puts source/backend/tests before ROOT's tests,
# while its fixture fingerprint expression still names ROOT's fixture.
path_assignment = next(node for node in ast.walk(harness) if isinstance(node, ast.Assign)
                       and any(isinstance(target, ast.Subscript)
                               and isinstance(target.value, ast.Attribute)
                               and isinstance(target.value.value, ast.Name)
                               and target.value.value.id == "sys" and target.value.attr == "path"
                               for target in node.targets))
assert isinstance(path_assignment.value, ast.List)
assert [ast.unparse(element) for element in path_assignment.value.elts] == [
    "str(source / 'backend')", "str(source / 'backend/tests')", "str(ROOT / 'backend/tests')"
]

with tempfile.TemporaryDirectory(prefix="assurance-fixture-", dir=ROOT) as temporary:
    temporary = Path(temporary)
    source_root = temporary / "source"
    harness_root = temporary / "harness"
    source_tests = source_root / "backend/tests"
    harness_tests = harness_root / "backend/tests"
    source_tests.mkdir(parents=True)
    harness_tests.mkdir(parents=True)
    source_fixture = source_tests / "test_trade_reads.py"
    recorded_fixture = harness_tests / "test_trade_reads.py"
    source_fixture.write_text("MARKER = 'source-side-shadow'\n", encoding="utf-8")
    recorded_fixture.write_text("MARKER = 'reported-fixed-fixture'\n", encoding="utf-8")
    spec = PathFinder.find_spec("test_trade_reads", [str(source_root / "backend"),
                                                   str(source_tests), str(harness_tests)])
    assert spec is not None and Path(spec.origin).resolve() == source_fixture.resolve()
    recorded_sha256 = hashlib.sha256(recorded_fixture.read_bytes()).hexdigest()
    resolved_sha256 = hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()
    assert recorded_sha256 != resolved_sha256
    fixture_control = {
        "fixture_module_executed": False,
        "source_fixture_shadows_recorded_harness_fixture": True,
        "recorded_fixture_sha256": recorded_sha256,
        "resolved_fixture_sha256": resolved_sha256,
    }

print(json.dumps({
    "python": sys.version,
    "scope": "synthetic assurance predicates/module resolution only; NOT PostgreSQL, pytest, or performance",
    "candidate": CANDIDATE,
    "query_budget_controls": rows,
    "fixture_import_control": fixture_control,
}, indent=2))
