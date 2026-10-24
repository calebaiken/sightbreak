# Fresh-context Sol CI-repair critic

## Verdict

**No verified blocker in the six-file review scope. Actual Linux execution is still pending. This is not release approval.**

Reviewed the current working-tree versions at HEAD `88bfc51da026be42b3dec517817459ed89630ded`, not the earlier executed CI revision `2a026e61cabee3c66334066d45e92eb3ec6c2641`. The checkout is dirty with the proposed changes and unrelated concurrent work already present. No repository file was edited, staged, committed, pushed, posted, or discarded by this critic.

Scope: `scripts/test_validate_matrix.py`, `scripts/verify_integration_export.py`, `scripts/verify_offline_export.py`, `scripts/offline_hud.py`, `scripts/test_export_ui.py`, `scripts/test_offline_hud.py`, and the immediate source/receipt/process contracts needed to evaluate them. All evidence writes are in this new external directory.

## Executed controls

Interpreter: `C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe` (CPython 3.13.15, Windows x86-64). All tests ran serially. No Godot, export, native client, Xvfb, Tesseract, database, service, or network workload was executed. No extracted payload was executed.

| Maintained suite | Tests | Failures/errors/skips |
| --- | ---: | --- |
| `scripts/test_validate_matrix.py` | 19 | 0 / 0 / 0 |
| `scripts/test_export_ui.py` | 14 | 0 / 0 / 0 |
| `scripts/test_offline_hud.py` | 6 | 0 / 0 / 0 |
| `scripts/test_export_flow.py` (narrow watchdog/OCR contract) | 28 | 0 / 0 / 0 |
| **Total** | **67** | **0 / 0 / 0** |

`audit.py units` returned exit 0. `units.json` holds the counts; `units/<module>/unittest.log` holds raw test output. The runner changes only temporary-directory retention, so generated synthetic process logs, failed receipts, and partial streams survive rather than being deleted by test cleanup. The printed matrix precondition `UNAVAILABLE` is an expected dirty-source negative control, not an actual matrix run or waived failure.

`controls.py` returned exit 0 with **26 synthetic controller wiring controls** (two positive, 24 negative), **four protocol/layout controls**, and **two replays of retained original HUD OCR**. These execute the current controller main functions and real manifest/HUD/receipt logic but replace desktop/process/time/image/OCR boundaries. Their positive receipts are explicitly synthetic, not exported-client validation. Synthetic `.png` files contain labeled JSON fixtures, not real screenshots.

## Source-backed conclusions

### 1. The matrix subprocess mock is localized

- `scripts/test_validate_matrix.py:27-40` replaces only `matrix.subprocess` with `Mock(wraps=...)`, not the shared `subprocess.check_output` function.
- `scripts/test_validate_matrix.py:174-182` explicitly exercises a real CPython `check_output` from the mocked platform callback while matrix Git metadata is stubbed.
- The actual positive-control subprocess and the 19 matrix unit tests passed. The inventory and final source/leak gates still run in the tests (`:198-250`).
- Limitation: these controls ran on Windows, not Linux's actual `platform.platform()`/uname path. They demonstrate the object-isolation fix and actual CPython subprocess coexistence, not an executed Linux matrix.

### 2. Prepared native close has correct scoped ordering and fail gates

- `scripts/verify_integration_export.py:91-103` declares `XSync`, `XGetWMProtocols(Display*, Window, Atom**, int*)`, and `XSendEvent` signatures. `Atom`/`Window` use `c_ulong`, matching Xlib's unsigned-long API on Linux.
- `scripts/verify_integration_export.py:107-134` opens the display, creates both close atoms with `only_if_exists=0`, synchronizes the connection, and frees any returned protocol allocation in `finally`.
- `scripts/verify_integration_export.py:201-221` requires advertised `WM_DELETE_WINDOW` and sends a normal ClientMessage: type 33, window target, `WM_PROTOCOLS` message type, format 32, delete atom in `data.l[0]`, CurrentTime in `data.l[1]`. There is no replacement signal/kill/frame-budget pass path.
- Both launch sequences create the UI **before** the ELF and recheck source/receipt/binary **after** UI initialization and before client launch: network `:300-305`, offline `scripts/verify_offline_export.py:146-151`.
- Real `unchanged_export` checks in synthetic main-function controls rejected a source mutation injected during UI construction in both flows, with no client launch. Mutations before final audit also produced failed receipts.
- Existing unit controls verify missing atoms, missing advertisement/property, undelivered event, serialization, and allocation freeing (`scripts/test_export_ui.py:15-85`). Independent extra controls verify exact freed addresses for valid, empty, and failure-with-allocation protocol queries.
- A pure LP64 layout model gives ClientMessage size 96 and offsets `type=0, serial=8, send_event=16, display=24, window=32, message_type=40, format=48, data=56`, consistent with the declared structure. This is only a type-layout model: Windows's actual `c_long` is 32-bit; this does not test native Linux ABI or libX11.

### 3. Offline pause inspection does not replace live HUD evidence

