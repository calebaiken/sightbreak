#!/usr/bin/env python3
import gzip,hashlib,json,os,subprocess
from pathlib import Path
assert sorted(os.sched_getaffinity(0))==[4]
P=Path(__file__).resolve().parents[1];ROOT=P.parents[3];MODEL='docs/reports/gauntlet/windows-input-reader-r7-assessment-20261024/';R5BUILDER='docs/reports/gauntlet/windows-input-consumption-r5-20261024/';R5CRITIC='docs/reports/gauntlet/windows-input-reader-r5-independent-20261024/';BROOT=Path('/workspace/sightbreak-windows-input-consumption-r7');BPREFIX='docs/reports/gauntlet/windows-input-consumption-r7-absorbing-lifecycle-20261024/';HANDOFF='2fd161e4536911d0d86280b2a53444376534259c'
entries=[]
for f in sorted((P/'controls/model-assessment').rglob('*')):
 if f.is_file() and '__pycache__' not in f.parts:entries.append((f,'953d7b063e5e918c588a5ef1b30b3f85c622d698',MODEL+f.relative_to(P/'controls/model-assessment').as_posix(),'independent-model'))
for group,commit,prefix in [('r5-builder-frozen','eb2dbc7cc97b337fb8e0bbf601fcb0bbfd984701',R5BUILDER),('r5-critic-frozen','c909a9cb88d4ab77dfc1a5a5bba266ce15fc5e4d',R5CRITIC)]:
 for f in sorted((P/'controls'/group).rglob('*')):
  if f.is_file():entries.append((f,commit,prefix+f.relative_to(P/'controls'/group).as_posix(),'retained-corpus'))
manifest=json.loads((BROOT/BPREFIX/'MANIFEST.json').read_text())
for r in manifest['files']:
 f=BROOT/BPREFIX/r['path'];raw=f.read_bytes();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];entries.append((f,HANDOFF,BPREFIX+r['path'],'builder-sealed'))
entries.append((BROOT/BPREFIX/'MANIFEST.json',HANDOFF,BPREFIX+'MANIFEST.json','builder-sealed'))
requests=''.join(commit+':'+path+'\n' for f,commit,path,kind in entries).encode();raw=subprocess.check_output(['git','-C',str(ROOT),'cat-file','--batch'],input=requests);pos=0;provenance=[];counts={}
for f,commit,path,kind in entries:
 end=raw.index(b'\n',pos);info=raw[pos:end].split();assert info[1]==b'blob',path;size=int(info[2]);body=raw[end+1:end+1+size];assert f.read_bytes()==body,path;pos=end+size+2;counts[kind]=counts.get(kind,0)+1;provenance.append(dict(copy=str(f),origin=commit+':'+path,bytes=size,sha256=hashlib.sha256(body).hexdigest()))
assert pos==len(raw) and counts['independent-model']==690 and counts['retained-corpus']==426
(P/'BUILDER_HANDOFF.md').write_bytes((BROOT/BPREFIX/'HANDOFF.md').read_bytes());(P/'BUILDER_MANIFEST.json').write_bytes((BROOT/BPREFIX/'MANIFEST.json').read_bytes())
views=[]
for name in ['own-final','depth-final']:
 run=json.loads((P/name/'RUNS.json').read_text());groups=[]
 for group,total in [('projected',3746),('history',18),('deadline',40),('source-clocks',198),('coincident',4212),('preforget',8)]:
  s=json.loads((P/name/group/'SUMMARY.json').read_text());assert s['cases']==s['matches']==total and s['prototype_sha256']=='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1';groups.append(dict(group=group,cases=total,matches=total))
 retained=json.loads((P/name/'retained139/results.json').read_text());assert retained['total']==retained['met']==139 and retained['newly_obsolete_positive_count']==1
 purepath=P/'own-pure-fixture-rerun' if name=='own-final' else P/name/'selected-pure';pure=json.loads((purepath/'SUMMARY.json').read_text());assert pure['methods']==257 and pure['skips']==3 and pure['failures']==pure['errors']==0
 shell=[r for r in run['records'] if r['group']=='shell-syntax'];assert len(shell)==13 and not any(r['exit'] for r in shell)
 views.append(dict(view=name,model_groups=groups,model_expectations=8222,retained_outcomes=139,pure_path=str(purepath),pure_methods=257,pure_pass=254,pure_skips=3,pure_errors=0,pure_failures=0,shell_parses=13))
parity=[];exceptions=[]
for group in ['projected','history','deadline','source-clocks','coincident','preforget','retained139']:
 left=P/'own-final'/group;right=P/'depth-final'/group;exact=0
 for f in sorted(left.rglob('*')):
  if not f.is_file() or f.name in {'SUMMARY.json','results.json'}:continue
  counterpart=right/f.relative_to(left)
  if f.read_bytes()!=counterpart.read_bytes():
   assert group=='retained139' and f.relative_to(left).as_posix()=='versioned/consumption_older_than_latest_accepted/authority.log',str(f)
   def parsed(path):return [json.loads(line[len('SIGHTBREAK_INPUT_OBSERVATION '):]) for line in path.read_text().splitlines() if line.startswith('SIGHTBREAK_INPUT_OBSERVATION ')]
   assert parsed(f)==parsed(counterpart);exceptions.append(dict(group=group,path=f.relative_to(left).as_posix(),reason='Frozen corrected-fixture builder serializer uses set key order; parsed rows identical'))
  else:exact+=1
 parity.append(dict(group=group,exact_byte_members=exact))
for view in ['own-final','depth-final']:
 folder=P/view/'coincident';s=json.loads((folder/'SUMMARY.json').read_text());data=gzip.decompress((folder/'CASES.jsonl.gz').read_bytes());assert hashlib.sha256(data).hexdigest()==s['raw_jsonl_sha256'];assert hashlib.sha256((folder/'CASES.jsonl.gz').read_bytes()).hexdigest()==s['gzip_sha256'];assert len(data.splitlines())==4212
pure_summaries=[json.loads((p/'SUMMARY.json').read_text()) for p in [P/'own-pure-fixture-rerun',P/'depth-final/selected-pure']];trim=lambda s:[{k:r[k] for k in ['name','methods','failures','errors','skips']} for r in s['rows']];assert trim(pure_summaries[0])==trim(pure_summaries[1])
first=json.loads((P/'own-final/selected-pure/SUMMARY.json').read_text());assert first['methods']==257 and first['errors']==11 and first['failures']==0 and first['skips']==3
print(json.dumps(dict(source='2d4214c4d3314df568796f0a6f3a38fc357db318',handoff=HANDOFF,origin_file_counts=counts,origin_provenance=provenance,views=views,case_parity=parity,serialization_exceptions=exceptions,original_own_fixture_setup_failure_preserved=dict(methods=257,errors=11,failures=0,skips=3),pure_outcome_parity_exact=True,cpu_affinity=[4],native_executed=False,actual_logs_replayed=False),indent=2))
