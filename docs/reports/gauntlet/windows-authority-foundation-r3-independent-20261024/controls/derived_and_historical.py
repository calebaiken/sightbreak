#!/usr/bin/env python3
import argparse,ast,copy,hashlib,json,os,sys,types,unittest
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert sorted(os.sched_getaffinity(0))==[4];a.output.mkdir(parents=True,exist_ok=False);home=Path(__file__).resolve().parents[1];sys.path.insert(0,str(a.source/'scripts'));import analyze_input_consumption as candidate
from test_input_consumption_observation import declared_rows,text
from test_input_consumption_stream import second_accept
original=json.loads((home/'frozen-derived-a45/original-nine-rows.json').read_text());versioned=json.loads((home/'frozen-derived-a45/versioned-nine-rows.json').read_text());assert original==second_accept(2);expected=copy.deepcopy(original);expected[7].update(input_age_msec=3000,deadline_remaining_msec=10000);expected[8].update(input_age_msec=0,deadline_remaining_msec=9000);assert expected==versioned
changes=[dict(index=x['index'],field=k,old=x[k],proposed=y[k]) for x,y in zip(original,versioned) for k in x if x[k]!=y[k]];assert len(changes)==4 and {r['field'] for r in changes}=={'input_age_msec','deadline_remaining_msec'}
results=[]
for name,rows in [('original',original),('versioned',versioned)]:
 r=candidate.analyze(text(declared_rows('client')),text(rows));folder=a.output/name;folder.mkdir();(folder/'client.txt').write_text(text(declared_rows('client')));(folder/'authority.txt').write_text(text(rows));(folder/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');results.append(dict(name=name,status=r['transition_status'],complete=r['diagnostic_complete'],errors=r['errors']))
assert [r['status'] for r in results]==['INVALID','CONSISTENT']
# Separate exact historical layer for only two prior-expiry methods.
captured=a.source/'docs/reports/gauntlet/windows-input-reader-foundation-20261024/legacy-source/scripts';raw=(captured/'analyze_input_consumption.py').read_bytes();helper=(captured/'test_input_consumption_observation.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1' and hashlib.sha256(helper).hexdigest()=='9f81e903c5932ab1762f347ae400f45ae7b928c29abf3d9f719eb6e7141ead8c'
old=types.ModuleType('frozen_expiry_scope_reader');old.__file__=str(captured/'analyze_input_consumption.py');exec(compile(raw,old.__file__,'exec'),old.__dict__);nodes=[n for n in ast.parse(helper).body if isinstance(n,ast.FunctionDef) and n.name in {'control','declared_rows'}];namespace={'deepcopy':copy.deepcopy};exec(compile(ast.Module(body=nodes,type_ignores=[]),'<frozen-old-helper>','exec'),namespace)
import test_input_consumption_expiry as tests
assert hashlib.sha256(Path(tests.__file__).read_bytes()).hexdigest()=='d642c4f0be7fbe2e34c08ca46f45b23eb27a787212d94504e8a6609440f505b7'
suite=unittest.TestSuite([tests.FullExpiryReaderControls('test_new_positive_lifecycle_projection_and_old_helper_unchanged'),tests.ExpiryHistoryControls('test_missing_legacy_connected_foundation_stays_unknown_then_later_invalid')])
with (a.output/'historical-two.stderr').open('w') as stream,patch.multiple(tests,analyze=old.analyze,declared_rows=namespace['declared_rows']):run=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
s=dict(scope='Exact disclosed four-field constructor and two historical-only expiry methods',source_constructor_proposal='a45a2b683407184ea15ef1f9eec044978f3ada56',changes=changes,results=results,whole_other_fields_exact=True,old_snapshot_methods=run.testsRun,old_snapshot_failures=len(run.failures),old_snapshot_errors=len(run.errors),candidate_pass_credit=0,raw_input_normalization=False,native_executed=False);(a.output/'SUMMARY.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2));raise SystemExit(not run.wasSuccessful())
