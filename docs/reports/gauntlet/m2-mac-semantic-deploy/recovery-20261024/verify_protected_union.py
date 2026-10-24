#!/usr/bin/env python3
"""Outer full-source proof. Pure test suites never call historical Git objects."""
import hashlib,json,subprocess,sys
from pathlib import Path
root,candidate,target=sys.argv[1:]
def git(*args):return subprocess.check_output(['git','-C',root,*args])
candidate=git('rev-parse',candidate).decode().strip()
def tree(ref):
 result={}
 for row in git('ls-tree','-r','-z',ref).split(b'\0'):
  if row:
   meta,name=row.split(b'\t',1);name=name.decode();mode,kind,blob=meta.decode().split()
   if not name.startswith('docs/'):result[name]={'mode':mode,'type':kind,'blob':blob}
 return result
def content(ref,path):return git('show',ref+':'+path)
union=json.loads(content(candidate,'docs/reports/gauntlet/m2-mac-semantic-deploy/source-union.json'))
base=union['base'];old,new=tree(base),tree(candidate)
sections=('exact_imports','adapted_tests','combined_new_or_changed_runtime','self_contained_source_fixtures','new_source_tests','qualification_workflows')
declared={p:sha for section in sections for p,sha in union[section].items()}
rows=[];changed=[]
for path in sorted(old.keys()|new.keys()):
 row={'path':path,'base':old.get(path),'candidate':new.get(path)}
 if path in new:row['candidate_sha256']=hashlib.sha256(content(candidate,path)).hexdigest()
 if old.get(path)!=new.get(path):changed.append(path)
 rows.append(row)
byname={row['path']:row for row in rows}
imports={p:hashlib.sha256(content(union['read_only_source'],p)).hexdigest() for p in union['exact_imports']}
result={'scope':'Complete non-document mode/blob union; source preparation only','base':base,'candidate':candidate,
 'base_non_docs':len(old),'candidate_non_docs':len(new),'unchanged':sum(old.get(p)==new.get(p) for p in old.keys()|new.keys()),
 'changed':changed,'undeclared_delta':sorted(set(changed)-set(declared)),
 'declared_sha256_match':all(byname[p]['candidate_sha256']==sha for p,sha in declared.items()),
 'accepted_imports_match':imports==union['exact_imports'],
 'base_game_tree':git('rev-parse',base+':game').decode().strip(),'candidate_game_tree':git('rev-parse',candidate+':game').decode().strip(),
 'desktop_workflow_sha256':hashlib.sha256(content(candidate,'.github/workflows/desktop-alpha.yml')).hexdigest(),
 'source_union_sha256':hashlib.sha256(content(candidate,'docs/reports/gauntlet/m2-mac-semantic-deploy/source-union.json')).hexdigest(),'paths':rows}
result['passed']=(not result['undeclared_delta'] and result['declared_sha256_match'] and result['accepted_imports_match']
 and result['base_game_tree']==result['candidate_game_tree']==union['unaltered_game_tree']
 and result['desktop_workflow_sha256']==union['unaltered_workflow_sha256'])
Path(target).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='paths'},indent=2))
raise SystemExit(0 if result['passed'] else 1)
