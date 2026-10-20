#!/usr/bin/env python3
"""Inspect actual native artifacts; does not substitute for mobile device testing."""
import argparse
import json
import platform
import os
import pathlib
import plistlib
import re
import struct
import subprocess
import zipfile

from native_log import failed as native_log_failed
from build_manifest import BUILDS, ROOT, OUTPUTS, VERSION, BUILD_NUMBER, IOS_VERSION, payload, source, write_json, validate_record, clean, LEGACY_TARGETS


def packed_paths(path, embedded=False):
    with path.open("rb") as stream:
        start = 0
        if embedded:
            stream.seek(-12, 2)
            size, magic = struct.unpack("<QI", stream.read(12))
            require(magic == 0x43504447, "Missing embedded Godot pack trailer")
            stream.seek(-12-size, 2)
            start = stream.tell()
        magic, version, major, minor, patch, flags, base = struct.unpack("<6IQ", stream.read(32))
        require(magic == 0x43504447 and version in (3, 4), "Unexpected pack header")
        require(not flags & 1, "Encrypted pack directory is not inspected by this check")
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
    require(paths, "Artifact contains no resources")
    require(not any("tests/" in path or "_test.gdc" in path for path in paths), "Test harness shipped in artifact")


def integrated_resources(paths):
    """Check imported payloads, not just GLB references or source filenames."""
    for basename in ("relay_ar.glb-", "relay_ar_arms.glb-", "relay_ar_hands.glb-"):
        require(any(basename in path and path.endswith('.scn') for path in paths), f"Missing imported scene: {basename}")
    for basename in ("relay_ar_albedo.png-", "relay_ar_normal.png-", "relay_ar_orm.png-",
                     "relay_ar_arms_albedo.png-", "relay_ar_arms_normal.png-", "relay_ar_arms_orm.png-"):
        require(any(basename in path and path.endswith('.ctex') for path in paths), f"Missing imported texture: {basename}")
    for basename in ("state_privacy", "snapshot_buffer", "movement_prediction", "movement_step", "peer_lifecycle", "reconnect_policy", "result_outbox", "viewmodel_shading", "bot_ai", "reload_audio", "reload_phases", "confirm_sheet"):
        require(any(path.endswith('/' + basename + '.gdc') for path in paths), f"Missing compiled module: {basename}")


def require(condition, message="Artifact validation failed"):
    if not condition:
        raise RuntimeError(message)


def desktop_resources(target):
    executable = BUILDS / OUTPUTS[target]
    if target == "linux":
        with executable.open("rb") as stream:
            header = stream.read(20)
        require(header[:5] == b"\x7fELF\x02" and struct.unpack_from("<H", header, 18)[0] == 62, "Linux export must be x86_64 ELF")
        require(os.name == "nt" or executable.stat().st_mode & 0o111, "Linux executable permissions missing")
        paths = packed_paths(executable, embedded=True)
    elif target == "windows":
        with executable.open("rb") as stream:
            data = stream.read()
        require(data[:2] == b"MZ", "Missing Windows DOS header")
        pe = struct.unpack_from("<I", data, 0x3c)[0]
        require(data[pe:pe+4] == b"PE\0\0" and struct.unpack_from("<H", data, pe+4)[0] == 0x8664, "Windows export must be AMD64 PE")
        require("SIGHTBREAK".encode("utf-16-le") in data and f"{IOS_VERSION}.{BUILD_NUMBER}".encode("utf-16-le") in data, "Missing Windows product/version resources")
        # Resolve the PE resource directory and require icon, group-icon and version types.
        optional = pe + 24
        require(struct.unpack_from("<H", data, optional)[0] == 0x20b, "Expected PE32+")
        resource_rva = struct.unpack_from("<I", data, optional + 112 + 16)[0]
        sections = struct.unpack_from("<H", data, pe+6)[0]
        section_offset = optional + struct.unpack_from("<H", data, pe+20)[0]
        resource_offset = None
        for index in range(sections):
            section = section_offset + index * 40
            size, address, raw_size, raw = struct.unpack_from("<IIII", data, section+8)
            if address <= resource_rva < address + max(size, raw_size):
                resource_offset = raw + resource_rva - address
        require(resource_offset is not None, "Missing Windows resource section")
        named, ids = struct.unpack_from("<HH", data, resource_offset+12)
        types = {struct.unpack_from("<I", data, resource_offset+16+8*i)[0] for i in range(named+ids)}
        require({3, 14, 16}.issubset(types), "Windows icon/version resources missing")
        paths = packed_paths(executable, embedded=True)
    else:
        app = BUILDS / "macos/SIGHTBREAK.app/Contents"
        with (app / "Info.plist").open("rb") as stream:
            plist = plistlib.load(stream)
        require(plist["CFBundleIdentifier"] == "com.sightbreak.game", "Wrong macOS bundle ID")
        require(plist["CFBundleExecutable"] == "SIGHTBREAK", "Wrong macOS executable")
        require(plist["CFBundleShortVersionString"] == IOS_VERSION and str(plist["CFBundleVersion"]) == str(BUILD_NUMBER), "Wrong macOS version")
        require((app / "Resources" / plist["CFBundleIconFile"]).is_file(), "Missing macOS app icon")
        with executable.open("rb") as stream:
            header = stream.read(4096)
        require(header[:4] == b"\xca\xfe\xba\xbe", "Expected Universal 2 Mach-O")
        count = struct.unpack_from(">I", header, 4)[0]
        architectures = {struct.unpack_from(">I", header, 8+20*i)[0] for i in range(count)}
        require(architectures == {0x01000007, 0x0100000c}, "macOS must contain x86_64 and arm64")
        require(os.name == "nt" or executable.stat().st_mode & 0o111, "macOS executable permissions missing")
        paths = packed_paths(app / "Resources/SIGHTBREAK.pck")
    no_test_harnesses(paths)
    integrated_resources(paths)
    return len(paths)


