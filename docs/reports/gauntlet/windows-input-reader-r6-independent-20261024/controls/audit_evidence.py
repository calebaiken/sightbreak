#!/usr/bin/env python3
import collections,gzip,hashlib,json,os,subprocess
from pathlib import Path
assert sorted(os.sched_getaffinity(0))==[4]
P=Path(__file__).resolve().parents[1];ROOT=P.parents[3];BUILDER='docs/reports/gauntlet/windows-input-consumption-r6-20261024/';HANDOFF='abd5a57223ffe8c4481271f06884eb5fe883b96f'
def blob(commit,path):return subprocess.check_output(['git','-C',str(ROOT),'show',commit+':'+path])
copied=[]
for group,oldcommit,oldprefix in [('r5-builder-frozen','eb2dbc7cc97b337fb8e0bbf601fcb0bbfd984701','docs/reports/gauntlet/windows-input-consumption-r5-20261024/'),('r5-critic-frozen','c909a9cb88d4ab77dfc1a5a5bba266ce15fc5e4d','docs/reports/gauntlet/windows-input-reader-r5-independent-20261024/')]:
 for f in sorted((P/'controls'/group).rglob('*')):
  if not f.is_file():continue
  suffix=f.relative_to(P/'controls'/group).as_posix();handoffpath=BUILDER+group+'/'+suffix;raw=f.read_bytes();assert raw==blob(HANDOFF,handoffpath)
  assert raw==blob(oldcommit,oldprefix+suffix)
  copied.append(dict(copy=f.relative_to(P).as_posix(),source_commit=oldcommit,source_path=oldprefix+suffix,sha256=hashlib.sha256(raw).hexdigest()))
for name in ['run_selected_pure.py','replay_controls.py']:assert (P/'controls'/name).read_bytes()==blob(HANDOFF,BUILDER+name)
assert (P/'BUILDER_HANDOFF.md').read_bytes()==blob(HANDOFF,BUILDER+'HANDOFF.md')
views=[]
for name in ['own-final','depth-final']:
 p=P/name;runs=json.loads((p/'RUNS.json').read_text());assert runs['all_exit_zero']
 pure=json.loads((p/'selected-pure/SUMMARY.json').read_text());assert pure['methods']==227 and pure['skips']==3 and pure['errors']==pure['failures']==0
 retained=json.loads((p/'retained-controls/results.json').read_text());assert retained['total']==retained['met']==139 and retained['newly_obsolete_positive_count']==1
 for group,n in [('queue-models',13),('aggregate-models',5)]:
  s=json.loads((p/group/'SUMMARY.json').read_text());assert s['cases']==s['matches']==n
 s=json.loads((p/'generated-histories/SUMMARY.json').read_text());assert s['cases']==s['matched']==36948 and not s['mismatches']
 rawhash=hashlib.sha256();count=0;results=collections.Counter()
 with gzip.open(p/'generated-histories/cases.jsonl.gz','rb') as stream:
  for line in stream:
   rawhash.update(line);r=json.loads(line);count+=1;assert r['id']==count;results[(r['expected'],r['actual'])]+=1
 assert count==36948 and results=={('VALID','VALID'):5896,('INVALID','INVALID'):31052}
 assert rawhash.hexdigest()==s['raw_jsonl_sha256'] and hashlib.sha256((p/'generated-histories/cases.jsonl.gz').read_bytes()).hexdigest()==s['gzip_sha256']
 views.append(dict(view=name,pure_methods=227,pure_pass=224,pure_skip=3,retained=139,queue=13,aggregate=5,generated=36948,generated_feasible=5896,generated_infeasible=31052,shell_syntax_checks=sum(r['group']=='shell-syntax' for r in runs['records']),generated_gzip_sha256=s['gzip_sha256']))
