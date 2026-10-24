"""Retain job-log/source-recipe provenance facts without executing a toolchain."""
import argparse,ast,hashlib,json,re,subprocess
from pathlib import Path
SOURCE='c32415148db1f110bbc7eadfca3793d4693429ff'
SHA=lambda raw:hashlib.sha256(raw).hexdigest()
p=argparse.ArgumentParser();p.add_argument('checkout',type=Path);p.add_argument('log',type=Path);p.add_argument('bounded',type=Path);p.add_argument('full',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
raw=a.log.read_bytes();lines=raw.decode().splitlines();starts=[i for i,x in enumerate(lines) if '##[group]Run ' in x]
groups=[]
for j,start in enumerate(starts):
 end=starts[j+1] if j+1<len(starts) else len(lines);chunk=lines[start:end];command=chunk[0].split('##[group]Run ',1)[1]
 groups.append({'command':command,'start_line':start+1,'end_line':end,'lines':chunk})
wanted=['python scripts/toolchain.py setup --targets windows','python scripts/test_build_manifest.py -v','python scripts/test_native_log.py -v','python scripts/test_native_observation.py -v','python scripts/test_offline_export_ocr.py -v','python scripts/test_package_qa_receipts.py -v','python scripts/export.py windows','python scripts/verify_builds.py --targets windows','python scripts/verify_builds.py --targets windows --graphical','python scripts/run_native_regressions.py --output builds/desktop-playability/regressions','python scripts/build_manifest.py package --targets windows']
records=[]
for cmd in wanted:
 selected=[g for g in groups if g['command']==cmd]
 for g in selected:
  tests=[{'line':g['start_line']+i,'text':line} for i,line in enumerate(g['lines']) if re.search(r' test_.*\) \.\.\. ',line)]
  summaries=[{'line':g['start_line']+i,'text':line} for i,line in enumerate(g['lines']) if re.search(r'Ran \d+ tests|Z OK(?: |$)|##\[error\]|stable.official',line)]
  records.append({'command':cmd,'start_line':g['start_line'],'end_line':g['end_line'],'test_rows':tests,'summary_lines':summaries,'skips':[x for x in tests if ' ... skipped ' in x['text']],'step_error_lines':[x for x in g['lines'] if '##[error]' in x]})
 if not selected:records.append({'command':cmd,'missing_command_group':True})
toolraw=subprocess.check_output(['git','show',SOURCE+':scripts/toolchain.py'],cwd=a.checkout);constants={}
for node in ast.parse(toolraw).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('VERSION','ENGINE','EDITORS','TEMPLATES_SHA512'):
  constants[node.targets[0].id]=ast.literal_eval(node.value)
full=a.full;bounded=a.bounded/'evidence' if (a.bounded/'evidence').is_dir() else a.bounded
shared=[];missing=[];different=[]
for path in sorted(bounded.rglob('*')):
 if not path.is_file():continue
 rel=path.relative_to(bounded);target=full/rel;row={'path':rel.as_posix(),'bytes':path.stat().st_size,'bounded_sha256':SHA(path.read_bytes())}
 if target.is_file():
  row['full_sha256']=SHA(target.read_bytes());row['identical']=row['bounded_sha256']==row['full_sha256']
  if not row['identical']:different.append(rel.as_posix())
 else:missing.append(rel.as_posix())
 shared.append(row)
extras=[{'path':p.relative_to(full).as_posix(),'bytes':p.stat().st_size,'sha256':SHA(p.read_bytes())} for p in sorted(full.rglob('*')) if p.is_file() and not (bounded/p.relative_to(full)).is_file()]
result={'source_commit':SOURCE,'job_log':{'path':str(a.log),'bytes':len(raw),'sha256':SHA(raw),'line_count':len(lines),'post_job_cleanup':[{'line':i,'text':x} for i,x in enumerate(lines,1) if 'Post job cleanup.' in x]},'source_pinned_toolchain':{'script_sha256':SHA(toolraw),'version':constants['VERSION'],'engine':constants['ENGINE'],'windows_editor_archive_sha512_pin':constants['EDITORS']['windows'][2],'export_templates_archive_sha512_pin':constants['TEMPLATES_SHA512'],'scope':'Exact source fetch() checks SHA512 archive pins before extract; actual job executes setup and prints pinned engine version. No raw editor/template archive bytes or computed digest values are retained in supported QA; independent archive-byte rehash BLOCKED.'},'job_groups':records,'controls_summary':{'recorded_tests':sum(len(x.get('test_rows',[])) for x in records),'recorded_skips':sum(len(x.get('skips',[])) for x in records),'all_wanted_commands_present':all(not x.get('missing_command_group',False) for x in records),'step_error_lines':[{'command':x['command'],'errors':x.get('step_error_lines')} for x in records if x.get('step_error_lines')]},'raw_replica_crosswalk':{'bounded_files':len(shared),'full_files':len(shared)+len(extras)-len(missing),'shared_byte_mismatches':different,'bounded_missing_in_full':missing,'all_bounded_files_identical':bool(shared) and not missing and not different,'bounded_inventory':shared,'full_additional_files':extras},'scope':'Derived indexes of original full job log and official artifact replicas. No native command rerun. Workflow-skipped platform controls remain outside Windows execution; connector step inventory is owned by parent.'}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'controls':result['controls_summary'],'job_log':result['job_log'],'crosswalk':{k:v for k,v in result['raw_replica_crosswalk'].items() if k not in ('bounded_inventory','full_additional_files')}}))
