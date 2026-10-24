"""Publish completed custody receipts without altering their bytes or rerunning tests."""
import hashlib
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
OUT = ROOT / "docs/reports/three-agent-evidence/development-v3/retry-freeze"


def main():
    if OUT.exists():
        raise SystemExit("Refusing to replace an earlier custody packet")
    sources = [HERE / name for name in (
        "audit.py", "audit_retry.py", "retry-index-before.json", "retry-source-before.json")]
    for source in sources:
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"Missing/nonregular source: {source}")
    for receipt in sources[2:]:
        if json.loads(receipt.read_text(encoding="utf-8")).get("passed") is not True:
            raise ValueError(f"Custody audit failed: {receipt}")
    OUT.mkdir(parents=True)
    for source in sources:
        destination = OUT / source.name
        with destination.open("xb") as stream:
            stream.write(source.read_bytes())
        if destination.read_bytes() != source.read_bytes():
            raise ValueError(f"Copy mismatch: {source}")
    shutil.copyfile(__file__, OUT / "seal_retry.py")
    (OUT / ".gitattributes").write_text(
        "* -text -filter -ident -working-tree-encoding\n", encoding="utf-8", newline="\n")
    (OUT / "README.md").write_text("""# Retry-freeze custody receipts

These read-only audits were completed before the commit containing this packet.
They are not new tests, native runs, independent review or candidate acceptance.

- `retry-index-before.json`: all 2,443 payloads in six completed evidence packets
  match both physical bytes and the Git index. The six packet ledgers are listed
  in the receipt. Their own historical failures remain unchanged.
- `retry-source-before.json`: all 44 Python files still match the source-stable
  serial run with 280 normal tests plus 74 optimized verifier tests. All eleven
  actual process exits were zero. Seven accepted upstream source files match
  their exact staged Git bytes, including backend assurance and additive
  snapshot diagnostics. Physical CRLF files are not mislabeled as raw Git bytes.
- The original auditors and this byte-copying publication script are retained.

The repair critic's source/HEAD-drift qualification is in
`../ci-repair-followup/`; the serial logs are in `../retry-tooling-review/`.
The frozen Linux run at `2a026e6` still failed overall. The commit containing
this packet must receive its own maintained matrix, separate network campaign,
native audio controls, development exports and actual exported-client results.
No human, device, production or 8.5 quality gate is waived.
""", encoding="utf-8", newline="\n")
    paths = sorted(path for path in OUT.iterdir() if path.is_file())
    (OUT / "SHA256SUMS.txt").write_text("".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n" for path in paths),
        encoding="utf-8", newline="\n")
    print(json.dumps({"copied": len(sources), "ledger_payloads": len(paths), "output": str(OUT)}))


if __name__ == "__main__":
    main()
