"""Offline packaging of the completed, committed two-case follow-up only."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import runpy
import secrets
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / ".runtime/build_neutral_receipt_packet.py"
helpers = runpy.run_path(str(HELPER))
encoded, digest = helpers["encoded"], helpers["digest"]
neutralize, semantics, STAGES = helpers["neutralize"], helpers["semantics"], helpers["STAGES"]
PREFIX = "docs/reports/native-journal-only-restart-evidence/"


def git(*args, data=None):
    return subprocess.check_output(["git", "-C", str(REPO), *args], input=data)


def load_objects(commit):
    paths = [PREFIX, "scripts/validate_native_transaction_restart.py", "scripts/native_transaction_restart_probe.gd"]
    objects = {}
    for row in git("ls-tree", "-rz", commit, "--", *paths).split(b"\0"):
        if row:
            metadata, path = row.split(b"\t", 1)
            objects[path.decode()] = metadata.decode().split()[2]
    names = sorted(objects)
    raw = git("cat-file", "--batch", data="".join(objects[name] + "\n" for name in names).encode())
    originals, offset = {}, 0
    for name in names:
        end = raw.index(b"\n", offset)
        oid, kind, size = raw[offset:end].decode().split()
        assert kind == "blob" and oid == objects[name]
        size = int(size)
        originals[name] = raw[end + 1:end + 1 + size]
        offset = end + size + 2
    assert offset == len(raw)
    return objects, originals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--run", default="r2")
    args = parser.parse_args()
    commit = git("rev-parse", args.evidence).decode().strip()
    objects, originals = load_objects(commit)
    nonce = secrets.token_hex(8)
    base = Path("C:/Users/blith/AppData/Local/Temp/opencode") / ("journal-review-" + nonce)
    packet, controller = base / "critic", base / "CONTROLLER"
    packet.mkdir(parents=True)
    controller.mkdir()
    labels = ["Set-" + secrets.token_hex(4).upper() for _ in range(2)]
    assert len(set(labels)) == 2
    secrets.SystemRandom().shuffle(labels)
    key = dict(evidence_commit=commit, labels={}, files=[], withheld=[],
               transformation_policy="Exact path/OS-environment-path/source-hash substitutions only; per-file originals, replacements and occurrence counts below. Embedded original fixture/environment hashes are preserved, not relabelled as hashes of transformed files.")
    manifest = {}
    overview = dict(groups={}, status="Observed data, not a critic verdict.")
    forbidden = [b"baseline", b"candidate", b"701ce2c", b"7b6f379", b"7be70f7", b"31438cbc", b"49268b87", commit[:7].encode(), b"sightbreak-pr18", b"sightbreak_local_only"]

    def binding(path):
        return dict(commit=commit, path=path, git_blob=objects[path], sha256=digest(originals[path]), bytes=len(originals[path]))

    def emit(name, data, kind, source=None, changes=None, inputs=None):
        path = packet / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        manifest[name] = dict(sha256=digest(data), bytes=len(data), kind=kind)
        row = dict(packet_path=name, packet_sha256=digest(data))
        if source:
            row.update(original=binding(source), transformations=changes, byte_identical=data == originals[source])
        else:
            row.update(generated=True, derivation=kind, original_inputs=[binding(source) for source in inputs or []])
        key["files"].append(row)

    for label, arm in zip(labels, ["baseline-701", "candidate-7b6f379"]):
        arm_prefix = PREFIX + args.run + "/" + arm + "/"
        summary = json.loads(originals[arm_prefix + "summary.json"])
        assert summary["core_pass"] and len(summary["runs"]) == 1 and "native_economy" not in summary
        key["labels"][label] = dict(original_arm=arm, source=summary["source"],
                                    harness=summary["harness_checkout"], original_summary=binding(arm_prefix + "summary.json"))
        prefix = arm_prefix + "run-1/"
        sources = sorted(path for path in originals if path.startswith(prefix))
        original_files = {path[len(prefix):]: originals[path] for path in sources}
        initial = json.loads(original_files["send.launch-inputs.json"])
        context = json.loads(original_files["fixture.redacted.json"])
        command = initial["command"]
        aliases = [("executable_path", command[0], "[EXECUTABLE]/native-client"),
                   ("project_path", command[command.index("--path") + 1], "[PROJECT_ROOT]"),
                   ("probe_path", command[command.index("--script") + 1], "[EXTERNAL_PROBE]/driver.gd"),
                   ("private_fixture_path", initial["fixture_path"], "[ISOLATED_STATE]/fixture.json"),
                   ("private_journal_path", context["journal"], "[ISOLATED_STATE]/pending.json")]
        environment_paths = {}
        for name, value in initial["environment"].items():
            if name != "SIGHTBREAK_RECEIPT_FIXTURE" and re.search(r"[\\/]|^[A-Za-z]:", value):
                environment_paths.setdefault(value, []).append(name)
        for value, names in environment_paths.items():
            aliases.append(("OS_environment_path", value, "[OS_ENV:" + "+".join(sorted(names)) + "]"))
        for name, value in initial["source_file_sha256"].items():
            if value:
                aliases.append(("withheld_source_sha256", value, "[SOURCE_SHA256:" + name + "]"))
                forbidden.append(value.encode())
        key["labels"][label]["aliases"] = aliases
        case, files = label + "/case-01", {}
        for source in sources:
            name = source[len(prefix):]
            data, changes = neutralize(originals[source], aliases)
            files[name] = data
            emit(case + "/" + name, data, "transformed observation copy" if changes else "unchanged published observation bytes", source=source, changes=changes)
        assert all(files[name] == original_files[name] for name in STAGES)
        comparison = semantics(files)
        comparison["launch_input_comparisons"] = []
        for phase, stdout_name in [("send", "killed-client"), ("recovery", "recovery"), ("second-restart", "second-restart")]:
            inputs = json.loads(files[phase + ".launch-inputs.json"])
            config = json.loads(files[phase + ".fixture.redacted.json"])
            reads = [json.loads(line.removeprefix("NATIVE_RECEIPT_EVENT ")) for line in files[stdout_name + ".stdout.txt"].decode().splitlines() if line.startswith("NATIVE_RECEIPT_EVENT ")]
            read = next(row for row in reads if row["event"] == "fixture_read")
            comparison["launch_input_comparisons"].append(dict(
                phase=phase, supplied_config_keys=sorted(config), native_read=read,
                config_keys_match_prelaunch_and_native=sorted(config) == inputs["keys"] == read["keys"],
                original_private_file_digest_matches_native=inputs["fixture_sha256"] == read["sha256"],
                original_private_file_length_matches_native=inputs["fixture_bytes"] == read["bytes"],
                strict_six_key_restart=sorted(config) == ["journal", "mode", "owner", "password", "url", "username"] if phase != "send" else None,
                supplied_environment_keys=sorted(inputs["environment"]),
                source_identity_hashes="Withheld; exact values are controller-only."))
        emit(case + "/semantic-comparison.json", encoded(comparison), "derived from full supplied observations", inputs=sources)
        overview["groups"][label] = dict(case="case-01", price=context["payload"]["expected_price"],
            initial_economic_row_counts=comparison["actual_economic_table_row_counts"][STAGES[0]],
            initial_session_row_count=len(json.loads(files[STAGES[0]])["sessions"]))
        for path in originals:
            if path.startswith(arm_prefix) and not path.startswith(prefix):
                relative = "source-context/" + arm + "/" + path[len(arm_prefix):]
                target = controller / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(originals[path])
                key["withheld"].append(dict(controller_path=relative, original=binding(path), byte_identical=True))

    emit("OBSERVED_COMPARISON.json", encoded(overview), "observed initial counts and price")
    emit("README.md", (REPO / ".runtime/neutral_journal_only_review_readme.md").read_bytes(), "fixed reviewer quality bar and limitations")
    prior = PREFIX + "prior-review/_FROZEN_VERDICT.md"
    assert digest(originals[prior]) == "750bfb02e65f3f348567b8bf453b4387f931c70549d7c50469d377fc63bec2ee"
    (controller / "prior-frozen-verdict.md").write_bytes(originals[prior])
    key["withheld"].append(dict(controller_path="prior-frozen-verdict.md", original=binding(prior), byte_identical=True))
    for name, record in manifest.items():
        data = (packet / name).read_bytes()
        assert digest(data) == record["sha256"]
        assert not any(term.lower() in data.lower() for term in forbidden), name
        assert not re.search(rb"\b[A-Za-z]:[\\/]|receipt-oracle-[0-9a-f]{32}|Bearer [A-Za-z0-9_-]{20,}", data), name
    for row in key["files"]:
        if "original" in row:
            data = originals[row["original"]["path"]]
            for change in row["transformations"]:
                old, new = change["original_text"].encode(), change["replacement_text"].encode()
                assert data.count(old) == change["occurrences"]
                data = data.replace(old, new)
            assert data == (packet / row["packet_path"]).read_bytes()
    manifest_bytes = encoded(dict(schema=1, hash_algorithm="SHA-256", scope="Every ZIP payload except this manifest", files=manifest))
    (packet / "MANIFEST.json").write_bytes(manifest_bytes)
    zip_path = base / ("journal-review-" + nonce + ".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(packet.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(packet).as_posix(), date_time=(2000, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(zip_path) as archive:
        assert set(archive.namelist()) == set(manifest) | {"MANIFEST.json"}
        for name, record in manifest.items():
            assert digest(archive.read(name)) == record["sha256"]
        assert archive.read("MANIFEST.json") == manifest_bytes and archive.testzip() is None
    zip_bytes = zip_path.read_bytes()
    key["packet"] = dict(zip_path=str(zip_path), zip_sha256=digest(zip_bytes), zip_bytes=len(zip_bytes),
                         manifest_sha256=digest(manifest_bytes), zip_entries=len(manifest) + 1,
                         git_blob=git("hash-object", "--stdin", data=zip_bytes).decode().strip())
    key["verification"] = dict(case_count=2, unchanged_economic_stages=10, exact_transformation_replay=True,
        identity_and_secret_pattern_scan=True, zip_manifest_verified=True,
        unchanged_observations=sum(row.get("byte_identical") is True for row in key["files"]),
        transformed_observations=sum(row.get("byte_identical") is False for row in key["files"]))
    key_path = controller / "mapping.json"
    key_path.write_bytes(encoded(key))
    for path in [Path(__file__), HELPER, REPO / ".runtime/neutral_journal_only_review_readme.md"]:
        (controller / path.name).write_bytes(path.read_bytes())
    pins = dict(packet=key["packet"], controller_key_path=str(key_path), controller_key_sha256=digest(key_path.read_bytes()),
                critic_directory=str(packet), verification=key["verification"])
    (controller / "pins.json").write_bytes(encoded(pins))
    print(json.dumps(pins, indent=2))


if __name__ == "__main__":
    main()
