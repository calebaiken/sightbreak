# Sightbreak V3 final pre-freeze critic

## Outcome

**One new verified source/synthetic CI-facing blocker: the Windows OS mock in `test_matrix_process.py` is not isolated from POSIX pathlib.** No new false-passing OCR/export flow was reproduced. This is a bounded source/mock review, **not release approval, native acceptance, an actual Linux run, or proof of exceptional cleanup**.

- Workspace: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3`.
- Branch: `integration/sightbreak-v3-validation`; HEAD: `320e0ef3cca01566bb5858c90a8021b136737be0`.
- The 53-file before/after byte-hash inventory is unchanged: `True`. Git status unchanged: `False`.
- All 41 Python-script hashes present in the supplied source-stable serial attempt match this review's opening inventory; prior-check drift: `[]`. Workflow hashes were independently captured before/after here, not inferred from that earlier Python-only inventory.
- No repository edits, staging, commits, posts, native Godot/editor/import/export, network, DB, agent polling, or full-suite reruns. All executed Python used the exact approved CPython 3.13.15 with `-B`; spawned synthetic children also used that executable. New artifacts exist only in this external directory.

## F1 — P2: shared `os.name` mutation breaks a Linux-facing matrix unit

**Locations:** `scripts/test_matrix_process.py:196-201,207-210`; `scripts/matrix_process.py:214`; execution path `.github/workflows/v3-development.yml:24,30` → `scripts/validate_matrix.py:108`.

`run_parent()` patches `processes.os.name` to `nt`. That is the shared `os` module, so it also changes the OS identity observed by `pathlib.Path`. On a POSIX-initialized CPython stdlib, `Path(__file__)` consequently selects `WindowsPath`, whose constructor is unsupported on that platform. `run_process()` catches the resulting runtime error before creating the Job or launching the mock command. The existing unit then errors at `launch.call_args.kwargs` because no launch occurred.

**Concrete reproduction retained:** `linux_pathlib_repro.py`, `linux-pathlib-repro.log`, `linux-pathlib-repro.json`, and exact command/actual exit in `linux-pathlib-repro-command.json`. It initializes a private copy of the actual approved interpreter's pathlib implementation with POSIX identity, shares one private OS namespace between it and the real `matrix_process` module, then executes the existing `SupervisorTests.test_parent_keeps_actual_exit` unchanged. No Linux process or native tool is launched.

Observed: one existing unit run, one error; the actual runner emitted:

```text
HARNESS_ERROR cannot instantiate 'WindowsPath' on your system
AttributeError: 'NoneType' object has no attribute 'kwargs'
```

The repro exits **1**. A corrected positive control (`linux_pathlib_local_os_control.py`, `linux-pathlib-corrected-local-os.json`) replaces only the module-local OS reference rather than mutating shared `os.name`; it returns actual fixture exit **7**, launches its mock once, performs mock Job cleanup once, emits no harness error, and exits **0**. This supports a narrow test-mock isolation correction, not a production process-ownership refactor. Other parent-unit cases reuse the same defective helper.

**Qualification:** this is verified source/synthetic platform behavior on Windows CPython 3.13.15, not actual Ubuntu/Python 3.12 execution. The workflow's full matrix explicitly selects Python 3.12; that exact Linux run remains pending. The predicted consequence is a red `matrix-process-unit` check, not a false-green matrix. The first repro's separate positive comparison had a critic-only mock bug (writing its receipt on both waits); that failed comparison is retained unchanged, and the corrected positive comparison above is authoritative. It does not affect the original failing-unit reproduction.

## Bounded controls and fail-closed findings

Eight ordinary observations passed (`controls-summary.json`):

- Real OCR worker streamed fixture stdin and retained independent stdout/stderr; exit 0 returned `100 HEALTH`.
- The same parseable text with actual exit **3** was rejected; receipt retained exit 3.
- A real finite CPython OCR timeout was rejected, partial output retained, and no late marker appeared.
- A real exit-0 OCR root spawned a child in a new Windows process group. The child startup marker was observed; OCR was rejected for containment errors, the receipt retained actual exit **0**, and the child's late-write marker remained absent. This is synthetic CPython/Job behavior, not native Godot or Tesseract validation.
- Existing OCR output was refused before `run_process` launch; stale bytes remained unchanged.
- The Windows already-exited-root helper produced an explicit descendant-cleanup-unverified failure, not a clean cleanup result.
- A mocked Linux receipt without successful cleanup attestation retained exit 0 but emitted `HARNESS_ERROR ... detached-descendant cleanup unverified`.
- Settled late-write observation saw neither timeout nor descendant escape marker.

Source checks confirm `ocr_process.py` is launched through prelaunch `matrix_process.run_process`; attempt input/stream/log files are opened exclusively by the parent; receipts cannot silently reuse existing evidence; `ocr_text()` checks elapsed deadline, native/harness log errors, and actual exit before returning text. The worker's truncating stream opens operate only on the parent's newly claimed attempt files. Windows supervisor Job assignment still precedes command `Popen`. All in-scope production callers audited combine actual exits with raw `HARNESS_ERROR` gates rather than accepting PASS text.

Linux supervisor-death detached-descendant cleanup remains explicitly **unverified and fail-closed**, not repaired or proven here. The supervisor's attestation is required before the parent claims verified POSIX cleanup. Windows dead-root taskkill uncertainty is likewise retained as a failure. Neither platform's exceptional/native cleanup behavior is proven by these controls.

## Workflow source review / remaining limits

The workflow has three independent public-repository Ubuntu 24.04 jobs, full-history checkout, explicit `xauth`/Xvfb and OCR/Pillow dependencies where used, pinned uv installation, root backend venv creation, a separate ten-client campaign retained after matrix failure, and separately retained actual exported network/offline flow evidence. The adversarial job uses an external tools/state directory, exact-commit worktree and explicit CPython 3.13.15; its nine broad baseline commands and A5/A6/A7 tuples were not changed by this critic. Setup/export shell entrypoints have executable Git modes. No further concrete setup/command blocker was verified from source.

Actual Linux setup downloads/package availability, Python 3.12 runtime, runner resources, full matrix/network campaign, native exported UI/Tesseract behavior, exceptional cleanup, audio/native acceptance and physical-device behavior remain unverified. Earlier serial suite results are provenance only; they are not reclassified as Linux/native acceptance. The known previous failed attempt was not reused or deleted.

## Exact primary source SHA-256 (raw bytes)

| Path | SHA-256 |
|---|---|
| `scripts/ocr_process.py` | `82f872b0160617f8bcccb4335f4786f7a2298fcae9c4ebd4d1d9af5d8ad30e64` |
| `scripts/verify_offline_export.py` | `63a6c3ea5def77c4a02f1a3726938f825cab1410c087a882d29d4626922fb342` |
| `scripts/matrix_process.py` | `829afa5defa5a43d62391cc9e42ba329a0677bfdb2330446d1fdf124bdb946d8` |
| `scripts/godot_process.py` | `6d04212b2126c4bc7d2ac127a39e4a982a8bc3835f60d79db0e1f26b720009c2` |
| `.github/workflows/v3-development.yml` | `a394388ed9020045969795a888d7e908ae2823e19a98b7bc71b8cab760dceda4` |
| `scripts/test_matrix_process.py` | `8cf21988c6ca1222b89a53b25753a72b9fc4e231790a9541491788f864d6cddc` |
| `scripts/validate_matrix.py` | `136c52ef7334774df2c1ed391e2b7831912e7b1113883dc6588b1372526ab760` |
| `scripts/export_flow.py` | `529f50d48dd42935d516531a6248cba3144ea923e789350ddaf60d0e55161987` |

Full inventories: `source-hashes-before.json`, `source-hashes-after.json`; stability and prior-attempt drift: `source-stability.json`, `metadata.json`. All control failures, raw streams, process logs/receipts, exact executable commands and actual exits are retained. To reproduce, copy a control program to a **new empty external directory**, then use the approved executable with `-B`; these controls intentionally refuse output overwrites.
