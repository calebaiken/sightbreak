"""Archive completed tooling attempts without re-executing or relabelling them."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

TEMP = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
ROOT = TEMP / "sightbreak-v3"
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/pre-freeze-tooling-review"
SELECTIONS = [
    ("serial-attempts", TEMP / "sightbreak-v3-evidence/pre-freeze-tooling-20261019", True),
    ("final-cleanup", TEMP / "final-cleanup-20261019T2006528479460Z", True),
    ("audio-source-critic", TEMP / "sightbreak-audio-critic-20261019T200840532200Z", False),
    ("audio-harness-attempts", TEMP / "negative-audio-harness-20261019T195154884107Z", False),
    ("ci-source-critic", TEMP / "sol-final-ci-critic-20261019T195638920772Z", False),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise SystemExit("Refusing to reuse publication directory")
    entries = []
    for label, source, recursive in SELECTIONS:
        paths = sorted(source.rglob("*") if recursive else source.iterdir())
        for path in paths:
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise SystemExit("Symlink outside this archive contract: " + str(path))
            entries.append((path, Path("raw") / label / path.relative_to(source)))
    total = sum(path.stat().st_size for path, _ in entries)
    if total > 5 * 1024 * 1024:
        raise SystemExit("Selected evidence exceeds the five MiB publication cap")
    OUT.mkdir(parents=True)
    inventory = []
    for original, relative in entries:
        destination = OUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, destination)
        if digest(original) != digest(destination):
            raise SystemExit("Archive byte mismatch: " + str(original))
        inventory.append({"origin": str(original), "path": relative.as_posix(),
                          "bytes": destination.stat().st_size, "sha256": digest(destination)})
    report_path = TEMP / "sightbreak-v3-evidence/pre-freeze-tooling-20261019/attempt-20261019T201340147085Z/results.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    mismatches = [relative for relative, expected in report["source_after"].items()
                  if digest(ROOT / relative) != expected]
    collection = {"collected_at_utc": datetime.now(timezone.utc).isoformat(),
                  "scope": "Byte-for-byte archival only; no native or unit re-execution",
                  "payload_files": len(inventory), "payload_bytes": total, "files": inventory,
                  "latest_serial_source_hash_mismatches_at_collection": mismatches,
                  "omissions": [
                      "Audio critic/harness and CI critic selections include regular root files only; nested synthetic fixtures remain in their unchanged external directories.",
                      "Generated Python caches are omitted. Unittest temporary fixtures already removed by their tests are not reconstructed.",
                      "Native execution, actual Linux containment, exported-client behavior and physical-device gates are not established by this collection."]}
    (OUT / "COLLECTION.json").write_text(json.dumps(collection, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(Path(__file__), OUT / "collector.py")
    (OUT / ".gitattributes").write_text("raw/** -text\n", encoding="utf-8")
    (OUT / ".gitignore").write_text("!raw/**\n", encoding="utf-8")
    (OUT / "README.md").write_text("""# Final pre-freeze tooling review receipts

These are **pre-freeze pure/synthetic controls and source reviews**, not native
matrix/campaign, audio acceptance, export or device results. Original attempts
remain unchanged at the origins recorded in `COLLECTION.json`.

- The first serial attempt (`201117`) failed two OCR checks after Windows
  standalone dead-root cleanup became truthfully unverified. It is retained.
- The OCR path was moved into the shared prelaunch containment boundary, using
  a streaming I/O worker. Its new actual-CPython late-descendant control rejects
  a root exit of zero while stopping the descendant; it is not a game run.
- The fresh `201340` serial attempt has **272 normal tests plus 74 optimized
  artifact-verifier executions**, all actual exits zero, with unchanged source
  hashes before/after. Both raw logs and the previous failed batch are included.
- Final cleanup controls contain **17 process plus 60 harness/source/campaign
  tests**. Exceptional Linux supervisor death may still leave detached children
  reparented elsewhere. Missing cleanup attestation is a failure, not proof of
  durable recovery; no broad unrelated-process scan/kill was introduced.
- The audio source critic ran **32 maintained tests plus nine guarded probes**
  and found no verified scoped false-pass blocker. It did **not** execute Godot.
  The native broad baseline and A5/A6/A7 captures must still run on frozen source.

Only regular root files from audio/CI critique directories are selected to avoid
republishing hundreds of synthetic fixture artifacts. Their original manifests,
failures and source hashes are retained; omissions are explicit in the collection.
The collection-time source comparison is a later read-only witness, not a new
test execution or a retroactive change to the October 19 receipts.

`SHA256SUMS.txt` covers every published file except itself. Raw bytes are protected
from Git newline conversion. No human, physical-device, production or 8.5 gate is
waived by a tooling assertion count.
""", encoding="utf-8")
    ledger = "".join(digest(path) + "  " + path.relative_to(OUT).as_posix() + "\n"
                     for path in sorted(OUT.rglob("*")) if path.is_file())
    (OUT / "SHA256SUMS.txt").write_text(ledger, encoding="utf-8")
    print(json.dumps({"publication": str(OUT), "raw_files": len(inventory), "raw_bytes": total,
                      "source_hash_mismatches": mismatches}, indent=2))
    return bool(mismatches)


if __name__ == "__main__":
    raise SystemExit(main())
