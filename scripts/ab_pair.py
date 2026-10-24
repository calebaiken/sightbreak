#!/usr/bin/env python3
"""Blind A/B pairs for visual review.

Builds randomized, unlabelled pairs from two sets of frames (ours and a reference: the previous build, or a CS2 reference
image when one is provided) so a reviewer who has not seen the work can pick the stronger presentation without knowing which is which.

    scripts/ab_pair.py make --ours f1.png f2.png ... --ref g1.png g2.png ... --out DIR --key KEYFILE --seed TEXT
                       [--crop x,y,w,h] [--size WxH] [--label "short neutral caption"] [--strip]
    scripts/ab_pair.py decode --key KEYFILE --winner A|B [--pair N]

`make` pairs ours[i] with ref[i] (same count), writes DIR/pair<i>_A.jpg, DIR/pair<i>_B.jpg and DIR/pair<i>.jpg (A left, B right, neutral
"A"/"B" tags) and, with --strip, DIR/strip_A.jpg and DIR/strip_B.jpg (all frames of a side tiled in order, for motion judged as a
filmstrip). Which side is ours is drawn per pair from a seeded RNG and stored ONLY in the key file, which must live outside DIR and
must not be shown to the reviewer. Both sides are resized to one size and re-encoded through the same JPEG quality so the file type
and compression do not give the answer away. The key file also records every source path and the seed so a result can be audited.
"""
import argparse
import hashlib
import json
import os
import random
import sys

from PIL import Image, ImageDraw


def load(path, crop, size):
    image = Image.open(path).convert("RGB")
    if crop:
        x, y, w, h = crop
        image = image.crop((x, y, x + w, y + h))
    if size:
        image = image.resize(size, Image.LANCZOS)
    return image


def tag(image, text):
    out = image.copy()
    draw = ImageDraw.Draw(out)
    draw.rectangle((0, 0, 14 + 9 * len(text), 22), fill=(0, 0, 0))
    draw.text((7, 5), text, fill=(255, 255, 255))
    return out


def tile(images, columns):
    w, h = images[0].size
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (w * columns, h * rows))
    for i, image in enumerate(images):
        sheet.paste(image, ((i % columns) * w, (i // columns) * h))
    return sheet


def make(args):
    if len(args.ours) != len(args.ref):
        sys.exit("--ours and --ref need the same number of frames (%d vs %d)" % (len(args.ours), len(args.ref)))
    crop = tuple(int(v) for v in args.crop.split(",")) if args.crop else None
    size = tuple(int(v) for v in args.size.lower().split("x")) if args.size else None
    os.makedirs(args.out, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(args.key)), exist_ok=True)
    key = {"seed": args.seed, "label": args.label, "pairs": []}
    sides_a, sides_b = [], []
    for i, (ours_path, ref_path) in enumerate(zip(args.ours, args.ref)):
        rng = random.Random("%s:%d" % (args.seed, i))
        ours_is = rng.choice("AB")
        ours = load(ours_path, crop, size)
        ref = load(ref_path, crop, size)
        if size is None and ours.size != ref.size:
            ref = ref.resize(ours.size, Image.LANCZOS)
        a, b = (ours, ref) if ours_is == "A" else (ref, ours)
        a_path = os.path.join(args.out, "pair%d_A.jpg" % i)
        b_path = os.path.join(args.out, "pair%d_B.jpg" % i)
        a.save(a_path, quality=92, subsampling=0)
        b.save(b_path, quality=92, subsampling=0)
        both = Image.new("RGB", (a.width * 2 + 8, a.height), (24, 24, 24))
        both.paste(tag(a, "A"), (0, 0))
        both.paste(tag(b, "B"), (a.width + 8, 0))
        both.save(os.path.join(args.out, "pair%d.jpg" % i), quality=92, subsampling=0)
        sides_a.append(a)
        sides_b.append(b)
        key["pairs"].append({"pair": i, "ours_is": ours_is, "ours": os.path.abspath(ours_path), "ref": os.path.abspath(ref_path),
                             "ours_sha256": hashlib.sha256(open(ours_path, "rb").read()).hexdigest()})
    if args.strip and len(sides_a) > 1:
        columns = min(len(sides_a), args.columns)
        # a filmstrip keeps each side's own order, but which side is ours per pair was drawn per pair, so a strip mixes: use one draw for the strip
        rng = random.Random("%s:strip" % args.seed)
        ours_is = rng.choice("AB")
        ours_strip = [load(p, crop, size) for p in args.ours]
        ref_strip = [load(p, crop, size) for p in args.ref]
        sa, sb = (ours_strip, ref_strip) if ours_is == "A" else (ref_strip, ours_strip)
        tile([tag(f, "A %d" % n) for n, f in enumerate(sa)], columns).save(os.path.join(args.out, "strip_A.jpg"), quality=90, subsampling=0)
        tile([tag(f, "B %d" % n) for n, f in enumerate(sb)], columns).save(os.path.join(args.out, "strip_B.jpg"), quality=90, subsampling=0)
        key["strip_ours_is"] = ours_is
    json.dump(key, open(args.key, "w"), indent=1)
    print(json.dumps({"out": args.out, "pairs": len(key["pairs"]), "strip": "strip_ours_is" in key}))


def decode(args):
    key = json.load(open(args.key))
    if args.pair is None and "strip_ours_is" in key:
        ours_is = key["strip_ours_is"]
    else:
        ours_is = key["pairs"][args.pair or 0]["ours_is"]
    print("ours" if args.winner.upper() == ours_is else "reference")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("make")
    m.add_argument("--ours", nargs="+", required=True)
    m.add_argument("--ref", nargs="+", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--key", required=True)
    m.add_argument("--seed", required=True)
    m.add_argument("--crop")
    m.add_argument("--size")
    m.add_argument("--label", default="")
    m.add_argument("--strip", action="store_true")
    m.add_argument("--columns", type=int, default=4)
    d = sub.add_parser("decode")
    d.add_argument("--key", required=True)
    d.add_argument("--winner", required=True)
    d.add_argument("--pair", type=int)
    args = p.parse_args()
    {"make": make, "decode": decode}[args.cmd](args)


if __name__ == "__main__":
    main()
