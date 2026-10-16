"""Spectrogram PNG of a 16-bit mono WAV (the reload audio capture's mix_*.wav), for the evidence folder.

python3 spectrogram.py <in.wav> <out.png> [title]

Time runs left to right (a tick every 0.5 s), frequency bottom to top (log axis, 100 Hz to 10 kHz), level as brightness (dB
relative to the loudest cell, 60 dB range). Needs Pillow and NumPy (system Python). It shows WHEN things sound and how loud; it
cannot say how they sound."""
import sys
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
title = sys.argv[3] if len(sys.argv) > 3 else src
with wave.open(src) as w:
    rate = w.getframerate()
    data = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(float) / 32768.0
win, hop = 2048, 256
frames = [data[i:i + win] * np.hanning(win) for i in range(0, len(data) - win, hop)]
spec = np.abs(np.fft.rfft(np.array(frames), axis=1)).T + 1e-9
freqs = np.fft.rfftfreq(win, 1.0 / rate)
centres = np.geomspace(100, 10000, 160)
rows = np.array([np.interp(centres, freqs, spec[:, k]) for k in range(spec.shape[1])]).T
db = 20 * np.log10(rows / rows.max())
img = np.clip((db + 60) / 60, 0, 1)[::-1]
pic = Image.fromarray((img * 255).astype(np.uint8)).resize((img.shape[1], img.shape[0] * 3), Image.NEAREST).convert('RGB')
canvas = Image.new('RGB', (pic.width, pic.height + 30), (17, 17, 17))
canvas.paste(pic, (0, 30))
d = ImageDraw.Draw(canvas)
font = ImageFont.load_default(size=14)
d.text((6, 7), title, fill=(230, 230, 230), font=font)
seconds = len(data) / rate
for t in np.arange(0, seconds, 0.5):
    x = int(t * rate / hop)
    d.line([(x, 30), (x, 36)], fill=(255, 255, 0))
    d.text((x + 2, 30), '%.1fs' % t, fill=(255, 255, 0), font=font)
canvas.save(out)
print(out, canvas.size)
