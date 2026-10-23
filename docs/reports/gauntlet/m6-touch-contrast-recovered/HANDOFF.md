# Touch contrast source handoff

Native execution is BLOCKED on independent R2 source/method review and the root's
single shared CPU/render-lane release. No engine, import, export, render, OCR or
recording ran. Product improvement and contrast remain unverified.

Branch `codex/m6-touch-contrast-recovered` is pushed. Product commit `b4d0c1b`
changes only `_draw` in touch_controls.gd. Preregistration `61151b5`; latest
source/method freeze `3c954d33546d70bf59cf6f9b6846f1cb82b6bca3`; exact receipt
[SOURCE_FREEZE-r2.json](SOURCE_FREEZE-r2.json). Baseline is exact published
`138a1ab810a29e3c504f5811a0051a08e1ad52b9`.

R2 has fourteen passing pure controls and replays all four independent retained
R1 falsifiers with zero false accepts. The two prepared projects have verified
323 original paths each, plus exact fixture and generated diagnostic UID/source
hashes. They are under `/workspace/sightbreak-touch-contrast-fixture-recovered-r2`.
R1 projects and rejected source/receipts remain retained separately.

The next critic must audit the actual R2 code, isolated footprints, full-support
underlay/occlusion checks, exact matrix/source/background/image identities, and
inactive reconstruction gate. Native later-layer overlap may fail the strict
oracle; retain such failures. The complete dark surround against external
backgrounds remains an explicit independent-review requirement.

After both releases, use a fresh root-owned display, private state and fresh
output folders. The following commands are prepared and UNEXECUTED; the Xvfb
process, timeout, command receipts and cleanup belong to the root's released lane.

```sh
sightbreak_engine=/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64
touch_r2_root=/workspace/sightbreak-touch-contrast-fixture-recovered-r2
touch_r2_raw=/workspace/sightbreak-touch-contrast-native-recovered-r2
mkdir -p "$touch_r2_raw/backgrounds" "$touch_r2_raw/baseline" "$touch_r2_raw/candidate"
"$sightbreak_engine" --path "$touch_r2_root/baseline/game" --headless --editor --import --quit
"$sightbreak_engine" --path "$touch_r2_root/candidate/game" --headless --editor --import --quit
# DISPLAY must be the root-owned released display.
"$sightbreak_engine" --path "$touch_r2_root/baseline/game" --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/touch_contrast_capture.gd -- --mode=backgrounds --out="$touch_r2_raw/backgrounds"
"$sightbreak_engine" --path "$touch_r2_root/baseline/game" --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/touch_contrast_capture.gd -- --mode=controls --out="$touch_r2_raw/baseline" --background-dir="$touch_r2_raw/backgrounds"
"$sightbreak_engine" --path "$touch_r2_root/candidate/game" --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/touch_contrast_capture.gd -- --mode=controls --out="$touch_r2_raw/candidate" --background-dir="$touch_r2_raw/backgrounds"
python3 scripts/analyze_touch_contrast.py --baseline "$touch_r2_raw/baseline" --candidate "$touch_r2_raw/candidate" --backgrounds "$touch_r2_raw/backgrounds" --freeze docs/reports/gauntlet/m6-touch-contrast-recovered/SOURCE_FREEZE-r2.json --out "$touch_r2_raw/recomputed.json"
```

Then retain exact original PNGs, native logs, source/UID receipts, all failures,
cleanup and archive hashes. Root assigns a separate fresh blind judge to comparable
normal captures with the mapping outside its packet. Existing touch/input-mode
native tests, live HUD touch-toggle capture and appropriate broader validation
remain unrun. No new native result may inherit historical numbers.

Official Luanti pixels were inspected as contextual references; no third-party
pixels entered Git. Shipped CS2 media hosts remain blocked. No shipped-title
parity, physical touch ergonomics, complete accessibility or presentation gate
is closed by source/pure work.