- `scripts/verify_offline_export.py:122-136` uses ordinary native Escape input and requires a captured `FIELD MENU` plus `Training is paused` proof; `scripts/offline_hud.py:5-11` rejects missing labels and the continuing-match label.
- `scripts/verify_offline_export.py:182-198` captures each live HUD **before** pausing, OCRs the original live frame while paused, resumes for native R reload input, then captures/repeats inspection. It does not OCR the pause overlay as if it were a live HUD.
- Source supports the ordinary pause assumption: `game/scripts/main.gd:1141-1146` routes non-echo Escape to `toggle_pause`; `:1433-1459` disables offline match processing, displays the matching text, and resumes processing through `close_overlay`. `game/tests/ux_contract_test.gd:111-121` contains the corresponding clock-pause/resume and network-not-paused contracts (read, not executed here).
- The positive synthetic trace records all six OCR operations while the field menu is open, with HUD OCR inputs named `05-after-fire` and `06-after-reload`, and R accepted only after resume. See `controls/offline-none/control.json`.
- Ignored pause, network-menu text, ignored resume, ignored reload input, eliminated player in either stage, zero-health player after reload, and nonconserved ammunition each produced failed receipts. In particular, ignored resume did not turn into a pass from a paused HUD; the unchanged magazine failed the reload gate.
- Living-health, initial-magazine depletion, reserve, full reload, and ammunition-conservation checks remain intact (`scripts/offline_hud.py:14-21`; `scripts/verify_offline_export.py:184-197`). No runtime/game/bot/invulnerability/private-hook change is present in the reviewed patch.
- The result explicitly limits this to ordinary paused inspection, **not continuous-match play** (`scripts/verify_offline_export.py:212-218`).

### 4. Native close, exception receipts, and watchdog success remain distinct

- Network requires the client still alive before close, actual zero client/server exit, passing authority, clean logs, and final immutable export (`scripts/verify_integration_export.py:348-377`). Offline retains the equivalent client/HUD/log/source gates (`scripts/verify_offline_export.py:202-225`).
- In both synthetic main-function flows, unadvertised close, ignored/hanging close, close exit 7, native leak, early zero exit before close, and final source mutation all failed. Network authority=false and server exit 7 also failed. Normal positive controls never terminate/kill the client to pass.
- `scripts/export_flow.py:45-115` owns failed initial receipts and rejects worker nonzero exit, absent/invalid/nonboolean success, containment `HARNESS_ERROR`, native errors, and late completion including cleanup. Its 28 maintained real-CPython/synthetic controls passed, including retained partial OCR streams, surviving/detached descendants, ignored passing JSON on timeout/nonzero exit, and final-audit deadline rejection.
- Controller `finally` cleanup is not acceptance: if later cleanup raises after a written success, the worker nonzero exit is still rejected by the watchdog. Native timeout/containment remains a failure, not a close-success claim.

## Original failed Linux evidence remains failed

Read only selected small members from `sightbreak-v3-evidence/ci-39880125007/artifact-12470681259.zip` and existing extracted OCR text. Member bytes/hashes are in `controls.json`; no archive was overwritten and no payload was executed.

- Network authority records six shots, lowest ammo 24, ack 95, native reload command observed/completed, and authority `passed=true`. `08-settled.png` exists in the archive (metadata only inspected here). The flow watchdog still reports a roughly 240-second timeout and failure; authority success is not flow success.
- Original offline `05` OCR parses as health 100, magazine 14, reserve 60. Original `06` OCR says `ELIMINATED - SPECTATING` and `RELOADING 0.1s`; the current parser still rejects it. No relaxed OCR acceptance or retroactive pass was introduced.

The proposed fixes are therefore reasonable candidates for a fresh Linux run, not proof that the original native failures are repaired.

## Drift and custody

- `source-before.json`, per-suite before/after snapshots, `source-controls-before.json`, `source-controls-after.json`, and `source-after.json` record hashes/lengths/mtimes for all six scoped files and 16 immediate contracts, along with HEAD, status, interpreter, and UTC.
- `drift.json`: HEAD unchanged, full porcelain status unchanged, **no selected-file drift**. The checked-out dirty state was not represented as clean exported evidence.
- `scoped-working-diff.patch` records the proposed six-file patch without altering it.
- `SHA256SUMS.txt` and `FINALIZATION.json` bind the retained report/control evidence and verify the directory stays below 2 MiB. Expected negative-control failures, logs, process receipts and streams are retained.
- The server restart did not cause a test rerun or evidence overwrite; the completed receipts were reused and final drift checking was performed afterwards.

## Remaining gates / limits

1. A committed, frozen exact-source Linux matrix rerun is still required; local unit success is not the 83-group CI result.
2. A real bare-Xvfb/Linux/Godot 4.7.2 exported-client run must show prepared atom advertisement, actual WM_DELETE_WINDOW-driven exit, zero native exit and clean logs inside the watchdog. The cited engine source behavior was supplied as review context; the engine C++ source was not locally available for an independent re-read.
3. A real offline run must show both pause labels readable in the chosen crop, unpaused live-HUD fire/reload evidence, living health, conserved ammo, menu return and clean normal close. Native input delivery, rendering/OCR timing, crop geometry and continued survival were not established by fake desktop boundaries.
4. Independent visual review of actual screenshots is still necessary. No continuous-play, physical-device, performance, full-match, release-quality or production-deployment approval is given.

No speculative refactor or source patch is requested by this review.
