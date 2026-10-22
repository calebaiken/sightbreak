#!/usr/bin/env python3
"""Replay exact production OCR transformation on original saved Windows pixels."""
import argparse,ast,csv,hashlib,io,json,os,shutil,subprocess,time
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--controller',type=Path,required=True);p.add_argument('--pixels',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
text=a.controller.read_text();node=next(n for n in ast.walk(ast.parse(text)) if isinstance(n,ast.FunctionDef) and n.name=='ocr_words')
commands=[]
def ocr(image,psm,label):
 path=a.output/'production-transform.png';image.save(path);data=io.BytesIO();image.save(data,format='PNG');command=['tesseract','stdin','stdout','--psm',str(psm),'tsv'];started=time.monotonic()
 completed=subprocess.run(command,input=data.getvalue(),capture_output=True,timeout=20,env={**os.environ,'OMP_THREAD_LIMIT':'1'})
 (a.output/'ocr.tsv').write_bytes(completed.stdout);(a.output/'ocr-stderr.log').write_bytes(completed.stderr);commands.append({'command':command,'exit':completed.returncode,'seconds':time.monotonic()-started,'OMP_THREAD_LIMIT':'1'});completed.check_returncode();return completed.stdout.decode('utf-8',errors='replace')
namespace={'ui':SimpleNamespace(capture=lambda path:shutil.copyfile(a.pixels,path)),'out':a.output,'Image':Image,'REFERENCE':(1280,720),'ocr':ocr,'csv':csv,'io':io,'remaining':lambda:None}
exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual production ocr_words>','exec'),namespace);rows=namespace['ocr_words']();got=next((r for r in rows if r['text'].upper()=='LEAVE'),None)
r={'scope':'Linux OCR supporting replay of original Windows pixels; no native Windows OCR reconstruction','controller_sha256':hashlib.sha256(a.controller.read_bytes()).hexdigest(),'ocr_words_ast_sha256':hashlib.sha256(ast.dump(node).encode()).hexdigest(),'original_pixels_sha256':hashlib.sha256(a.pixels.read_bytes()).hexdigest(),'commands':commands,'tesseract':subprocess.check_output(['tesseract','--version'],stderr=subprocess.STDOUT).decode(),'rows':rows,'exact_LEAVE_row':got}
(a.output/'results.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'exact_LEAVE_row':got,'rows':[r['text'] for r in rows]},indent=2))
