#!/usr/bin/env bash
# Real-time 60 Hz sequences of the reload and the first shots after it, for the evidence folder: lighting views, aspect
# variants (simulated viewports, with the dimensions the PNGs really have recorded in viewport.txt), reduced motion variants.
#   scripts/capture_reload_matrix.sh <out_dir> [scratch_dir]        needs a native display (DISPLAY=:99 under Xvfb) and ffmpeg
# Per configuration: a labelled contact sheet (sheets/), a normal-speed and a quarter-speed clip (clips/), the per-tick CSV and
# the viewport record (logs/), and the PNGs of the stage ticks (frames/). The PNGs of every tick stay in the scratch directory.
set -euo pipefail
out="$(cd "$(dirname "${1:?out dir}")" && pwd)/$(basename "$1")"
scratch="${2:-$(mktemp -d)}"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$out/sheets" "$out/clips" "$out/logs" "$out/frames" "$scratch"
export DISPLAY="${DISPLAY:-:99}"
# name | args
configs=(
  "sunlit|--view=sunlit"
  "backlight|--view=backlight"
  "shade|--view=shade"
  "dark-interior|--view=dark"
  "sunlit-wide-20x9|--view=sunlit --size=1600x720"
  "sunlit-tall-4x3|--view=sunlit --size=960x720"
  "reduced-current|--view=sunlit --reduced --variant=current"
  "reduced-calm|--view=sunlit --reduced --variant=calm"
  "reduced-still|--view=sunlit --reduced --variant=still"
)
for entry in "${configs[@]}"; do
  name="${entry%%|*}"; args="${entry#*|}"
  dir="$scratch/$name"
  rm -rf "$dir"
  "$repo/scripts/godot.sh" --audio-driver Dummy --rendering-method gl_compatibility --script res://tests/reload_sequence_capture.gd -- --out="$dir" --fire --tail=0.55 $args 2>&1 | grep "RELOAD_SEQUENCE_CAPTURE\|ERROR" || true
  cp "$dir/frames.csv" "$out/logs/frames-$name.csv"
  cp "$dir/viewport.txt" "$out/logs/viewport-$name.txt"
  last=$(ls "$dir"/*.png | wc -l); last=$((last - 1))
  # 20 tiles, evenly across the reload (0..134) then the first shots (135..)
  python3 "$repo/tools/art/motion_sheet.py" "$dir" "$out/sheets/$name.jpg" "$name  $(cat "$dir/viewport.txt")" 0 14 28 34 44 52 58 66 74 82 90 98 104 110 118 126 134 137 141 146 >/dev/null
  ffmpeg -y -loglevel error -framerate 60 -i "$dir/%03d.png" -c:v libx264 -pix_fmt yuv420p -crf 22 "$out/clips/$name.mp4"
  ffmpeg -y -loglevel error -framerate 15 -i "$dir/%03d.png" -c:v libx264 -pix_fmt yuv420p -crf 22 "$out/clips/$name-quarter-speed.mp4"
  for tick in 0 36 52 68 96 104 118 137; do
    [ -f "$dir/$(printf %03d $tick).png" ] && python3 -c "from PIL import Image; Image.open(\"$dir/$(printf %03d $tick).png\").convert(\"RGB\").save(\"$out/frames/$name-$(printf %03d $tick).jpg\", quality=88, optimize=True)"
  done
  echo "done $name ($last ticks)"
done
