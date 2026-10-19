# Neutral input/lifecycle packet — independent outcome handoff

**Independent source review: PASS. Blind outcome verdict: pending.** Main has
dispatched the accepted packet to a fresh blind critic and will record the
independent outcome verdict after return. This publication adds evidence only:
**no new native run or shipping change**.

## Neutral-only dispatch

Give the outcome critic these artifacts and pins:

- [Exact accepted neutral ZIP](neutral-input-packet.zip), **1,319,139 bytes**.
- [Exact inner manifest, also published separately](MANIFEST.json).
- [SHA256 pins](SHA256SUMS).

| Artifact | SHA256 |
| --- | --- |
| `neutral-input-packet.zip` | `8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112` |
| `MANIFEST.json` | `fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce` |

The archive is a byte-for-byte copy of the accepted packet, not a rebuilt ZIP.
It contains 362 manifest-listed files plus the manifest: anonymous run metadata,
32 complete pairs / 64 native peer logs and receipts, 22 focused gate logs,
original measurement timelines and counters, configured schedules, clock/coverage
limits, failure-retention indices and an offline verifier. Raw captures, native
logs and ready/barrier records retain their bytes. Metadata redactions and opaque
original-counterpart references are documented inside the packet.

The parent identity map and counterpart bundle remain separate and unpublished
until the independent outcome-only verdict(s) are frozen. For blind dispatch,
use only the ZIP, manifest and pins; the coordinator references below are outside
the neutral payload. The existing host packet was not overwritten.

## Verify on another host

From a repository checkout containing this directory, save the following as a
temporary Python script and run it with Python 3. It verifies the published bytes,
checks the embedded manifest against the separate copy, and runs the packet's
offline verifier in a newly created temporary extraction directory. It starts
only Python and performs no native game or service operation.

```python
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import zipfile

bundle = Path("docs/reports/network-input-freshness-v3/blind")
zip_pin = "8fb111324051b4bfc590a216ab09c107ef0c10605f755b7e481757d125172112"
manifest_pin = "fe83c4bdcc1ea662f034ff4ebc340a4e115ed27e8a7d404a2aa80175d84146ce"
archive = bundle / "neutral-input-packet.zip"
manifest = (bundle / "MANIFEST.json").read_bytes()
assert hashlib.sha256(archive.read_bytes()).hexdigest() == zip_pin
assert hashlib.sha256(manifest).hexdigest() == manifest_pin
with tempfile.TemporaryDirectory(prefix="input-freshness-blind-") as temporary:
    with zipfile.ZipFile(archive) as packet:
        assert packet.testzip() is None
        assert packet.read("MANIFEST.json") == manifest
        packet.extractall(temporary)
    subprocess.run([
        sys.executable, "-B", str(Path(temporary) / "verify_packet.py"),
        "--manifest-sha256", manifest_pin,
    ], check=True)
```

The verifier checks file bytes, all 64 recorded peer exits/completion markers,
22 focused gate receipts, source-clean fields and reproducible timeline indices.
Its integrity result is not a comparative outcome verdict. The packet distinguishes
300 ms **simulation-time control neutralization** from physical deceleration,
and 30-second **wall-time expiry** from callback-sampling uncertainty.

There is no retained wire-packet archive or impairment RNG seed, and per-peer
warmup timestamps/full 3D positions were not captured. The configured schedule,
actual captured counters, x-axis authority traces and limits are supplied rather
than an invented packet trace. The 120-command history-cap gap remains explicit;
default-off prediction and disabled live rewind remain the measured settings.

## Coordinator references — outside the blind payload

- [Recorded independent source-review PASS](https://github.com/calebaiken/sightbreak/pull/20#issuecomment-6276000222),
  for runtime `f3ceaad98e089aa393c7f5fa650a52695094d979` against frozen V2.
- [Original source-bound report](https://github.com/calebaiken/sightbreak/blob/1627a9a0ca2a954fe8f246c42ff2f205c578b5c5/docs/reports/NETWORK_INPUT_FRESHNESS_V3.md).
- [Original raw evidence and unsuccessful-attempt index](https://github.com/calebaiken/sightbreak/tree/1627a9a0ca2a954fe8f246c42ff2f205c578b5c5/docs/reports/network-input-freshness-v3-evidence).
- [Exact measured fixture/source checkpoint](https://github.com/calebaiken/sightbreak/tree/77f204083ab5bea4dc9149d3179daf540a994de4).
- [Runtime correction](https://github.com/calebaiken/sightbreak/commit/f3ceaad98e089aa393c7f5fa650a52695094d979).

Main owns the eventual outcome-verdict record. This evidence publication does not
change the measured source, dispatch another critic, or confer aggregate/shipping
acceptance.
