"""Derive review sheets/MP4s; preserve source frames and aspect ratio."""
import csv,json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
root=Path('/workspace/reviews/integration-20261013/art-independent')
results=[]
for d in sorted((root/'motion').glob('*')):
 if not (d/'frames.csv').exists(): continue
 rows=list(csv.DictReader((d/'frames.csv').open()))
 sizes={Image.open(p).size for p in d.glob('*.png')}
 phases={r['phase'] for r in rows}
 ammo=[int(r['ammo']) for r in rows]
 picks=[0,6,8,12,20,26,35,36,40,44,46,53,65,80,95,len(rows)-1]
 width,height=400,300
 sheet=Image.new('RGB',(width*4,40+(height+24)*4),(18,22,27))
 draw=ImageDraw.Draw(sheet);font=ImageFont.load_default(size=14)
 draw.text((8,10),f'Native combined d084e500 / {d.name} / diagnostic simulated 30 fps sequence / tiles preserve aspect',font=font,fill='white')
 for i,n in enumerate(picks):
  r=rows[n];im=Image.open(d/f'{n:03}.png').convert('RGB')
  tile=ImageOps.contain(im,(width,height))
  x=(i%4)*width;y=40+(i//4)*(height+24)
  draw.text((x+4,y+3),f'#{n} {r["time_s"]}s {r["phase"]} ammo {r["ammo"]} clip {r["clip_time_s"]}',font=font,fill='white')
  sheet.paste(tile,(x+(width-tile.width)//2,y+24+(height-tile.height)//2))
 sheet.save(root/f'motion-{d.name}-sheet.png')
 if not (root/f'motion-{d.name}.mp4').exists(): subprocess.run(['ffmpeg','-loglevel','error','-y','-framerate','30','-i',str(d/'%03d.png'),'-c:v','libx264','-threads','1','-preset','fast','-crf','20','-pix_fmt','yuv420p',str(root/f'motion-{d.name}.mp4')],check=True)
 results.append({'directory':d.name,'frames':len(rows),'source_sizes':sorted(sizes),'simulated_duration_s':len(rows)/30,'phases':sorted(phases),'min_ammo':min(ammo),'end_ammo':ammo[-1],'final_reload_remaining':rows[-1]['reload_remaining_s'],'final_clip_time':rows[-1]['clip_time_s']})
(root/'motion-summary.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
