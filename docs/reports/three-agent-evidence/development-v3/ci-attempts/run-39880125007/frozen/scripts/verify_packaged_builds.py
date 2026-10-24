#!/usr/bin/env python3
"""Extract and verify delivery ZIPs, then smoke their actual Linux ELF and wrappers.

Requires a clean, identical source checkout and Linux to execute the packaged ELF.
No device installation, mobile performance, or Xcode compilation is claimed.
All extraction, runtime state and raw logs remain in a fresh evidence directory.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import stat
import sys
import zipfile

from build_manifest import BUILDS, OUTPUTS, VERSION, descriptor, require_clean, same_source
from verify_builds import (VerificationAttempt, integrated_resources, linux_elf, load_exports,
                           no_test_harnesses, packed_paths, recheck_exports, require)


def safe_member(name, target=None):
    require(isinstance(name, str) and bool(name) and "\\" not in name and ":" not in name
            and not any(ord(character) < 32 for character in name), "Unsafe archive path: " + repr(name))
    path = pathlib.PurePosixPath(name)
    require(bool(path.parts) and not path.is_absolute() and path.as_posix() == name
            and all(part not in (".", "..") for part in path.parts), "Unsafe archive path: " + name)
    if target is not None:
        require(len(path.parts) > 1 and path.parts[0] == target, "Archive member has wrong target: " + name)
    return path


def expected_members(record, receipt_bytes):
    target = record["target"]
    require(target in OUTPUTS, "Unexpected export target")
    expected = {}
    for item in record["payload"]:
        name = item["path"]
        safe_member(name, target)
        require(name not in expected and name != target + "/source.json", "Duplicate or self-referential payload: " + name)
        require(type(item["bytes"]) is int and item["bytes"] >= 0, "Invalid member byte count: " + name)
        require(isinstance(item["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", item["sha256"]),
                "Invalid member SHA-256: " + name)
        require(type(item["mode"]) is int and item["mode"] in (0o644, 0o755), "Invalid member mode: " + name)
        expected[name] = item
    require(expected.get(OUTPUTS[target]) == record["artifact"], "Primary artifact missing from payload receipt")
    require(json.loads(receipt_bytes) == record, "Receipt bytes do not match the frozen export record")
    name = target + "/source.json"
    expected[name] = {"path": name, "bytes": len(receipt_bytes),
                      "sha256": hashlib.sha256(receipt_bytes).hexdigest(), "mode": 0o644}
    return expected


def extract_archive(archive, record, receipt_bytes, destination):
    """Validate the complete inventory before writing any untrusted member path."""
    expected = expected_members(record, receipt_bytes)
    with zipfile.ZipFile(archive) as bundle:
        entries = bundle.infolist()
        names = [entry.filename for entry in entries]
        for entry in entries:
            require(entry.orig_filename == entry.filename, "Unsafe truncated archive path")
            safe_member(entry.filename, record["target"])
            require(not entry.is_dir(), "Unexpected directory entry: " + entry.filename)
            mode = entry.external_attr >> 16
            require(entry.create_system == 3 and stat.S_IFMT(mode) == stat.S_IFREG,
                    "Archive member is not a POSIX regular file: " + entry.filename)
        require(len(names) == len(set(names)) and set(names) == set(expected),
                "Packaged file inventory differs from its export receipt (duplicates, missing or extra members)")
        for entry in entries:
            item = expected[entry.filename]
            require((entry.external_attr >> 16) & 0o7777 == item["mode"],
                    "Packaged executable mode differs from receipt: " + entry.filename)
            require(entry.file_size == item["bytes"], "Packaged byte count differs from receipt: " + entry.filename)
        for entry in entries:
            item = expected[entry.filename]
            path = destination.joinpath(*safe_member(entry.filename).parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            require(path.resolve().is_relative_to(destination.resolve()), "Extraction escaped its attempt directory")
            digest, size = hashlib.sha256(), 0
            with bundle.open(entry) as stream, path.open("xb") as output:
                while content := stream.read(1024 * 1024):
                    digest.update(content)
                    size += len(content)
                    output.write(content)
            require(size == item["bytes"] and digest.hexdigest() == item["sha256"],
                    "Extracted bytes differ from receipt: " + entry.filename)
            path.chmod(item["mode"])
            if os.name == "posix":
                require(stat.S_IMODE(path.stat().st_mode) == item["mode"],
                        "Extracted executable mode differs from receipt: " + entry.filename)
    recheck_extracted(destination, expected, record["target"])
    return expected


def recheck_extracted(destination, expected, target):
    root = destination / target
    files = [root, *root.rglob("*")]
    require(not any(path.is_symlink() for path in files), "Symlink appeared in extracted payload")
    require(all(stat.S_ISDIR(path.stat().st_mode) or stat.S_ISREG(path.stat().st_mode) for path in files),
            "Non-regular file appeared in extracted payload")
    actual = {path.relative_to(destination).as_posix() for path in files if path.is_file()}
    require(actual == set(expected), "Extracted payload inventory changed during verification: " + target)
    for name, item in expected.items():
        path = destination.joinpath(*safe_member(name, target).parts)
        require(path.resolve().is_relative_to(destination.resolve()), "Extracted payload escaped its attempt directory")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        require(path.stat().st_size == item["bytes"] and digest == item["sha256"],
                "Extracted payload changed during verification: " + name)
        if os.name == "posix":
            require(stat.S_IMODE(path.stat().st_mode) == item["mode"],
                    "Extracted payload mode changed during verification: " + name)


def delivery_inputs(current, records):
    manifest_bytes = (BUILDS / "manifest.json").read_bytes()
    checksum_bytes = (BUILDS / "checksums.txt").read_bytes()
    manifest = json.loads(manifest_bytes)
    require_clean(manifest)
    require(same_source(manifest, current), "Packaged manifest has a different frozen source identity")
    require(manifest["game"] == "SIGHTBREAK" and manifest["version"] == VERSION
            and manifest["engine"] == "Godot 4.7.2" and manifest["build_type"] == "debug",
            "Packaged manifest has unexpected game/version/engine/build type")
    exports = manifest["exports"]
    require(len(exports) == len(records) and len({record["target"] for record in exports}) == len(records)
            and {record["target"]: record for record in exports} == records,
            "Packaged exports differ from current frozen export receipts")
    expected_paths = {OUTPUTS[target] for target in OUTPUTS if target != "ios"}
    expected_paths.update(f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip" for target in OUTPUTS)
    artifacts = {}
    for item in manifest["artifacts"]:
        name = item["path"]
        safe_member(name)
        require(name not in artifacts, "Duplicate artifact descriptor: " + name)
        require(descriptor(BUILDS / name) == item, "Packaged artifact changed: " + name)
        artifacts[name] = item
    require(set(artifacts) == expected_paths, "Packaged artifact inventory differs from required targets")
    checksums = {}
    for line in checksum_bytes.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(match is not None, "Malformed checksums.txt entry")
        digest, name = match.groups()
        safe_member(name)
        require(name not in checksums, "Duplicate checksum entry: " + name)
        checksums[name] = digest
    require(checksums == {name: item["sha256"] for name, item in artifacts.items()},
            "Checksums do not exactly match packaged manifest artifacts")
    return manifest, manifest_bytes, checksum_bytes, artifacts


def recheck_delivery(manifest_bytes, checksum_bytes, artifacts, receipt_bytes):
    require((BUILDS / "manifest.json").read_bytes() == manifest_bytes, "Packaged manifest changed during verification")
    require((BUILDS / "checksums.txt").read_bytes() == checksum_bytes, "Package checksums changed during verification")
    for name, item in artifacts.items():
        require(descriptor(BUILDS / name) == item, "Packaged artifact changed during verification: " + name)
    for target, content in receipt_bytes.items():
        require((BUILDS / target / "source.json").read_bytes() == content,
                "Export receipt bytes changed during verification: " + target)


def linux_host():
    return sys.platform.startswith("linux")


def verify_packages(attempt):
    current = attempt.report["source_before"]
    records = load_exports(current)
    attempt.final_checks.append(("Final export payload/receipt check", lambda: recheck_exports(records, current)))
    manifest, manifest_bytes, checksum_bytes, artifacts = delivery_inputs(current, records)
    receipt_bytes = {target: (BUILDS / target / "source.json").read_bytes() for target in records}
    attempt.final_checks.append(("Final packaged input check", lambda: recheck_delivery(
        manifest_bytes, checksum_bytes, artifacts, receipt_bytes)))
    attempt.report.update({"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                           "checksums_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
                           "artifact_source": manifest, "archives_verified": {}})
    destination = attempt.output / "extracted"
    expected = {}
    for target, record in records.items():
        name = f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip"
        members = extract_archive(BUILDS / name, record, receipt_bytes[target], destination)
        expected[target] = members
        attempt.final_checks.append(("Final extracted " + target + " payload check",
                                     lambda target=target, members=members: recheck_extracted(destination, members, target)))
        attempt.report["archives_verified"][target] = {"archive": name, "members": list(members.values()),
                                                       "byte_hashes_verified": True, "archive_modes_verified": True,
                                                       "extracted_modes_verified": os.name == "posix"}
        attempt.save()
    executable_name = OUTPUTS["linux"]
    wrappers = sorted(name for name in expected["linux"] if name.endswith(".sh"))
    require(wrappers, "Linux console wrapper(s) missing; the debug console wrapper export preset is enabled")
    for name in [executable_name, *wrappers]:
        require(expected["linux"][name]["mode"] == 0o755, "Linux entry point is not executable: " + name)
    executable = destination / executable_name
    linux_elf(executable)
    paths = packed_paths(executable, embedded=True)
    no_test_harnesses(paths)
    integrated_resources(paths)
    require(linux_host(), "Actual packaged Linux ELF/wrapper smoke requires Linux; no runtime pass is available on this host")
    for index, name in enumerate([executable_name, *wrappers]):
        path = destination / name
        label = "linux-elf-menu" if index == 0 else f"linux-wrapper-{index - 1}"
        text = attempt.run(label, [str(path), "--headless", "--", "--smoke"], cwd=path.parent)
        require("SIGHTBREAK_MAIN_READY screen=menu" in text, "Packaged Linux menu readiness marker missing: " + name)
    attempt.report.update({"packaged_linux_elf_smoke": True, "packaged_linux_console_wrappers_smoke": wrappers,
                           "linux_pck_resources": len(paths), "test_harnesses_excluded": True,
                           "android_scope": "Archive bytes and modes only; no device test",
                           "ios_scope": "Unsigned project archive bytes and modes only; no Xcode build or device test"})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, default=BUILDS / "packaged-verification",
                        help="New or empty attempt directory; keeps extracted packages and raw logs")
    args = parser.parse_args(argv)
    try:
        attempt = VerificationAttempt(args.output, "Actual delivery archive bytes/modes and extracted Linux ELF/console-wrapper smoke")
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return attempt.execute(verify_packages)


if __name__ == "__main__":
    raise SystemExit(main())
