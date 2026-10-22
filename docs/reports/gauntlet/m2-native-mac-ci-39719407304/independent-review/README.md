# Independent Mac CI review

Run [39719407304](https://github.com/calebaiken/sightbreak/actions/runs/39719407304), frozen commit `0ca125dfba637868e6e8e9772ff9c40400413e32`.

ARM default startup, graphical controls and ten native source suites pass within their stated scope. The new unsigned iOS device build fails in the real arm64 linker with Xcode 16.4/iPhoneOS 18.5. [ARM_REPORT.md](ARM_REPORT.md) records the raw failure, verifier parser issue, checks and limitations.

Intel default startup and explicit OpenGL time out. Minimal native graphics controls pass, while frozen/current games and all five grouped feature cases time out at the unchanged 120-second budget. No instrumented completed viewport-render phase or capture is logged for any feature case. [INTEL_REPORT.md](INTEL_REPORT.md) records the exact traces, native samples and limits. No shipping graphics correction is supported.

G13 remains FAILED. The original iOS compile attempt remains FAILED; a separate source/run follow-up at `2a2b732`/`39721286005` independently passes the unsigned device-compile slice in the [separate follow-up report](../../m2-native-mac-ci-39721286005/independent-review/REPORT.md). Startup, source suites, export structure, device compilation, signing, installation, runtime, physical devices, human play and release acceptance stay distinct. No gameplay or release gate is approved here.

`brief.txt` is the exact parent assignment. `CRITERIA_REVIEW.md` sets the review boundaries. `source/independent-source-identity.json` records independently recomputed commit/tree/content/validation identities. `ARTIFACTS.json` binds downloaded originals and records oversized artifacts not requested. Raw connector metadata, completed job logs and independent audits are under `raw/`; frozen source/criteria snapshots are under `source/`.

Original ZIPs are retained under `archives/`. On a fresh evidence checkout, run `bash commands.sh` to verify digests, extract originals and repeat the receipt/native PNG audits. This only reopens retained evidence. Python and Pillow are required. Existing extracted directories are refused to preserve prior attempts.

All review work is foreground session work. No implementation change, renderer launch, external comment, merge, push or publication was performed by this critic. The local audit scripts only reopen retained evidence.
