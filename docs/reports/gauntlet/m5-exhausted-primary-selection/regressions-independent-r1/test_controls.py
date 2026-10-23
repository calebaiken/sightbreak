#!/usr/bin/env python3
"""Pure corruptions of actual retained regression streams; originals stay untouched."""
import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('regression_rows',HERE/'audit_rows.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
read_text=Path.read_text


def changed_rows(text,prefix,select,mutate):
    result=[]
    for line in text.splitlines():
        if line.startswith(prefix):
            row=json.loads(line[len(prefix):])
            if select(row):mutate(row)
            line=prefix+json.dumps(row,separators=(',',':'))
        result.append(line)
    return '\n'.join(result)+'\n'


def run():
    raw=audit.RAW
    ai=raw/'bot_ai_regression.stdout.log';dry=raw/'bot_dry_weapon.stdout.log';sym=raw/'bot_squad_symmetry.stdout.log'
    aierr=raw/'bot_ai_regression.stderr.log';symerr=raw/'bot_squad_symmetry.stderr.log'
    texts={p:read_text(p) for p in [ai,dry,sym,aierr,symerr]}
    controls={
        'duplicate_AI_success_in_stderr':{aierr:'BOT_AI_REGRESSION_TESTS_OK\n'},
        'explicit_AI_failure_beside_success':{aierr:'BOT_AI_REGRESSION_FAILURE explicit failure\n'},
        'extra_dry_failure_result':{dry:texts[dry]+'BOT_DRY_WEAPON_RESULT {"passed":false}\n'},
        'duplicate_symmetry_result':{sym:texts[sym]+'BOT_SQUAD_SYMMETRY_RESULT samples=960 checks=2722 failures=0 mode=assertion\n'},
        'explicit_squad_failure_beside_success':{symerr:'BOT_SQUAD_FAILURE explicit failure\n'},
        'dry_numeric_boolean_counterfeit':{dry:changed_rows(texts[dry],'BOT_DRY_WEAPON_CASE ',lambda r:r['difficulty']=='easy' and r['name']=='rifle_dry',lambda r:r.__setitem__('reload',0))},
        'missing_dry_case':{dry:'\n'.join(l for l in texts[dry].splitlines() if not(l.startswith('BOT_DRY_WEAPON_CASE ') and '"name":"rifle_dry"' in l and '"difficulty":"easy"' in l))+'\n'},
        'unequal_pair':{sym:changed_rows(texts[sym],'BOT_SQUAD_SAMPLE ',lambda r:r['difficulty']=='easy' and r['team']==0 and r['kind']=='close' and r['id']==1,lambda r:r['output']['command'].__setitem__('fire',True))},
        'equal_pair_unsafe_smoke':{sym:changed_rows(texts[sym],'BOT_SQUAD_SAMPLE ',lambda r:r['difficulty']=='normal' and r['team']==0 and r['kind']=='smoke_near' and r['slot']==0,lambda r:r['output']['command'].__setitem__('smoke',True))},
        'equal_pair_wrong_anchor':{sym:changed_rows(texts[sym],'BOT_SQUAD_SAMPLE ',lambda r:r['difficulty']=='hard' and r['team']==1 and r['kind']=='travel' and r['slot']==0,lambda r:r['output'].__setitem__('destination','(0.0, 0.0, 0.0)'))},
    }
    outcomes=[]
    for name,replacements in controls.items():
        def read(path,*args,**kwargs):return replacements[path] if path in replacements else read_text(path,*args,**kwargs)
        try:
            with patch.object(Path,'read_text',read):audit.run()
        except (AssertionError,KeyError,ValueError,TypeError) as error:outcomes.append(dict(control=name,rejected=True,error=str(error)))
        else:raise AssertionError('corrupted actual output accepted: '+name)
    return dict(actual_corruption_controls=outcomes,passed=True,engine_invocations=0,scope='In-memory mutations only; original actual logs preserved.')

if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
