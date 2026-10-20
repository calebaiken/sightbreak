#!/usr/bin/env python3
"""Bind native exports to exact source, then package with licenses and checksums."""
import argparse
import datetime
import configparser
import hashlib
import json
import os
import stat
import pathlib
import subprocess
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDS = pathlib.Path(os.environ.get("SIGHTBREAK_BUILDS_DIR", ROOT / "builds")).resolve()
VERSION = "0.3.2-dev"
BUILD_NUMBER = 5
IOS_VERSION = "0.3.2"
OUTPUTS = {"linux": "linux/sightbreak.x86_64", "android": "android/sightbreak-debug.apk", "ios": "ios/sightbreak.xcodeproj/project.pbxproj",
           "windows": "windows/SIGHTBREAK.exe", "macos": "macos/SIGHTBREAK.app/Contents/MacOS/SIGHTBREAK"}
LEGACY_TARGETS = ("linux", "android", "ios")
IDENTITY = ("source_commit", "source_game_tree", "source_content_sha256", "source_validation_sha256")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def validate_versions():
    presets = configparser.ConfigParser(interpolation=None)
    presets.read(ROOT / "game/export_presets.cfg", encoding="utf-8")
    project = configparser.ConfigParser(interpolation=None)
    project.read_string("[root]\n" + (ROOT / "game/project.godot").read_text(encoding="utf-8"))
    expected = [(project["application"]["config/version"], f'"{VERSION}"'),
                (presets["preset.1.options"]["version/name"], f'"{VERSION}"'),
                (presets["preset.1.options"]["version/code"], str(BUILD_NUMBER)),
                (presets["preset.2.options"]["application/short_version"], f'"{IOS_VERSION}"'),
                (presets["preset.2.options"]["application/version"], f'"{BUILD_NUMBER}"'),
                (presets["preset.3.options"]["application/file_version"], f'"{IOS_VERSION}.{BUILD_NUMBER}"'),
                (presets["preset.3.options"]["application/product_version"], f'"{IOS_VERSION}.{BUILD_NUMBER}"'),
                (presets["preset.4.options"]["application/short_version"], f'"{IOS_VERSION}"'),
                (presets["preset.4.options"]["application/version"], f'"{BUILD_NUMBER}"')]
    if any(actual != wanted for actual, wanted in expected):
        raise SystemExit("Application/export versions disagree with build metadata.")


