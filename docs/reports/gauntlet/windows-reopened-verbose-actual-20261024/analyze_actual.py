#!/usr/bin/env python3
"""Offline review of preserved official raw; never imports/runs a native controller."""
import argparse
import hashlib
import json
import math
import ntpath
from pathlib import Path
import re

SOURCE = '7101350e5d0a2f6e4afb9a913b5b1bcf2107857a'
GAME = 'bca627d5dc8e4482b63e263020a6382f2d36f33c'
CONTENT = '43a71ef7ea38febc735b67e24337c8f975bf69d57e3e4b06f94d175170d56eb8'
VALIDATION = 'be2f4ea73ede8a94e6dede7198353cdcd339b74c2fe6208c37863c7286c23e71'
STRICT = re.compile(r'^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$', re.M)
INSTANCE = re.compile(r'^Leaked instance: (?P<native_class>[^:]+):(?P<instance_id>[0-9]+)(?: - (?P<detail>.*))?$')
RESOURCE = re.compile(r'^Resource still in use: (?P<path>.*) \((?P<native_class>[^()]*)\)$')
COUNT = re.compile(r'([0-9]+) ObjectDB instance(?:s were| was) leaked at exit')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def logs(directory):
    output = []
    for path in sorted(directory.rglob('*.log')):
        data = path.read_bytes()
        text = data.decode('utf-8', errors='replace')
        rows, resources, counts, unmatched, warnings, failures = [], [], [], [], [], []
        for number, line in enumerate(text.splitlines(), 1):
            anchor = {'line_number': number, 'raw_text': line}
            if 'WARNING' in line:
                warnings.append(anchor)
            if STRICT.search(line):
                failures.append(anchor)
            count = COUNT.search(line)
            if count:
                counts.append({**anchor, 'count': int(count.group(1))})
            if line.startswith('Leaked instance:'):
                match = INSTANCE.fullmatch(line)
                if not match:
                    unmatched.append(anchor)
                    continue
                fields = match.groupdict()
                detail = fields.pop('detail')
                row = {**anchor, **fields, 'instance_id_in_uint64_range': 0 < int(fields['instance_id']) < 2**64, 'node_path': None, 'reference_count': None,
                       'resource_path_as_printed': None, 'unparsed_detail': None, 'parse_status': 'PARSED'}
                if detail is not None:
                    if detail.startswith('Node path: '):
                        row['node_path'] = detail.removeprefix('Node path: ')
                    elif re.fullmatch(r'Reference count: [0-9]+', detail):
                        row['reference_count'] = int(detail.removeprefix('Reference count: '))
                    elif detail.startswith('Resource path: '):
                        row['resource_path_as_printed'] = detail.removeprefix('Resource path: ')
                    else:
                        row.update(unparsed_detail=detail, parse_status='UNPARSED_DETAIL')
                rows.append(row)
            if line.startswith('Resource still in use:'):
                match = RESOURCE.fullmatch(line)
                resources.append({**anchor, **(match.groupdict() if match else {}),
                                  'parse_status': 'PARSED' if match else 'UNPARSED'})
        output.append({'relative_path': path.relative_to(directory).as_posix(), 'bytes': len(data),
                       'sha256': hashlib.sha256(data).hexdigest(), 'utf8_replacement_present': '\ufffd' in text,
                       'strict_failed': bool(STRICT.search(text)), 'strict_lines': failures,
                       'warnings': warnings, 'objectdb_summaries': counts, 'instances': rows,
                       'instance_ids_are_decimal_strings': True, 'unmatched_instance_lines': unmatched,
                       'separate_resource_cache_rows': resources,
                       'instance_id_duplicates': sorted({x['instance_id'] for x in rows if sum(y['instance_id']==x['instance_id'] for y in rows)>1}),
                       'single_summary_count_matches_rows': len(counts)==1 and counts[0]['count']==len(rows)})
    return output

