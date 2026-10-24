"""Direct canonical blob/physical source comparison; local Git reads only."""
from pathlib import Path
import subprocess,json,hashlib,stat
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
refs={'candidate':'ab864ab9dd1a620ff86ca27bad0f59031c734555','baseline':'b16b012d720c0981cfc28146a651b3ba5f8a9caa'}
roots={'candidate':ROOT,'baseline':Path('/workspace/reviews/windows-fov-math-acquisition-runtime-20261024')}
report={}
for label,ref in refs.items():
    records=[]
    for line in subprocess.check_output(['git','ls-tree','-rz',ref],cwd=ROOT).split(b'\0'):
        if not line:continue
        ident,name=line.split(b'\t',1);name=name.decode();mode,kind,oid=ident.decode().split()
        if name.startswith('docs/'):continue
        assert kind=='blob';records.append(dict(path=name,mode=mode,blob=oid))
    missing=[row['path'] for row in records if not (roots[label]/row['path']).is_file()]
    assert not missing,(label,'missing materialized source',missing)
    stream=subprocess.check_output(['git','cat-file','--batch'],cwd=ROOT,input=b''.join((r['blob']+'\n').encode() for r in records));pos=0
    for row in records:
        end=stream.index(b'\n',pos);oid,kind,size=stream[pos:end].split();pos=end+1;size=int(size);expected=stream[pos:pos+size];pos+=size
        assert stream[pos:pos+1]==b'\n';pos+=1
        assert oid.decode()==row['blob'] and kind==b'blob'
        path=roots[label]/row['path'];actual=path.read_bytes();mode='100755' if path.stat().st_mode&stat.S_IXUSR else '100644'
        assert not path.is_symlink() and actual==expected and mode==row['mode'],(label,row['path'])
        row.update(bytes=len(actual),sha256=hashlib.sha256(actual).hexdigest())
    report[label]=dict(commit=ref,root=str(roots[label]),paths=len(records),files=records)
old={r['path']:r for r in report['baseline']['files']};new={r['path']:r for r in report['candidate']['files']}
delta=[n for n in sorted(set(old)|set(new)) if old.get(n)!=new.get(n)]
assert delta==['scripts/test_windows_fov_math_finalization.py','scripts/windows_fov_math.py'],delta
report.update(source_delta=delta,protected_paths=len(new)-2,scope='Physical source bytes/modes; no loaded-code, atomic snapshot or Windows semantics claim')
(OUT/'SOURCE_BOTH.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:{k:v for k,v in value.items() if k!='files'} if isinstance(value,dict) else value for key,value in report.items()}))
