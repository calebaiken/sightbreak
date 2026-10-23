#!/usr/bin/env python3
"""Compare exact production menu readers on retained native Windows pixels."""
import argparse,ast,csv,hashlib,io,json,os,shutil,subprocess,time
from pathlib import Path
from types import SimpleNamespace
from PIL import Image,ImageDraw
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--captures',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
def extract(text,name,namespace):
 node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name==name);exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual production '+name+'>','exec'),namespace);return namespace[name]
caption=extract(a.candidate.read_text(),'exact_ocr_caption',{})
cases=[('actual-final-leave','ocr-current.png','LEAVE',True,True),('earlier-field-leave','07-field-menu.png','LEAVE',True,True),('field-settings-control','07-field-menu.png','SETTINGS',False,True),('mouse-setting','07b-field-settings.png','MOUSE',False,True),('requisition-vectorline','06d-funded-requisition.png','VECTORLINE',False,True),('actual-settings-negative','07c-settings-changed.png','LEAVE',True,False),('actual-main-menu-negative','01-menu.png','LEAVE',True,False),('actual-live-game-negative','07d-explicit-resume.png','LEAVE',True,False)]
for name,box in [('removed-entire-caption',(560,365,720,410)),('removed-MATCH',(635,365,720,410)),('removed-FIELD-MENU',(40,50,330,115))]:
 with Image.open(a.captures/'ocr-current.png') as original:
  im=original.copy();scaled=tuple(round(v*im.size[i%2]/(1280,720)[i%2]) for i,v in enumerate(box));ImageDraw.Draw(im).rectangle(scaled,fill=(0,0,0));im.save(a.output/(name+'.png'))
 cases.append((name,a.output/(name+'.png'),'LEAVE',True,False))
rows=[];commands=[]
for version,text in [('baseline',a.baseline.read_text()),('candidate',a.candidate.read_text())]:
 for name,file,word,full,expected in cases:
  original=file if isinstance(file,Path) else a.captures/file
  work=a.output/(version+'-'+name);work.mkdir()
  def ocr(image,psm,label):
   b=io.BytesIO();image.save(b,format='PNG');image.save(work/'analysis-transform.png');cmd=['tesseract','stdin','stdout','--psm',str(psm),'tsv'];start=time.monotonic();r=subprocess.run(cmd,input=b.getvalue(),capture_output=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'});(work/'ocr.tsv').write_bytes(r.stdout);(work/'stderr.log').write_bytes(r.stderr);commands.append({'version':version,'case':name,'command':cmd,'exit':r.returncode,'seconds':time.monotonic()-start,'OMP_THREAD_LIMIT':'1'});r.check_returncode();return r.stdout.decode(errors='replace')
  ns={'ui':SimpleNamespace(capture=lambda target:shutil.copyfile(original,target)),'out':work,'Image':Image,'REFERENCE':(1280,720),'ocr':ocr,'csv':csv,'io':io,'remaining':lambda:None}
  tokens=extract(text,'ocr_words',ns)()
  if full: found=caption(tokens,'FIELD MENU') is not None and caption(tokens,'LEAVE MATCH') is not None
  else: found=any(r['text'].upper()==word for r in tokens)
  rows.append({'version':version,'case':name,'expected_visible_control':expected,'recognized':found,'passed':found==expected,'original_pixels_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'native_original':not isinstance(file,Path),'tokens':[r['text'] for r in tokens]})
r={'scope':'Linux saved-image OCR analysis, never a native Windows rerun; altered images labeled','candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'baseline_sha256':hashlib.sha256(a.baseline.read_bytes()).hexdigest(),'rows':rows,'commands':commands,'tesseract':subprocess.check_output(['tesseract','--version'],stderr=subprocess.STDOUT).decode()};(a.output/'results.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({v:{'passed':sum(r['passed'] for r in rows if r['version']==v),'checks':sum(r['version']==v for r in rows),'failures':[r['case'] for r in rows if r['version']==v and not r['passed']]} for v in ('baseline','candidate')},indent=2))
if not all(r['passed'] for r in rows if r['version']=='candidate'):raise SystemExit(1)
