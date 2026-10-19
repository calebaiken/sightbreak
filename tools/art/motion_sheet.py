"""Labelled contact sheet of a game/tests/weapon_motion_capture.gd frame sequence.

python3 motion_sheet.py <capture_dir> <out.png> <title> [frame ...]

Each tile is labelled with its frame number, simulated time, phase, ammunition and,
during a reload, the clip time, all read from the capture's frames.csv. Without frame
numbers it picks 16 evenly spaced frames. Requires Pillow (system Python).
"""
import csv, os, re, sys
from PIL import Image, ImageDraw, ImageFont
d, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
# The stage of the reload each tile is in, from the phase boundaries the game and the clip share (reload_phases.gd).
_phases_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'game', 'scripts', 'gameplay', 'reload_phases.gd')
P = {m.group(1): float(m.group(2)) for m in re.finditer(r'^const ([A-Z_]+) := ([0-9.]+)\s*$', open(_phases_file).read(), re.M)}
STAGES = [(0.0, 'reach'), (P['GRASP'], 'grasp'), (P['UNLATCH'], 'unlatch + extraction'), (P['CLEAR'], 'swing out'), (P['DROP'], 'release / drop'),
          (P['HIP_OUT'], 'to the hip (retrieval)'), (P['ACQUIRE'], 'replacement taken'), (P['HIP_IN'], 'carry up'), (P['ALIGN'], 'align + insertion'),
          (P['SEAT'], 'seated'), (P['LETGO'], 'return'), (1.0, 'ready')]


def stage_of(r):
    if r['phase'] != 'reload':
        return 'ready' if int(r['ammo']) >= 30 else 'first shots'
    p = float(r['clip_time_s'])
    return [name for start, name in STAGES if p >= start][-1]


rows = {int(r['frame']): r for r in csv.DictReader(open(f'{d}/frames.csv'))}
picks = [int(f) for f in sys.argv[4:]] or list(range(0, max(rows) + 1, max(1, (max(rows) + 1) // 16)))[:16]
first = Image.open(f'{d}/{picks[0]:03d}.png')
tw, lab, cols = 400, 22, 4
th = round(tw * first.height / first.width)   # tiles keep the frame's own aspect ratio (16:9, 20:9, 4:3 captures)
font = ImageFont.load_default(size=15)
n = len(picks); rws = (n + cols - 1) // cols
sheet = Image.new('RGB', (cols * tw, 30 + rws * (th + lab)), (17, 17, 17))
dr = ImageDraw.Draw(sheet)
dr.text((8, 7), title, fill=(230, 230, 230), font=font)
for i, f in enumerate(picks):
    r = rows[f]
    x, y = (i % cols) * tw, 30 + (i // cols) * (th + lab)
    sheet.paste(Image.open(f'{d}/{f:03d}.png').convert('RGB').resize((tw, th), Image.LANCZOS), (x, y + lab))
    clip = f"  clip {float(r['clip_time_s']):.2f}" if r['phase'] == 'reload' else ''
    dr.text((x + 6, y + 3), f"#{f} {float(r['time_s']):.2f}s {stage_of(r)}{clip}", fill=(200, 200, 200), font=font)
sheet.save(out, optimize=True)
print(out, sheet.size)
