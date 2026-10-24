#!/usr/bin/env python3
"""Bind native exports to exact source, then package with licenses and checksums."""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import zipfile
from godot_process import source_snapshot

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDS = ROOT / "builds"
VERSION = "0.3.2-dev"
BUILD_NUMBER = 5
IOS_VERSION = "0.3.2"
OUTPUTS = {"linux": "linux/sightbreak.x86_64", "android": "android/sightbreak-debug.apk", "ios": "ios/sightbreak.xcodeproj/project.pbxproj"}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "game").rglob("*")):
        relative = path.relative_to(ROOT / "game")
        if not path.is_file() or ".godot" in relative.parts or "tests" in relative.parts:
            continue
        digest.update(relative.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    validation = source_snapshot(root=ROOT)
    return {"source_commit": git("rev-parse", "HEAD"), "source_game_tree": git("rev-parse", "HEAD:game"),
            "source_content_sha256": digest.hexdigest(),
            "source_validation_sha256": validation["content_sha256"],
            "source_game_dirty": bool(git("status", "--porcelain", "--untracked-files=all", "--", "game")),
            "source_dirty": bool(git("status", "--porcelain", "--untracked-files=all"))}


def require_clean(current):
    if current["source_game_dirty"] or current.get("source_dirty", False):
        raise SystemExit("Commit game source and validation tooling before producing delivery packages.")


def same_source(record, current):
    # Identical game bytes alone do not identify the exporter/harness revision.
    # Require the exact frozen commit, tree and on-disk bytes at every boundary.
    return all(record.get(key) and record.get(key) == current.get(key) for key in
               ("source_commit", "source_game_tree", "source_content_sha256", "source_validation_sha256"))


def archive_mode(path):
    # Keep executable entry points (including the generated console wrapper),
    # without propagating special permission bits into development packages.
    return 0o755 if path.stat().st_mode & 0o111 or path.name == "sightbreak.x86_64" else 0o644


def descriptor(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.relative_to(BUILDS).as_posix(), "bytes": path.stat().st_size,
            "sha256": digest, "mode": archive_mode(path)}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def payload(target):
    return [descriptor(path) for path in sorted((BUILDS / target).rglob("*"))
            if path.is_file() and path.name != "source.json" and path.suffix != ".log"]


def begin(target):
    data = source()
    require_clean(data)
    directory = BUILDS / target
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise SystemExit(f"Use a fresh empty {target} export directory; prior artifacts and receipts are retained.")
    data.update({"target": target, "export_completed": False,
                 "built_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write_json(directory / "source.json", data)


def finish(target):
    path = BUILDS / target / "source.json"
    data = json.loads(path.read_text())
    if data.get("export_completed"):
        raise SystemExit("Export receipt is already completed; never re-attest an earlier artifact.")
    current = source()
    require_clean(current)
    require_clean(data)
    if not same_source(data, current):
        raise SystemExit("Frozen source changed during export; rebuild before packaging.")
    output = BUILDS / OUTPUTS[target]
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"Missing export output: {output}")
    data.update({"export_completed": True, "artifact": descriptor(output), "payload": payload(target)})
    write_json(path, data)


def package():
    current = source()
    require_clean(current)
    if any((BUILDS / name).exists() for name in ("manifest.json", "checksums.txt")) or list(BUILDS.glob("sightbreak-*.zip")):
        raise SystemExit("Use a fresh packaging attempt; prior packages and success receipts are retained.")
    records = []
    artifacts = []
    for target in OUTPUTS:
        directory = BUILDS / target
        record = json.loads((directory / "source.json").read_text())
        if (not record["export_completed"] or record["source_game_dirty"]
                or record.get("source_dirty", False) or not same_source(record, current)):
            raise SystemExit(f"Stale or incomplete {target} export; rebuild all targets from current source.")
        if descriptor(BUILDS / OUTPUTS[target]) != record["artifact"] or payload(target) != record["payload"]:
            raise SystemExit(f"Changed {target} artifact; rebuild before packaging.")
        records.append(record)
        if target != "ios":
            artifacts.append(record["artifact"])
        archive = BUILDS / f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip"
        expected = {item["path"]: item for item in record["payload"]}
        with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.suffix == ".log":
                    continue
                info = zipfile.ZipInfo(path.relative_to(BUILDS).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (0o100000 | archive_mode(path)) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                content = path.read_bytes()
                if path.name == "source.json":
                    if json.loads(content) != record:
                        raise SystemExit(f"Changed {target} export receipt during packaging.")
                elif (info.filename not in expected or len(content) != expected[info.filename]["bytes"]
                      or hashlib.sha256(content).hexdigest() != expected[info.filename]["sha256"]
                      or archive_mode(path) != expected[info.filename]["mode"]):
                    raise SystemExit(f"Changed {target} payload during packaging: {info.filename}")
                bundle.writestr(info, content, compresslevel=1)
        inspect_archive(archive, record)
        artifacts.append(descriptor(archive))
    if source() != current or any(payload(record["target"]) != record["payload"] for record in records):
        raise SystemExit("Frozen source or payload changed during packaging; attempt retained without a success manifest.")
    manifest = {"game": "SIGHTBREAK", "version": VERSION, "engine": "Godot 4.7.2", "build_type": "debug",
                **current, "exports": records, "artifacts": artifacts,
                "limitations": ["Android debug signed; physical device installation and performance unverified.",
                                "iOS unsigned Xcode project; macOS/Xcode compilation and signing unverified.",
                                "Development candidate only: see docs/reports/DEVELOPMENT_V3_PROGRESS.md for exact-source results, retained failures and open gates.",
                                "Human full-match/gunplay, touch/gyro, sustained device performance, production deployment and each applicable 8.5 quality gate remain unverified."]}
    write_json(BUILDS / "manifest.json", manifest)
    (BUILDS / "checksums.txt").write_text("".join(f"{a['sha256']}  {a['path']}\n" for a in artifacts))
    print(json.dumps(manifest, indent=2))


def inspect_archive(archive, record):
    """Verify actual packaged bytes and entry-point modes, not just ZIP hashes."""
    expected = {item["path"]: item for item in record["payload"]}
    receipt = record["target"] + "/source.json"
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or set(bundle.namelist()) != set(expected) | {receipt}:
            raise SystemExit("Packaged file inventory differs from its export receipt.")
        for name, item in expected.items():
            content = bundle.read(name)
            if (len(content) != item["bytes"] or hashlib.sha256(content).hexdigest() != item["sha256"]
                    or (bundle.getinfo(name).external_attr >> 16) & 0o777 != item["mode"]):
                raise SystemExit("Packaged payload differs from its export receipt: " + name)
        if json.loads(bundle.read(receipt)) != record:
            raise SystemExit("Packaged export receipt differs from the validated receipt.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["begin", "finish", "package"])
    parser.add_argument("target", nargs="?", choices=OUTPUTS)
    arguments = parser.parse_args()
    if arguments.action == "package":
        package()
    elif arguments.target:
        (begin if arguments.action == "begin" else finish)(arguments.target)
    else:
        parser.error("begin/finish require a target")