def review(directory, out):
    offline = directory / 'offline-input'
    checks, read_errors = [], []
    def check(name, value):
        checks.append({'name': name, 'passed': bool(value)})
    def read_json(path):
        try:
            return json.loads(path.read_text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        except (OSError, ValueError) as error:
            read_errors.append({'path': str(path), 'error': str(error)})
            return None
    raw_result = read_json(offline/'results.json')
    result = raw_result if type(raw_result) is dict else {}
    commands = read_json(offline/'commands.json')
    contract = json.loads((Path(__file__).parent/'EXACT_COMMAND_CONTRACT.json').read_text())
    original = json.loads((Path(__file__).parent/'ORIGINAL_COUNTERPART.json').read_text())
    check('result object available', type(raw_result) is dict)
    check('result passed is literal Boolean', type(result.get('passed')) is bool)
    check('target Windows', result.get('target') == 'windows')
    check('pinned engine', result.get('engine') == '4.7.2.stable.official.ed1daf0bf')
    for label in ('source','artifact_source'):
        record = result.get(label)
        record = record if type(record) is dict else {}
        for key,wanted in (('source_commit',SOURCE),('source_game_tree',GAME),('source_content_sha256',CONTENT),('source_validation_sha256',VALIDATION)):
            check(label+'.'+key, record.get(key)==wanted)
        for key in ('source_dirty','source_game_dirty'):
            check(label+'.'+key+' literal false', record.get(key) is False)
    artifact_source = result.get('artifact_source')
    artifact_source = artifact_source if type(artifact_source) is dict else {}
    artifact = artifact_source.get('artifact')
    artifact = artifact if type(artifact) is dict else {}
    digest = result.get('executable_sha256')
    check('executable SHA256 shape and artifact-receipt equality', type(digest) is str and re.fullmatch('[0-9a-f]{64}',digest) is not None and digest==artifact.get('sha256'))
    controller = result.get('controller_command')
    check('evaluated controller command exact suffix', type(controller) is list and all(type(x) is str for x in controller) and controller[1:] == contract['windows_living_controller_argv_after_python'])
    good_rows = type(commands) is list and len(commands)==2 and all(type(x) is dict for x in commands)
    check('two command row objects',good_rows)
    check('two ordered uniquely named command rows',good_rows and [x.get('name') for x in commands]==['client','reopened'])
    check('commands equal results commands', type(commands) is list and commands==result.get('commands'))
    for name in ('initial_exit','reopened_exit'):
        check(name+' literal integer', type(result.get(name)) is int)
    cleanup=result.get('cleanup_errors')
    check('cleanup_errors list of strings', type(cleanup) is list and all(type(x) is str for x in cleanup))
    elapsed=result.get('elapsed_seconds')
    check('elapsed finite nonnegative number', type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0)
    if good_rows:
        for index,name in enumerate(('client','reopened')):
            row=commands[index]
            check(name+' PID positive integer', type(row.get('pid')) is int and row['pid']>0)
            check(name+' exit nonBoolean integer', type(row.get('exit_code')) is int)
            started=row.get('started_seconds')
            check(name+' start finite nonnegative number',type(started) in (int,float) and math.isfinite(started) and started>=0)
        check('process IDs distinct',commands[0].get('pid')!=commands[1].get('pid'))
    good_argv=good_rows and all(type(x.get('command')) is list and all(type(v) is str for v in x['command']) for x in commands)
    check('literal native argv arrays available',good_argv)
    argv_confounds=[]
    if good_argv:
        initial,reopened=[row['command'] for row in commands]
        old_initial=original['commands'][0]['command']
        good_initial=len(initial)==10 and initial[1:6]==['--audio-driver','Dummy','--position','0,0','--resolution'] and re.fullmatch('[1-9][0-9]*x[1-9][0-9]*',initial[6]) is not None and initial[7:9]==['--','--offline-validation']
        check('initial engine arguments exact schema',good_initial)
        check('initial argv has no verbose','--verbose' not in initial)
        check('reopened engine argv changes only by one verbose',len(reopened)==11 and len(initial)==10 and reopened[:7]==initial[:7] and reopened[7:10]==['--verbose','--','--offline-validation'] and reopened.count('--verbose')==1 and reopened.count('--')==1)
        check('same original exported artifact path',len(initial)>0 and initial[0]==old_initial[0] and len(reopened)>0 and reopened[0]==old_initial[0])
        check('same owned separate trace paths',len(initial)==10 and len(reopened)==11 and initial[-1]==old_initial[-1] and reopened[-1]==original['commands'][1]['command'][-1])
        if good_initial and initial[6]!=old_initial[6]:
            argv_confounds.append({'native_resolution_old':old_initial[6],'native_resolution_actual':initial[6]})
    normal=read_json(directory/'native-input'/'commands.json')
    normal_rows=type(normal) is list and len(normal)==2 and all(type(x) is dict and type(x.get('command')) is list and all(type(v) is str for v in x['command']) for x in normal)
    check('ordinary input command rows available',normal_rows)
    if normal_rows:
        check('ordinary client/server exact names',[x.get('name') for x in normal]==['server','client'])
        check('ordinary server/client have no verbose',all('--verbose' not in x['command'] for x in normal))
        check('original enabled observer user-argument position',all(x['command'].count('--native-input-observation')==1 and x['command'].count('--')==1 and x['command'].index('--')<x['command'].index('--native-input-observation') for x in normal))
    focus=result.get('native_focus_recovery')
    focus=focus if type(focus) is dict else {}
    fence=focus.get('context_fence')
    fence=fence if type(fence) is dict else {}
    check('source living-focus completion markers retained',focus.get('passed') is True and fence.get('status')=='LIVING_CONTEXT_PRESERVED_THROUGH_CAPTURE')
    all_logs=logs(directory)
    relevant=[x for x in all_logs if x['relative_path']=='offline-input/reopened.log']
    check('one reopened log available',len(relevant)==1)
    reopened_log=relevant[0] if len(relevant)==1 else None
    reproduced=bool(reopened_log and (any(x['count']>0 for x in reopened_log['objectdb_summaries']) or reopened_log['instances'] or reopened_log['unmatched_instance_lines']))
    row_integrity=bool(reopened_log and reopened_log['single_summary_count_matches_rows'] and reopened_log['instances'] and not reopened_log['utf8_replacement_present'] and not reopened_log['unmatched_instance_lines'] and not reopened_log['instance_id_duplicates'] and all(x['parse_status']=='PARSED' and x['instance_id_in_uint64_range'] for x in reopened_log['instances']))
    out.mkdir(parents=True,exist_ok=True)
    report={
        'scope':'Read-only offline extraction; checks measure evidence consistency, not product acceptance',
        'run_id':40083894472,'job_id':120842796227,'source_commit':SOURCE,'evidence_checks':checks,
        'evidence_checks_failed':[x['name'] for x in checks if not x['passed']],
        'read_errors':read_errors,'leak_reproduced':reproduced,'verbose_identity_rows_internally_complete':row_integrity,
        'diagnostic_result':'PENDING_MANUAL_ADMISSION_AND_FLOW_REVIEW',
        'manual_checks_pending':['Export source.json and official package/ZIP provenance','Complete HUD/action/progression/cleanup-context source predicates','Complete root release/push/dispatch chronology'],
        'offline_result_anchors':{key:result.get(key) for key in ('passed','error','initial_exit','reopened_exit','elapsed_seconds','cleanup_errors','incomplete_training_unchanged_after_reopened_exit','settings_restart_equal','settings_loaded_into_reopened_process')},
        'commands':commands,'argv_confounds':argv_confounds,'all_logs':all_logs,
        'allocation_stack_or_retaining_owner_established':False,'original40080238905_retained_failure':True,
    }
    (out/'ACTUAL_ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('diagnostic_result','leak_reproduced','verbose_identity_rows_internally_complete','evidence_checks_failed','offline_result_anchors')}))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--raw',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    review(args.raw,args.output)
