"""Rows of the same capture ticks from several capture directories, labelled, as one contact sheet.
   compare_stages.py <out.jpg> <title> <ticks comma separated> <label=dir> [<label=dir> ...]
The tick labels sit in a strip above each column so they never cover the frame."""
import sys
from PIL import Image, ImageDraw

out, title, ticks = sys.argv[1], sys.argv[2], [int(t) for t in sys.argv[3].split(",")]
rows = [arg.split("=", 1) for arg in sys.argv[4:]]
TILE_W = 400
STAGES = {14: "reach", 36: "old magazine out", 58: "to the hip", 82: "carry up", 98: "insertion", 118: "return"}
first = Image.open("%s/%03d.png" % (rows[0][1], ticks[0]))
tile_h = round(TILE_W * first.height / first.width)
LEFT, TOP, STRIP = 90, 30, 22
sheet = Image.new("RGB", (LEFT + TILE_W * len(ticks), TOP + (tile_h + STRIP) * len(rows)), (16, 16, 18))
draw = ImageDraw.Draw(sheet)
draw.text((8, 8), title, fill=(235, 235, 235))
for r, (label, directory) in enumerate(rows):
    y = TOP + r * (tile_h + STRIP)
    draw.text((8, y + STRIP + tile_h // 2), label, fill=(235, 235, 235))
    for c, tick in enumerate(ticks):
        x = LEFT + c * TILE_W
        draw.text((x + 6, y + 5), "#%d %s" % (tick, STAGES.get(tick, "")), fill=(240, 210, 90))
        sheet.paste(Image.open("%s/%03d.png" % (directory, tick)).convert("RGB").resize((TILE_W, tile_h), Image.LANCZOS), (x, y + STRIP))
sheet.save(out, quality=88, optimize=True)
print(out, sheet.size)
