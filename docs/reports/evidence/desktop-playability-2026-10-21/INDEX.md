# Desktop playability evidence — 2026-10-21

Product/build freeze **S12** is `e3c1194a9c7bb2ff8a5e3b81ab122513dce4a32c`, game tree `45b6c6ea9d3244700e324e90d6df4778ee28d18e`, official Godot `4.7.2.stable.official.ed1daf0bf`. [The delivery report](../../DESKTOP_PLAYABILITY_REPORT.md) explains the failed gates and platform limits. Validation-only **S13** is `475e00a7d3129398d04d423a25b1807547987693`, with identical game content. Validation-only **S14** is `d6784ab2d81dae204b6a699f0177f7e9d70bec4e`; its fire-capture fence retains the original wait. Later documentation does not re-attest older exports.

[index.json](index.json) records each retained file's original path, exact SHA-256 and size. PNG/JSON/Markdown bytes are unchanged. `.gz` files are lossless compressed original logs/actions, with both compressed and original hashes. These curated copies supplement immutable native CI artifacts; they are evidence, not game packages or a new build attestation.

## Native execution and failures

- [Final S12 job matrix](reviews/ci-s12-final-jobs.json), [artifact IDs, sizes, digests and expiry](reviews/ci-s12-artifacts.json).
- [Completed S14 job/step matrix](reviews/ci-s14-final-jobs.json), [final S14 artifact IDs, sizes, digests and expiry](reviews/ci-s14-final-artifacts.json). ARM SUCCESS; Windows/Linux/Intel FAILURE. Passed scenario steps do not pass a whole failed job.
- [Independent Windows final-source findings](windows/S12_WINDOWS_NATIVE_FINDINGS.md), [original full job log](windows/ci-s12-full.log.gz), [full-match receipt](windows/ci-s12/offline-full-match/results.json), [player defuse receipt](windows/ci-s12/offline-defuse/results.json). Offline/plant failed attempts remain beside them.
- [Independent Linux final-source findings](reviews/independent-qa-s12-linux-review.md), [original full job log](linux/ci-s12-full.log.gz), [full-match receipt](linux/ci-s12/offline-full-match/results.json). CI defuse/layout failures remain retained.
- [Extracted Linux runtime/960 review](reviews/independent-qa-r12-extracted-review.md), [native launcher/plant/defuse aggregate](linux/extracted-native-r12/result.json), [actual defuse receipt](linux/extracted-native-r12/defuse/results.json), [960 layout receipt](linux/extracted-layout-960-r12/results.json). The extracted plant and aggregate failed; successful defuse does not replace them.
- [Local Linux offline input/restart/focus](linux/linux-offline-r12/results.json), [51-check independent audit](reviews/independent-qa-r12-offline-audit.json). Earlier r9/r10/r11 failures remain under `linux/`.
- [ARM final review](macos/ARM_S12_INDEPENDENT_REVIEW.md), [Intel final failure review](macos/INTEL_S12_INDEPENDENT_REVIEW.md), and compressed original Mac job logs in `macos/`. [Mac diagnostic/physical qualification procedure](../../MACOS_PLAYABILITY_DIAGNOSIS.md).
- [Final S14 Mac independent review](macos/S14_FINAL_MACOS_REVIEW.md), [original-file hash index](macos/S14_MACOS_EVIDENCE_INDEX.json), [ARM original job log](macos/S14_ARM_JOB.log.gz), [Intel original job log](macos/S14_INTEL_JOB.log.gz), [ARM comparison receipt](macos/ci-s14-arm/macos-diagnostics/results.json), [Intel failed comparison receipt](macos/ci-s14-intel/macos-diagnostics/results.json). Candidate software-GL stack samples and failed helper receipts remain under `macos/ci-s14-intel/`; no absent frozen stack is claimed.

## Selected unedited rendered captures

| Evidence | Original screenshot |
| --- | --- |
| Windows complete match | [Operation summary](screens/windows-ci-s12/offline-full-match/07-operation-complete.png), [final ten-player roster](screens/windows-ci-s12/offline-full-match/08-final-scoreboard.png) |
| Linux complete match | [Operation summary](screens/linux-ci-s12/offline-full-match/07-operation-complete.png), [final ten-player roster](screens/linux-ci-s12/offline-full-match/08-final-scoreboard.png) |
| Extracted player defuse | [Held E](screens/extracted-r12-defuse/05-objective-hold.png), [authoritative completion](screens/extracted-r12-defuse/06-player-objective-completed.png) |
| Desktop focus and resume | [Restored but paused](screens/linux-offline-r12/11a-restored-focus-still-paused.png), [held-input neutral](screens/linux-offline-r12/11b-resumed-held-input-neutral.png), [fresh movement](screens/linux-offline-r12/11c-fresh-press-movement.png) |
| Extracted 960×540 default UI | [Live HUD](screens/960x540/02-live-hud.png), [roster](screens/960x540/03-tab-roster.png), [settings](screens/960x540/05-field-settings.png) |

Screenshots establish only the visible view and recorded source. OS injection is not physical keyboard/touch/controller evidence. Software/virtual graphics do not establish human input feel, hardware performance or an 8.5 quality score. Other layout attempts retain their exact image/gate scopes in the report.

## Regression, source and package integrity

