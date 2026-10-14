#!/usr/bin/env python3
"""Bind native exports to exact source, then package with licenses and checksums."""
import argparse
import datetime
import hashlib
import json
import pathlib
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDS = ROOT / "builds"
VERSION = "0.3.0-dev"
BUILD_NUMBER = 3
IOS_VERSION = "0.3.0"
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
    return {"source_commit": git("rev-parse", "HEAD"), "source_game_tree": git("rev-parse", "HEAD:game"),
            "source_content_sha256": digest.hexdigest(), "source_game_dirty": bool(git("status", "--porcelain", "--", "game"))}


def descriptor(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.relative_to(BUILDS).as_posix(), "bytes": path.stat().st_size,
            "sha256": digest}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def payload(target):
    return [descriptor(path) for path in sorted((BUILDS / target).rglob("*"))
            if path.is_file() and path.name != "source.json" and path.suffix != ".log"]


def begin(target):
    directory = BUILDS / target
    directory.mkdir(parents=True, exist_ok=True)
    data = source()
    data.update({"target": target, "export_completed": False,
                 "built_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write_json(directory / "source.json", data)


def finish(target):
    path = BUILDS / target / "source.json"
    data = json.loads(path.read_text())
    if data["source_content_sha256"] != source()["source_content_sha256"]:
        raise SystemExit("Game source changed during export; rebuild before packaging.")
    output = BUILDS / OUTPUTS[target]
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"Missing export output: {output}")
    data.update({"export_completed": True, "artifact": descriptor(output), "payload": payload(target)})
    write_json(path, data)


def package():
    current = source()
    if current["source_game_dirty"]:
        raise SystemExit("Commit game source before producing delivery packages.")
    records = []
    artifacts = []
    for target in OUTPUTS:
        directory = BUILDS / target
        record = json.loads((directory / "source.json").read_text())
        if (not record["export_completed"] or record["source_game_dirty"]
                or record["source_game_tree"] != current["source_game_tree"]
                or record["source_content_sha256"] != current["source_content_sha256"]):
            raise SystemExit(f"Stale or incomplete {target} export; rebuild all targets from current source.")
        if descriptor(BUILDS / OUTPUTS[target]) != record["artifact"] or payload(target) != record["payload"]:
            raise SystemExit(f"Changed {target} artifact; rebuild before packaging.")
        records.append(record)
        if target != "ios":
            artifacts.append(record["artifact"])
        archive = BUILDS / f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.suffix == ".log":
                    continue
                info = zipfile.ZipInfo(path.relative_to(BUILDS).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.external_attr = (0o100755 if path.name == "sightbreak.x86_64" else 0o100644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes(), compresslevel=1)
        artifacts.append(descriptor(archive))
    manifest = {"game": "SIGHTBREAK", "version": VERSION, "engine": "Godot 4.7.2", "build_type": "debug",
                **current, "exports": records, "artifacts": artifacts,
                "limitations": ["Android debug signed; physical device installation and performance unverified.",
                                "iOS unsigned Xcode project; macOS/Xcode compilation and signing unverified.",
                                "See docs/reports/COMBINED_INTEGRATION_REPORT.md and CODEX_NETWORK_QA.md for measured results and open gates."]}
    write_json(BUILDS / "manifest.json", manifest)
    (BUILDS / "checksums.txt").write_text("".join(f"{a['sha256']}  {a['path']}\n" for a in artifacts))
    print(json.dumps(manifest, indent=2))


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
