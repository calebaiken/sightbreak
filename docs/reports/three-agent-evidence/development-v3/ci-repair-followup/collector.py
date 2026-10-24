"""Copy completed controls; never execute or rewrite historical attempts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

TEMP = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
ROOT = TEMP / "sightbreak-v3"
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/ci-repair-followup"
CAP = 4 * 1024 * 1024


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    if OUT.exists():
        raise SystemExit("Refusing to replace an existing publication")
    selected: list[tuple[str, Path, str]] = []
    omissions: list[dict] = []

    def tree(label: str, source: Path, excluded: set[str] | None = None) -> None:
        excluded = (excluded or set()) | {"__pycache__", ".git", ".godot", ".state", ".local"}
        for path in sorted(source.rglob("*")):
            if path.is_symlink():
                raise SystemExit(f"Symlink refused: {path}")
            if not path.is_file():
                continue
            relative = path.relative_to(source)
            if any(part in excluded for part in relative.parts):
                omissions.append({"origin": str(path), "bytes": path.stat().st_size,
                                  "reason": "Scratch/generated cache excluded, not new execution"})
                continue
            selected.append((label, path, relative.as_posix()))

    def file(label: str, path: Path, relative: str | None = None) -> None:
        if not path.is_file() or path.is_symlink():
            raise SystemExit(f"Missing regular input: {path}")
        selected.append((label, path, relative or path.name))

    tree("ci-repair-critic", TEMP / "sol-ci-repair-critic-20261024T085242Z", {"scratch"})
    tree("maintained-unit-controls", TEMP / "sightbreak-v3-evidence/ci-repair-20261024/units-20261024T085137184633Z")
    file("maintained-unit-controls", TEMP / "sightbreak-v3-evidence/ci-repair-20261024/run_unit_controls.py")
    tree("uid-import-completed", TEMP / "snapshot-uid-20261024/attempt-r2")
    tree("uid-import-blocked", TEMP / "snapshot-uid-20261024/attempt")
    file("uid-import-driver", TEMP / "snapshot-uid-20261024/generate.py")
    for name in ("results.json", "SHA512-SUMS.txt"):
        file("official-engine-reacquisition", TEMP / "engine-reacquire-20261024/attempt" / name)
    file("official-engine-reacquisition", TEMP / "engine-reacquire-20261024/restore.py")
    for name in ("audit.py", "index-before.json", "index-after.json"):
        file("sealed-packet-publication-audit", TEMP / "publication-audit-20261024" / name)
    total = sum(path.stat().st_size for _, path, _ in selected)
    if total > CAP:
        raise SystemExit(f"Publication cap exceeded: {total} > {CAP}")

    OUT.mkdir(parents=True)
    records = []
    for label, origin, relative in selected:
        data = origin.read_bytes()
        target = OUT / "raw" / label / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(data)
        if target.read_bytes() != data:
            raise SystemExit(f"Copied bytes changed: {target}")
        records.append({"origin": str(origin), "path": target.relative_to(OUT).as_posix(),
                        "bytes": len(data), "sha256": sha(data)})
    (OUT / "collector.py").write_bytes(Path(__file__).read_bytes())
    (OUT / "COLLECTOR_ATTEMPTS.md").write_bytes(Path(__file__).with_name("ATTEMPTS.md").read_bytes())
    (OUT / ".gitattributes").write_bytes(b"* -text -filter -ident -working-tree-encoding\n")
    (OUT / ".gitignore").write_bytes(b"!raw/**\n")
    (OUT / "COLLECTION.json").write_text(json.dumps({
        "scope": "Byte-preserving collection, not execution or candidate acceptance",
        "raw_files": len(records), "raw_bytes": total, "copies": records,
        "omissions": omissions,
        "external_only": ["Official engine ZIP and executables; hashes and published SHA512 retained",
                          "Generated Godot caches and critic scratch fixtures; see omissions"]
    }, indent=2) + "\n", encoding="utf-8")
    (OUT / "README.md").write_text("""# CI repair follow-up — not a candidate pass

The failed Linux source is `2a026e61cabee3c66334066d45e92eb3ec6c2641`, run
[39880125007](https://github.com/calebaiken/sightbreak/actions/runs/39880125007).
Its 82/83 matrix result and both failed exported flows remain failed. This
collection copies completed local controls; it does not rerun or replace them.

## Repairs awaiting a new frozen Linux run

- Isolate matrix Git mocks from Python's shared `subprocess` module. The old
  Linux error came from `platform.platform()` consuming the Git fixture.
- Create and synchronize X11 close atoms before starting the exported ELF,
  require its advertised delete protocol, then request normal window closure.
  No process-kill or frame-quit substitute can pass.
- Use ordinary offline Field Menu pauses during OCR inspection of the original
  live HUD frames. Require visible `FIELD MENU` and `Training is paused` text;
  resume actual play for reload. Positive health and ammunition conservation
  remain mandatory. This is an inspection-paused flow, not continuous play.

The local maintained suites run **19 matrix + 14 UI + 6 HUD + 28 export-flow
tests**, all actual exit zero. They are pure/synthetic controls, not Linux/X11
or exported-game passes. Read their raw logs and source hashes under
`raw/maintained-unit-controls/`.

The independent critic ran those 67 maintained tests, 26 synthetic controller
controls and four protocol/layout controls. Read **both**
[REPORT.md](raw/ci-repair-critic/REPORT.md) and
[SOURCE_DRIFT_ADDENDUM.md](raw/ci-repair-critic/SOURCE_DRIFT_ADDENDUM.md).
HEAD advanced from the backend slice to the additive snapshot slice while the
critic sealed its report. All 22 reviewed source hashes and reviewed working
tree state stayed unchanged; this is not an exact-new-commit frozen campaign.
The failed aggregate drift receipt is retained. Actual Linux pause rendering,
Xlib behavior and completion-driven normal exits remain to be checked.

## Engine and generated UID custody

The old local engine disappeared after a restart; blocked pre-launch attempts
are not passes. Official Godot 4.7.2 was reacquired, its ZIP checked against
the published SHA512 before extraction, and its executable SHA256 matches the
previously frozen engine. Binaries stay external; sums, metadata and collector
are copied here. The first UID attempt's failure is explicitly a transcription,
not invented native output. A new isolated **one-script** editor import completed
with matching source bytes, process receipt and engine log. It generated
`uid://bfcad5gtqd8rv`; this does not validate the whole game or its performance.

## Publication audit

The first index audit found 18 raw input-component logs missing because of the
root log-ignore rule. A narrow parent ignore exception preserves the sealed
packet bytes and ledger. The second audit checks all **761 payloads** in the
completed backend and input-component packets against physical and Git-index
bytes, with zero mismatches. Both audit attempts are retained.

`COLLECTION.json` lists exact origins, sizes, hashes and omissions.
`SHA256SUMS.txt` covers every published file except itself. Nothing in these
tooling controls waives human, device, production or per-category 8.5 gates.
""", encoding="utf-8")
    files = sorted(path for path in OUT.rglob("*") if path.is_file())
    (OUT / "SHA256SUMS.txt").write_text("".join(
        f"{sha(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n" for path in files
    ), encoding="utf-8")
    print(json.dumps({"published": str(OUT), "raw_files": len(records),
                      "raw_bytes": total, "ledger_payloads": len(files)}, indent=2))


if __name__ == "__main__":
    main()
