#!/usr/bin/env python3
import ast,hashlib,json,os,stat,subprocess,sys
from pathlib import Path
assert sorted(os.sched_getaffinity(0))==[4]
ROOT=Path(__file__).resolve().parents[5];P=ROOT/'docs/reports/gauntlet/windows-input-reader-foundation-independent-20261024';REPORT='docs/reports/gauntlet/windows-input-reader-foundation-20261024/';BASE='2d4214c4d3314df568796f0a6f3a38fc357db318';SOURCE='72868589eaf343f10c5df47f92de7372baec5f5b';HANDOFF='9e3b85db1814a7e06c1306da10cce2fcdb9e7984'
def git(*args):return subprocess.check_output(['git','-C',str(ROOT),*args])
def table(commit):
 result={}
 for item in git('ls-tree','-rz',commit).split(b'\0'):
  if item:
   info,path=item.split(b'\t');mode,kind,blob=info.decode().split();result[path.decode()]=dict(mode=mode,kind=kind,blob=blob)
 return result
old=table(BASE);new=table(SOURCE);handoff=table(HANDOFF);left={k:v for k,v in old.items() if not k.startswith('docs/')};right={k:v for k,v in new.items() if not k.startswith('docs/')};assert len(left)==517 and len(right)==519 and all(right[k]==v for k,v in left.items());assert {k:v for k,v in handoff.items() if not k.startswith('docs/')}==right
assert sorted(set(right)-set(left))==['scripts/input_consumption_foundation_model.py','scripts/test_input_consumption_foundation_model.py']
for path,wanted in right.items():
 f=ROOT/path;raw=f.read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==wanted['blob'];assert ('100755' if f.stat().st_mode&stat.S_IXUSR else '100644')==wanted['mode']
files=[p for p in left if p.startswith('scripts/test_input_consumption_') and p.endswith('.py')];methods=[];asserts=[]
for path in files:
 before=git('show',BASE+':'+path);assert before==(ROOT/path).read_bytes()
 for node in ast.walk(ast.parse(before)):
  if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):methods.append((path,node.name))
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr.startswith('assert'):asserts.append((path,ast.dump(node,include_attributes=False)))
assert len(methods)==105
reportroot=ROOT/REPORT;inventory=json.loads((reportroot/'LEGACY_SOURCE_INVENTORY.json').read_text());assert len(inventory)==12
for member in inventory:
 path=member['path'];raw=(reportroot/'legacy-source'/path).read_bytes();assert raw==git('show',BASE+':'+path)==(ROOT/path).read_bytes();assert len(raw)==member['bytes'] and hashlib.sha256(raw).hexdigest()==member['sha256']
# Copy all final sealed builder documents/raw originals without editing them.
manifest=json.loads(git('show',HANDOFF+':'+REPORT+'MANIFEST.json'));frozen=P/'frozen-builder';frozen.mkdir(exist_ok=False);source_members=[]
for item in manifest['files']:
 raw=git('show',HANDOFF+':'+REPORT+item['path']);assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'];out=frozen/item['path'];out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw);source_members.append(item)
(frozen/'MANIFEST.json').write_bytes(git('show',HANDOFF+':'+REPORT+'MANIFEST.json'));assert len(source_members)==36
sys.path.insert(0,str(ROOT/'scripts'));from test_input_consumption_observation import declared_rows,text
fixture=[]
for role in ['authority','client']:
 original=declared_rows(role);assert len(original)==7;assert original==json.loads((frozen/('legacy-declared-'+role+'.json')).read_text());assert text(original).encode()==(frozen/('legacy-declared-'+role+'.log')).read_bytes();fixture.append(dict(role=role,rows=7,original_framed_sha256=hashlib.sha256(text(original).encode()).hexdigest()))
independent=json.loads((P/'independent-model-v1/independent-expected-authority.json').read_text());assert independent==json.loads((frozen/'versioned-authority-lifecycle-v1.json').read_text());deltas=[]
for oldrow,newrow in zip(declared_rows('authority'),independent):
 changes={k:dict(old=oldrow[k],proposed=newrow[k]) for k in oldrow if oldrow[k]!=newrow[k]}
 if changes:deltas.append(dict(index=oldrow['index'],reason=oldrow['reason'],changes=changes))
proposal=json.loads((frozen/'CONSTRUCTOR_DELTA_PROPOSAL.json').read_text());assert deltas==proposal['deltas'] and len(deltas)==6 and sum(len(row['changes']) for row in deltas)==10;assert all(set(row['changes'])<={'input_age_msec','deadline_remaining_msec'} for row in deltas)
print(json.dumps(dict(scope='Pre-edit model/constructor preservation audit only',source=SOURCE,handoff=HANDOFF,base=BASE,non_doc_union=519,protected_existing_paths=517,all_physical_bytes_Gitmodes_exact=True,reader_sha256=hashlib.sha256((ROOT/'scripts/analyze_input_consumption.py').read_bytes()).hexdigest(),original_test_methods=len(methods),original_assertion_calls=len(asserts),all_original_test_files_byte_exact=True,source_snapshots_exact=12,builder_sealed_members=36,builder_manifest_also_retained=True,original_fixtures=fixture,exact_six_row_proposal_matches_independent_witness=True,changed_fields=10,delta=deltas,native_executed=False,new207_replay_executed=False,cpu_affinity=[4]),indent=2))
