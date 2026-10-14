"""Turn bake.py's raw passes into the game texture set.

python3 textures.py <bake_dir> <name> <out_dir> [--size 1024]

  <name>_albedo.png  sRGB base colour
  <name>_orm.png     R occlusion, G roughness, B metallic (Godot ORMMaterial3D)
  <name>_normal.png  tangent-space normal, OpenGL (+Y), renormalised after resizing
Requires Pillow and NumPy (system Python; Blender's bundled Python has no Pillow).
"""
import pathlib
import sys
import numpy as np
from PIL import Image

args = sys.argv[1:]
size = 1024
if '--size' in args:
    i = args.index('--size'); size = int(args[i + 1]); del args[i:i + 2]
bake_dir, name, out = pathlib.Path(args[0]), args[1], pathlib.Path(args[2])
out.mkdir(parents=True, exist_ok=True)


def load(label, mode='L'):
    image = Image.open(bake_dir / f'{name}_{label}_raw.png').convert(mode)
    return image.resize((size, size), Image.LANCZOS) if image.width != size else image


load('albedo', 'RGB').save(out / f'{name}_albedo.png', optimize=True)
orm = Image.merge('RGB', (load('occlusion'), load('roughness'), load('metallic')))
orm.save(out / f'{name}_orm.png', optimize=True)

normal = np.asarray(load('normal', 'RGB'), dtype=np.float32) / 127.5 - 1.0
normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-6)
Image.fromarray(np.clip((normal + 1.0) * 127.5 + 0.5, 0, 255).astype(np.uint8)).save(out / f'{name}_normal.png', optimize=True)
for label in ('albedo', 'orm', 'normal'):
    path = out / f'{name}_{label}.png'
    print('TEXTURE', path, path.stat().st_size)
