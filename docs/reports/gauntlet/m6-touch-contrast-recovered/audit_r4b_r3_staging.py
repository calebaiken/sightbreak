#!/usr/bin/env python3
"""Pure exact-source/UID audit; no Godot, cache creation or stage mutation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "scripts"))
from prepare_touch_contrast_r4b import BASELINE, TOUCH, instrument

SOURCE = "108d1cdc6cf471daa7390298c234bb1c087ae865"
FAILED = "b001fc5087960729535f63c896b40d6dc25bd272"
STAGE = Path("/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r3")
OLD_STAGE = Path("/workspace/sightbreak-touch-contrast-fixture-recovered-r4b-r2")
OLD_RAW = Path("/workspace/sightbreak-touch-contrast-native-recovered-r4b-r2")
REPORT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, data):
    (REPORT / name).write_text(json.dumps(data, indent=2) + "\n")


def entries(manifest):
    return manifest["files"] + manifest["fixture"] + [
        {"path": "game/tests/touch_contrast_instrumented.gd", "sha256": manifest["instrumented_sha256"]},
        {"path": "game/tests/touch_contrast_instrumented.gd.uid", "sha256": manifest["instrumented_uid_sha256"]}]


def main():
    assert not Path("/workspace/sightbreak-touch-contrast-native-recovered-r4b-r3").exists()
    fixtures, audited = [], []
    for name, source in (("baseline", BASELINE), ("candidate", SOURCE)):
        root = STAGE / name
        manifest = json.loads((root / "SOURCE.json").read_text())
        assert manifest["source"] == source
        original = git("ls-tree", "-r", "--name-only", source, "game").decode().splitlines()
        assert original == [x["path"] for x in manifest["files"]] and len(original) == 323
        rows = entries(manifest)
        assert len(rows) == len({x["path"] for x in rows}) == 327
        for entry in manifest["files"]:
            data = (root / entry["path"]).read_bytes()
            assert data == git("show", source + ":" + entry["path"])
            assert len(data) == entry["bytes"]
        for entry in rows:
            assert sha((root / entry["path"]).read_bytes()) == entry["sha256"]
        wrapped, calls = instrument((root / TOUCH).read_text())
        wrapped = wrapped.replace("class_name TacticalTouch\n", "", 1)
        assert wrapped.encode() == (root / "game/tests/touch_contrast_instrumented.gd").read_bytes()
        assert calls == manifest["instrumentation"]
        for entry in manifest["fixture"]:
            assert (root / entry["path"]).read_bytes() == (REPO / "scripts/fixtures/touch_contrast_r4b" / Path(entry["path"]).name).read_bytes()
        actual = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}
        assert actual == {x["path"] for x in rows} | {"SOURCE.json"}
        assert not any(root.rglob(".godot"))
        uids = [(root / x["path"]).read_text().strip() for x in rows if x["path"].endswith(".uid")]
        assert len(uids) == len(set(uids)) == 138 and all(x.startswith("uid://") for x in uids)
        previous_root = OLD_STAGE / name
        previous = json.loads((previous_root / "SOURCE.json").read_text())
        for entry in entries(previous):
            assert sha((previous_root / entry["path"]).read_bytes()) == entry["sha256"]
        assert calls == previous["instrumentation"]
        if name == "candidate":
            before = (previous_root / TOUCH).read_bytes()
            after = (root / TOUCH).read_bytes()
            assert after == before.replace(b'var compact := key != "fire" and r < 32.0', b'var compact: bool = key != "fire" and r < 32.0', 1)
            assert (root / "game/tests/touch_contrast_instrumented.gd").read_bytes() == (previous_root / "game/tests/touch_contrast_instrumented.gd").read_bytes().replace(b'var compact := key != "fire" and r < 32.0', b'var compact: bool = key != "fire" and r < 32.0', 1)
        receipt = {"name": name, "path": str(root), "source_full": source,
            "manifest_sha256": sha((root / "SOURCE.json").read_bytes()), "paint_variant": manifest["paint_variant"],
            "original_touch_sha256": manifest["original_touch_sha256"], "original_paths": len(original),
            "original_bytes": sum(x["bytes"] for x in manifest["files"])}
        fixtures.append(receipt)
        audited.append({**receipt, "verified_paths": 327, "unique_uids": 138, "godot_cache_absent": True,
            "path_hashes": [[x["path"], x["sha256"]] for x in rows], "wrapper_sha256": manifest["instrumented_sha256"],
            "diagnostic_draw_receipts_unchanged": True, "old_r2_stage_paths_unchanged": 327})
        (REPORT / (name + "-SOURCE-r4b-r3.json")).write_bytes((root / "SOURCE.json").read_bytes())
    old_payload = json.loads((REPORT / "native-r4b-r2/payload-manifest.json").read_text())
    assert {str(p.relative_to(OLD_RAW)) for p in OLD_RAW.rglob("*") if p.is_file()} == {x["path"] for x in old_payload["files"]}
    for entry in old_payload["files"]:
        data = (OLD_RAW / entry["path"]).read_bytes()
        assert len(data) == entry["bytes"] and sha(data) == entry["sha256"]
    assert git("diff", "--name-only", FAILED, SOURCE, "--", "game").decode().splitlines() == [TOUCH]
    assert git("diff", "--name-only", FAILED, SOURCE, "--", "scripts").decode().splitlines() == ["scripts/test_touch_declaration_r4b_r3.py", "scripts/touch_geometry_r4b.py"]
    audit = {"scope": "SOURCE/PURE ONLY", "source": SOURCE, "fixtures": audited,
        "old_r2_raw_files_verified_unchanged": len(old_payload["files"]),
        "old_r2_stage_source_paths_each_verified_unchanged": 327,
        "new_raw_root_absent": True, "engine_invocations": 0, "uid_generation": 0,
        "audit_script_sha256": sha(Path(__file__).read_bytes())}
    write("r4b-r3-staging-audit.json", audit)
    previous_freeze = json.loads((REPORT / "SOURCE_FREEZE-r4b-r2.json").read_text())
    paths = [x["path"] for x in previous_freeze["frozen_files"]] + [
        "scripts/test_touch_declaration_r4b_r3.py",
        "docs/reports/gauntlet/m6-touch-contrast-recovered/R4B_R3_PREREGISTRATION.md"]
    frozen = []
    for path in paths:
        data = (REPO / path).read_bytes()
        assert data == git("show", SOURCE + ":" + path)
        frozen.append({"path": path, "sha256": sha(data), "bytes": len(data)})
    assert len(frozen) == 24
    freeze = {**previous_freeze, "phase": "SOURCE_AND_PURE_ONLY_REVIEW_PENDING", "round": "4B-R3",
        "freeze_commit": SOURCE, "preregistration_commit": "439bd2597836d3bb881e8e2c7711eb44efca6cb8",
        "lexical_preregistration_commit": git("rev-parse", "08548776").decode().strip(),
        "prior_source_method": FAILED, "prior_source_method_acceptance": "abb837b4",
        "r4b_r2_native_handoff": "384d17d0b44c5e5c46178023e52009010bc280f7",
        "r4b_r2_native_actual_verdict": "ACQUISITION FAIL / preservation ACCEPT 5c5837123a951ec12c3e2ea0f2c3ec76071e6413",
        "product_commit": SOURCE,
        "correction_scope": "ONE product declaration annotation preserving expression; exact inferred/bool lexical helper accommodation only. Native analyzer, geometry/math/paint/ownership predicates and all thresholds unchanged.",
        "fixtures": fixtures, "frozen_files": frozen, "pure_controls": 60,
        "staging_audit_sha256": sha((REPORT / "r4b-r3-staging-audit.json").read_bytes()),
        "pure_log_sha256": sha((REPORT / "r4b-r3-pure-freeze.log").read_bytes()),
        "source_delta_sha256": sha((REPORT / "r4b-r3-source-delta.json").read_bytes()),
        "legacy_parser_rejection_sha256": sha((REPORT / "r4b-r3-declaration-parser-precheck.json").read_bytes()),
        "geometry_certificate_scope": "Historical same-expression source certificate; no native or new continuous-certificate result claimed.",
        "remaining": "Fresh independent source review, then separate explicit root native release. Explicit bool compilation, actual complete pixels/ownership/contrast, dark surround, occlusion, truthful affordance and blind actual images remain unobserved."}
    write("SOURCE_FREEZE-r4b-r3.json", freeze)
    print(json.dumps({"source": SOURCE, "fixtures": fixtures, "frozen_files": 24,
        "old_r2_raw_files_unchanged": len(old_payload["files"]), "source_uid_paths_each": 327,
        "new_raw_root_absent": True, "engine_invocations": 0}))


if __name__ == "__main__":
    main()
