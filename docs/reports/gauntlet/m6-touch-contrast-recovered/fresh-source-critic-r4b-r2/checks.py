#!/usr/bin/env python3
"""Independent method-only R4B R2 review; source/pure, never native."""
import ast
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import types

import numpy as np

REPO=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(REPO/'scripts'))
import analyze_touch_contrast_r4b as corrected
from prepare_touch_contrast_r4b import instrument,TOUCH
from test_touch_method_r4b import Ownership
from test_touch_receipts_r4b_r2 import FullProvenanceComparison

FREEZE='b001fc5087960729535f63c896b40d6dc25bd272'
OLD='2ea23f947aec6085449bced53c9b061618a67029'
CRITIC='ce3510e3776c8fec42ef1de648b14a453c221724'
REPORT='docs/reports/gauntlet/m6-touch-contrast-recovered/'
report={'freeze':FREEZE,'scope':'SOURCE_PURE_ONLY','engine_invocations':0,'native_captures':0,'checks':{}}
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def sha(data):return hashlib.sha256(data).hexdigest()
def check(name,condition,**evidence):
    report['checks'][name]={'pass':bool(condition),**evidence}
    assert condition,name

freeze_bytes=(REPO/REPORT/'SOURCE_FREEZE-r4b-r2.json').read_bytes()
freeze=json.loads(freeze_bytes)
for entry in freeze['frozen_files']:
    data=(REPO/entry['path']).read_bytes()
    assert data==git('show',FREEZE+':'+entry['path'])
    assert sha(data)==entry['sha256'] and len(data)==entry['bytes']
check('all22_frozen_files_exact',len(freeze['frozen_files'])==22,freeze_sha256=sha(freeze_bytes))

old_bytes=git('show',OLD+':scripts/analyze_touch_contrast_r4b.py')
new_bytes=(REPO/'scripts/analyze_touch_contrast_r4b.py').read_bytes()
old_tree,new_tree=ast.parse(old_bytes),ast.parse(new_bytes)
old_without=ast.Module(body=[n for n in old_tree.body if not isinstance(n,ast.FunctionDef) or n.name!='audit_ownership'],type_ignores=[])
new_without=ast.Module(body=[n for n in new_tree.body if not isinstance(n,ast.FunctionDef) or n.name!='audit_ownership'],type_ignores=[])
assert ast.dump(old_without)==ast.dump(new_without)
changed=git('diff','--name-only',OLD,FREEZE,'--','game','scripts').decode().splitlines()
check('correction_changes_only_ownership_validator_and_new_pure_tests',changed==['scripts/analyze_touch_contrast_r4b.py','scripts/test_touch_receipts_r4b_r2.py'],changed=changed,
      game_tree_unchanged=git('rev-parse',OLD+':game')==git('rev-parse',FREEZE+':game'))
assert git('rev-parse',OLD+':game')==git('rev-parse',FREEZE+':game')
for entry in json.loads(git('show','a4f942af1213f2d4a18a790adea624bcbcd3b7b5:'+REPORT+'SOURCE_FREEZE-r4b.json'))['frozen_files']:
    if entry['path']!='scripts/analyze_touch_contrast_r4b.py':assert sha((REPO/entry['path']).read_bytes())==entry['sha256']
check('prior_geometry_fixture_predicates_and_thresholds_unchanged',True,
      geometry_certificate_sha256=sha((REPO/REPORT/'r4b-continuous-certificate.json').read_bytes()))

stages=[]
for receipt in freeze['fixtures']:
    root=Path(receipt['path']);manifest_bytes=(root/'SOURCE.json').read_bytes();manifest=json.loads(manifest_bytes)
    assert sha(manifest_bytes)==receipt['manifest_sha256'] and manifest['source']==receipt['source_full']
    paths=git('ls-tree','-r','--name-only',receipt['source_full'],'game').decode().splitlines()
    assert paths==[e['path'] for e in manifest['files']]
    expected=set()
    for entry in manifest['files']:
        data=(root/entry['path']).read_bytes()
        assert data==git('show',receipt['source_full']+':'+entry['path'])
        assert sha(data)==entry['sha256'] and len(data)==entry['bytes']
        expected.add(entry['path'])
    for entry in manifest['fixture']:
        data=(root/entry['path']).read_bytes()
        assert data==(REPO/'scripts/fixtures/touch_contrast_r4b'/Path(entry['path']).name).read_bytes()
        assert sha(data)==entry['sha256'];expected.add(entry['path'])
    wrapped,calls=instrument((root/TOUCH).read_text());wrapped=wrapped.replace('class_name TacticalTouch\n','',1)
    assert calls==manifest['instrumentation']
    for filename,key in (('touch_contrast_instrumented.gd','instrumented_sha256'),('touch_contrast_instrumented.gd.uid','instrumented_uid_sha256')):
        rel='game/tests/'+filename;data=(root/rel).read_bytes()
        assert sha(data)==manifest[key]
        if filename.endswith('.gd'):assert data==wrapped.encode()
        expected.add(rel)
    assert {str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}==expected|{'SOURCE.json'}
    uids=[p.read_bytes() for p in root.rglob('*.uid')]
    assert len(uids)==len(set(uids)) and not any(root.rglob('.godot'))
    stages.append({'name':receipt['name'],'source':receipt['source_full'],'original_paths':len(paths),'checked_paths':len(expected),'unique_uid_paths':len(uids),'manifest_sha256':sha(manifest_bytes)})
