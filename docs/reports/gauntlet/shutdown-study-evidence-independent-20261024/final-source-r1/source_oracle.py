"""Corroborate existing fence cases using two pure frozen-source functions."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import types

REPORT=Path(__file__).resolve().parent
SOURCE=REPORT.parents[4]
raw=(SOURCE/'scripts/verify_offline_export.py').read_bytes();tree=ast.parse(raw)
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('require_living_capture_phase','capture_living_phase')]
assert len(functions)==2
scope={'time':types.SimpleNamespace(monotonic=lambda:0.)}
exec(compile(ast.Module(body=functions,type_ignores=[]),'<two frozen pure source functions>','exec'),scope)


def evaluate(row):
    fence=row['phase_capture_fences']['06c-next-round'];observed_fields=iter(('acknowledged','ready','before_capture','after_capture_barrier','after_capture'))
    checks=[];captures=[];error=None
    def observed(predicate,budget,label,after=-1):
        field=next(observed_fields);state=copy.deepcopy(fence[field])
        record=dict(field=field,label=label)
        try:
            record['predicate']=bool(predicate(state));checks.append(record)
            if not record['predicate']:raise RuntimeError('false source wait predicate cannot populate returned '+field)
            return state
        except RuntimeError as caught:
            record['error']=str(caught)
            if record not in checks:checks.append(record)
            raise
    try:
        scope['capture_living_phase']('06c-next-round',actor_id=1,round_number=2,
            after=fence['acknowledged']['wall_msec']-1,until=10.,observed=observed,capture=captures.append,
            binding=lambda:copy.deepcopy(fence['expected_binding']),expected_binding=copy.deepcopy(fence['expected_binding']),receipt={},clock=lambda:0.)
    except RuntimeError as caught:error=str(caught)
    return dict(error=error,predicate_checks=checks,fake_capture_calls=captures,scope='local source predicates only; no physical history or native/UI action')


run=REPORT/'own-independent';rows={}
baseline=json.loads((run/'baseline/results.json').read_bytes());rows['accepted-format-baseline']=evaluate(baseline);assert rows['accepted-format-baseline']['error'] is None
for folder in sorted((run/'cases').iterdir()):
    info=json.loads((folder/'INPUT.json').read_text());label=info['label']
    if label not in ('capture-wrong-phase','capture-wrong-actor','capture-missing-two-frames','capture-dead-after-capture'):continue
    row=json.loads((folder/'delta/results.json').read_bytes());result=evaluate(row)
    assert info['actual_strict_passed'] is True and result['error'] is not None
    result['candidate_strict_passed']=True;result['input_sha256']=hashlib.sha256((folder/'delta/results.json').read_bytes()).hexdigest();rows[label]=result
constants={name:[] for name in ('completion_watchdog_seconds','whole_flow_deadline_unchanged','same_living_player_required')}
for node in ast.walk(tree):
    if isinstance(node,ast.Dict):
        for key,value in zip(node.keys,node.values):
            if isinstance(key,ast.Constant) and key.value in constants:
                constants[key.value].append(dict(line=node.lineno,value=ast.literal_eval(value),kind=type(ast.literal_eval(value)).__name__))
for name,expected in [('completion_watchdog_seconds',15),('whole_flow_deadline_unchanged',True),('same_living_player_required',True)]:assert constants[name] and all(item['value']==expected and item['kind']==type(expected).__name__ for item in constants[name])
output=dict(source='0f478a078277fdb0d711837bef67cf14262d9d8f',default_driver_sha256=hashlib.sha256(raw).hexdigest(),source_function_lines={n.name:n.lineno for n in functions},local_fence_oracles=rows,source_constants=constants,
            target_reader_rerun=False,native_invocations=0,qualification='UNREVIEWED; local pure-source corroboration only')
(REPORT/'SOURCE_ORACLE.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(dict(baseline_pure_predicates_pass=True,existing_bad_fence_cases_corroborated=len(rows)-1,source_constants=constants,target_reader_rerun=False)))
