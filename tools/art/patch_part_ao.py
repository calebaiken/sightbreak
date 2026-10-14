"""Merge a part's re-baked occlusion (rebake_part_ao.py) into a full occlusion bake.

python3 patch_part_ao.py <occlusion_raw.png> <part_ao_on_black.png> <part_ao_on_white.png> <out.png>

The part's UV islands (with their bleed margin) are the texels where the black-canvas and
white-canvas bakes agree; there the part's own occlusion replaces the full bake's, and
every other texel is left exactly as it was. Prints how much of the part's surface was
nearly fully occluded before and after. Requires Pillow and NumPy (system Python).
"""
import sys
import numpy as np
from PIL import Image

full_path, black_path, white_path, out_path = sys.argv[1:5]
full = np.asarray(Image.open(full_path).convert('L'), dtype=np.float32) / 255.0
black = np.asarray(Image.open(black_path).convert('L'), dtype=np.float32) / 255.0
white = np.asarray(Image.open(white_path).convert('L'), dtype=np.float32) / 255.0
assert full.shape == black.shape == white.shape, 'bakes must share one resolution'

island = np.abs(black - white) < 0.02
own = black
patched = np.where(island, own, full)
dark_before = float((full[island] < 0.1).mean())
dark_after = float((patched[island] < 0.1).mean())
print('island texels: %d (%.1f %% of the atlas)' % (island.sum(), 100.0 * island.mean()))
print('mean occlusion over the part: %.3f -> %.3f' % (full[island].mean(), patched[island].mean()))
print('texels below 0.1 over the part: %.1f %% -> %.1f %%' % (100 * dark_before, 100 * dark_after))
Image.fromarray(np.clip(patched * 255.0 + 0.5, 0, 255).astype(np.uint8), 'L').save(out_path)
print('WROTE', out_path)
