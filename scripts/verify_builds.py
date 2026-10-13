#!/usr/bin/env python3
"""Inspect actual native artifacts; does not substitute for mobile device testing."""
import json
import os
import pathlib
import plistlib
import re
import struct
import subprocess
import zipfile

from build_manifest import BUILDS, ROOT, OUTPUTS, VERSION, BUILD_NUMBER, IOS_VERSION, payload, source, write_json


def packed_paths(path, embedded=False):
    with path.open("rb") as stream:
        start = 0
        if embedded:
            stream.seek(-12, 2)
            size, magic = struct.unpack("<QI", stream.read(12))
            assert magic == 0x43504447, "Missing embedded Godot pack trailer"
            stream.seek(-12-size, 2)
            start = stream.tell()
        magic, version, major, minor, patch, flags, base = struct.unpack("<6IQ", stream.read(32))
        assert magic == 0x43504447 and version in (3, 4), "Unexpected pack header"
        assert not flags & 1, "Encrypted pack directory is not inspected by this check"
        directory, = struct.unpack("<Q", stream.read(8))
        stream.seek(start + directory)
        count, = struct.unpack("<I", stream.read(4))
        paths = []
        for _ in range(count):
            size, = struct.unpack("<I", stream.read(4))
            paths.append(stream.read(size).rstrip(b"\0").decode())
            stream.seek(36, 1)
        return paths


def no_test_harnesses(paths):
    assert paths, "Artifact contains no resources"
    assert not any("tests/" in path or "_test.gdc" in path for path in paths), "Test harness shipped in artifact"


def main():
    build_source = source()
    assert not build_source["source_game_dirty"], "Commit game changes before artifact verification"
    for target in OUTPUTS:
        record = json.loads((BUILDS / target / "source.json").read_text())
        assert record["export_completed"] and not record["source_game_dirty"], f"{target}: incomplete or uncommitted export"
        assert record["source_game_tree"] == build_source["source_game_tree"], f"{target}: stale game tree"
        assert record["source_content_sha256"] == build_source["source_content_sha256"], f"{target}: stale source content"
        assert record["payload"] == payload(target), f"{target}: artifact changed after export"
    logs = BUILDS / "verification"
    logs.mkdir(exist_ok=True)
    environment = dict(os.environ)
    state = ROOT / ".local/export-smoke"
    for variable, suffix in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
        environment[variable] = str(state / suffix)
        (state / suffix).mkdir(parents=True, exist_ok=True)

    def run(label, command):
        result = subprocess.run(command, env=environment, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        (logs / f"{label}.log").write_text(result.stdout)
        assert result.returncode == 0, f"{label} failed; see {logs}"
        assert not re.search(r"^(?:SCRIPT ERROR|ERROR:)|Parse Error", result.stdout, re.M), f"{label} emitted error; see {logs}"
        return result.stdout

    executable = str(BUILDS / "linux/sightbreak.x86_64")
    menu = run("linux-menu", [executable, "--headless", "--", "--smoke"])
    assert "SIGHTBREAK_MAIN_READY screen=menu" in menu
    run("linux-demo", [executable, "--headless", "--quit-after", "120", "--", "--demo"])
    linux_paths = packed_paths(pathlib.Path(executable), embedded=True)
    no_test_harnesses(linux_paths)
    tools = pathlib.Path(os.environ.get("SIGHTBREAK_TOOLS_DIR", ROOT.parent / "tools"))
    sdk = pathlib.Path(os.environ.get("ANDROID_SDK_ROOT", tools / "android-sdk"))
    android_tools = sdk / "build-tools/36.0.0"
    apk = str(BUILDS / "android/sightbreak-debug.apk")
    signature = run("android-signature", [str(android_tools / "apksigner"), "verify", "--verbose", apk])
    assert "Verified using v2 scheme (APK Signature Scheme v2): true" in signature
    assert "Verified using v3 scheme (APK Signature Scheme v3): true" in signature
    badging = run("android-manifest", [str(android_tools / "aapt"), "dump", "badging", apk])
    for expected in [f"versionCode='{BUILD_NUMBER}'", f"versionName='{VERSION}'", "sdkVersion:'24'", "targetSdkVersion:'36'", "'arm64-v8a'", "'x86_64'"]:
        assert expected in badging, f"Missing APK metadata: {expected}"
    android_manifest = run("android-layout", [str(android_tools / "aapt"), "dump", "xmltree", apk, "AndroidManifest.xml"])
    assert re.search(r"android:screenOrientation[^\n]*\(type 0x10\)0x0\b", android_manifest), "Android landscape orientation missing"
    launcher_alias = android_manifest.split("E: activity-alias", 1)[1].split("E: meta-data", 1)[0]
    assert '"com.godot.game.GodotAppLauncher"' in launcher_alias
    assert '"com.godot.game.GodotApp"' in launcher_alias
    assert re.search(r"android:exported[^\n]*0xffffffff", launcher_alias), "Launcher alias must be exported"
    assert '"android.intent.action.MAIN"' in launcher_alias and '"android.intent.category.LAUNCHER"' in launcher_alias
    with zipfile.ZipFile(apk) as archive:
        android_paths = [name for name in archive.namelist() if name.startswith("assets/")]
    no_test_harnesses(android_paths)
    ios = BUILDS / "ios"
    ios_paths = packed_paths(ios / "sightbreak.pck")
    no_test_harnesses(ios_paths)
    with (ios / "sightbreak/sightbreak-Info.plist").open("rb") as stream:
        plist = plistlib.load(stream)
    assert plist["CFBundleIdentifier"] == "$(PRODUCT_BUNDLE_IDENTIFIER)"
    assert plist["NSLocalNetworkUsageDescription"]
    assert plist["UISupportedInterfaceOrientations"]
    assert all("Landscape" in value for value in plist["UISupportedInterfaceOrientations"])
    project = (ios / "sightbreak.xcodeproj/project.pbxproj").read_text()
    assert "UNSIGNED00" not in project and 'DEVELOPMENT_TEAM = "";' in project
    assert "PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;" in project
    assert f"MARKETING_VERSION = {IOS_VERSION};" in project, "Wrong iOS marketing version"
    assert f"CURRENT_PROJECT_VERSION = {BUILD_NUMBER};" in project, "Wrong iOS build number"
    assert source()["source_content_sha256"] == build_source["source_content_sha256"], "Game changed during verification"
    report = {**build_source, "passed": True, "linux_menu_smoke": True, "linux_demo_120_frames": True,
              "linux_pck_resources": len(linux_paths), "android_assets": len(android_paths), "ios_pck_resources": len(ios_paths),
              "test_harnesses_excluded": True, "android_signature_schemes": ["v2", "v3"],
              "android_version": f"{VERSION} ({BUILD_NUMBER})", "android_min_sdk": 24, "android_target_sdk": 36,
              "android_abis": ["arm64-v8a", "x86_64"], "android_landscape_manifest": True,
              "android_launcher_alias": "com.sightbreak.game/com.godot.game.GodotAppLauncher", "ios_project_plist_and_unsigned_team": True,
              "physical_device_installation": "NOT TESTED", "device_performance": "NOT TESTED", "xcode_build": "NOT TESTED"}
    write_json(logs / "results.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
