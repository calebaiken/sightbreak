#!/usr/bin/env bash
set -u
cd /workspace/sightbreak-integration
export DISPLAY=:99
out=/workspace/reviews/integration-20261013/art-independent
git rev-parse HEAD > "$out/capture-source-sha.txt"
git rev-parse HEAD:game > "$out/capture-game-tree.txt"
scripts/godot.sh --audio-driver Dummy --script "$out/projection_render_test.gd" > "$out/projection-render.log" 2>&1
printf 'projection exit=%s\n' "$?"
scripts/godot.sh --audio-driver Dummy --script res://tests/paint_visibility_test.gd > "$out/combined-paint-visibility.log" 2>&1
printf 'paint exit=%s\n' "$?"
for size in 1280x720 1600x720 1024x768; do
  scripts/godot.sh --audio-driver Dummy --script res://tests/weapon_art_capture.gd -- "--capture-dir=$out/stills/$size" "--size=$size" > "$out/captures-$size.log" 2>&1
  printf 'stills %s exit=%s\n' "$size" "$?"
done
scripts/godot.sh --audio-driver Dummy --script "$out/fallback_projection.gd" > "$out/fallback.log" 2>&1
printf 'fallback exit=%s\n' "$?"
for size in 1280x720 1600x720 1024x768; do
  for view in sunlit backlit shade; do
    scripts/godot.sh --audio-driver Dummy --fixed-fps 30 --script res://tests/weapon_motion_capture.gd -- "--capture-dir=$out/motion/$size-$view" "--view=$view" "--size=$size" > "$out/motion-$size-$view.log" 2>&1
    printf 'motion %s %s exit=%s\n' "$size" "$view" "$?"
  done
done

git rev-parse HEAD > "$out/capture-source-sha-after.txt"
