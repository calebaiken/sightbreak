"""Direct frozen Git blob and physical-source verification; Git children only."""
import argparse,ast,hashlib,json,os,stat,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
candidate='71b779b73016f3b634e07e92c64e2e989cc234e1';baseline='8cc38cdcd7dfff37056782149e513c08037e4e77'
def git(*parts,input=None):return subprocess.check_output(['git',*parts],cwd=args.root,input=input,timeout=30)
def files(ref):
    rows=[]
    for raw in git('ls-tree','-r','-z','--full-tree',ref).split(b'\0'):
        if not raw:continue
        header,name=raw.split(b'\t',1);mode,kind,blob=header.split()
        if name.startswith(b'docs/'):continue
        assert kind==b'blob';rows.append(dict(path=os.fsdecode(name),mode=mode.decode(),blob=blob.decode()))
    payload=git('cat-file','--batch',input=b''.join(x['blob'].encode()+b'\n' for x in rows));offset=0
    for row in rows:
        end=payload.index(b'\n',offset);oid,kind,size=payload[offset:end].split();size=int(size);offset=end+1
        data=payload[offset:offset+size];offset+=size
        assert payload[offset:offset+1]==b'\n' and oid.decode()==row['blob'] and kind==b'blob';offset+=1
        row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),data=data)
    assert offset==len(payload);return rows
old=files(baseline);new=files(candidate);previous={r['path']:r for r in old};current={r['path']:r for r in new}
delta=[name for name in sorted(set(previous)|set(current)) if previous.get(name)!=current.get(name)]
assert delta==['scripts/acquire_fov_math_reference.py','scripts/fixtures/fov_source_binding_timing_baseline.json','scripts/test_fov_binary_input.py','scripts/test_fov_math_reference.py','scripts/test_fov_physical_binding.py'],delta
for row in new:
    path=args.root/row['path'];assert path.is_file() and not path.is_symlink(),row['path']
    assert path.read_bytes()==row['data'] and ('100755' if path.stat().st_mode&stat.S_IXUSR else '100644')==row['mode'],row['path']
oldacquire=previous['scripts/acquire_fov_math_reference.py']['data'];newacquire=current['scripts/acquire_fov_math_reference.py']['data']
assert oldacquire[oldacquire.index(b'class LinuxKernel:'):]==newacquire[newacquire.index(b'class LinuxKernel:'):]
newtests=current['scripts/test_fov_math_reference.py']['data'];oldtests=previous['scripts/test_fov_math_reference.py']['data']
sys.path.insert(0,str(args.root/'scripts'))
import acquire_fov_math_reference as a
from test_fov_binary_input import erase_timing_constructor
assert erase_timing_constructor(newtests)==oldtests
oldcodec=previous['scripts/test_fov_binary_input.py']['data'];newcodec=current['scripts/test_fov_binary_input.py']['data']
start=newcodec.index(b'def timing_binding_baseline():');stop=newcodec.index(b'def rehash(',start)
assert (newcodec[:start]+newcodec[stop:]).replace(b'        tests=erase_timing_constructor(tests)\n',b'')==oldcodec
head=git('rev-parse','HEAD').decode().strip()
physical=a.source_binding(head,deadline=time.monotonic()+30)
assert physical['non_doc_paths']==len(new)==527 and set(physical['physical_sources'])==set(current)
for row in new:row.pop('data')
record=dict(candidate=candidate,baseline=baseline,actual_head=head,root=str(args.root),physical_paths=len(new),protected_paths=len(new)-len(delta),delta=delta,all_rows=new,
            linux_kernel_through_main_byteexact=True,timing_donor_reconstructs_whole_old_module=True,codec_only_declared_helper_and_call=True,physical_binding=physical,
            scope='source-only exact physical bytes and owner mode; no loaded-bytecode/atomic/native/capability proof')
args.output.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('all_rows','physical_binding')}))
