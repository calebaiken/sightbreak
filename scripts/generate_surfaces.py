#!/usr/bin/env python3
"""Generate original seamless 128px surface tiles using only Python's standard library.

Neutral greys multiply existing arena colors. Grain stays baked; no runtime noise,
procedural shaders, transparency or added lights. Optional companion normal and
roughness maps are disabled on low graphics. Seeded and byte-reproducible.
"""
import math
from pathlib import Path
import random
import struct
import zlib

SIZE = 128
DEST = Path(__file__).resolve().parents[1] / "game/assets/materials"


def chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def generate(name, seed):
    rng = random.Random(seed)
    rows = bytearray()
    for y in range(SIZE):
        rows.append(0)
        for x in range(SIZE):
            broad = math.sin(x / SIZE * math.tau * 2 + 0.7) * math.cos(y / SIZE * math.tau * 3)
            grain = rng.random()
            if name == "asphalt":
                value = 231 + broad * 7 + (grain - 0.5) * 32
                if grain < 0.08:
                    value -= 25
            elif name == "concrete":
                value = 239 + broad * 1 + (grain - 0.5) * 14
                if grain < 0.026:
                    value -= 28
            else:
                value = 247 + broad * 0.4 + (grain - 0.5) * 7
                # Short sparse paint scratches repeat without an obvious broad stripe.
                if (y * 71 + seed) % 127 < 2 and (x + y * 3) % 29 < 12:
                    value -= 22
            v = max(0, min(255, round(value)))
            rows.extend((v, v, v))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows), 9))
    png += chunk(b"IEND", b"")
    (DEST / f"{name}.png").write_bytes(png)


if __name__ == "__main__":
    DEST.mkdir(parents=True, exist_ok=True)
    for name, seed in (("asphalt", 7301), ("concrete", 9181), ("painted_metal", 4303)):
        generate(name, seed)

# Optional PBR companion maps. These have no runtime noise or transparency and
# share 128px residency with the color tiles. Low graphics disables both maps.
def generate_companions(name, seed):
    rng = random.Random(seed)
    heights = []
    for y in range(SIZE):
        row = []
        for x in range(SIZE):
            broad = math.sin(x / SIZE * math.tau * 2 + .7) * math.cos(y / SIZE * math.tau * 3)
            grain = rng.random()
            value = broad * .03 + (grain - .5) * (.20 if name == 'asphalt' else .07)
            if name == 'painted_metal' and (y * 71 + seed) % 127 < 2 and (x + y * 3) % 29 < 12:
                value -= .12
            row.append(value)
        heights.append(row)
    for kind in ('normal', 'roughness'):
        rows = bytearray()
        for y in range(SIZE):
            rows.append(0)
            for x in range(SIZE):
                if kind == 'normal':
                    dx = (heights[y][(x + 1) % SIZE] - heights[y][(x - 1) % SIZE]) * .8
                    dy = (heights[(y + 1) % SIZE][x] - heights[(y - 1) % SIZE][x]) * .8
                    length = math.sqrt(dx * dx + dy * dy + 1)
                    pixel = [round((v / length * .5 + .5) * 255) for v in (-dx, dy, 1)]
                else:
                    base = .78 if name == 'painted_metal' else .96
                    value = max(0, min(255, round((base + heights[y][x] * .4) * 255)))
                    pixel = [value] * 3
                rows.extend(pixel)
        png = b'\x89PNG\r\n\x1a\n'
        png += chunk(b'IHDR', struct.pack('>IIBBBBB', SIZE, SIZE, 8, 2, 0, 0, 0))
        png += chunk(b'IDAT', zlib.compress(bytes(rows), 9))
        png += chunk(b'IEND', b'')
        (DEST / f'{name}_{kind}.png').write_bytes(png)


if __name__ == '__main__':
    for name, seed in (('asphalt', 7301), ('concrete', 9181), ('painted_metal', 4303)):
        generate_companions(name, seed)
