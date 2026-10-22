# Independent local four-size capture review

The frozen local export at source `872a57618c079c5854dea47d361cc7da732378ec` passes capture generation at all four requested sizes. This is the root agent's completed local run, independently audited from its original files. It is separate from GitHub Actions run 39725980732, whose final raw outcome is pending at this increment.

| Size | Generation | Wall seconds | Named captures |
| --- | --- | ---: | ---: |
| 960×540 | Pass | 47.191501 | 5 |
| 1280×720 | Pass, including explicit touch on/off | 71.280758 | 7 |
| 1920×1080 | Pass | 100.213823 | 5 |
| 1280×800 | Pass | 61.357670 | 5 |

Aggregate wall time is 280.214609 seconds. Every case satisfies the original 120-second limit, and the aggregate satisfies the original 520-second limit. All twelve owned child processes exit 0; every case records native menu and live exits 0 with no cleanup errors. Sixteen UI transitions retain at least two actual drawn frames before confirming rendered pixels. This verifies functional software-rendered capture generation, not physical-device performance.

## Source and original-byte preservation

The original directory is `/workspace/sightbreak-linux-872a576/builds/layouts-872a576`. The command is `scripts/capture_desktop_layouts.py --touch-toggle --output builds/layouts-872a576`. The host receipt reports Linux 6.18.55, x86_64, glibc 2.41 and Godot `4.7.2.stable.official.ed1daf0bf`. Each case uses its own fresh Xvfb display and user-data directory. The main menu is a real exported menu; the separate live layout session explicitly uses `--demo`. It does not establish ordinary menu navigation, player objectives or full-match acceptance.

Independent reconstruction from 374 tracked Git-object byte records, including 126 shipping records and 248 validation records, gives:

- Game tree: `b13548eb130058468b3778d824f17ac1bfd3f724`.
- Shipping content SHA256: `9703e3b19f3feb13243f30ea9b244d411b08a5bb2b48d4c6a2bf88f5d2d71b47`.
- Validation SHA256: `2a7348b6f057b511ab9002d10120c98bc70096cde631b199cf080707d0474dc4`.
- Actual local ELF SHA256: `7f9d219340ba5192e7defa1467bbf78ceec4d0472770d605b2ada17481f39efb`, independently read from the 84,222,888-byte executable and matched against the export and capture receipts.

All identity fields match the clean source receipts; the final capture receipt attests exact source unchanged. Later documentation commits do not relabel this export. The reviewer does not independently reconstruct compiled game semantics from the ELF.

`local-layouts-originals.zip` retains 263 original files: 123 PNGs, 102 TSVs, ten JSON files, four JSONL traces and 24 logs. Only developer/import/shader caches are excluded. The archive is 19,756,308 bytes, SHA256 `6cdaee6df5c6f76b40b7a981b535c7df2ee8050e3b140fa7dc30e7fb18bac977`. Every archived member was read back and matched to the size/hash inventory. The original receipt files are unchanged, and no original pixels or TSV bytes were reconstructed from stdout.

The read-only verifier checks every named PNG's actual dimensions and hash, all 102 native OCR command input hashes and retained TSVs, source identity, actual executable bytes, standalone/aggregate case equality, frame fences, timing and exits. The final retained menu TSV at each size contains the required SIGHTBREAK and DEPLOY words. All OCR commands exit 0 within their original per-call limits, with child-only `OMP_THREAD_LIMIT=1`. This review executes no Godot, new render or OCR process.

## Direct image findings

The reviewer directly inspected all 22 original named PNGs: main menu, live HUD, roster, field menu and field settings at each size, plus touch opt-in and restored keyboard/mouse frames at 1280×720. The menus, roster rows and setting labels are visible in those stills; there is no additional obvious clipping in this named-frame sample. The 1280×800 frames retain their native letterboxing. The settings overlay dims the underlying game intentionally and has a visible scrollbar. No visual score or complete visual acceptance is assigned.

The original `1280x720/06-touch-hud-opt-in.png` shows a specific spacing defect: the top-right circular MENU control intersects the DEVICE / CARRIED label. The circle occupies approximately x 1201–1257, y 22–79 in the 1280×720 image, while the label crosses its upper band around y 28–40. Both texts remain readable in this still; this is an overlap finding, not a claim that the label is wholly unreadable. The original PNG hash is `2bd9a745dcf07ab6dc8b8c91f6a1ef0ac9980992bd81706242a3838cbcbc046f`.

That same touch-enabled frame still displays the keyboard footer, B BUY / E OBJECTIVE / TAB ROSTER / ESC MENU. The source sets the device-label right margin and footer visibility in `build_hud()` using the current control mode. That suggests inspecting whether a live mode change refreshes these elements. The source observation is a diagnosis lead; the overlap and stale keyboard footer are the actual retained pixel findings. No implementation change is part of this review.

The subsequent original `07-keyboard-mouse-restored.png` has no touch buttons, the keyboard footer is visible, and the carried-device label has no menu-circle overlap. Its SHA256 is `615b14c49dbe97a84454d16f06d132a90e097635a36980422d3e1373cbc7c8ac`. These images and their authority context support explicit native touch opt-in/off generation while leaving the spacing defect open.

## Comparison and remaining deficiency

The original Linux job at source `0ca125dfba637868e6e8e9772ff9c40400413e32`, run 39719407304, failed 960×540 and 1920×1080 with late positive menu confirmations and 1280×720 with a settings OCR timeout. Only its 1280×800 case passed. This new local run reaches every named frame and completes the touch transaction within the unchanged gates. Its native receipts provide actual improvement evidence on this local host. The saved-image CPU comparison alone would not establish that result, and neither the local pass nor the earlier microbenchmark establishes the pending remote run's layout outcome or sole causality.

The largest open product finding in these local images is the touch MENU/device-label overlap with a stale keyboard footer. Remote player-plant failure details and the remote four-size/full-match outcomes remain pending raw artifact review. These local captures do not close G1, Windows/macOS qualification, human play, broad bot behavior, physical performance or Linux release acceptance.
