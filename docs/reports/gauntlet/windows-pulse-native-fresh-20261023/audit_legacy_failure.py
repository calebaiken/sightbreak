"""Reconstruct the original legacy reload timeout without promoting later success."""
import argparse
import hashlib
import json
from pathlib import Path

READ = lambda p: json.loads(p.read_text())


def audit(root):
    d = root/'evidence/reload-legacy-delayed'
    r, actions = READ(d/'results.json'), READ(d/'actions.json')
    telemetry = READ(d/'authority-telemetry.json')['samples']
    authority, diagnostic = READ(d/'authority.json'), READ(d/'diagnostic-exit.json')
    wait = next(x for x in actions if x['event']=='wait_begin' and x.get('label')=='Authority reload completion')
    timeout = next(x for x in actions if x['event']=='wait_timeout' and x.get('label')=='Authority reload completion')
    failed = next(x for x in actions if x['event']=='failure')
    completed = [x for x in telemetry if x.get('joined_id')==1 and x.get('ammo')==30
        and x.get('reserve')==86 and x.get('reload_remaining')==0 and x.get('shots')==4]
    first = min(completed,key=lambda x:x['wall_unix_msec']) if completed else None
    checks = {
        'original_failed_diagnostic_retained': r['passed'] is False and r['error']=='Authority reload completion'
            and diagnostic['exit_code']==1,
        'original_five_second_wait': wait['budget_seconds']==5 and timeout['seconds']-wait['seconds']>=5,
        'timeout_then_failure_same_incomplete_reload': timeout['seconds']<failed['seconds']
            and timeout['authority']==failed['authority'] and timeout['authority']['ammo']==26
            and timeout['authority']['reserve']==90 and 0<timeout['authority']['reload_remaining']<1,
        'later_completion_does_not_erase_timeout': bool(first) and first['wall_unix_msec']>timeout['wall_unix_msec']
            and r['failure_authority_observation']['ammo']==30 and authority['reload_completed'] is True,
        'failed_owned_process_termination_retained': len(r['commands'])==2
            and all(x['exit_code']==1 for x in r['commands']) and r['cleanup_errors']==[],
        'real_reload_input_reached_authority': any(x.get('reload_input') is True and x.get('reload_remaining',0)>0 for x in telemetry),
    }
    return {'run_id':39940242244,'qualification_verdict':'FAIL','checks_of_failure_facts':checks,
            'all_failure_fact_checks_passed':all(checks.values()),'original_wait':wait,'original_timeout':timeout,
            'original_failure':failed,'first_later_complete_sample':first,'original_final_authority':authority,
            'diagnostic_exit':diagnostic,'original_failed_processes':r['commands'],
            'wait_observed_wall_seconds':timeout['seconds']-wait['seconds'],
            'first_completion_after_timeout_msec':first['wall_unix_msec']-timeout['wall_unix_msec'] if first else None,
            'actions_sha256':hashlib.sha256((d/'actions.json').read_bytes()).hexdigest(),
            'scope':'Independent audit of original timeout and later completion. Wrapper step success cannot replace failed inner diagnostic; no missed-input or causal scheduling claim.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root)
    a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('qualification_verdict','all_failure_fact_checks_passed',
        'wait_observed_wall_seconds','first_completion_after_timeout_msec')}))
