"""Archive completed local controls; never execute their programs or tests."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

TEMP = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
ROOT = TEMP / "sightbreak-v3"
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/retry-tooling-review"
SOURCES = [
    (TEMP / "sightbreak-v3-evidence/pre-freeze-tooling-20261019/attempt-20261024T091611731546Z", "serial"),
    (TEMP / "sightbreak-v3-evidence/backend-source-reconciliation-20261024", "backend-source-reconciliation"),
]
if OUT.exists():
    raise SystemExit("Refusing an existing publication directory")
selected = []
for source, label in SOURCES:
    for path in sorted(source.iterdir()):
        if path.is_symlink():
            raise SystemExit(f"Unexpected symbolic link: {path}")
        if path.is_file():
            selected.append((path, f"raw/{label}/{path.name}"))
selected.append((TEMP / "sightbreak-v3-evidence/pre-freeze-tooling-20261019/run.py", "raw/serial/run.py"))
if sum(path.stat().st_size for path, _ in selected) > 2 * 1024 * 1024:
    raise SystemExit("Publication exceeds the 2 MiB raw-data limit")
OUT.mkdir(parents=True)
records = []
for source, relative in selected:
    data = source.read_bytes()
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(data)
    if target.read_bytes() != data:
        raise SystemExit(f"Copy verification failed: {relative}")
    records.append({"origin": str(source), "path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
(OUT / "COLLECTION.json").write_text(json.dumps({
    "collected_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "Byte-preserving collection of completed local pure/synthetic tests and AST/source-transfer checks. No programs rerun.",
    "omissions": "Only regular root files of the two named completed attempts and their serial runner are copied; no caches, builds or external executables.",
    "files": records,
}, indent=2) + "\n", encoding="utf-8", newline="\n")
(OUT / "collector.py").write_bytes(Path(__file__).read_bytes())
(OUT / "COLLECTOR_ATTEMPTS.md").write_bytes(Path(__file__).with_name("ATTEMPTS.md").read_bytes())
(OUT / ".gitattributes").write_text("* -text -filter -ident -working-tree-encoding\nraw/** -text -filter -ident -working-tree-encoding\n", encoding="utf-8", newline="\n")
(OUT / ".gitignore").write_text("!raw/**\n", encoding="utf-8", newline="\n")
(OUT / "README.md").write_text("""# Retry tooling and source-transfer receipts

These are completed local controls, **not a Linux candidate pass**.

- The source-stable serial attempt `20261024T091611731546Z` ran ten normal
  suites / **280 tests**, then **74 optimized verifier tests**. Every process
  exited 0; its raw logs, exact commands and before/after Python-source hashes
  are retained. The runner is copied, not rerun by this collector.
- The backend source-reconciliation attempt checks four transferred files
  against the exact upstream blobs, records physical versus Git-normalized
  hashes and parses their Python ASTs. It does **not** run PostgreSQL, pytest,
  the benchmark, or the new bind-cap/fixture-provenance assurance workloads.
- The serial tests include the matrix subprocess-mock isolation repair,
  X11 atom/protocol controller controls, positive-health HUD checks and hard
  process/OCR watchdog controls. Windows mocks and synthetic children do not
  establish actual Linux window closure or living-player reload completion.

The earlier failed CI at `2a026e6`, old mock/fixture failures and independent
critic custody addendum remain in their separate packets. No historical
result is replaced. The next frozen source still requires the full native
matrix, separate network campaign, exported-client flows and audio controls.
Human/device/production and per-category 8.5 gates remain open.

`COLLECTION.json` names every copied origin and byte hash. `SHA256SUMS.txt`
covers every published file except itself. This collector executes no tests,
Git operations, engine, database, network or build payload.
""", encoding="utf-8", newline="\n")
entries = []
for path in sorted(OUT.rglob("*")):
    if path.is_file():
        entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(OUT).as_posix()}\n")
(OUT / "SHA256SUMS.txt").write_text("".join(entries), encoding="utf-8", newline="\n")
print(json.dumps({"published": str(OUT), "raw_files": len(records), "ledger_payloads": len(entries), "tests_rerun": False}))
