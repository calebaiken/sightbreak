#!/usr/bin/env python3
"""Independent local OCR replay on untouched retained Linux capture pixels."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path('/workspace/sightbreak-offline-flow')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'scripts'))
from verify_offline_export import read_hud_pixels

commands = []
def ocr(image, psm, label):
    payload = io.BytesIO()
    image.save(payload, format='PNG')
    command = ['tesseract','stdin','stdout','--psm',str(psm)]
    started = time.monotonic()
    result = subprocess.run(command, input=payload.getvalue(), capture_output=True, timeout=20)
    commands.append(dict(command=command,label=label,elapsed_seconds=time.monotonic()-started,
                         exit=result.returncode,stdout=result.stdout.decode(errors='replace'),
                         stderr=result.stderr.decode(errors='replace')))
    if result.returncode:
        raise RuntimeError('OCR failed')
    return result.stdout.decode(errors='replace')

paths = [('native-r1/native-candidate-r2/'+name+'.png',expected) for name,expected in [
    ('02-offline-spawn',(15,60)),('04-move-aim',(15,60)),('05-after-fire',(14,60)),
    ('06-after-reload',(15,59)),('06b-scoreboard',(15,59)),('06e-purchased-smg',(30,120))]]
paths += [('focus-r1/native-focus-r1/'+name+'.png',expected) for name,expected in [
    ('02-offline-spawn',(15,60)),('11b-resumed-held-input-neutral',(14,60)),('11c-fresh-press-movement',(14,60))]]
rows = []
for path, expected in paths:
    try:
        reading = read_hud_pixels(HERE / path, ocr)
        rows.append(dict(path=path,expected_ammo_reserve=expected,reading=reading,
                         passed=(reading['ammo'],reading['reserve'])==expected,
                         sha256=hashlib.sha256((HERE/path).read_bytes()).hexdigest()))
    except Exception as error:
        rows.append(dict(path=path,expected_ammo_reserve=expected,error=str(error),passed=False))
output = HERE / ('independent-linux-hud.json' if len(sys.argv)<2 else sys.argv[1])
assert not output.exists(), 'Preserve earlier evidence; provide a fresh output filename'
output.write_text(json.dumps(dict(scope='Unchanged actual candidate Linux captures, local OCR only',rows=rows,commands=commands),indent=2)+'\n')
print(json.dumps(dict(passes=sum(row['passed'] for row in rows),total=len(rows),
                      maximum_ocr_seconds=max(command['elapsed_seconds'] for command in commands))))
sys.exit(not all(row['passed'] for row in rows))
