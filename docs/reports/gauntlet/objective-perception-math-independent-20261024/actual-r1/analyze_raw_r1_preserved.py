#!/usr/bin/env python3
"""Decode retained failed-attempt bytes; never invokes an acquisition or engine."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'scripts'))
import fov_math_reference as reference
from native_log import failed


def need(value,message):
    if not value:raise ValueError(message)


def bits(value):return struct.pack('<d',value).hex()
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]


def independent_shadow(case,single):
    cast=f32 if single else float
    actor=[cast(x) for x in case['actor_position']]
    enemy=[cast(x) for x in case['enemy_position']]
    delta=[cast(enemy[i]-actor[i]) for i in range(3)]
    squares=[cast(x*x) for x in delta]
    squared=cast(cast(squares[0]+squares[1])+squares[2])
    length=cast(math.sqrt(squared))
    toward=[cast(x/length) for x in delta] if length else [0.,0.,0.]
    facing=[cast(-math.sin(case['yaw'])),cast(0.),cast(-math.cos(case['yaw']))]
    products=[cast(facing[i]*toward[i]) for i in range(3)]
    dot=cast(cast(products[0]+products[1])+products[2])
    age=case['elapsed']-case['damaged_at']
    recent=age<1.2 and case['enemy_id']==case['attacker_id']
    geometric=dot>case['threshold'];range_reject=length>case['vision_range']
    stage='range' if range_reject else ('requires_visibility' if geometric or recent else 'fov')
    return dict(dot=dot,distance=length,facing=facing,toward=toward,delta=delta,
                geometric=geometric,recent=recent,stage=stage)


originals=HERE/'originals'
payload_raw=(originals/'project/cases.json').read_bytes()
program=(originals/'project/reference.gd').read_bytes()
payload=json.loads(payload_raw)
stdout=(originals/'stdout.log').read_bytes();stderr=(originals/'stderr.log').read_bytes()
producer=json.loads((originals/'receipt.json').read_text())
cases_sha=hashlib.sha256(payload_raw).hexdigest();program_sha=hashlib.sha256(program).hexdigest()
need(cases_sha=='d3e3cbc53b89cd0f872d333262524e43a84155c2b8ae0aaab06850e1337dcbae','case payload')
need(not stderr and not failed(stdout.decode()),'strict raw stream failure')
maintained=reference.parse_output(stdout,payload,cases_sha256=cases_sha,program_sha256=program_sha)


def unique(pairs):
    result={}
    for key,value in pairs:
        need(key not in result,'duplicate JSON key');result[key]=value
    return result


records=[];banner=0
for line in stdout.decode().splitlines():
    if line.startswith('FOV_MATH '):
        records.append(json.loads(line[len('FOV_MATH '):],object_pairs_hook=unique,
                                 parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))))
    elif line.startswith('Godot Engine v'):banner+=1
    else:need(not line.strip(),'unrecognized native line')
need(len(records)==590 and records[0]['kind']=='header' and records[-1]['kind']=='done','framing')
need(records[-1]['count']==588,'terminal count')
header=records[0];single=header['precision']['single']
case_rows=[];fields_checked=0;predicates_checked=0;single_storage_checked=0;signed_zero_losses=[]
groups=Counter();stages=Counter();clear_controls=0;diff64=[];diff32=[];exact32_dot=0;max64=0.;max32=0.
for case,row in zip(payload['cases'],records[1:-1]):
    need(row['id']==case['id'] and row['input_sha256']==case['input_sha256'],'case identity')
    canonical=json.dumps({k:v for k,v in case.items() if k!='input_sha256'},sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    need(hashlib.sha256(canonical).hexdigest()==case['input_sha256'],'independent input hash')
    decoded={}
    for key,value in row['values'].items():
        vector=type(value) is list
        nums=value if vector else [value]
        encodings=row['bits64'][key] if vector else [row['bits64'][key]]
        need(len(nums)==len(encodings),'bit count')
        values=[]
        for number,encoding in zip(nums,encodings):
            need(type(number) in (int,float) and math.isfinite(number),'finite typed output')
            actual=struct.unpack('<d',bytes.fromhex(encoding))[0]
            need(math.isfinite(actual) and actual==number,'binary/decimal consistency')
            if actual==0 and bits(float(number))!=encoding:
                signed_zero_losses.append(dict(id=case['id'],field=key,bits=encoding))
            if single and (vector or key in ('dot','distance')):
                need(f32(actual)==actual,'non-binary32 vector/primitive value');single_storage_checked+=1
            values.append(actual);fields_checked+=1
        decoded[key]=values if vector else values[0]
    for key in ('yaw','threshold','vision_range','elapsed','damaged_at'):
        need(row['bits64'][key]==bits(case[key]),'scalar input roundtrip')
    need(row['bits64']['age']==bits(case['elapsed']-case['damaged_at']),'age source operation')
    cast=f32 if single else float
    for key in ('actor_position','enemy_position'):
        need(row['bits64'][key]==[bits(cast(x)) for x in case[key]],'position construction')
    geo=decoded['dot']>decoded['threshold']
    specific=case['enemy_id']==case['attacker_id']
    recent=decoded['age']<1.2 and specific
    outside=decoded['distance']>decoded['vision_range']
    wanted=dict(geometric=geo,specific_attacker=specific,recent_attacker=recent,
                range_reject=outside,in_fov=geo or recent)
    wanted['stage']='range' if outside else ('requires_visibility' if geo or recent else 'fov')
    for key,value in wanted.items():
        need(type(row['predicates'][key]) is type(value) and row['predicates'][key]==value,'strict predicate');predicates_checked+=1
    shadow64=independent_shadow(case,False);shadow32=independent_shadow(case,True)
    if shadow64['geometric']!=geo or shadow64['stage']!=wanted['stage']:diff64.append(case['id'])
    if shadow32['geometric']!=geo or shadow32['stage']!=wanted['stage']:diff32.append(case['id'])
    max64=max(max64,abs(decoded['dot']-shadow64['dot']));max32=max(max32,abs(decoded['dot']-shadow32['dot']))
    if bits(decoded['dot'])==bits(shadow32['dot']):exact32_dot+=1
    analytical=case['group'] in ('axis','recent') or (case['group']=='range' and case['enemy_position']==[0,0,-38.])
    if analytical:
        # These controls have yaw0 and zero/axis-only finite displacements.
        delta=[b-a for a,b in zip(case['actor_position'],case['enemy_position'])]
        length=abs(next((x for x in delta if x!=0),0.))
        toward=[x/length for x in delta] if length else [0.,0.,0.]
        need(decoded['facing']==[0.,0.,-1.] and decoded['delta']==delta,'exact facing/delta')
        need(decoded['toward']==toward and decoded['distance']==length and decoded['dot']==-toward[2],'exact normalized/primitive')
        clear_controls+=1
    groups[case['group']]+=1;stages[wanted['stage']]+=1
    case_rows.append(dict(id=case['id'],group=case['group'],reported_dot=decoded['dot'],threshold=decoded['threshold'],
                          geometric=geo,stage=wanted['stage'],python64_dot=shadow64['dot'],nominal32_dot=shadow32['dot'],
                          qualification='UNQUALIFIED_FAILED_PROCESS_IDENTITY_ACQUISITION',
                          transfer='UNRESOLVED_FOR_UNMEASURED_INPUTS'))
need(producer['passed'] is False and producer['native_invocations']==1,'producer terminal failure')
need(producer['error']=='owned native root identity/session not observed','exact failed gate')
need(not producer['observed_processes'] and 'root_identity' not in producer and 'native_exit' not in producer,'identity/exit gap')
report=dict(scope='Raw schema and numerical consistency only; acquisition remains REJECTED, not native calibration',
            acquisition_accepted=False,certified_native_reference=False,ownership_accepted=False,cleanup_accepted=False,
            raw_schema_consistent=True,raw_strict_log_clean=True,raw_case_records=len(case_rows),record_count=len(records),banner_count=banner,
            engine_self_report=header['engine'],precision_self_report=header['precision'],groups=dict(groups),stages=dict(stages),
            decoded_scalars=fields_checked,strict_predicates_checked=predicates_checked,single_storage_values_checked=single_storage_checked,
            exact_analytical_controls=clear_controls,signed_zero_decimal_losses=len(signed_zero_losses),
            python64_gate_difference_count=len(diff64),python64_gate_difference_ids=diff64,
            nominal32_gate_difference_count=len(diff32),nominal32_gate_difference_ids=diff32,
            nominal32_exact_dot_bits=exact32_dot,observed_max_dot_residual_python64=max64,observed_max_dot_residual_nominal32=max32,
            residual_policy='DESCRIPTIVE_FAILED_ATTEMPT_ONLY; NOT A PORTABLE ERROR BOUND OR EPSILON',
            producer_elapsed=producer['elapsed_seconds'],producer_cleanup_report=producer['cleanup'],root_identity_observed=False,native_exit_recorded=False,
            cases=case_rows,signed_zero_examples=signed_zero_losses[:20])
(HERE/'RAW_SCHEMA_MATH_ANALYSIS.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('cases','signed_zero_examples','engine_self_report','precision_self_report')},indent=2))
