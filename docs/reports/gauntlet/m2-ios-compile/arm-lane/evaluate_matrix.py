#!/usr/bin/env python3
"""Replay the exact workflow scalar and compare all unrelated YAML sections.

Requires PyYAML 6 (available in the review environment); no CI step is added.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[5]
WORKFLOW = ".github/workflows/desktop-alpha.yml"


def evaluate(expression, event, lane):
    # Interpret the actual limited GitHub Actions expression, rather than a
    # second independently configured matrix. JSON strings are nonempty/truthy.
    grammar = (r"\$\{\{ fromJSON\(github\.event_name == '([^']+)' && "
               r"inputs\.lane == '([^']+)' && '([^']+)' \|\| '([^']+)'\) \}\}")
    match = re.fullmatch(grammar, expression)
    if not match:
        raise AssertionError("Unexpected matrix expression grammar")
    wanted_event, wanted_lane, selected, default = match.groups()
    return json.loads(selected if event == wanted_event and lane == wanted_lane else default)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    args = parser.parse_args()
    before_text = subprocess.check_output(["git", "show", args.baseline_ref + ":" + WORKFLOW], cwd=ROOT, text=True, timeout=10)
    after_text = (ROOT / WORKFLOW).read_text()
    # BaseLoader avoids YAML 1.1 treating the GitHub key `on` as a boolean.
    before, after = [yaml.load(text, Loader=yaml.BaseLoader) for text in (before_text, after_text)]
    assert after["on"]["workflow_dispatch"]["inputs"]["lane"] == {
        "description": "Native qualification hosts", "type": "choice", "required": "true",
        "default": "all", "options": ["all", "arm-macos-ios"]}
    original = before["jobs"]["native"]["strategy"]["matrix"]["include"]
    arm = [{"os": "macos-15", "target": "macos"}]
    assert original == [{"os": "ubuntu-24.04", "target": "linux"}, {"os": "windows-latest", "target": "windows"},
                        {"os": "macos-15", "target": "macos"}, {"os": "macos-15-intel", "target": "macos"}]
    expression = after["jobs"]["native"]["strategy"]["matrix"]["include"]
    cases = [("default dispatch", "workflow_dispatch", None, original), ("push", "push", None, original),
             ("explicit all", "workflow_dispatch", "all", original),
             ("explicit ARM", "workflow_dispatch", "arm-macos-ios", arm),
             ("push cannot select ARM", "push", "arm-macos-ios", original),
             ("unknown lane", "workflow_dispatch", "unknown", original)]
    results = []
    for name, event, lane, wanted in cases:
        actual = evaluate(expression, event, lane)
        assert actual == wanted, name
        results.append({"case": name, "event": event, "lane": lane, "matrix_include": actual, "pass": True})
    stripped = copy.deepcopy(after)
    stripped["on"]["workflow_dispatch"] = before["on"]["workflow_dispatch"]
    stripped["jobs"]["native"]["strategy"]["matrix"]["include"] = original
    assert stripped == before, "A step, gate, permission, timeout, artifact or unrelated workflow field changed"
    print(json.dumps({"baseline_ref": args.baseline_ref, "pyyaml_version": yaml.__version__,
                      "baseline_workflow_sha256": hashlib.sha256(before_text.encode()).hexdigest(),
                      "candidate_workflow_sha256": hashlib.sha256(after_text.encode()).hexdigest(),
                      "exact_expression": expression, "cases": results,
                      "all_unrelated_yaml_fields_identical": True}, indent=2))


if __name__ == "__main__":
    main()
