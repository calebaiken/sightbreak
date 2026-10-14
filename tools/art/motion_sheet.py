"""Labelled contact sheet of a game/tests/weapon_motion_capture.gd frame sequence.

python3 motion_sheet.py <capture_dir> <out.png> <title> [frame ...]

Each tile is labelled with its frame number, simulated time, phase, ammunition and,
during a reload, the clip time, all read from the capture's frames.csv. Without frame
numbers it picks 16 evenly spaced frames. Requires Pillow (system Python).
"""
import csv, sys
from PIL import Image, ImageDraw, ImageFont
d, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
rows = {int(r['frame']): r for r in csv.DictReader(open(f'{d}/frames.csv'))}
picks = [int(f) for f in sys.argv[4:]] or list(range(0, max(rows) + 1, max(1, (max(rows) + 1) // 16)))[:16]
tw, th, lab, cols = 400, 225, 22, 4
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
    dr.text((x + 6, y + 3), f"#{f}  t={float(r['time_s']):.2f}s  {r['phase']}  ammo {r['ammo']}{clip}", fill=(200, 200, 200), font=font)
sheet.save(out, optimize=True)
print(out, sheet.size)
