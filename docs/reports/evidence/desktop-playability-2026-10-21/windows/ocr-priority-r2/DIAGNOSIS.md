# Native Windows OCR rendering-priority diagnostic

Source `7effe4c897c38b2df1c93acd09402ad1e3b0a1c3`; dedicated diagnostic branch only. Run https://github.com/calebaiken/sightbreak/actions/runs/39675076664, job119482705020. Artifact12381496833, archive SHA256 `752acab0fd089b0413e0ba632da47736a7e87a7df65a48c36cfe9a9bd2657399`. Raw `ocr-probe/results.json` and decoded log retained beside this report.

A fixed retained raw screenshot was proven byte-identical to the exact failed `ocr-current.png` from the earlier native Windows offline attempt: SHA256 `522549e44d7f0f3fd0ef532aef9e4c55aafc508f71dff6ac16e3568514b42a59`. Same grayscale/145threshold/2560x1440 analysis input, Tesseract `stdin stdout --psm11 tsv`, unchanged20second subprocess limit. No OpenMP change, affinity mutation, game logic change, gameplay injection or active match in this diagnostic. Native actual exported menu runs normally and closes with exit0.

Four counterbalanced ABBA trials changed ONLY the owned menu game's Windows process priority between NORMAL0x20 and BELOW_NORMAL0x4000, restoring independently observed original ABOVE_NORMAL0x8000 after each trial. This NORMAL comparison is not the original game default. The OCR child itself was independently observed BELOW_NORMAL0x4000 in all four trials; do not describe it as actually NORMAL. Foreground PID/window and actual priorities/affinity were measured each time; both processes retained mask0xf, all4logicalCPUs.

| Game priority | Trial1 OCR wall | Trial2 OCR wall | Result |
|---|---:|---:|---|
| NORMAL0x20 |10.234s|10.344s|exit0, no timeout|
| BELOW_NORMAL0x4000 |1.203s|1.109s|exit0, no timeout|

All4 TSV outputs were exactly identical (SHA256 `a1f841bc2844c9b6911d6be4a0e7e331dedc696f0e43721fb93f11534356c42c`,4117bytes,34words, same VECTORLINE bounds705,461,247,27). OCR CPU time .4375–.53125s. The synchronized game CPU windows consumed39.3125/39.765625 CPU seconds at NORMAL versus4.15625/3.953125 at BELOW_NORMAL. This supports measured resource starvation under this hosted software-rendering load and a bounded test-only resource-normalization option; it does not reproduce the earlier20s timeout or establish any historical network reload cause.

The preceding eight-trial default-versus-OMP_THREAD_LIMIT1 experiment showed no improvement: normal idle OCR .218–.235s, rendered-menu8.125–10.734s, all exit0/identical output. Both raw negative OpenMP evidence and the original failed gameplay evidence remain retained. No OMP fix was implemented.