check('new_stages_read_only_exact327_paths',all(x['original_paths']==323 and x['checked_paths']==327 for x in stages),stages=stages)

# Execute the original critic expressions unchanged on old and new methods.
original=git('show',CRITIC+':'+REPORT+'fresh-source-critic-r4b/checks.py')
assert original==(REPO/REPORT/'retained-r4b-fresh-critic/checks.py').read_bytes()
text=original.decode();block=text[text.index('# BLOCKER:'):text.index('report["verdict"] =')]
old=types.ModuleType('old_exact_r4b_method');old.__file__=str(REPO/'scripts/analyze_touch_contrast_r4b.py')
exec(compile(old_bytes,'rejected-exact-source','exec'),old.__dict__)
def replay(method):
    findings={}
    def capture(name,condition,**evidence):findings[name]={'original_condition':bool(condition),**evidence}
    env={'method':method,'Ownership':Ownership,'check':capture}
    exec(compile(block,'unchanged-independent-critic-block','exec'),env)
    return {'findings':findings,'false_accept':bool(env['false_accept']),'false_zero_errors':env['ownership']['errors'],'forged_winner_errors':env['forged']['errors']}
replays={'old':replay(old),'corrected':replay(corrected)}
check('original_falsifiers_replayed_unchanged',replays['old']['false_accept'] and not replays['corrected']['false_accept'] and bool(replays['corrected']['false_zero_errors']) and bool(replays['corrected']['forged_winner_errors']),
      original_sha256=sha(original),block_sha256=sha(block.encode()),replays=replays)

# Reviewer-built independent scalar winner reference. The arrays are synthetic.
def samples(variant):
    actions=list(corrected.ACTIONS)
    info={'geometry':{},'ownership':{},'action_order':actions+['move']};components={}
    for i,action in enumerate(actions):
        info['geometry'][action]={'point':[40+i*60,50],'hit_radius':31}
        image=np.zeros((100,720,3),np.uint8);image[50,40+i*60]=1
        components[action]=image
    components['fire'][:]=0
    for x,y in ((10,10),(40,50),(100,50),(160,50)):components['fire'][y,x]=1
    order=sorted(actions) if variant=='r4b' else actions
    def winner(x,y):
        distances=[(math.hypot(x+.5-info['geometry'][a]['point'][0],y+.5-info['geometry'][a]['point'][1])/31,a) for a in order]
        selected=min(enumerate(distances),key=lambda v:(v[1][0],v[0]))[1]
        return selected[1] if selected[0]<=1 else ''
    for action,image in components.items():
        yy,xx=np.where(image.max(axis=-1)>=1)
        bad=[[int(x),int(y),winner(int(x),int(y))] for x,y in zip(xx,yy) if winner(int(x),int(y))!=action]
        info['ownership'][action]={'support_pixels':len(xx),'wrong_owner_pixels':len(bad),'unclaimed_pixels':sum(w[2]=='' for w in bad),'wrong_owner_witnesses_xy_action':bad}
    return info,components

def mutation(name,variant):
    info,images=samples(variant);r=info['ownership']['fire'];w=r['wrong_owner_witnesses_xy_action']
    if name=='false_zero':r.update(wrong_owner_pixels=0,unclaimed_pixels=0,wrong_owner_witnesses_xy_action=[])
    elif name=='omit_coordinate':w.pop();r['wrong_owner_pixels']-=1
    elif name=='extra_own_coordinate':w.append([40,50,'pause']);r['wrong_owner_pixels']+=1
    elif name=='duplicate_same':w.append(list(w[1]));r['wrong_owner_pixels']+=1
    elif name=='duplicate_other':w.append([100,50,'pause']);r['wrong_owner_pixels']+=1
    elif name=='forged_valid_winner':w[1][2]='pause'
    elif name=='swap_winners':w[1][2],w[2][2]=w[2][2],w[1][2]
    elif name=='false_unclaimed':w[1][2]='';r['unclaimed_pixels']+=1
    elif name=='hide_unclaimed':w[0][2]='pause';r['unclaimed_pixels']=0
    elif name=='unknown_winner':w[1][2]='invented'
    elif name=='own_winner':w[1][2]='fire'
    elif name=='movement_winner':w[1][2]='move'
    elif name=='nonstring_winner':w[1][2]=None
    elif name=='unsupported':w[1][0]=101
    elif name=='negative':w[1][0]=-1
    elif name=='right_oob':w[1][0]=720
    elif name=='float_coordinate':w[1][0]=100.0
    elif name=='bool_coordinate':w[1][0]=True
    elif name=='short_sample':w[1].pop()
    elif name=='dict_sample':w[1]={'x':100,'y':50,'winner':'jump'}
    elif name=='missing_list':r.pop('wrong_owner_witnesses_xy_action')
    elif name=='null_record':info['ownership']['fire']=None
    elif name=='support_count':r['support_pixels']+=1
    elif name=='wrong_count':r['wrong_owner_pixels']=2
    elif name=='unclaimed_count':r['unclaimed_pixels']=0
    elif name=='float_count':r['wrong_owner_pixels']=3.0
    elif name=='bool_count':r['unclaimed_pixels']=True
    elif name=='negative_count':r['wrong_owner_pixels']=-1
    else:raise ValueError(name)
    return info,images