def source():
    validate_versions()
    digest = hashlib.sha256()
    for path in sorted((ROOT / "game").rglob("*")):
        relative = path.relative_to(ROOT / "game")
        if not path.is_file() or ".godot" in relative.parts or "tests" in relative.parts:
            continue
        digest.update(relative.as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    validation = hashlib.sha256()
    for directory in ("scripts", ".github", "game/tests"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and not any(part in ("__pycache__", ".godot") for part in path.parts) and path.suffix != ".pyc":
                validation.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return {"source_dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
            "source_validation_sha256": validation.hexdigest(), "source_commit": git("rev-parse", "HEAD"), "source_game_tree": git("rev-parse", "HEAD:game"),
            "source_content_sha256": digest.hexdigest(), "source_game_dirty": bool(git("status", "--porcelain", "--", "game"))}


def delivery_mode(path):
    if os.name != "nt":
        return stat.S_IMODE(path.stat().st_mode) & 0o777
    relative = path.relative_to(BUILDS)
    executable = path.name in ("sightbreak.x86_64", "sightbreak.sh", "SIGHTBREAK.command") or (relative.parts[0] == "macos" and "MacOS" in relative.parts)
    return 0o755 if executable else 0o644


def descriptor(path):
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"path": path.relative_to(BUILDS).as_posix(), "bytes": path.stat().st_size,
            "sha256": digest, "mode": stat.S_IMODE(path.stat().st_mode), "archive_mode": delivery_mode(path)}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def payload(target):
    records = []
    for path in sorted((BUILDS / target).rglob("*")):
        relative = path.relative_to(BUILDS / target)
        if path.is_symlink():
            raise SystemExit(f"Symlink in export: {relative}")
        if not path.is_file() or relative.as_posix() == "source.json" or path.suffix == ".log":
            continue
        if any(part in ("tests", ".godot", "__pycache__", ".git") or part.startswith(".env") for part in relative.parts):
            raise SystemExit(f"Developer-only file in export: {relative}")
        catalog_json = target == "ios" and relative.as_posix() in (
            "sightbreak/Images.xcassets/AppIcon.appiconset/Contents.json",
            "sightbreak/Images.xcassets/SplashImage.imageset/Contents.json")
        if (path.suffix.lower() == ".json" and not catalog_json) or path.suffix.lower() in (".py", ".pyc", ".gd", ".gdc", ".ts", ".js", ".pem", ".key", ".p12", ".pfx", ".keystore") or any(word in path.name.lower() for word in ("credential", "secret", "private_key", "steam_appid")):
            raise SystemExit(f"Developer/credential file in export: {relative}")
        if target in ("linux", "windows", "android"):
            allowed = {pathlib.Path(OUTPUTS[target]).name, "GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"}
            allowed.update({"sightbreak.sh"} if target == "linux" else {"SIGHTBREAK.console.exe"} if target == "windows" else set())
            if relative.as_posix() not in allowed:
                raise SystemExit(f"Unexpected {target} payload: {relative}")
        if target == "macos" and relative.parts[0] not in ("SIGHTBREAK.app", "GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt", "SIGHTBREAK.command"):
            raise SystemExit(f"Unexpected macOS payload: {relative}")
        records.append(descriptor(path))
    return records


def clean(current):
    if current.get("source_dirty") or current["source_game_dirty"]:
        raise SystemExit("Commit game source and validation changes before exporting or packaging.")


def same_source(record, current):
    return all(record.get(key) == current.get(key) for key in IDENTITY)


def validate_record(target, current=None):
    current = current or source()
    clean(current)
    record = json.loads((BUILDS / target / "source.json").read_text())
    if (record.get("target") != target or record.get("version") != VERSION or record.get("build_number") != BUILD_NUMBER or not record.get("export_completed")
            or record.get("source_game_dirty") or record.get("source_dirty") or not same_source(record, current)):
        raise SystemExit(f"Stale or incomplete {target} export; rebuild from the exact current commit.")
    if descriptor(BUILDS / OUTPUTS[target]) != record["artifact"] or payload(target) != record["payload"]:
        raise SystemExit(f"Changed {target} artifact; rebuild before packaging.")
    return record


def begin(target):
    directory = BUILDS / target
    data = source()
    clean(data)
    if directory.exists() and any(directory.iterdir()):
        raise SystemExit(f"Existing {target} output; use a fresh SIGHTBREAK_BUILDS_DIR and preserve the earlier attempt.")
    directory.mkdir(parents=True, exist_ok=True)
    data.update({"target": target, "version": VERSION, "build_number": BUILD_NUMBER, "export_completed": False,
                 "built_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write_json(directory / "source.json", data)


def finish(target):
    path = BUILDS / target / "source.json"
    data = json.loads(path.read_text())
    current = source()
    if not same_source(data, current) or current.get("source_dirty", current["source_game_dirty"]):
        raise SystemExit("Game source changed during export; rebuild before packaging.")
    if data["export_completed"]:
        raise SystemExit("Export already attested; use a new build directory.")
    output = BUILDS / OUTPUTS[target]
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"Missing export output: {output}")
    data.update({"export_completed": True, "artifact": descriptor(output), "payload": payload(target)})
    write_json(path, data)


def package(targets=None):
    current = source()
    clean(current)
    targets = list(LEGACY_TARGETS if targets is None else targets)
    if not targets or len(targets) != len(set(targets)) or any(t not in OUTPUTS for t in targets):
        raise SystemExit("Select distinct valid export targets.")
    if (BUILDS / "manifest.json").exists() or (BUILDS / "checksums.txt").exists():
        raise SystemExit("Existing package manifest; preserve earlier packages and use a new build directory.")
    records = [validate_record(target, current) for target in targets]
    archives = [BUILDS / f"sightbreak-{target}-{'xcode-project' if target == 'ios' else 'debug'}.zip" for target in targets]
    if any(path.exists() for path in archives):
        raise SystemExit("Existing package archive; refusing to overwrite evidence.")
    artifacts = []
    for target, record, archive in zip(targets, records, archives):
        directory = BUILDS / target
        if target != "ios":
            artifacts.append(record["artifact"])
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as bundle:
            for path in sorted(directory.rglob("*")):
                if not path.is_file() or path.suffix == ".log":
                    continue
                info = zipfile.ZipInfo(path.relative_to(BUILDS).as_posix(), (2026, 1, 1, 0, 0, 0))
                # Receipt records both physical and delivery mode on non-POSIX hosts.
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | delivery_mode(path)) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                bundle.writestr(info, path.read_bytes(), compresslevel=1)
        validate_record(target, current)
        artifacts.append(descriptor(archive))
    clean(source())
    if not same_source(current, source()):
        raise SystemExit("Source changed during packaging.")
    manifest = {"targets": targets, "game": "SIGHTBREAK", "version": VERSION, "engine": "Godot 4.7.2", "build_type": "debug",
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
    parser.add_argument("--targets", nargs="+", choices=OUTPUTS, help="Package only these targets (default preserves Linux/Android/iOS).")
    arguments = parser.parse_args()
    if arguments.action == "package":
        package(arguments.targets)
    elif arguments.target:
        (begin if arguments.action == "begin" else finish)(arguments.target)
    else:
        parser.error("begin/finish require a target")
