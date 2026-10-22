# Independent SDK correction review

Reviewed on 2026-10-22. Candidate: `90740e0`; comparison: `ac3cfde`.
The reviewer used an isolated worktree and made no implementation change.
The installed Gauntlet and No AI Slop skills were read and reused.

Verdict: accept this correction for the next native ARM Mac attempt. No blocking
defect was found in the candidate delta. The iOS build gate remains unverified.

The candidate is better for the observed failure. The previous implementation
accepted the runner's default Xcode 16.4/iPhoneOS 18.5 SDK, which reached the
game's linker and failed on five globals. The candidate enumerates installed
Xcodes and requires an actual unsigned arm64 device link resolving those exact
globals before choosing a process-local `DEVELOPER_DIR`. This addresses the
observed failure without replacing the pinned engine or suppressing unresolved
symbols. This comparison is based on retained failure output and source review;
the candidate has not completed a native game build.

The largest remaining gap is the full game link and final unsigned-app inspection
under the selected Xcode. The five-symbol probe does not exercise the complete
Godot archive or its Swift and framework dependencies. The old native log also
contains auto-link warnings. Only a new native attempt can establish whether
the selected SDK resolves the complete link and whether the final app passes
the unchanged signature and Mach-O checks. Simulator and physical-device runtime
qualification remain separate open gates.

## Evidence and correctness

All three files in `failure-0ca125d` match the downloaded ARM receipts from run
39719407304 byte-for-byte: compile receipt, exported-source receipt and raw link
log. Their SHA256 values are retained in [content-controls.txt](content-controls.txt).
The native receipt binds the failed attempt to clean source
`0ca125dfba637868e6e8e9772ff9c40400413e32`, Godot
`4.7.2.stable.official.ed1daf0bf`, and the checksum-pinned templates. It records
`compile_completed: false`, Xcode 16.4, iPhoneOS 18.5 and linker exit 65.
The retained runner header and exact-image software manifest document newer
installed Xcodes, including 26.3 with iPhoneOS 26.2. The Apple SDKDB excerpts
identify the five missing globals as introduced in iOS 26. These sources justify
trying installed SDKs; they do not prove what a future runner will provide.

The probe forces all five unresolved symbols with the linker's `-u` option,
requires undefined symbols to be errors, uses the observed iOS 15 deployment
target, and disables ad-hoc signing. Acceptance also requires a fresh thin arm64
device-iOS executable without an `LC_CODE_SIGNATURE` command. Fresh output paths,
an exclusive probe directory and distinct per-candidate filenames prevent reuse
of a previous probe. Resolved SDK paths must belong to the candidate Developer
directory. Aliases are deduplicated and the installed inventory is bounded.

All new SDK commands use the existing owned-process wrapper. Each receives at
most 30 seconds from the same remaining deadline; the registered workflow still
passes 900 seconds. Nonzero link exits allow fallback, while timeout, incomplete
cleanup and unexpected surviving descendants still abort. No Xcode installation
or global selection mutation is added. The selected child environment continues
through export, project inspection and the game build. A subsequent SDK identity
check rejects a changed selection.

The parser now recognizes the actual retained `Ld ... normal (in target ...)`
format. The failed native log remains rejected. Compiler action, native exit
zero, build success and the final app's architecture/platform/signature checks
remain mandatory. The delta preserves source snapshots, template checksums, exact
PCK hashes and resource checks, signing/provisioning exclusions, and the final
`codesign` unsigned assertion. Retained QA files contain receipts and logs;
native archives, PCKs, frameworks and apps are not added to this review evidence.

## Independent controls

All controls below ran on Linux. Synthetic Mach-O bytes and mocked Darwin
receipts test rejection logic only. They cannot establish Apple compiler success.

- [Qualification controls](qualify-controls.txt): 14 pass, including SDK fallback,
  environment isolation, failed-log rejection, PCK tampering, unsigned Mach-O,
  timeout and owned-group cleanup.
- [Provenance controls](provenance-controls.txt): 24 pass, including dirty/stale
  source, changed artifacts, developer files and missing payload rejection.
- [Receipt packaging controls](receipt-controls.txt): 6 pass, including exact
  reconstruction, size bounds and symlink rejection.
- [Independent content controls](content-controls.txt): 12 pass. These cover alias
  deduplication, zero-exit probes with absent/signed/simulator/truncated output,
  SDK ownership, stale prior probe output, empty/oversized inventories, the
  observed native linker format, mixed success/failure markers, and receipt
  identity. Source: [content-controls.py](content-controls.py).
- [Independent process controls](process-controls.txt): actual Linux timeout and
  residual-child cleanup pass; expired budgets prevent launch. Three full
  `qualify()` fixtures separately inject link rejection, timeout and cleanup
  failure. Each retains a failed receipt before export, keeps a decreasing shared
  remaining budget, and leaves `os.environ` unchanged. Source:
  [process-controls.py](process-controls.py).

Reproduce from a checkout containing the candidate:

```sh
python3 scripts/test_qualify_ios_compile.py -v
python3 scripts/test_build_manifest.py -v
python3 scripts/test_package_qa_receipts.py -v
python3 docs/reports/gauntlet/m2-ios-compile/sdk-iteration/independent-review/content-controls.py "$PWD"
python3 docs/reports/gauntlet/m2-ios-compile/sdk-iteration/independent-review/process-controls.py "$PWD"
```

The content control's downloaded-receipt identity check runs when the original
local receipt directory is available; the remaining controls are self-contained.
No Darwin process inspection, native cancellation, full native link, simulator
build, installation or physical-device execution was available locally. The
unchanged process-group cleanup does not contain a descendant that deliberately
creates a separate session. No such escape was demonstrated by this candidate.

Next action: dispatch an exact clean reviewed source on ARM macOS, retain each
real SDK probe and the complete build receipt, then independently inspect the
native result before changing the iOS gate status.
