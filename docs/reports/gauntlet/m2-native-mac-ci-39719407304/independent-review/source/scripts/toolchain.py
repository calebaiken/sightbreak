#!/usr/bin/env python3
"""Pinned native editor/template setup and launch, using only Python's stdlib."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import subprocess
import struct
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.7.2"
ENGINE = "4.7.2.stable.official.ed1daf0bf"
TOOLS = Path(os.environ.get("SIGHTBREAK_TOOLS_DIR", ROOT.parent / "tools")).resolve()
INSTALL = TOOLS / f"godot-{VERSION}"
STATE = Path(os.environ.get("SIGHTBREAK_STATE_DIR", ROOT / ".local")).resolve()
EDITORS = {
    "linux": ("linux.x86_64", "Godot_v4.7.2-stable_linux.x86_64", "9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65"),
    "windows": ("win64.exe", "Godot_v4.7.2-stable_win64.exe", "83decd58fdf67b9d657958a1ae6bf1929c20785315a81effe245874cdc57acb709bf868e00778a96984338c1b29dafdb453c6847747694621c6ecf5da2259993"),
    "macos": ("macos.universal", "Godot.app/Contents/MacOS/Godot", "38aa16e5bba2083941fc5b3e54be0089bd4cc35e32415f5b9fd9a8a6a7b9818255d44532ea8ef94b5aef56c4b407c2d634fa4f657e4ebe681ebbf59b7bac69ca"),
}
TEMPLATES_SHA512 = "ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079"
TARGET_FILES = {
    "linux": ["linux_debug.x86_64", "linux_release.x86_64"],
    "windows": [f"windows_{kind}_x86_64{suffix}.exe" for kind in ("debug", "release") for suffix in ("", "_console")],
    "macos": ["macos.zip"], "android": ["android_debug.apk", "android_release.apk"], "ios": ["ios.zip"],
}


def host():
    name = {"Linux": "linux", "Windows": "windows", "Darwin": "macos"}.get(platform.system())
    if not name or (name != "macos" and platform.machine().lower() not in ("x86_64", "amd64")):
        raise SystemExit("Supported build hosts: Linux/Windows x86_64 or macOS Universal 2.")
    return name


def environment():
    env = dict(os.environ)
    # Godot uses native AppData/Library paths on Windows/macOS. Never substitute HOME.
    if host() == "linux":
        for key, part in (("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")):
            env[key] = str(STATE / part)
            (STATE / part).mkdir(parents=True, exist_ok=True)
    env["ANDROID_USER_HOME"] = str(STATE / "android")
    (STATE / "android").mkdir(parents=True, exist_ok=True)
    return env


def template_dir():
    name = host()
    if name == "linux":
        data = STATE / "data/godot"
    elif name == "windows":
        data = Path(os.environ["APPDATA"]) / "Godot"
    else:
        data = Path.home() / "Library/Application Support/Godot"
    return data / "export_templates" / f"{VERSION}.stable"


def binary():
    result = Path(os.environ.get("GODOT_BIN", INSTALL / EDITORS[host()][1])).resolve()
    if not result.is_file():
        raise SystemExit("Godot is missing; run python scripts/toolchain.py setup --targets <target>, or set GODOT_BIN.")
    return str(result)


def command(*args):
    return [binary(), "--path", str(ROOT / "game"), *args]


def verify_engine():
    result = subprocess.run([binary(), "--headless", "--version"], env=environment(), capture_output=True, text=True, timeout=30, check=True)
    if result.stdout.strip() != ENGINE:
        raise SystemExit(f"Expected {ENGINE}; got {result.stdout.strip()!r}")
    return result.stdout.strip()


def fetch(asset, destination, expected):
    if destination.is_file():
        with destination.open("rb") as stream:
            if hashlib.file_digest(stream, "sha512").hexdigest() == expected:
                return
    url = f"https://github.com/godotengine/godot/releases/download/{VERSION}-stable/{asset}"
    temporary = destination.with_suffix(destination.suffix + ".download")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as output:
        while block := response.read(1024 * 1024):
            output.write(block)
    with temporary.open("rb") as stream:
        if hashlib.file_digest(stream, "sha512").hexdigest() != expected:
            raise SystemExit(f"SHA512 mismatch: {temporary}; retained for diagnosis")
    temporary.replace(destination)


def extract(archive, destination, members=None, flatten=False):
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            if members is not None and info.filename not in members:
                continue
            path = destination / (Path(info.filename).name if flatten else info.filename)
            if not path.resolve().is_relative_to(destination.resolve()):
                raise SystemExit("Unsafe archive path")
            if info.is_dir():
                path.mkdir(parents=True, exist_ok=True)
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit("Unexpected template/editor symlink")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bundle.read(info))
            mode = (info.external_attr >> 16) & 0o777
            if mode:
                path.chmod(mode)


def setup(targets, editor_only=False):
    INSTALL.mkdir(parents=True, exist_ok=True)
    suffix, executable, digest = EDITORS[host()]
    archive = INSTALL / ("godot.zip" if host() == "linux" else f"godot-{host()}.zip")
    fetch(f"Godot_v{VERSION}-stable_{suffix}.zip", archive, digest)
    extract(archive, INSTALL)
    (INSTALL / executable).chmod(0o755)
    if not editor_only:
        templates = INSTALL / "templates.tpz"
        fetch(f"Godot_v{VERSION}-stable_export_templates.tpz", templates, TEMPLATES_SHA512)
        selected = ["templates/version.txt"] + ["templates/" + filename for target in targets for filename in TARGET_FILES[target]]
        extract(templates, template_dir(), selected, flatten=True)
        for filename in TARGET_FILES["linux"]:
            path = template_dir() / filename
            if path.exists():
                path.chmod(0o755)
    print(verify_engine())


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        argv, env = command(*sys.argv[2:]), environment()
        if os.name != "nt":
            os.execvpe(argv[0], argv, env)
        # Join a kill-on-close job BEFORE spawning. Children inherit membership,
        # so terminating this CLI cannot orphan the native Windows executable.
        import ctypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.restype = ctypes.c_void_p
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
        kernel.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        job = kernel.CreateJobObjectW(None, None)
        limits = ctypes.create_string_buffer(144)  # x64 JOBOBJECT_EXTENDED_LIMIT_INFORMATION
        struct.pack_into("<I", limits, 16, 0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not job or not kernel.SetInformationJobObject(job, 9, limits, len(limits)) or not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            result = subprocess.call(argv, env=env)
        except KeyboardInterrupt:
            result = 130
        # Keep the non-inheritable job handle open until process exit. This also
        # disposes any unexpected descendants after the main executable exits.
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(result)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup"])
    parser.add_argument("--editor-only", action="store_true")
    parser.add_argument("--targets", nargs="+", choices=TARGET_FILES, default=[host()])
    args = parser.parse_args()
    setup(args.targets, args.editor_only)


if __name__ == "__main__":
    main()
