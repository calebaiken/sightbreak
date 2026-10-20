#!/usr/bin/env python3
"""Export one native development target; retain failed attempts without re-attesting."""
import argparse
import json
import platform
import shutil
import subprocess
import sys
import time

from build_manifest import ROOT, BUILDS, OUTPUTS, begin, finish, write_json
from native_log import failed
import toolchain

PRESETS = {"linux": "Linux", "windows": "Windows", "macos": "macOS", "android": "Android"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=OUTPUTS)
    args = parser.parse_args()
    engine = toolchain.verify_engine()
    if args.target == "ios":
        # The separate project-only exporter preserves the unsigned iOS contract.
        return subprocess.call([sys.executable, str(ROOT / "scripts/export_ios.py")])
    target = args.target
    begin(target)
    output = BUILDS / OUTPUTS[target]
    if target != "macos":
        output.parent.mkdir(parents=True, exist_ok=True)
    destination = output.parents[2] if target == "macos" else output
    directory = BUILDS / target
    commands = []
    try:
        for label, arguments in (("import", ["--editor", "--import", "--quit"]),
                                 ("export", ["--export-debug", PRESETS[target], str(destination)])):
            command = toolchain.command("--headless", *arguments)
            started = time.monotonic()
            # File redirection bounds RAM and retains output even if the engine times out.
            with (directory / f"{label}.log").open("w", encoding="utf-8") as log:
                result = subprocess.run(command, env=toolchain.environment(), stdout=log, stderr=subprocess.STDOUT, timeout=600)
            commands.append({"command": command, "exit_code": result.returncode, "seconds": time.monotonic() - started})
            if result.returncode or failed((directory / f"{label}.log").read_text(encoding="utf-8", errors="replace")):
                raise RuntimeError(f"{target} {label} failed; see {directory}")
        if target == "linux":
            output.chmod(0o755)
            wrapper = directory / "sightbreak.sh"
            if wrapper.exists():
                wrapper.chmod(0o755)
        elif target == "macos":
            for path in (directory / "SIGHTBREAK.app/Contents/MacOS").iterdir():
                if path.is_file():
                    path.chmod(0o755)
        for name in ("GODOT-LICENSE.txt", "GODOT-COPYRIGHT.txt"):
            shutil.copy2(ROOT / "docs" / name, directory / name)
        finish(target)
    finally:
        write_json(directory / "export-run.json.log", {"engine": engine, "host": platform.platform(), "commands": commands})
    print(f"Exported {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
