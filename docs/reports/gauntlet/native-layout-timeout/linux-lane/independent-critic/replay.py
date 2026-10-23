#!/usr/bin/env python3
"""Independent parsed-YAML and precedence-aware Actions selector review."""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess

import yaml


ROOT = Path(__file__).resolve().parents[6]
WORKFLOW = ".github/workflows/desktop-alpha.yml"
BASE = "67a5f54"
CANDIDATE = "807b56b"
CURRENT = "738a381"


def source(ref):
    return subprocess.check_output(["git", "show", f"{ref}:{WORKFLOW}"], cwd=ROOT, text=True)


def evaluate(scalar, event, lane):
    """Tokenize and parse the actual scalar; == binds before && before ||."""
    if isinstance(scalar, list):
        return scalar
    assert scalar.startswith("${{ ") and scalar.endswith(" }}")
    expression = scalar[4:-3]
    pattern = re.compile(r"\s*(?:(fromJSON|github\.event_name|inputs\.lane)|('(?:[^']|'')*')|(==|&&|\|\||\(|\)))")
    tokens = []
    cursor = 0
    while cursor < len(expression):
        match = pattern.match(expression, cursor)
        assert match, expression[cursor:]
        tokens.append(next(group for group in match.groups() if group is not None))
        cursor = match.end()
    cursor = 0

    def atom():
        nonlocal cursor
        token = tokens[cursor]
        cursor += 1
        if token == "fromJSON":
            assert tokens[cursor] == "("
            cursor += 1
            value = disjunction()
            assert tokens[cursor] == ")"
            cursor += 1
            return json.loads(value)
        if token.startswith("'"):
            return token[1:-1].replace("''", "'")
        return {"github.event_name": event, "inputs.lane": lane or ""}[token]

    def equality():
        nonlocal cursor
        value = atom()
        while cursor < len(tokens) and tokens[cursor] == "==":
            cursor += 1
            other = atom()
            # GitHub Actions string comparisons ignore case.
            value = str(value).casefold() == str(other).casefold()
        return value

    def conjunction():
        nonlocal cursor
        value = equality()
        while cursor < len(tokens) and tokens[cursor] == "&&":
            cursor += 1
            other = equality()
            value = other if value else value
        return value

    def disjunction():
        nonlocal cursor
        value = conjunction()
        while cursor < len(tokens) and tokens[cursor] == "||":
            cursor += 1
            other = conjunction()
            value = value if value else other
        return value

    value = disjunction()
    assert cursor == len(tokens)
    return value


def differences(left, right, path=()):
    if type(left) is not type(right):
        return [list(path)]
    if isinstance(left, dict):
        result = []
        for key in sorted(left.keys() | right.keys()):
            if key not in left or key not in right:
                result.append(list(path + (key,)))
            else:
                result.extend(differences(left[key], right[key], path + (key,)))
        return result
    return [] if left == right else [list(path)]


def main():
    texts = {ref: source(ref) for ref in (BASE, CANDIDATE, CURRENT, "90740e0")}
    trees = {ref: yaml.load(value, Loader=yaml.BaseLoader) for ref, value in texts.items()}
    before, after = trees[BASE], trees[CANDIDATE]
    assert texts[CANDIDATE] == texts[CURRENT]
    diff = differences(before, after)
    assert diff == [["jobs", "native", "strategy", "matrix", "include"],
                    ["on", "workflow_dispatch", "inputs", "lane", "options"]], diff
    assert after["on"]["workflow_dispatch"]["inputs"]["lane"]["options"] == [
        "all", "arm-macos-ios", "windows", "linux"]
    restored = copy.deepcopy(after)
    restored["on"]["workflow_dispatch"]["inputs"]["lane"]["options"] = before["on"]["workflow_dispatch"]["inputs"]["lane"]["options"]
    restored["jobs"]["native"]["strategy"]["matrix"]["include"] = before["jobs"]["native"]["strategy"]["matrix"]["include"]
    assert restored == before
    old = before["jobs"]["native"]["strategy"]["matrix"]["include"]
    new = after["jobs"]["native"]["strategy"]["matrix"]["include"]
    hosts = [{"os": "ubuntu-24.04", "target": "linux"},
             {"os": "windows-latest", "target": "windows"},
             {"os": "macos-15", "target": "macos"},
             {"os": "macos-15-intel", "target": "macos"}]
    cases = [("default dispatch", "workflow_dispatch", None), ("push", "push", None),
             ("explicit all", "workflow_dispatch", "all"),
             ("explicit ARM", "workflow_dispatch", "arm-macos-ios"),
             ("push cannot select ARM", "push", "arm-macos-ios"),
             ("explicit Windows", "workflow_dispatch", "windows"),
             ("push cannot select Windows", "push", "windows"),
             ("explicit Linux", "workflow_dispatch", "linux"),
             ("push cannot select Linux", "push", "linux"),
             ("unknown lane", "workflow_dispatch", "unknown"),
             ("empty lane", "workflow_dispatch", ""),
             ("case-insensitive Linux", "workflow_dispatch", "LINUX"),
             ("case-insensitive Windows", "workflow_dispatch", "WINDOWS"),
             ("case-insensitive ARM", "workflow_dispatch", "ARM-MACOS-IOS"),
             ("other event cannot select Linux", "pull_request", "linux")]
    results = []
    for name, event, lane in cases:
        normalized = (lane or "").casefold()
        expected = hosts
        if event == "workflow_dispatch":
            expected = {"linux": hosts[:1], "windows": hosts[1:2],
                        "arm-macos-ios": hosts[2:3]}.get(normalized, hosts)
        actual, prior = evaluate(new, event, lane), evaluate(old, event, lane)
        assert actual == expected, name
        if event != "workflow_dispatch" or normalized != "linux":
            assert actual == prior, name
        results.append({"name": name, "event": event, "lane": lane,
                        "before": prior, "after": actual, "pass": True})
    job = after["jobs"]["native"]
    wrong_restored = copy.deepcopy(after)
    wrong_before = trees["90740e0"]
    wrong_restored["on"]["workflow_dispatch"] = wrong_before["on"]["workflow_dispatch"]
    wrong_restored["jobs"]["native"]["strategy"]["matrix"]["include"] = wrong_before["jobs"]["native"]["strategy"]["matrix"]["include"]
    wrong_differences = differences(wrong_before, wrong_restored)
    assert wrong_differences == [["jobs", "native", "steps"]]
    report = {"verdict": "CODE APPROVED; remote dispatch and native layout gates remain open",
              "baseline": BASE, "candidate": CANDIDATE, "workflow_identical_through": CURRENT,
              "resolved_refs": {ref: subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip() for ref in texts},
              "workflow_sha256": {ref: hashlib.sha256(value.encode()).hexdigest() for ref, value in texts.items()},
              "changed_yaml_paths": diff, "restored_exact_prior_scalar_and_options_equal_baseline": True,
              "job_guard": job["if"], "job_timeout_minutes": job["timeout-minutes"],
              "step_count": len(job["steps"]), "all_steps_permissions_deadlines_artifacts_identical": True,
              "cases": results, "retained_wrong_baseline_unrelated_difference_paths": wrong_differences}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