def main(targets=None, graphical=False):
    targets = list(LEGACY_TARGETS if targets is None else targets)
    build_source = source()
    clean(build_source)
    for target in targets:
        validate_record(target, build_source)
    logs = BUILDS / "verification"
    logs.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    if platform.system() == "Linux":
        for variable, suffix in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
            environment[variable] = str(logs / "state" / suffix)
            (logs / "state" / suffix).mkdir(parents=True, exist_ok=True)

    runs = []

    def run(label, command):
        try:
            with (logs / f"{label}.log").open("w", encoding="utf-8") as stream:
                result = subprocess.run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
        except subprocess.TimeoutExpired:
            runs.append({"label": label, "command": command, "exit_code": None, "status": "TIMEOUT"})
            print((logs / f"{label}.log").read_text(encoding="utf-8", errors="replace")[-16000:], flush=True)
            raise
        output = (logs / f"{label}.log").read_text(encoding="utf-8", errors="replace")
        runs.append({"label": label, "command": command, "exit_code": result.returncode, "clean_log": not native_log_failed(output)})
        if result.returncode or native_log_failed(output):
            print(output[-16000:], flush=True)
        require(result.returncode == 0, f"{label} failed (exit {result.returncode}); see {logs}")
        require(not native_log_failed(output), f"{label} emitted error; see {logs}")
        return output

    results = {}
    native_host = {"Linux": "linux", "Windows": "windows", "Darwin": "macos"}.get(platform.system())
    for target in targets:
        result = {"artifact_inspection": False, "native_execution": "UNVERIFIED"}
        results[target] = result
        try:
            if target in ("linux", "windows", "macos"):
                result["pck_resources"] = desktop_resources(target)
                if target == native_host:
                    executable = str(BUILDS / OUTPUTS[target])
                    menu = run(target+"-menu", [executable, "--headless", "--", "--smoke"])
                    require("SIGHTBREAK_MAIN_READY screen=menu" in menu, "Menu never became ready")
                    run(target+"-demo", [executable, "--headless", "--quit-after", "120", "--", "--demo"])
                    result["native_execution"] = "PASS (headless startup only)"
                    if graphical:
                        capture = logs / (target+"-menu.png")
                        menu = run(target+"-graphical-menu", [executable, "--audio-driver", "Dummy", "--", "--smoke", "--capture="+str(capture)])
                        require("SIGHTBREAK_MAIN_READY screen=menu" in menu and capture.is_file(), "Missing rendered menu")
                        result["native_graphical_menu"] = "PASS"
            elif target == "android":
                tools = pathlib.Path(os.environ.get("SIGHTBREAK_TOOLS_DIR", ROOT.parent / "tools"))
                sdk = pathlib.Path(os.environ.get("ANDROID_SDK_ROOT", tools / "android-sdk"))
                android_tools = sdk / "build-tools/36.0.0"
                apk = str(BUILDS / "android/sightbreak-debug.apk")
                signature = run("android-signature", [str(android_tools / "apksigner"), "verify", "--verbose", "--print-certs", apk])
                require("Verified using v2 scheme (APK Signature Scheme v2): true" in signature, "Artifact validation failed")
                require("Verified using v3 scheme (APK Signature Scheme v3): true" in signature, "Artifact validation failed")
                badging = run("android-manifest", [str(android_tools / "aapt"), "dump", "badging", apk])
                for expected in ["package: name='com.sightbreak.game'", f"versionCode='{BUILD_NUMBER}'", f"versionName='{VERSION}'", "sdkVersion:'24'", "targetSdkVersion:'36'", "'arm64-v8a'", "'x86_64'"]:
                    require(expected in badging, f"Missing APK metadata: {expected}")
                android_manifest = run("android-layout", [str(android_tools / "aapt"), "dump", "xmltree", apk, "AndroidManifest.xml"])
                require(re.search(r"android:screenOrientation[^\n]*\(type 0x10\)0x0\b", android_manifest), "Android landscape orientation missing")
                launcher_alias = android_manifest.split("E: activity-alias", 1)[1].split("E: meta-data", 1)[0]
                require('"com.godot.game.GodotAppLauncher"' in launcher_alias, "Artifact validation failed")
                require('"com.godot.game.GodotApp"' in launcher_alias, "Artifact validation failed")
                require(re.search(r"android:exported[^\n]*0xffffffff", launcher_alias), "Launcher alias must be exported")
                require('"android.intent.action.MAIN"' in launcher_alias and '"android.intent.category.LAUNCHER"' in launcher_alias, "Artifact validation failed")
                with zipfile.ZipFile(apk) as archive:
                    android_paths = [name for name in archive.namelist() if name.startswith("assets/")]
                no_test_harnesses(android_paths)
                integrated_resources(android_paths)
                result.update({"assets": len(android_paths), "debug_signature": ["v2", "v3"], "physical_device": "UNVERIFIED"})
            elif target == "ios":
                ios = BUILDS / "ios"
                ios_paths = packed_paths(ios / "sightbreak.pck")
                no_test_harnesses(ios_paths)
                integrated_resources(ios_paths)
                with (ios / "sightbreak/sightbreak-Info.plist").open("rb") as stream:
                    plist = plistlib.load(stream)
                require(plist["CFBundleIdentifier"] == "$(PRODUCT_BUNDLE_IDENTIFIER)", "Artifact validation failed")
                require(plist["NSLocalNetworkUsageDescription"], "Artifact validation failed")
                require(plist["UISupportedInterfaceOrientations"], "Artifact validation failed")
                require(all("Landscape" in value for value in plist["UISupportedInterfaceOrientations"]), "Artifact validation failed")
                project = (ios / "sightbreak.xcodeproj/project.pbxproj").read_text()
                require("UNSIGNED00" not in project and 'DEVELOPMENT_TEAM = "";' in project, "Artifact validation failed")
                require("PRODUCT_BUNDLE_IDENTIFIER = com.sightbreak.game;" in project, "Artifact validation failed")
                require(f"MARKETING_VERSION = {IOS_VERSION};" in project, "Wrong iOS marketing version")
                require(f"CURRENT_PROJECT_VERSION = {BUILD_NUMBER};" in project, "Wrong iOS build number")
                result.update({"pck_resources": len(ios_paths), "xcode_build": "UNVERIFIED", "physical_device": "UNVERIFIED"})
            result["artifact_inspection"] = True
            validate_record(target, build_source)
        finally:
            write_json(logs / "results.json", {**build_source, "host": platform.platform(), "targets": results, "runs": runs, "gameplay": "See separate real-input evidence; startup is not gameplay acceptance."})
    require(source() == build_source, "Source changed during verification")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", nargs="+", choices=OUTPUTS)
    parser.add_argument("--graphical", action="store_true", help="Also require a rendered menu on the matching native host")
    args = parser.parse_args()
    main(args.targets, args.graphical)
