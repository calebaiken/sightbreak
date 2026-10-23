#!/usr/bin/env python3
"""Pure independent verbose-output audit, reusing the frozen all-row critic."""
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

REPO=Path(__file__).resolve().parents[5]
SOURCE=Path('/workspace/sightbreak-exhausted-primary-verbose-r2')
RAW=SOURCE/'.local/verbose-leak-diagnostic-r1-20261023'
ORIGINAL=Path('/workspace/sightbreak-exhausted-primary-benchmark/.local/exhausted-primary-r2-single-attempt-20261023')
PACKAGE='239ee99'
PREFIX='docs/reports/gauntlet/m5-exhausted-primary-verbose-diagnostic/actual-r1/'
PRIOR=REPO/'docs/reports/gauntlet/m5-exhausted-primary-benchmark/independent-actual'

def sha(data):return hashlib.sha256(data).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO)
def blob(name):return git('show',PACKAGE+':'+PREFIX+name)

def audit():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=SOURCE).decode().strip()=='b87afb717bf09a78c6d36b164d48906902734bdb'
    assert subprocess.check_output(['git','status','--porcelain'],cwd=SOURCE)==b''
    # Require exact prior committed audit bytes before reusing its functions.
    for name in ['audit_identity.py','audit_raw.py']:
        assert (PRIOR/name).read_bytes()==git('show','b5fa18a:'+str((PRIOR/name).relative_to(REPO))),name
    identity_source=(PRIOR/'audit_identity.py').read_text()
    adaptations=[
        ("('preparation',34219,971492), ('baseline',34468,972148)","('preparation',45378,1084400), ('verbose_diagnostic',45630,1085054)"),
        ("'run_once.py'","'run_verbose_once.py'"),
        ("else ['--path', str(stage / 'game'), '--script'","else ['--verbose', '--path', str(stage / 'game'), '--script'"),
        ("'baseline-probe.stderr.log'","'verbose-diagnostic-probe.stderr.log'")]
    for old,new in adaptations:
        assert identity_source.count(old)==1,old
        identity_source=identity_source.replace(old,new)
    namespace={'__name__':'independent_verbose_identity'}
    exec(compile(identity_source,'<exact-prior-identity-with-explicit-attempt-adaptations>','exec'),namespace)
    identity=namespace['audit'](RAW,SOURCE)
    spec=importlib.util.spec_from_file_location('prior_independent_raw',PRIOR/'audit_raw.py')
    raw_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(raw_module)
    records,other=raw_module.parse(RAW/'verbose-diagnostic-probe.stdout.log')
    behavior=raw_module.audit(records,REPO)
    old_records,old_other=raw_module.parse(ORIGINAL/'baseline-probe.stdout.log')
    assert len(records)==len(old_records)==1318
    assert [(kind,row) for _,kind,row in records]==[(kind,row) for _,kind,row in old_records],'any fixture JSON changed'
    def fixture_bytes(path):return b'\n'.join(line for line in path.read_bytes().splitlines() if line.startswith(b'BOT_EXHAUSTED_'))
    fixture_stream=fixture_bytes(RAW/'verbose-diagnostic-probe.stdout.log')
    assert fixture_stream==fixture_bytes(ORIGINAL/'baseline-probe.stdout.log'),'fixture record bytes changed'
    # Every retained archive is checked against its Git object and original.
    archive_map=json.loads(blob('archive-map.json'))
    assert len(archive_map)==17
    publication_additions=git('diff','--name-only','0f6f5e4',PACKAGE,'--',PREFIX).decode().splitlines()
    assert publication_additions==[PREFIX+'preparation-import.stderr.log',PREFIX+'verbose-diagnostic-probe.stderr.log']
    for filename in ['preparation-import.stderr.log','verbose-diagnostic-probe.stderr.log']:
        assert subprocess.run(['git','cat-file','-e','0f6f5e4:'+PREFIX+filename],cwd=REPO,capture_output=True).returncode!=0
    archive_checks=[]
    for entry in archive_map:
        archived=blob(entry['archived_path'])
        assert (len(archived),sha(archived))==(entry['archive_bytes'],entry['archive_sha256']),entry['archived_path']
        original=gzip.decompress(archived) if entry['compression']=='gzip' else archived
        assert entry['compression'] in ['gzip','none']
        assert (len(original),sha(original))==(entry['original_bytes'],entry['original_sha256']),entry['relative_original']
        assert Path(entry['original_path'])==RAW/entry['relative_original']
        assert original==(RAW/entry['relative_original']).read_bytes(),entry['relative_original']
        archive_checks.append(dict(path=entry['relative_original'],compression=entry['compression'],original_bytes=len(original),original_sha256=sha(original)))
    controller=(RAW/'run_verbose_once.py').read_bytes()
    approved=git('show','817516a:docs/reports/gauntlet/m5-exhausted-primary-verbose-diagnostic/run_verbose_once.py')
    assert controller==approved and sha(controller)=='43dfdeae51aaa95dbb43aeb33125c772688f50e604cc471c8b4ba0309734c7fe'
    launch=json.loads((RAW/'root-launch-plan.json').read_text())
    assert launch['controller_sha256']==sha(controller)
    assert launch['command']==['/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(RAW/'run_verbose_once.py')]
    assert launch['original_strict_failure_preserved'] is True and launch['diagnostic_only'] is True
    # Independently parse exact typed failures; generic engine hints are retained
    # as hints, never converted into this probe's diagnosed allocation cause.
    leaks=[]
    for line,text in other:
        match=re.fullmatch(r'Leaked instance: (\w+):(\d+) - Reference count: (\d+)',text)
        if match:leaks.append(dict(line=line,type=match[1],instance_id=match[2],reference_count=int(match[3]),raw=text))
    assert [(x['type'],x['instance_id'],x['reference_count']) for x in leaks]==[('AudioStreamPlaybackWAV','9223372369278539738',1),('AudioStreamWAV','9223372163673757853',1)]
    names=[dict(line=line,raw=text) for line,text in other if text.startswith(('Orphan StringName:','StringName:'))]
    assert [x['raw'] for x in names]==['Orphan StringName: Master (static: 0, total: 2)','StringName: 1 unclaimed string names at exit.']
    assert all(x['line']>records[-1][0] for x in leaks+names),'typed failure must follow fixture result'
    stderr=(RAW/'verbose-diagnostic-probe.stderr.log').read_bytes()
    assert stderr==(ORIGINAL/'baseline-probe.stderr.log').read_bytes()
    errors=[dict(line=line,raw=text) for line,text in other if re.search(r'SCRIPT ERROR|Parse Error|(^|\s)ERROR:',text)]
    assert not errors,errors
    processes=[]
    for pid,start in [(45378,1084400),(45630,1085054)]:
        path=Path('/proc')/str(pid)/'stat'
        value=path.read_text() if path.exists() else None
        current_start=int(value[value.rfind(')')+2:].split()[19]) if value else None
        assert current_start!=start,'original native identity still present'
        processes.append(dict(pid=pid,original_start_ticks=start,current_start_ticks=current_start))
    summary=json.loads(blob('ROOT_SUMMARY.json'))
    assert summary['typed_leak_lines']==[x['raw'] for x in leaks]+[names[0]['raw']]
    assert summary['original_stderr']==stderr.decode() and summary['strict_native_result']=='FAILED_OBJECTDB_LEAKS'
    assert (summary['case_rows'],summary['sequence_steps'],summary['control_steps'],summary['fixture_checks'])==(567,576,96,18499)
    overall=json.loads((RAW/'overall.receipt.json').read_text())
    assert overall['original_failed_baseline_evidence']=='700abf8c9d43279518c5257edfdbaee513569cea'
    assert overall['diagnostic_purpose']=='Identify only this unchanged verbose run leaked object types; no acceptance replacement'
    return dict(strict_native_verdict='REJECT',diagnostic_evidence_verdict='ACCEPT exact provenance, observable behavior and typed failure records',package_commit=git('rev-parse',PACKAGE).decode().strip(),initial_publication_gap=dict(commit='0f6f5e4',missing_original_stderr_files=publication_additions,corrected_by=git('rev-parse',PACKAGE).decode().strip()),identity=identity,identity_adaptations=adaptations,adapted_identity_sha256=sha(identity_source.encode()),behavior=behavior,fixture_comparison=dict(original_and_verbose_records=1318,exact_fixture_record_bytes_equal=True,fixture_record_stream_sha256=sha(fixture_stream),differing_json_fields=0),archive_members=archive_checks,controller_sha256=sha(controller),root_launch_plan=launch,root_tool_receipt_limit='ROOT_SUMMARY reports tool session 23521 exit 0; the package retains a preregistered outer launch plan, not the external tool transcript or an outer PID/start identity.',typed_leaks=leaks,string_name_failures=names,original_stderr=stderr.decode(),all_nonfixture_stdout=[dict(line=line,raw=text) for line,text in other],review_time_original_pid_checks=processes,original_baseline_types_remain_unidentified=True,shared_ARM_cause_established=False,additional_runtime_by_critic=False)

if __name__=='__main__':print(json.dumps(audit(),indent=2,sort_keys=True))
