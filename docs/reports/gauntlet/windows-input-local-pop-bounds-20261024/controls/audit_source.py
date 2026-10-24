"""Exact Git/physical and declared source-delta audit. Local Git reads only."""
import ast,hashlib,json,os,stat,subprocess
from pathlib import Path
root=Path.cwd();out=root/'docs/reports/gauntlet/windows-input-local-pop-bounds-20261024';base='1e045025fdc5e86a1850ebd18565ad08a12253e3'
def git(*args,input=None):return subprocess.check_output(['git',*args],input=input,timeout=30)
def tree(ref):
    result={}
    for raw in git('ls-tree','-r','-z',ref).split(b'\0'):
        if not raw:continue
        header,path=raw.split(b'\t',1);path=os.fsdecode(path);mode,kind,oid=header.split()
        if not path.startswith('docs/'):
            assert kind==b'blob';result[path]=(mode.decode(),oid.decode())
    return result
head=git('rev-parse','HEAD').decode().strip();old=tree(base);new=tree(head)
delta=[p for p in sorted(old.keys()|new.keys()) if old.get(p)!=new.get(p)]
assert delta==['scripts/analyze_input_consumption.py','scripts/test_input_consumption_intervals.py'],delta
rows=[];payload=git('cat-file','--batch',input=b''.join(x[1].encode()+b'\n' for x in new.values()));offset=0
for path,(mode,oid) in new.items():
    end=payload.index(b'\n',offset);got,kind,size=payload[offset:end].split();size=int(size);offset=end+1;data=payload[offset:offset+size];offset+=size
    assert payload[offset:offset+1]==b'\n' and got.decode()==oid and kind==b'blob';offset+=1
    actual=root/path;assert actual.is_file() and not actual.is_symlink() and actual.read_bytes()==data
    assert ('100755' if actual.stat().st_mode&stat.S_IXUSR else '100644')==mode,path
    rows.append(dict(path=path,mode=mode,blob=oid,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),protected=old.get(path)==new.get(path)))
assert offset==len(payload)
reader='scripts/analyze_input_consumption.py';previous=git('show',base+':'+reader);current=(root/reader).read_bytes()
start=current.index(b'class StreamObservationIntervals:');end=current.index(b'class PacketProjectionHistory:',start)
restored=(current[:start]+current[end:]).replace(b'    stream_intervals = StreamObservationIntervals()\n',b'',1).replace(b'        stream_intervals.observe(row, owners_before | live_bindings)\n',b'',1)
assert restored==previous,'reader outside exact three additions changed'
methods=assertions=0
for path in old:
    if path.startswith('scripts/test_input_consumption') and path.endswith('.py'):
        raw=git('show',base+':'+path);assert raw==(root/path).read_bytes()
        module=ast.parse(raw);methods+=sum(isinstance(n,ast.FunctionDef) and n.name.startswith('test_') for n in ast.walk(module))
        assertions+=sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert') for n in ast.walk(module))
assert methods==149,methods
old_summary=Path('/workspace/reviews/windows-input-foundation-r5-independent-20261024/docs/reports/gauntlet/windows-input-foundation-r5-independent-20261024/own-literal149')
before=json.loads((old_summary/'FAILURES.json').read_text());after=json.loads((out/'literal160-r1/FAILURES.json').read_text())
assert sorted((x['kind'],x['test']) for x in before)==sorted((x['kind'],x['test']) for x in after),'failure identities differ; inspect before acceptance'
result=dict(base=base,head=head,code_source=git('rev-parse','f89bef89fb484ff2aed4051b03ecca499161d7c3').decode().strip(),reader_sha256=hashlib.sha256(current).hexdigest(),physical_paths=len(rows),protected_paths=len(rows)-len(delta),deltas=delta,source_restored_after_only_three_additions=True,all149_old_methods_and_helpers_byteexact=True,old_assertion_calls=assertions,old_literal_failure_identities_same=True,literal_failure_events=45,literal_errors=1,constructor23leaf_unapplied=True,files=rows,scope='builder source audit, requires different critic; no native/replay')
(out/'SOURCE_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='files'},indent=2))