NAMES=('false_zero','omit_coordinate','extra_own_coordinate','duplicate_same','duplicate_other','forged_valid_winner','swap_winners','false_unclaimed','hide_unclaimed','unknown_winner','own_winner','movement_winner','nonstring_winner','unsupported','negative','right_oob','float_coordinate','bool_coordinate','short_sample','dict_sample','missing_list','null_record','support_count','wrong_count','unclaimed_count','float_count','bool_count','negative_count')
owners={};positives={};negative_summary=[]
for variant in ('r3','r4b'):
    positive=corrected.audit_ownership(*samples(variant),variant)
    assert not positive['errors'] and not positive['pass']
    assert all(r['native_receipt_matches_replay'] for r in positive['rows'])
    positives[variant]=positive
    for name in NAMES:
        result=corrected.audit_ownership(*mutation(name,variant),variant)
        assert result['errors'] and not result['pass'],(variant,name,result)
        owners[(variant,name)]=result
        negative_summary.append({'variant':variant,'mutation':name,'receipt_error_count':len(result['errors'])})
check('28_independent_receipt_mutations_reject_both_variants',len(negative_summary)==56,results=negative_summary)

# Same geometry with coincident targets exercises source-specific exact ties.
ties=[]
for variant in ('r3','r4b'):
    info,images=samples(variant)
    info['geometry']['grenade']['point']=info['geometry']['smoke']['point']=[350.5,50.5]
    info['action_order']=['smoke','grenade']+[a for a in corrected.ACTIONS if a not in ('smoke','grenade')]+['move']
    images['grenade'][:]=images['smoke'][:]=0
    images['grenade'][50,350]=images['smoke'][50,350]=1
    winner='smoke' if variant=='r3' else 'grenade'
    for a in ('grenade','smoke'):
        wrong=[] if a==winner else [[350,50,winner]]
        info['ownership'][a]={'support_pixels':1,'wrong_owner_pixels':len(wrong),'unclaimed_pixels':0,'wrong_owner_witnesses_xy_action':wrong}
    result=corrected.audit_ownership(info,images,variant)
    assert not result['errors'],result['errors']
    ties.append({'variant':variant,'expected_winner':winner,'errors':result['errors']})
check('exact_ties_follow_each_source_policy',True,results=ties)

# Complete source receipt propagation and final CLI wiring. The inherited helper
# uses 32-scene marker metadata and explicitly stubs decoding, source geometry,
# contrast/affordance. Ownership itself was calculated above from real synthetic
# sample maps; no marker is native evidence.
FullProvenanceComparison.setUpClass()
paths=[]
try:
    case=FullProvenanceComparison('test_genuine_bad_baseline_stays_valid_and_cli_comparable')
    good=case.audited_source(corrected.audit_ownership(*Ownership().fixture(),'r4b'))
    assert good['provenance_valid'] and good['pass']
    for variant in ('r3','r4b'):
        genuine=case.audited_source(positives[variant])
        assert genuine['provenance_valid'] and not genuine['pass'] and not genuine['errors']
        assert case.cli(genuine,good)==0
        assert case.cli(good,genuine)==1
        paths.append({'variant':variant,'kind':'genuine_failure','provenance_valid':True,'baseline_cli':0,'candidate_cli':1})
        for name in NAMES:
            audited=case.audited_source(owners[(variant,name)])
            assert not audited['provenance_valid'] and audited['errors'] and not audited['pass']
            baseline_cli=case.cli(audited,good);candidate_cli=case.cli(good,audited)
            assert baseline_cli==candidate_cli==1
            paths.append({'variant':variant,'kind':name,'provenance_valid':False,'baseline_cli':baseline_cli,'candidate_cli':candidate_cli})
finally:FullProvenanceComparison.tearDownClass()
check('both_source_variants_both_comparison_roles_full_provenance_and_cli',len(paths)==58,synthetic_metadata_only=True,results=paths)

report['verdict']='ACCEPT_SOURCE_METHOD_ONLY_NO_NATIVE_LANE_RELEASE'
report['native_lane_released']=False
report['all_checks_pass']=all(x['pass'] for x in report['checks'].values())
(OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':len(report['checks']),'all_checks_pass':report['all_checks_pass'],'verdict':report['verdict']}))
