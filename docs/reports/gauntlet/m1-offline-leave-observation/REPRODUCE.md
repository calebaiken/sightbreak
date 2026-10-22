# Reproduce the observer checks

Extract `evidence-r1.tar.gz` into a new directory and verify its manifest before
replaying. The following commands analyze retained pixels; they do not run a
Windows client.

```sh
python3 replay_baseline.py \
  --controller /extracted/controllers/windows-dc2a198.py \
  --pixels /extracted/windows-native/ocr-current.png \
  --output /new/baseline-replay
python3 compare_menu_pixels.py \
  --candidate /extracted/controllers/candidate-4a9ee7b.py \
  --baseline /extracted/controllers/windows-dc2a198.py \
  --captures /extracted/windows-native --output /new/pixel-comparison
```

The comparison uses the candidate's strict complete-caption predicate for both
transforms. Its baseline score must be described that way. The separate baseline
replay invokes the original production word reader and exact LEAVE token lookup.

From a clean checkout containing the correction, export a fresh source identity
and use the existing bounded native probe:

```sh
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-leave" python3 scripts/export.py linux
SIGHTBREAK_BUILDS_DIR="$PWD/builds/new-leave" \
  XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb \
  python3 docs/reports/gauntlet/m1-offline-journey-life-boundary/verify_native_settings_only.py \
  --target linux --display :195 --output builds/new-leave-probe
python3 scripts/test_offline_export_ocr.py -v
```

The native probe runs the first stock match with a sidearm. Settings restart,
second-round purchase, focus recovery and native Windows remain outside its
scope. Retain the actual main-menu image, actions, source/export records and raw
`ocr-stdout` logs; inspect them independently before accepting the slice.