# All final model/corpus input/results (apart from path-bearing summaries) match.
parity=[];serialization_differences=[]
for group in ['queue-models','aggregate-models','generated-histories','causal-cases','retained-controls']:
 left=P/'own-final'/group;right=P/'depth-final'/group;members=0
 for f in left.rglob('*'):
  if f.is_file() and f.name not in {'SUMMARY.json','results.json'}:
   if f.read_bytes()!=(right/f.relative_to(left)).read_bytes():
    assert group=='retained-controls' and f.relative_to(left).as_posix()=='versioned/consumption_older_than_latest_accepted/authority.log',str(f)
    def parsed(path):return [json.loads(line[len('SIGHTBREAK_INPUT_OBSERVATION '):]) for line in path.read_text().splitlines() if line.startswith('SIGHTBREAK_INPUT_OBSERVATION ')]
    assert parsed(f)==parsed(right/f.relative_to(left))
    serialization_differences.append(dict(group=group,path=f.relative_to(left).as_posix(),parsed_objects_identical=True,reason='Frozen builder correction iterates CONTROL_KEYS set; serialized object key order differs.'))
   else:members+=1
 parity.append(dict(group=group,byte_identical_members=members))
pure_summaries=[json.loads((P/name/'selected-pure/SUMMARY.json').read_text()) for name in ['own-final','depth-final']]
assert [[{k:r[k] for k in ['name','methods','failures','errors','skips']} for r in summary['rows']] for summary in pure_summaries][0]==[[{k:r[k] for k in ['name','methods','failures','errors','skips']} for r in summary['rows']] for summary in pure_summaries][1]
fresh=[]
for group in ['causal-v3','epoch-ties']:
 own=P/('own-'+group);depth=P/('depth-'+group)
 s=json.loads((own/'SUMMARY.json').read_text());t=json.loads((depth/'SUMMARY.json').read_text());assert s['cases']==t['cases'] and s['matches']==t['matches']
 expected=collections.Counter();actual=collections.Counter()
 for folder in own.iterdir():
  if folder.is_dir():
   for f in folder.iterdir():assert f.read_bytes()==(depth/folder.name/f.name).read_bytes()
   r=json.loads((folder/'RESULT.json').read_text());expected[r['expected']]+=1;actual[r['actual']]+=1
 fresh.append(dict(group=group,cases=s['cases'],matches=s['matches'],expected=dict(expected),actual=dict(actual),unexpected=[r['name'] for r in s['unexpected']],own_depth_all_case_bytes_identical=True))
positive=P/'own-causal-v3/joined_idle_expiry_with_real_clock';negative=P/'own-causal-v3/joined_expiry_before_idle_and_before_deadline'
assert (positive/'client.txt').read_bytes()==(negative/'client.txt').read_bytes()
def rows(path):return [json.loads(line.split(' ',1)[1]) for line in path.read_text().splitlines() if line.startswith('SIGHTBREAK_INPUT_OBSERVATION ')]
a=rows(positive/'authority.txt');b=rows(negative/'authority.txt');deltas=[]
for i,(x,y) in enumerate(zip(a,b),1):
 if x!=y:deltas.append(dict(index=i,reason=x['reason'],changed={key:[x[key],y[key]] for key in x if x[key]!=y[key]}))
assert len(deltas)==1 and deltas[0]['reason']=='peer_expired' and set(deltas[0]['changed'])=={'input_age_msec','deadline_remaining_msec'}
for name in ['own-causal-v1','own-causal-v2','own-causal-v3','own-epoch-ties']:
 s=json.loads((P/name/'SUMMARY.json').read_text());assert s['analyzer_sha256']=='c53b1ced5743c7440d0530874115d474da2a70f2416c7515e098109837182be8'
# Preserve all authority v1/v2 bytes: only the separately registered client clock changes.
for f in (P/'own-causal-v1').glob('*/authority.txt'):assert f.read_bytes()==(P/'own-causal-v2'/f.parent.name/f.name).read_bytes()
print(json.dumps(dict(source='c8827e7d158431097a5413273b5a1e93715961b0',copied_frozen_members=len(copied),frozen_provenance=copied,views=views,parity=parity,serialization_differences=serialization_differences,fresh=fresh,expiry_pair_exact_delta=deltas,prior_rig_authority_v1_v2_unchanged=True,cpu_affinity=[4],native_executed=False),indent=2))
