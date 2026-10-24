"""Additional source combinations, separate expected obligations from fixture."""
from pathlib import Path
import json,os,sys
ROOT=Path(os.environ['MATH_REVIEW_ROOT']);sys.path.insert(0,str(ROOT/'scripts'))
from test_windows_fov_math_finalization import run_case
OUT=Path(__file__).resolve().parent/os.environ['MATH_REVIEW_LABEL'];OUT.mkdir(exist_ok=True)
specs=[('multiple_close_faults',dict(sink_fail=('stdout','stderr'),pipe_fail=('stderr',),extra=(300,301),fail_handle=1300)),
       ('audit_query_state_and_pipe_faults',dict(query_fail=True,state_fail=(1,2,3),pipe_fail=('stdout',))),
       ('terminal_snapshot_and_pipe_faults',dict(audit_snapshot_fail=True,pipe_fail=('stderr',)))]
rows=[]
for name,kwargs in specs:
    result,state=run_case(**kwargs)
    required=('sink/stdout','sink/stderr','pipe/stdout','pipe/stderr','job.close_held')
    obligations=dict(failed_structured=result['passed'] is False,
                     all_later_resources_attempted=all(item in state['events'] for item in required),
                     final_time_retained='finished' in result and 'elapsed' in result,
                     audit_retained=bool(result.get('audit',{}).get('samples',0)),
                     close_failure_recorded=bool(result.get('finalization',{}).get('errors')))
    if name=='multiple_close_faults':
        obligations.update(both_child_handles_attempted=all('handle/'+str(h) in state['events'] for h in (1300,1301)),
                           failed_child_handle_retained=state['remaining_owned_handles']==[1300],
                           offending_audit_retained=result['audit']['last']['ids']==[100,200,300,301])
    if name=='terminal_snapshot_and_pipe_faults':
        obligations['terminal_snapshot_error_typed']='audit_snapshot_error' in result
    rows.append(dict(name=name,scope='pure source combination; no actual native/API',input=kwargs,result=result,observations=state,obligations=obligations,matched=all(obligations.values())))
(OUT/'CASES.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps(dict(cases=len(rows),matched=sum(r['matched'] for r in rows),details=[dict(name=r['name'],obligations=r['obligations']) for r in rows])))
assert all(r['matched'] for r in rows)
