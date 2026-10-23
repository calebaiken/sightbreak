# Reproduced exported baseline

Clean source561d0cbba651514bfac96c50437a849d65843545, game tree45b6c6ea9d3244700e324e90d6df4778ee28d18e.
Godot4.7.2 official, Linux Xvfb1280x720, Mesa software renderer, LP_NUM_THREADS=2.
Actual OS keyboard/mouse input; ordinary objective fixture, no altered timers or save writes.

The original controller fails in68.384 wall seconds at `move_to(-15,8)` with its
original15s budget. The local player remains alive100HP and oscillates around the
target; final observed z7.6983 with velocity−5.1m/s. Ordinary Q smoke inventory was
consumed. Both native process cleanup and Xvfb cleanup are clean. Plant/defuse and
restart were not reached. This reproduces the retained S14 overshoot failure.

The archive preserves unmodified results, actions, raw screenshots/logs/trace,
source receipt and a60s five-frame/second X11 recording started after initial
conditions. Encoding used one CPU thread/ultrafast and adds capture overhead;
software timing is not hardware responsiveness or phone performance evidence.
The original source-bound export and screenshot are inspected; this record makes
no shipped-game visual-quality comparison.

```sh
python3 scripts/export.py linux
XVFB_BIN=/workspace/tools/xvfb/usr/bin/Xvfb LIBGL_ALWAYS_SOFTWARE=1 LP_NUM_THREADS=2 python3 scripts/verify_offline_match.py --target linux --scenario plant --display :181 --timeout 180 --output builds/mission-m1/plant-baseline
```

Reference baseline is the actual exported561d0cb candidate, with exact receipt and
hashes inside the archive. Read results/error and full action trace before judging
candidate improvement. The existing15s/.45m/neutral/stopped/two-tick contract stays fixed.
