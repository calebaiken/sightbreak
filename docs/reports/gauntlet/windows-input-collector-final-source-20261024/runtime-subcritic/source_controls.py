#!/usr/bin/env python3
"""Pure byte/source controls; never imports or executes candidate code."""
import hashlib
import json
import os
import re
import subprocess

ROOT = "11c5773eff6888c5157784c272aca144614338d4"
TARGET = "c32415148db1f110bbc7eadfca3793d4693429ff"
PATHS = ["game/scripts/gameplay/match.gd", "game/tests/movement_prediction_test.gd", "scripts/fixtures/export_integration.gd", "scripts/verify_integration_export.py"]

def blob(rev, path):
    return subprocess.check_output(["git", "show", rev + ":" + path])

def erase(source):
    source = re.sub(rb"(?m)^.*# INPUT_OBSERVATION_HOOK\n", b"", source)
    return re.sub(rb"(?m)^[ \t]*# BEGIN INPUT OBSERVATION ([^\n]+)\n.*?^[ \t]*# END INPUT OBSERVATION \1\n", b"", source, flags=re.S)

def release_guard(source):
    return b'if not debug or not "--native-input-observation" in args or bool(settings.get("require_accounts", false)) or not str(settings.get("join_ticket", "")).is_empty(): return false' in source

def guarded_actor_traversal(source):
    return b'if reason == "snapshot_applied":\n\t\t\tfor value: Variant in data.get("actors", []):' in source

assert os.sched_getaffinity(0) == {4}, os.sched_getaffinity(0)
results = {"target": TARGET, "root": ROOT, "affinity": sorted(os.sched_getaffinity(0)), "erasure": {}}
for path in PATHS:
    old, new = blob(ROOT,path), blob(TARGET,path)
    clean = erase(new)
    assert clean == old, path
    mutated = new.replace(b"var _simulation_tick := 0", b"var _simulation_tick := 1", 1) if path.endswith("match.gd") else None
    if mutated is not None:
        assert erase(mutated) != old
    results["erasure"][path] = {"original_sha256": hashlib.sha256(old).hexdigest(), "erased_sha256": hashlib.sha256(clean).hexdigest(), "equal": clean == old}
match = blob(TARGET, PATHS[0])
assert release_guard(match)
assert guarded_actor_traversal(match)
assert not release_guard(match.replace(b"if not debug or not", b"if not", 1))
assert not guarded_actor_traversal(match.replace(b'if reason == "snapshot_applied":\n\t\t\tfor value:', b'if true:\n\t\t\tfor value:', 1))
results["positive_source_controls"] = ["exact release/flag/account/ticket admission guard retained", "only applied snapshots traverse actor array"]
results["mutation_negative_controls"] = ["protected simulation tick initialization mutation rejected by erasure", "release gate deletion rejected", "unguarded actor traversal rejected"]
results["limitations"] = "These are byte/source assertions, not execution of GDScript or proof of native/API/timing behavior."
print(json.dumps(results,indent=2))
