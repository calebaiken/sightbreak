#!/usr/bin/env python3
"""Adjudicate the original no-op control without changing its code or outputs."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[5]
report = Path(__file__).resolve().parent
script = report / "independent_controls.py"
fixture = Path("/workspace/reviews/m5-objective-observability-shallow-source")
original_commit = "705de40383b1789d1a3eae42ab17ac3e7f9ef5ef"
relative_script = str(script.relative_to(root))
original_bytes = subprocess.check_output(["git", "show", original_commit + ":" + relative_script], cwd=root)
assert original_bytes == script.read_bytes(), "original rig was changed"
before = hashlib.sha256(script.read_bytes()).hexdigest()
completed = subprocess.run([sys.executable, str(script), str(fixture)], cwd=root,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
(report / "rig-original-rerun.stdout").write_bytes(completed.stdout)
(report / "rig-original-rerun.stderr").write_bytes(completed.stderr)
(report / "rig-original-rerun.exit").write_text(str(completed.returncode) + "\n")
assert before == hashlib.sha256(script.read_bytes()).hexdigest()
sys.path.insert(0, str(fixture / "scripts"))
import test_bot_objective_observation as maintained
import verify_bot_objective_observation as oracle
calls = [node.value for node in ast.parse(script.read_text()).body
         if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
         and isinstance(node.value.func, ast.Name) and node.value.func.id == "run"]
first, second = calls[:2]
rows_by_name = {}
entries = []
for call in [first, second]:
    name = ast.literal_eval(call.args[0])
    mutation = eval(compile(ast.Expression(call.args[1]), str(script), "eval"))
    rows = copy.deepcopy(maintained.synthetic_records())
    before_rows = copy.deepcopy(rows)
    mutation(rows)
    terminal = rows[-1][1]
    terminal["decisions"] = sum(tag == "DECISION" for tag, _ in rows)
    terminal["interactions"] = sum(tag == "INTERACTION" for tag, _ in rows)
    expected_rejection = ast.literal_eval(call.args[2]) if len(call.args) > 2 else True
    result = oracle.verify(maintained.log(rows))
    rows_by_name[name] = rows
    entries.append({"name": name, "mutation_changes_input": rows != before_rows,
                    "mutation_ast": ast.dump(call.args[1], include_attributes=False),
                    "expected_rejection": expected_rejection,
                    "accepted": result["observable_contract_passed"],
                    "serialized_input_sha256": hashlib.sha256(maintained.log(rows).encode()).hexdigest()})
rerun = json.loads(completed.stdout)
original = json.loads((report / "independent-controls.json").read_text())
assert rerun == original, "unchanged original replay differs"
excluded = "forward_rows_have_no_dt_pose_command_objective_or_progress"
mutations = [r for r in original["results"]
             if r["name"] not in {excluded, "valid_maintained_synthetic_receipt"}]
forward = [row for tag,row in rows_by_name[entries[0]["name"]]
           if tag == "INTERACTION" and row["label"] == "forward_live_122"]
result = {"source_commit": original_commit, "script_sha256_before_and_after": before,
          "original_script_unchanged": True, "original_rerun_exit": completed.returncode,
          "original_rerun_equal_to_preserved_result": rerun == original,
          "assertion_is_valid": True, "identical_inputs": list(rows_by_name.values())[0] == list(rows_by_name.values())[1],
          "controls": entries, "defective_negative_control": excluded,
          "raw_original_cases": original["total"], "raw_original_unexpected_acceptances": original["unexpected_acceptances"],
          "corrected_distinct_cases": len(mutations) + 1,
          "actual_mutation_controls": len(mutations),
          "accepted_mutated_receipts": sum(not r["rejected"] for r in mutations),
          "rejected_mutated_receipts": sum(r["rejected"] for r in mutations),
          "baseline_acceptance_smoke_cases": 1,
          "baseline_forward_rows": len(forward), "baseline_forward_row_keys": sorted(forward[0]),
          "interpretation": "The original negative is a no-op with the opposite expectation to the identical baseline smoke case. Exclude it from independent mutation counts. The baseline is not proven complete/valid; its missing forward fields are a direct schema observation, not an independent deletion falsifier. Other actual mutation acceptances and the original source rejection remain.",
          "native_executed": False, "new_candidate_reviewed": False}
(report / "rig-adjudication.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
