"""Static-only source/proposal binding; never import or execute the proposal."""
import ast
import hashlib
import json
import os
from pathlib import Path

REPORT=Path(__file__).resolve().parent
ROOT=REPORT.parents[4]


def main():
    assert os.sched_getaffinity(0)=={4}
    draft=(REPORT/'FIXTURE_ACTION_PLAN_PROPOSAL.py').read_bytes()
    tree=ast.parse(draft)
    strings={n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) is str}
    imports=[ast.unparse(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    assert imports==['import copy']
    source=(ROOT/'scripts/verify_offline_export.py').read_bytes()
    fixture=(ROOT/'scripts/shutdown_evidence_fixtures.py').read_bytes()
    expected_source='b744b9bb8d594d2018f3ca71c89a22ca03fc0966570e5e1bf7658725aea90edd'
    expected_fixture='c0d98d6d94cf9bc5875a919d56ebc734536fa88f1d82c9e8d1c5cef7f13a6f3b'
    assert hashlib.sha256(source).hexdigest()==expected_source
    assert hashlib.sha256(fixture).hexdigest()==expected_fixture
    absent=['Real offline match readiness after one Deploy click',
            'Living second-round player before fixed settings route',
            'Restore actual native input focus',
            'native_focus_loss_before','native_focus_loss_after',
            'native_focus_restore_before','native_focus_restore_after',
            'deploy_click_before','deploy_click_after',
            'reopened_deploy_click_before','reopened_deploy_click_after']
    assert all(s not in strings for s in absent)
    f_tree=ast.parse(fixture)
    original_event_calls=[]
    for n in ast.walk(f_tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='action' and n.args and isinstance(n.args[0],ast.Constant):
            original_event_calls.append(dict(line=n.lineno,event=n.args[0].value))
    assert {r['event'] for r in original_event_calls}=={'capture_begin','capture_end','click_text','settings_slider_click'}
    top=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='producer_action_plan')
    nested={n.name:n for n in top.body if isinstance(n,ast.FunctionDef)}
    action_src=ast.get_source_segment(draft.decode(),nested['action'])
    observed_src=ast.get_source_segment(draft.decode(),nested['observed'])
    assert 'held_keys=[]' in action_src
    assert all(label in observed_src for label in ('wait_begin','wait_completed','offline_observation'))
    lines=source.decode().splitlines()
    intervals=[(285,339),(590,606),(609,620),(669,674),(694,706),(745,753),(767,792),(837,850),(926,941),(960,1009),(1020,1048)]
    excerpts=[dict(first_line=a,last_line=b,text='\n'.join(lines[a-1:b])+'\n') for a,b in intervals]
    prior=REPORT.parent/'final-source-r1'
    manifest=json.loads((prior/'MANIFEST.json').read_text())
    for name,info in manifest.items():
        raw=(prior/name).read_bytes()
        assert len(raw)==info['bytes'] and hashlib.sha256(raw).hexdigest()==info['sha256'],name
    result=dict(proposal='63021bac381c3f5e7119d3769131754c584f4823',proposal_sha256=hashlib.sha256(draft).hexdigest(),
                imports=imports,proposal_imports_or_execution=0,source_sha256=expected_source,fixture_sha256=expected_fixture,
                source_excerpts=excerpts,missing_literal_operations_not_in_original_action_stream=absent,
                original_fixture_action_calls=sorted(original_event_calls,key=lambda row:row['line']),
                held_key_reset_source=action_src,observed_helper_source=observed_src,
                prior_final_manifest_members_preserved=len(manifest),prior_final_manifest_bytes_preserved=sum(r['bytes'] for r in manifest.values()),
                prior_final_manifest_sha256=hashlib.sha256((prior/'MANIFEST.json').read_bytes()).hexdigest(),
                verdict_scope='Static construction adjudication only',native_API_helper_process_or_CI_trials=0,
                lookup_note='A broad source search named nonexistent scripts/native_control.py; actual trace/key/wait/capture definitions are nested in frozen verify_offline_export.py and were read directly. No test was skipped.')
    (REPORT/'STATIC_SOURCE_EVIDENCE.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(static=True,proposal_execution=0,missing_operations=len(absent),held_key_reset=True,original_final_members_preserved=len(manifest))))


if __name__=='__main__':main()
