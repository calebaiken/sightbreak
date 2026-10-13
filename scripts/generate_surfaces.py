#!/usr/bin/env python3
"""Generate original seamless 128px surface tiles using only Python's standard library.

Neutral greys multiply existing arena colors. Grain stays baked; no runtime noise,
normal mapping, transparency or added lights. Seeded and byte-reproducible.
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
