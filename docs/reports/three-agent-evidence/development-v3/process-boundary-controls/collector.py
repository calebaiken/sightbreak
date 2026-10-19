"""Archive completed synthetic attempts without executing or altering originals."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

TEMP = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
ROOT = TEMP / "sightbreak-v3"
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/process-boundary-controls"
ATTEMPTS = {
    "critic-original": TEMP / "critic-current-20261019T191820649592Z",
    "critic-controller-recheck": TEMP / "critic-after-controller-20261019T193151501897Z",
    "matrix-descendant": TEMP / "matrix-descendant-20261019T1926379212688Z",
    "export-flow-descendant": TEMP / "export-flow-descendant-20261019T1939301091253Z",
    "verifier-descendant": TEMP / "verifier-descendant-20261019-154834-904",
    "campaign-descendant": TEMP / "sightbreak-v3-evidence/campaign-containment-20261019T194928Z",
    "final-serial-units": TEMP / "sightbreak-v3-evidence/final-tooling-serial-20261019T195617Z",
}
raw = OUT / "raw"
if raw.exists() or (OUT / "COLLECTION.json").exists():
    raise SystemExit("Refuse to replace prior archival evidence")
inventory = []
omitted = []
for label, directory in ATTEMPTS.items():
    if not directory.is_dir():
        raise FileNotFoundError(directory)
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            omitted.append({"origin": str(path), "reason": "generated Python bytecode"})
            continue
        if path.is_symlink():
            raise RuntimeError(f"Unexpected link: {path}")
        data = path.read_bytes()
        inventory.append((path, Path("raw") / label / relative, data))
total = sum(len(data) for _, _, data in inventory)
if total > 12 * 1024 * 1024:
    raise SystemExit(f"Archive needs an explicit smaller selection: {total} bytes")
rows = []
for origin, relative, data in inventory:
    destination = OUT / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as stream:
        stream.write(data)
    rows.append({"origin": str(origin), "published": relative.as_posix(),
                 "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
(OUT / "COLLECTION.json").write_text(json.dumps({
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Byte-identical archival copies; no control execution or native validation",
    "copied_files": len(rows), "copied_bytes": total, "files": rows,
    "omitted": omitted,
}, indent=2) + "\n", encoding="utf-8")
(OUT / "collector.py").write_bytes(Path(__file__).read_bytes())
checks = []
for path in sorted(OUT.rglob("*")):
    if path.is_file() and path.name != "SHA256SUMS.txt":
        checks.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(OUT).as_posix()}")
(OUT / "SHA256SUMS.txt").write_text("\n".join(checks) + "\n", encoding="utf-8")
print(json.dumps({"output": str(OUT), "copied_files": len(rows), "copied_bytes": total,
                  "omitted_generated_files": len(omitted)}, indent=2))
