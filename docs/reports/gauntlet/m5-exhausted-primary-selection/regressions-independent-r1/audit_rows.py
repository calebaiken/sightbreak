#!/usr/bin/env python3
"""Independent actual regression inventory, prior-output comparison and safety checks."""
import ast
import copy
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
SOURCE=Path('/workspace/sightbreak-exhausted-primary-selection')
RAW=SOURCE/'.local/exhausted-selection-regressions-r1'
OLD='6a0ef573c67df73c574f525bd1461176d3995241'
OLD_REPORT='docs/reports/gauntlet/m5-dry-weapon-recovered/'
DIFFICULTIES=('easy','normal','hard')
KINDS=('close','long','travel','stuck','stuck_low','stuck_jump','idle','smoke','spent_smoke','empty_smoke','smoke_near','smoke_far','carrier_smoke','carrier','defuser','cover')

def git(*args):return subprocess.check_output(['git',*args],cwd=SOURCE)
def sha(data):return hashlib.sha256(data).hexdigest()
def module(path):
    spec=importlib.util.spec_from_file_location('independent_dry',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def records(text,prefix):
    relevant=[line for line in text.splitlines() if line.startswith(prefix.rstrip())]
    assert all(line.startswith(prefix) for line in relevant),'malformed relevant record '+prefix
    return [json.loads(line[len(prefix):]) for line in relevant]

def vector(value,size):
    result=ast.literal_eval(value)
    assert isinstance(result,tuple) and len(result)==size and all(type(x) in (int,float) and math.isfinite(x) for x in result),'finite vector'
    return result

def run():
    checks=0
    def check(v,m):
        nonlocal checks
        checks+=1
        assert v,m
    paths={s:RAW/(s+'.stdout.log') for s in ('bot_ai_regression','bot_dry_weapon','bot_squad_symmetry')}
    texts={s:p.read_text()+'\n'+(RAW/(s+'.stderr.log')).read_text() for s,p in paths.items()}
    # Relevant inventory includes malformed/extra records and both streams.
    ai=[line.strip() for line in texts['bot_ai_regression'].splitlines() if line.strip().startswith(('BOT_AI_REGRESSION_TESTS_','BOT_AI_REGRESSION_RESULT'))]
    check(ai==['BOT_AI_REGRESSION_TESTS_OK'],'unique AI success/no contradictory result')
    for s,t in texts.items():
        check(not any(l.strip().startswith(('BOT_AI_REGRESSION_FAILURE','BOT_DRY_WEAPON_FAILURE','BOT_SQUAD_FAILURE')) for l in t.splitlines()),'no explicit failure '+s)
    drylines=[l.strip() for l in texts['bot_dry_weapon'].splitlines() if l.strip().startswith('BOT_DRY_WEAPON_RESULT')]
    check(len(drylines)==1,'unique complete dry result inventory')
    check(json.loads(drylines[0].split(' ',1)[1])==dict(cases=84,sequence_steps=48,checks=590,failures=0,passed=True),'exact complete dry result')
    symlines=[l.strip() for l in texts['bot_squad_symmetry'].splitlines() if l.strip().startswith('BOT_SQUAD_SYMMETRY_RESULT')]
    check(symlines==['BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion'],'unique complete assertion symmetry result')
    dry=module(HERE/'original-independent-dry-recompute.py')
    expected,_=dry.expectations('candidate')
    cases=records(texts['bot_dry_weapon'],'BOT_DRY_WEAPON_CASE ')
    steps=records(texts['bot_dry_weapon'],'BOT_DRY_WEAPON_STEP ')
    summaries=records(texts['bot_dry_weapon'],'BOT_DRY_WEAPON_SEQUENCE ')
    check(len(cases)==84 and len(steps)==48 and len(summaries)==6,'complete dry observable counts')
    check([(r['difficulty'],r['name']) for r in cases]==list(expected),'source-declared dry case order')
    for row in cases:
        e=expected[row['difficulty'],row['name']]
        want=dict(e,expected_weapon=e['requested'],expected_reload=e['reload'])
        check(row==want,'complete dry observed case '+str((row['difficulty'],row['name'])))
        for k,v in want.items():check(type(row[k]) is type(v),'strict dry type '+k)
    stepkeys=list(itertools.product(DIFFICULTIES,('idle','alternating'),range(8)))
    check([(r['difficulty'],r['sequence'],r['step']) for r in steps]==stepkeys,'exact dry step order')
    for r in steps:
        d,s,i=r['difficulty'],r['sequence'],r['step']
        want=dict(difficulty=d,sequence=s,step=i,visible=s=='alternating' and i%2==1,prior_weapon='sidearm',requested='',reload=False,fire=False,active='sidearm',ammo=15,reserve=60,reload_remaining=0.0,deploy_remaining=0.0,total_ammo=75,shots=0)
        check(r==want,'complete dry action/resource step '+str((d,s,i)))
        for k in ('visible','reload','fire'):check(type(r[k]) is bool,'strict dry command boolean')
    check(summaries==[dict(difficulty=d,sequence=s,switches=0,dry_equips=0,empty_reloads=0,shots=0) for d,s in itertools.product(DIFFICULTIES,('idle','alternating'))],'all dry sequence summaries derived')
    olddry=git('show',OLD+':'+OLD_REPORT+'candidate-r1/runtime.log').decode()
    for prefix in ('BOT_DRY_WEAPON_CASE ','BOT_DRY_WEAPON_STEP ','BOT_DRY_WEAPON_SEQUENCE ','BOT_DRY_WEAPON_RESULT '):
        check(records(texts['bot_dry_weapon'],prefix)==records(olddry,prefix),'complete accepted prior dry outputs '+prefix)
    for name in ('bot_dry_weapon_test.gd','bot_squad_symmetry_test.gd','bot_ai_regression_test.gd'):
        path='game/tests/'+name
        check(git('show','6276f0b:'+path)==git('show','8e8d13e:'+path),'unchanged prior accepted fixture '+name)
    samples=records(texts['bot_squad_symmetry'],'BOT_SQUAD_SAMPLE ')
    check(len(samples)==960,'all symmetry samples')
    expectedkeys=[(d,t,k,slot,id) for d,t,k,slot in itertools.product(DIFFICULTIES,(0,1),KINDS,range(5)) for id in (slot+1,slot+6)]
    check([(r['difficulty'],r['team'],r['kind'],r['slot'],r['id']) for r in samples]==expectedkeys,'exact symmetry identity/order')
    invariants=Counter()
    for a,b in zip(samples[::2],samples[1::2]):
        check(a['output']==b['output'],'all 480 paired full command/role/destination')
    for r in samples:
        d,t,k,slot=r['difficulty'],r['team'],r['kind'],r['slot']
        o=r['output'];c=o['command'];mv=vector(c['move'],2);look=vector(c['look'],2);dest=vector(o['destination'],3)
        check(set(c)==set('crouch fire grenade interact jump look move reload smoke weapon'.split()),'complete squad input')
        for field in ('crouch','fire','grenade','interact','jump','reload','smoke'):check(type(c[field]) is bool,'squad strict bool '+field)
        check(type(o['role']) is str and type(c['weapon']) is str,'squad string outputs')
        if k=='close':check(not c['fire'] and c['crouch']==(slot%3==0),'close reaction/crouch');invariants[k]+=1
        elif k=='long':
            check(c['crouch']==(slot%3==0 or d!='easy'),'long crouch')
            if d!='easy':check(mv==(0,0),'long braking')
            invariants[k]+=1
        elif k=='smoke':check(c['smoke']==(d!='easy' and(t==1 or slot%2==0)),'smoke role gate');invariants[k]+=1
        elif k in ('spent_smoke','empty_smoke','smoke_near','smoke_far'):check(not c['smoke'],'smoke suppression');invariants[k]+=1
        elif k=='carrier_smoke':check(c['smoke']==(d!='easy'),'carrier smoke exception');invariants[k]+=1
        elif k=='stuck':check(c['jump'] and mv==((1 if slot%2==0 else -1),-.6),'stuck reverse/jump');invariants[k]+=1
        elif k=='stuck_low':check(not c['jump'] and mv==(0,1),'low stuck guard');invariants[k]+=1
        elif k=='stuck_jump':check(c['jump'] and mv==((1 if slot%2==0 else -1),1),'stuck jump-before-reverse');invariants[k]+=1
        elif k=='idle':check(mv==(0,0),'stationary idle scan');invariants[k]+=1
        elif k=='carrier' and t==0:check(o['role']=='carrier' and c['interact'] and mv==(0,0) and not c['fire'] and not c['smoke'],'plant carrier guard');invariants[k]+=1
        elif k=='defuser' and t==1:check(o['role']=='defuser' and c['interact'] and mv==(0,0),'nearest defuser');invariants[k]+=1
        elif k=='cover' and t==1:check(o['role']=='retake_cover' and not c['interact'],'retake cover');invariants[k]+=1
        if k=='travel' and t==1:
            anchors=[(-15,0,12),(15,0,12),(-12,0,6),(12,0,6),(0,0,9)]
            sites=[(-15,0,10),(15,0,10)]
            check(o['role']=='anchor' and dest==(sites[slot%2] if d=='easy' else anchors[slot]),'defender slot destination');invariants['travel']+=1
    oldsym=git('show',OLD+':'+OLD_REPORT+'candidate-squad-r1/runtime.log').decode()
    check(samples==records(oldsym,'BOT_SQUAD_SAMPLE '),'all 960 prior accepted symmetry outputs unchanged')
    engines=records(texts['bot_dry_weapon'],'BOT_DRY_WEAPON_ENGINE ')
    check(len(engines)==1 and (engines[0]['major'],engines[0]['minor'],engines[0]['patch'])==(4,7,2),'actual dry engine header')
    check([l for l in texts['bot_squad_symmetry'].splitlines() if l.startswith('BOT_SQUAD_SYMMETRY engine=')]==['BOT_SQUAD_SYMMETRY engine=4.7.2-stable (official) observe=false'],'symmetry engine/no-observe header')
    return dict(independent_observable_predicates=checks,dry_case_count=len(cases),dry_step_count=len(steps),dry_sequence_count=len(summaries),symmetry_samples=len(samples),equal_full_output_pairs=480,raw_safety_invariant_samples=dict(invariants),prior_raw_commit=OLD,prior_dry_stdout_sha256=sha(olddry.encode()),prior_squad_stdout_sha256=sha(oldsym.encode()),complete_prior_dry_and_squad_observables_equal=True,stdout_sha256={s:sha(p.read_bytes()) for s,p in paths.items()},scope='Raw logged fields reconstructed; dry unlogged protected snapshots, symmetry reaction/smoke-reset/phase internals and AI marker-only details remain source-assertion-bound.')

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
