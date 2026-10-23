# Recovered Linux profile source handoff

Source/pure candidate only; fresh independent acceptance is pending. Runtime,
export and performance remain UNVERIFIED. The ordinary Linux next-buy deadline
remains FAILED.

The initial source freeze `3631f2d` was independently rejected because missing
Xvfb could mask a deleted sampler admission guard in the maintained negative
test. The corrected test now supplies fake Xvfb, forces an unused socket and
checks the intended rejection message before source/process/output side
effects. All three corrected tests pass and four meaningful source mutations
fail. See [the retained rejection and correction](REVIEW_CORRECTION.md).
The controller's bytes are unchanged; fresh independent re-review is pending.

The builder preregistered one capability attempt at `98cd21c`, before code, then
committed the eight-line controller extension and pure controls at `2bf9be1`.
Both commits are pushed on `diagnostic/linux-gles-profile-recovered`. The source
starts at exact recovered base `917b143ba4e4b0d9644a7a0ddeee1dd64c139682` and
does not inherit the unavailable `ab4fa6d0` candidate's review.

`--linux-gpu-profile` admits only native Linux plant / seed 42 / timeout 180 and
rejects external sampler coexistence. It inserts the engine option at initial
argv index 1, before the user-argument separator. The normal reopened command,
original conditions, renderer, quality and every deadline retain their original
statements. There is no game diff.

[`source_audit.py`](source_audit.py) removes exactly the new parser declaration,
admission condition and insertion condition, then compares the entire remaining
controller AST with the exact base. They match. Controller SHA-256 is
`f6f45ed28feceb1140e02bf5faffc6293c7d3cac96e83a5e1ab2d70dd07baabf`.
This also verifies the normal reopened-command statements and budgets. The
audit's source comparison and raw hashes are in
[`pure-controls/source-audit.json`](pure-controls/source-audit.json).

The pure interception executes the real controller through initial launch using
fixture processes, source/export receipts, engine identity and UI. It stops at
the first menu probe; no native process or engine runs. It verifies the exact
unchanged default argv, the opt-in argv with default/explicit seed 42, Xvfb
1280x720, and no sampler construction/output. Invalid platform/scenario/seed/
budget/sampler combinations reject before source checks, subprocesses or output
directory creation. Reopened runtime behavior is outside this interception;
the complete AST comparison covers its source invariance.

The system `python3` with Pillow 12.3.0 runs all controls. The suggested recovered
shared venv lacks Pillow, so its initial import failed before execution. The
first system-python fixture lacked a `platform.platform` mock, causing the
standard library's processor query to reach the fake Popen; that setup failed.
The correction mocks the host description as well. Both raw failures are
retained byte-for-byte in gzip archives with original/decompressed hashes in
[`raw-failure-archives.json`](pure-controls/raw-failure-archives.json).
An initial staged whitespace check flagged a trailing space in that raw failure
output. Archiving the exact bytes preserves it without editing the transcript;
the final whole-candidate whitespace check passes.

| Pure command | Result | Retained output |
| --- | --- | --- |
| `python3 scripts/test_linux_gpu_profile.py -v` | 3 tests, 0.033 s, no skips | [gpu-profile.txt](pure-controls/gpu-profile.txt) |
| `python3 scripts/test_linux_frame_sampler.py -v` | 18 tests, 1.182 s, no skips | [frame-sampler.txt](pure-controls/frame-sampler.txt) |
| `python3 scripts/test_offline_role_guidance.py -v` | 4 tests, 0.002 s, no skips | [role-guidance.txt](pure-controls/role-guidance.txt) |
| `python3 scripts/test_offline_capture_fences.py -v` | 15 tests, 0.262 s, no skips | [capture-fences.txt](pure-controls/capture-fences.txt) |
| `python3 docs/reports/gauntlet/m1-linux-gles-profile-recovered/source_audit.py` | exact remaining AST equality | [source-audit.json](pure-controls/source-audit.json) |
| `python3 -m py_compile scripts/verify_offline_match.py scripts/test_linux_gpu_profile.py docs/reports/gauntlet/m1-linux-gles-profile-recovered/source_audit.py` | exit 0 | no output |
| `git diff 917b143ba4e4b0d9644a7a0ddeee1dd64c139682 --check` | exit 0 after raw-log archiving | no output |

The [registration](PREREGISTRATION.md) defines the exact upstream output meaning
from Godot `ed1daf0bf001b61586d9930840f2f1394092c079` and its source hashes.
GLES query buffers supply historical results; the source comment says frame
minus two. The stdout loop can reuse retained profiles and emits no phase or
source-frame identity. Named rows are adjacent GPU-query differences averaged
over reporting-interval draw calls, with rows at or below 0.01 ms omitted. The
header total instead uses the latest retained profile's final timestamp offset.
No row/header sum, stdout-arrival phase assignment, process-CPU partition,
physical FPS or causal/overhead/improvement claim is supported.

The largest remaining deficiency is actual profiled output at the new frozen
source. Root must obtain a fresh independent source verdict before releasing
one source-bound export and the single registered sampler-off capability
attempt. Preserve the original failure if the 12-second next-buy gate fails
again. No engine, native client, export, CI or service has run for this candidate.
