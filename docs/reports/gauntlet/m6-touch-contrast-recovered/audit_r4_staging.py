#!/usr/bin/env python3
"""Pure staging/source/UID audit. Never invokes Godot or edits prepared files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))
from prepare_touch_contrast_r4 import BASELINE, TOUCH, instrument

STAGE = Path("/workspace/sightbreak-touch-contrast-fixture-recovered-r4")
FREEZE = "16335abfaf2068b2b2ea54c7e100a1505f62b5c1"
REPORT = Path(__file__).resolve().parent


def git(*args): return subprocess.check_output(["git", "-C", str(REPO), *args])
def sha(data): return hashlib.sha256(data).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=2) + "\n")


def main():
    results, receipts = [], []
    for name, source in (("baseline", BASELINE), ("candidate", FREEZE)):
        root = STAGE / name
        manifest_path = root / "SOURCE.json"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["source"] == source
        paths = git("ls-tree", "-r", "--name-only", source, "game").decode().splitlines()
        assert paths == [e["path"] for e in manifest["files"]] and len(paths) == 323
        checked, uids = [], {}
        for entry in manifest["files"]:
            data = (root / entry["path"]).read_bytes()
            assert data == git("show", source + ":" + entry["path"])
            assert sha(data) == entry["sha256"] and len(data) == entry["bytes"]
            checked.append({"path": entry["path"], "sha256": sha(data)})
        for entry in manifest["fixture"]:
            data = (root / entry["path"]).read_bytes()
            assert data == (REPO / "scripts/fixtures/touch_contrast_r4" / Path(entry["path"]).name).read_bytes()
            assert sha(data) == entry["sha256"]
            checked.append({"path": entry["path"], "sha256": sha(data)})
        wrapped, calls = instrument((root / TOUCH).read_text())
        wrapped = wrapped.replace("class_name TacticalTouch\n", "", 1)
        assert calls == manifest["instrumentation"]
        assert (root / "game/tests/touch_contrast_instrumented.gd").read_bytes() == wrapped.encode()
        for filename, key in (("touch_contrast_instrumented.gd", "instrumented_sha256"), ("touch_contrast_instrumented.gd.uid", "instrumented_uid_sha256")):
            path = "game/tests/" + filename
            assert sha((root / path).read_bytes()) == manifest[key]
            checked.append({"path": path, "sha256": manifest[key]})
        assert len(checked) == 327
        actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
        assert actual == {x["path"] for x in checked} | {"SOURCE.json"}
        assert not any(root.rglob(".godot"))
        for path in root.rglob("*.uid"):
            value = path.read_text().strip()
            assert value.startswith("uid://") and value not in uids
            uids[value] = str(path.relative_to(root))
        row = {"name": name, "source": source, "manifest_sha256": sha(manifest_path.read_bytes()), "checked_paths": len(checked),
            "uid_paths": len(uids), "uid_duplicates": 0, "godot_cache_present": False, "source_wrapper_fixture_uid_equal": True,
            "path_hashes": checked, "instrumented_sha256": manifest["instrumented_sha256"]}
        results.append(row)
        receipts.append({"name": name, "path": str(root), "source_full": source, "manifest_sha256": row["manifest_sha256"],
            "paint_variant": manifest["paint_variant"], "original_paths": len(paths), "original_bytes": sum(e["bytes"] for e in manifest["files"])})
        (REPORT / (name + "-SOURCE-r4.json")).write_bytes(manifest_path.read_bytes())
    changes = git("diff", "--name-only", BASELINE, FREEZE, "--", "game").decode().splitlines()
    assert changes == [TOUCH]
    audit = {"phase": "SOURCE_PURE_ONLY", "engine_invocations": 0, "native_captures": 0, "game_changes": changes,
        "fixtures": results, "audit_script_sha256": sha(Path(__file__).read_bytes())}
    write(REPORT / "r4-staging-audit.json", audit)
    paths = [TOUCH, TOUCH + ".uid", "scripts/prepare_touch_contrast_r4.py", "scripts/analyze_touch_contrast_r4.py",
        "scripts/analyze_touch_contrast.py", "scripts/test_touch_contrast_r4.py", "scripts/test_touch_contrast_r4_method.py",
        "scripts/test_touch_contrast_r4_receipts.py", "scripts/test_touch_contrast_method.py", "scripts/prepare_touch_contrast.py",
        "scripts/derive_touch_r4_reference.py", "scripts/fixtures/touch_contrast_r4/touch_contrast_capture.gd",
        "scripts/fixtures/touch_contrast_r4/touch_contrast_capture.gd.uid", "scripts/fixtures/touch_contrast_r4/r3_glyph_support.json",
        "docs/reports/gauntlet/m6-touch-contrast-recovered/R4_PREREGISTRATION.md"]
    frozen = []
    for path in paths:
        data = (REPO / path).read_bytes()
        assert data == git("show", FREEZE + ":" + path)
        frozen.append({"path": path, "sha256": sha(data), "bytes": len(data)})
    freeze = {"phase": "SOURCE_AND_PURE_ONLY_REVIEW_PENDING", "round": 4, "freeze_commit": FREEZE, "baseline_commit": BASELINE,
        "preregistration_commit": "d583359", "product_commit": "4153d91", "r3_result": "FAIL; immutable evidence 0f83243; independent verdict 39b5a9d/8a5f531",
        "engine_invocations": 0, "native_captures": 0, "pure_controls": 46, "expected_native_images_per_source": 2816,
        "expected_group_rows_per_source": 304, "expected_component_rows_per_source": 352, "retained_intermediate_rows_per_source": 48,
        "candidate_gated_rows_per_source": 608, "fixtures": receipts, "frozen_files": frozen,
        "staging_audit_sha256": sha((REPORT / "r4-staging-audit.json").read_bytes()),
        "pure_log_sha256": sha((REPORT / "r4-pure-freeze.log").read_bytes()),
        "remaining": "Fresh independent source/method critique, then explicit root native lane release. Actual contrast, visibility/occlusion, final dark surround, truthful affordance, scene occlusion and blind actual-image comparison remain unqualified."}
    write(REPORT / "SOURCE_FREEZE-r4.json", freeze)
    print(json.dumps({"freeze": FREEZE, "fixtures": receipts, "frozen_files": len(frozen), "all327paths_uid_wrapper_equal": True}))


if __name__ == "__main__": main()