- [Maintained suite receipt](regression/result.json): Bash exit **0**; outer cleanup wrapper **1**, with [original process-state diagnosis](regression/cleanup-diagnosis.json) and [full original output](regression/validate.log.gz). This includes native/source suites, 61 PostgreSQL backend tests, 37 real isolated native economy checks and 24 build-manifest controls. It is not exported physical-gameplay acceptance.
- [Actual network cleanup baseline/candidate/negative controls](regression/network-cleanup/summary.json): original zombie reproduced; candidate normal, SIGTERM, terminated-client and stopped-server fallback retain real statuses and empty child groups. Raw probes/logs are retained in the same directory.
- `input/` retains matched baseline/candidate simulated-capability and HUD failures/passes, existing-save isolation and critical-health OCR counterexamples.
- [Five-target export command receipts](reviews/all-exports-r12.json), [independent extracted-package positives/negatives](reviews/packages-r12/results.json), [original manifest](packages/manifest.json), [local development ZIP checksums](packages/checksums.txt), per-target original source receipts in `packages/`.
- [Windows OCR/priority measurements](windows/ocr-priority-r2/DIAGNOSIS.md) retain native exit/timing/priority evidence. They do not establish the historical network reload timeout's cause or promote pending scenario results.
- [S13 Windows draw and retained failures](windows/S13_WINDOWS_NATIVE_FINDINGS.md), [S13-equivalent priority/ownership/defuse probe](windows/hosted-priority-validation-r1/DIAGNOSIS.md), and [S14-equivalent fire-capture correction](windows/fire-ack-native-r1/DIAGNOSIS.md) keep follow-up sources separate. The separate fire-capture probe verifies fire/reload/buy/settings but fails after actual death; it does not complete restart.
- [Final S14 Windows matrix](windows/S14_WINDOWS_NATIVE_FINDINGS.md) and [full original job log](windows/ci-s14-full.log.gz) retain separate complete plant/defuse/full-match scenarios and failed offline OCR/reload gates. [Stock-match receipt](windows/ci-s14/offline-full-match/results.json), [ten-row final roster](screens/windows-ci-s14/offline-full-match/08-final-scoreboard.png), [summary](screens/windows-ci-s14/offline-full-match/07-operation-complete.png), [plant receipt](windows/ci-s14/offline-plant/results.json), [defuse receipt](windows/ci-s14/offline-defuse/results.json), [visible LEAVE MATCH at failed lookup](screens/windows-ci-s14/offline-input/ocr-current.png).
- [Independent final S14 Linux and documentation challenge](reviews/independent-qa-s14-linux-review.md), [final S14 Linux original log](linux/ci-s14-full.log.gz), [QA archive integrity](reviews/independent-qa-s14-linux-artifact-integrity.json), [stock-match receipt](linux/ci-s14/offline-full-match/results.json), [ten-row roster](screens/linux-ci-s14/offline-full-match/08-final-scoreboard.png), [defuse receipt](linux/ci-s14/offline-defuse/results.json), [failed offline flow](linux/ci-s14/offline-input/results.json), [failed plant](linux/ci-s14/offline-plant/results.json), [layout partial result](linux/ci-s14/layouts/results.json). The1280×720 case has no final receipt after Xlib BadWindow; later sizes were not reached and that attempt's cleanup is UNVERIFIED.
- [Reproduced reload gate and causal limits](windows/reload-s14-comparison/DIAGNOSIS.md), [independent clock arithmetic](windows/reload-s14-comparison/clock-recomputation.json), [raw authority telemetry](windows/ci-s14/reload-release-first/authority-telemetry.json), [raw actions](windows/ci-s14/reload-release-first/actions.json.gz). Late authority completion does not pass the failed controller/normal-exit gates. The [original PR22 artifact retrieval](windows/original-reload/historical-windows-original-failure-retrieval.md), [verified hash chain](windows/original-reload/historical-windows-slice-integrity.json), [original server log](windows/original-reload/native-input/server.log) and [original reload image](screens/windows-original-reload/06-after-authority-reload-start.png) preserve original R admission without inventing missing timing clocks.
- [Complete S13 matrix](reviews/ci-s13-final-jobs.json), [Linux S13 original job log](linux/ci-s13-linux-full.log.gz), and [source14 artifact metadata snapshot](reviews/ci-s14-artifacts-snapshot.json) preserve later sources separately from the frozen S12 packages.
- Unedited fire-capture [before](screens/windows-fire-before-after/hosted-priority-validation-r1-offline-input-05-after-fire.png) and [after](screens/windows-fire-before-after/fire-ack-native-r1-extracted-05-after-fire.png) show 15/60 versus acknowledged 14/60 at their respective recorded sources. This corrects test synchronization; it does not replace a failed whole flow with a pass.

Validate retained copy integrity from this directory:

```sh
python3 - <<'PY'
import gzip, hashlib, json
from pathlib import Path
for item in json.loads(Path('index.json').read_text())['entries']:
    data = Path(item['path']).read_bytes()
    assert len(data) == item['bytes']
    assert hashlib.sha256(data).hexdigest() == item['sha256']
    original = gzip.decompress(data) if item['encoding'] == 'gzip' else data
    assert len(original) == item['original_bytes']
    assert hashlib.sha256(original).hexdigest() == item['original_sha256']
print('Retained evidence bytes verified; behavioral gates keep their recorded status.')
PY
```

Source-bound native-host build bundles are linked in the main report and artifact metadata. Download/extract the named inner game ZIP with its own checksum and source receipt; the outer Actions bundle contains diagnostics and test state. Local five-target ZIPs remain in `builds/playability-r12/`. Neither a successful package inspection nor availability of a failed-job artifact certifies gameplay, signing/notarization, Steam readiness or production security.
