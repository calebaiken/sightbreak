"""Fixed-corpus and strict framing tools for the isolated native math reference.

Pure functions never start Godot. Model comparisons describe declared inputs;
no empirical residual becomes a tolerance for unmeasured gameplay histories.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import re
import struct

ENGINE = '4.7.2.stable.official.ed1daf0bf'
PREFIX = 'FOV_MATH '
MAX_CASES = 1024
GROUPS = {'captured', 'defuse', 'seeded', 'axis', 'vertical', 'angle', 'range', 'cutoff32', 'recent'}
SCALARS = ('yaw', 'threshold', 'vision_range', 'elapsed', 'damaged_at', 'age', 'distance', 'dot')
VECTORS = ('actor_position', 'enemy_position', 'facing', 'delta', 'toward')
INPUT_KEYS = {'id', 'group', 'actor_position', 'enemy_position', 'yaw', 'threshold', 'vision_range', 'elapsed', 'damaged_at', 'enemy_id', 'attacker_id', 'meta', 'input_sha256'}


def require(value, text):
    if not value:
        raise ValueError(text)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def bits64(value):
    return struct.pack('<d', value).hex()


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def new_case(identity, group, actor, enemy, yaw, *, elapsed=10., damaged_at=-100., enemy_id=2, attacker_id=0, threshold=-.15, meta=None):
    row = dict(id=identity, group=group, actor_position=list(actor), enemy_position=list(enemy), yaw=yaw,
               threshold=threshold, vision_range=38., elapsed=elapsed, damaged_at=damaged_at,
               enemy_id=enemy_id, attacker_id=attacker_id, meta=meta or {})
    row['input_sha256'] = sha(canonical(row))
    return row


def generate(root):
    raw = (Path(root) / 'game/tests/fixtures/bot_objective_timeout.jsonl').read_bytes()
    poses = {r['event_index']: r for r in map(json.loads, raw.decode().splitlines())}
    cases = []
    for ix in (120, 122, 127):
        for actor in poses[ix]['actors']:
            for enemy in poses[ix]['actors']:
                if enemy['team'] != actor['team']:
                    cases.append(new_case(f'captured/{ix}/{actor["id"]}/{enemy["id"]}', 'captured',
                                          actor['position'], enemy['position'], actor['yaw'], enemy_id=enemy['id'],
                                          elapsed=poses[ix]['elapsed'], meta=dict(event=ix, actor_id=actor['id'],
                                          actor_alive=actor['alive'], enemy_alive=enemy['alive'],
                                          scope='serialized captured geometry; not historical native bits')))
    pose = poses[127]
    actor = next(a for a in pose['actors'] if a['id'] == 6)
    for enemy in pose['actors']:
        if enemy['alive'] and enemy['team'] != 1 and enemy['id'] != 6:
            cases.append(new_case(f'defuse/6/{enemy["id"]}', 'defuse', [-15., 0., 10.], enemy['position'],
                                  actor['yaw'], enemy_id=enemy['id'], meta=dict(source_event=127, synthetic_team=1)))
    seed = 0x5342464F56
    rng = random.Random(seed)
    for ix in range(128):
        actor = [rng.uniform(-20, 20), rng.uniform(-2, 2), rng.uniform(-20, 20)]
        direction = [rng.uniform(-1, 1) for _ in range(3)]
        length = math.sqrt(sum(v*v for v in direction))
        distance = rng.uniform(.1, 37.9)
        enemy = [a + distance*d/length for a, d in zip(actor, direction)]
        cases.append(new_case(f'seeded/{ix:03}', 'seeded', actor, enemy, rng.uniform(-math.pi, math.pi), meta=dict(seed=seed)))
    for name, enemy in [('zero',[0,0,0]),('front',[0,0,-16]),('back',[0,0,16]),('left',[-16,0,0]),('right',[16,0,0])]:
        cases.append(new_case('axis/'+name, 'axis', [0,0,0], enemy, 0.))
    for height in (-64., -16., 16., 64.):
        for z in (-4., 4.):
            cases.append(new_case(f'vertical/{height}/{z}', 'vertical', [0,0,0], [0,height,z], 0.))
    for ix, yaw in enumerate((0., -0., math.pi/2, -math.pi/2, math.pi, -math.pi, 2*math.pi, -2*math.pi)):
        cases.append(new_case(f'angle/{ix}', 'angle', [0,0,0], [4,0,-8], yaw))
    center = struct.unpack('<I', struct.pack('<f', 38.))[0]
    for offset in (-1, 0, 1):
        distance = struct.unpack('<f', struct.pack('<I', center+offset))[0]
        cases.append(new_case(f'range/{center+offset:08x}', 'range', [0,0,0], [0,0,-distance], 0.))
    center = struct.unpack('<I', struct.pack('<f', -.15))[0]
    for offset in range(-128, 129):
        value = struct.unpack('<f', struct.pack('<I', center+offset))[0]
        cases.append(new_case(f'cutoff32/{center+offset:08x}', 'cutoff32', [0,0,0],
                              [math.sqrt(1-value*value),0,-value], 0.,
                              meta=dict(target_dot=value, float32_bits=f'{center+offset:08x}', offset=offset)))
    for threshold in (-.05, -.25):
        center = struct.unpack('<I', struct.pack('<f', threshold))[0]
        for offset in (-1, 0, 1):
            value = struct.unpack('<f', struct.pack('<I', center+offset))[0]
            cases.append(new_case(f'cutoff32/{threshold}/{center+offset:08x}', 'cutoff32', [0,0,0],
                                  [math.sqrt(1-value*value),0,-value], 0., threshold=threshold,
                                  meta=dict(target_dot=value, float32_bits=f'{center+offset:08x}')))
    pose = poses[122];actor = next(a for a in pose['actors'] if a['id']==6);enemy = next(a for a in pose['actors'] if a['id']==2)
    cases.append(new_case('captured/122/6/2/yaw-zero-synthetic', 'captured', actor['position'],enemy['position'],0.,
                          meta=dict(scope='same serialized positions; explicitly synthetic changed yaw')))
    for ix,(threshold,enemy) in enumerate([(1.,[0,0,-16]),(-1.,[0,0,16]),(0.,[16,0,0]),(-2.**-24,[16,0,0]),(2.**-24,[16,0,0])]):
        cases.append(new_case(f'axis/comparison/{ix}', 'axis', [0,0,0],enemy,0.,threshold=threshold,
                              meta=dict(scope='exact axis strict comparison control; not stock profile')))
    ages = [0., 1., math.nextafter(1.2, -math.inf), 1.2, math.nextafter(1.2, math.inf), 2., -1.]
    for ix, age in enumerate(ages):
        for specific in (False, True):
            cases.append(new_case(f'recent/{ix}/{int(specific)}', 'recent', [0,0,0], [0,0,16], 0.,
                                  elapsed=age, damaged_at=0., attacker_id=2 if specific else 3,
                                  meta=dict(age_bits64=bits64(age), specific=specific,
                                            scope='scalar predicate only; future damage not a valid-history claim')))
    result = dict(schema=1, engine=ENGINE, source_fixture_sha256=sha(raw), seed=seed, cases=cases)
    validate_cases(result)
    return result


def validate_cases(payload):
    require(type(payload) is dict and set(payload)=={'schema','engine','source_fixture_sha256','seed','cases'}, 'input schema')
    require(type(payload['schema']) is int and payload['schema']==1 and payload['engine']==ENGINE, 'input engine/schema')
    require(re.fullmatch('[0-9a-f]{64}',payload['source_fixture_sha256']) is not None and type(payload['seed']) is int, 'input provenance')
    cases=payload['cases'];require(type(cases) is list and 0<len(cases)<=MAX_CASES, 'input count')
    require(all(type(r) is dict and set(r)==INPUT_KEYS for r in cases), 'case schema')
    require(all(type(r['id']) is str for r in cases),'case id type')
    require(len({r['id'] for r in cases})==len(cases), 'duplicate input id')
    for row in cases:
        require(type(row) is dict and set(row)==INPUT_KEYS, 'case schema')
        require(type(row['id']) is str and re.fullmatch('[a-zA-Z0-9_./-]{1,100}',row['id']) is not None and row['group'] in GROUPS, 'case identity')
        for name in ('actor_position','enemy_position'):
            require(type(row[name]) is list and len(row[name])==3 and all(number(v) and abs(v)<=1e6 for v in row[name]), 'input vector')
        require(all(number(row[k]) for k in ('yaw','threshold','vision_range','elapsed','damaged_at')), 'input scalars')
        require(abs(row['yaw'])<=100 and -1<=row['threshold']<=1 and 0<row['vision_range']<=1000 and abs(row['elapsed'])<=1e6 and abs(row['damaged_at'])<=1e6, 'input scalar bounds')
        require(type(row['enemy_id']) is int and 1<=row['enemy_id']<=10 and type(row['attacker_id']) is int and 0<=row['attacker_id']<=10, 'input attacker ids')
        require(type(row['meta']) is dict and row['input_sha256']==sha(canonical({k:v for k,v in row.items() if k!='input_sha256'})), 'case hash')
    return cases


def model(row, single=False):
    cast=f32 if single else float
    actor=[cast(v) for v in row['actor_position']];enemy=[cast(v) for v in row['enemy_position']]
    delta=[cast(b-a) for a,b in zip(actor,enemy)]
    squares=[cast(v*v) for v in delta];length=cast(math.sqrt(cast(cast(squares[0]+squares[1])+squares[2])))
    toward=[cast(v/length) for v in delta] if length else [0.,0.,0.]
    facing=[cast(-math.sin(row['yaw'])),cast(0),cast(-math.cos(row['yaw']))]
    products=[cast(a*b) for a,b in zip(facing,toward)];dot=cast(cast(products[0]+products[1])+products[2])
    age=row['elapsed']-row['damaged_at'];recent=age<1.2 and row['enemy_id']==row['attacker_id']
    values=dict(actor_position=actor,enemy_position=enemy,yaw=row['yaw'],threshold=row['threshold'],vision_range=row['vision_range'],
                elapsed=row['elapsed'],damaged_at=row['damaged_at'],age=age,facing=facing,delta=delta,toward=toward,distance=length,dot=dot)
    predicates=dict(range_reject=length>row['vision_range'],geometric=dot>row['threshold'],specific_attacker=row['enemy_id']==row['attacker_id'],recent_attacker=recent,in_fov=dot>row['threshold'] or recent)
    predicates['stage']='range' if predicates['range_reject'] else ('requires_visibility' if predicates['in_fov'] else 'fov')
    return values,predicates


def bit_tree(values):
    return {k:[bits64(x) for x in v] if type(v) is list else bits64(v) for k,v in values.items()}


def parse_output(raw,payload,*,cases_sha256,program_sha256):
    validate_cases(payload)
    require(type(raw) is bytes,'output bytes')
    text=raw.decode('utf-8',errors='strict');records=[];banner=0
    for line in text.splitlines():
        if line.startswith(PREFIX):
            def unique(pairs):
                result={}
                for key,value in pairs:
                    require(key not in result,'duplicate output key');result[key]=value
                return result
            records.append(json.loads(line[len(PREFIX):],object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('nonfinite JSON'))))
        elif line=='Godot Engine v'+ENGINE+' - https://godotengine.org':banner+=1
        else:require(not line.strip(),'unexpected native output')
    require(banner<=1 and len(records)==len(payload['cases'])+2,'output framing/count')
    header,done=records[0],records[-1]
    require(type(header) is dict and set(header)=={'kind','schema','engine','cases_sha256','program_sha256','precision'},'header schema')
    require(header['kind']=='header' and type(header['schema']) is int and header['schema']==1,'header kind')
    engine=header['engine'];require(type(engine) is dict and [engine.get(k) for k in ('major','minor','patch')]==[4,7,2] and type(engine.get('hash')) is str and re.fullmatch('ed1daf0bf[0-9a-f]{0,31}',engine['hash']) is not None,'native engine')
    require(header['cases_sha256']==cases_sha256 and header['program_sha256']==program_sha256,'native payload identity')
    precision=header['precision'];require(set(precision)=={'single','double','scalar64','vector_component','packed32','packed64','scalar64_le','vector64_le','packed32_le','packed64_le'},'precision schema')
    require(type(precision['single']) is bool and type(precision['double']) is bool and precision['single']!=precision['double'],'precision feature')
    expected=dict(scalar64=16777217.,vector_component=16777216. if precision['single'] else 16777217.,packed32=16777216.,packed64=16777217.)
    for name,value in expected.items():
        require(type(precision[name]) in (float,int) and precision[name]==value,'precision value')
    require(precision['scalar64_le']==bits64(expected['scalar64']) and precision['vector64_le']==bits64(expected['vector_component']) and precision['packed32_le']==struct.pack('<f',expected['packed32']).hex() and precision['packed64_le']==bits64(expected['packed64']),'precision bits')
    require(type(done) is dict and set(done)=={'kind','count','cases_sha256'} and done['kind']=='done' and type(done['count']) is int and done['count']==len(payload['cases']) and done['cases_sha256']==cases_sha256,'done schema')
    comparisons=[]
    for expected,row in zip(payload['cases'],records[1:-1]):
        require(type(row) is dict and set(row)=={'kind','id','input_sha256','values','bits64','predicates'} and row['kind']=='case','output case schema')
        require(row['id']==expected['id'] and row['input_sha256']==expected['input_sha256'],'output case identity/order')
        values=row['values'];require(type(values) is dict and set(values)==set(SCALARS+VECTORS) and type(row['bits64']) is dict and set(row['bits64'])==set(values),'values schema')
        for name in SCALARS:require(number(values[name]),'finite native scalar')
        require(values['distance']>=0,'negative native distance')
        for name in VECTORS:require(type(values[name]) is list and len(values[name])==3 and all(number(v) for v in values[name]),'finite native vector')
        for name,value in values.items():
            pairs=zip(value,row['bits64'][name]) if type(value) is list else [(value,row['bits64'][name])]
            if type(value) is list:require(type(row['bits64'][name]) is list and len(row['bits64'][name])==3,'vector bits shape')
            for numeric,encoded in pairs:
                require(type(encoded) is str and re.fullmatch('[0-9a-f]{16}',encoded) is not None,'binary scalar')
                decoded=struct.unpack('<d',bytes.fromhex(encoded))[0];require(math.isfinite(decoded) and decoded==numeric,'binary/JSON mismatch')
        require(row['bits64']['age']==bits64(expected['elapsed']-expected['damaged_at']),'native age arithmetic')
        for name in ('yaw','threshold','vision_range','elapsed','damaged_at'):
            require(row['bits64'][name]==bits64(expected[name]),'input scalar roundtrip')
        cast=f32 if precision['single'] else float
        for name in ('actor_position','enemy_position'):
            require(row['bits64'][name]==[bits64(cast(v)) for v in expected[name]],'constructed position roundtrip')
        geometric=values['dot']>values['threshold'];recent=values['age']<1.2 and expected['enemy_id']==expected['attacker_id']
        want=dict(range_reject=values['distance']>values['vision_range'],geometric=geometric,specific_attacker=expected['enemy_id']==expected['attacker_id'],recent_attacker=recent,in_fov=geometric or recent)
        want['stage']='range' if want['range_reject'] else ('requires_visibility' if want['in_fov'] else 'fov')
        require(type(row['predicates']) is dict and row['predicates'].keys()==want.keys() and all(type(row['predicates'][k]) is type(v) and row['predicates'][k]==v for k,v in want.items()),'native strict predicate inconsistency')
        if expected['group'] in ('axis','recent') or (expected['group']=='range' and expected['enemy_position']==[0,0,-38.]):
            exact_values,exact_pred=model(expected)
            for key in ('facing','delta','toward','distance','dot'):
                require(values[key]==exact_values[key],'required exact analytical control: '+key)
            require(want==exact_pred,'required exact analytical strict predicate')
        double_values,double_pred=model(expected);single_values,single_pred=model(expected,True)
        same64=double_pred==want;same32=single_pred==want
        comparisons.append(dict(id=expected['id'],native_dot=values['dot'],python64_dot=double_values['dot'],nominal32_dot=single_values['dot'],python64_gate_agrees=same64,nominal32_gate_agrees=same32,
                                classification='AGREES_DECLARED_CASE_ONLY' if same64 and same32 else 'UNRESOLVED_MODEL_DIFFERENCE',
                                transfer='UNRESOLVED_FOR_UNMEASURED_INPUTS'))
    return dict(reference_capture_schema_valid=True,case_count=len(comparisons),precision=precision,comparisons=comparisons,
                broader_cutoff_parity='UNRESOLVED',visibility_gameplay_physical_acceptance=False)


# The schema1 corpus/parser above stay immutable controls. Native JSON decimal
# conversion did not preserve all of those input bits in actual550. Schema2
# therefore transports every operational primitive independently of presentation.
INPUT_CODEC = 'ieee754-binary64-little-endian-v1'
CANONICAL_CASES_SHA256 = 'd3e3cbc53b89cd0f872d333262524e43a84155c2b8ae0aaab06850e1337dcbae'
BINARY_CASES_NAME = 'cases-binary64-v2.json'
INPUT_SCALARS = ('yaw','threshold','vision_range','elapsed','damaged_at','enemy_id','attacker_id')
INPUT_VECTORS = ('actor_position','enemy_position')
TRANSPORT_KEYS = {'ordinal','input64_le','transport_sha256'}


def decode_binary64(encoded):
    require(type(encoded) is str and re.fullmatch('[0-9a-f]{16}',encoded) is not None,'exact binary64 hex')
    value=struct.unpack('<d',bytes.fromhex(encoded))[0]
    require(math.isfinite(value) and bits64(value)==encoded,'finite exact binary64')
    return value


def input_bits(row):
    result={}
    for name in INPUT_SCALARS+INPUT_VECTORS:
        values=row[name] if name in INPUT_VECTORS else [row[name]]
        require(type(values) is list and all(number(value) and float(value)==value for value in values),'finite representable input')
    for name in INPUT_VECTORS:
        require(type(row[name]) is list and len(row[name])==3,'input vector shape')
        result[name]=[bits64(value) for value in row[name]]
    for name in INPUT_SCALARS:result[name]=bits64(row[name])
    return result


def decode_inputs(encoded):
    require(type(encoded) is dict and set(encoded)==set(INPUT_SCALARS+INPUT_VECTORS),'binary input schema')
    result={}
    for name in INPUT_VECTORS:
        require(type(encoded[name]) is list and len(encoded[name])==3,'binary vector shape')
        result[name]=[decode_binary64(value) for value in encoded[name]]
    for name in INPUT_SCALARS:result[name]=decode_binary64(encoded[name])
    return result


def canonical_cases():
    path=Path(__file__).resolve().parents[1]/'tools/fov_math_reference/cases.json'
    raw=path.read_bytes();require(sha(raw)==CANONICAL_CASES_SHA256,'protected canonical corpus changed')
    payload=json.loads(raw);validate_cases(payload)
    return payload


def generate_binary_cases():
    original=canonical_cases();rows=[]
    for ordinal,case in enumerate(original['cases']):
        row=dict(case,ordinal=ordinal,input64_le=input_bits(case))
        row['transport_sha256']=sha(canonical(row));rows.append(row)
    payload=dict(original,schema=2,input_codec=INPUT_CODEC,canonical_cases_sha256=CANONICAL_CASES_SHA256,cases=rows)
    validate_binary_cases(payload)
    return payload


def validate_binary_cases(payload):
    original=canonical_cases()
    require(type(payload) is dict and set(payload)==set(original)|{'input_codec','canonical_cases_sha256'},'binary payload schema')
    require(type(payload['schema']) is int and payload['schema']==2 and payload['input_codec']==INPUT_CODEC,'binary payload version')
    require(payload['canonical_cases_sha256']==CANONICAL_CASES_SHA256,'canonical payload identity')
    for key in ('engine','source_fixture_sha256','seed'):
        require(type(payload[key]) is type(original[key]) and payload[key]==original[key],'canonical metadata')
    require(type(payload['cases']) is list and len(payload['cases'])==len(original['cases']),'canonical case count')
    for ordinal,(row,expected) in enumerate(zip(payload['cases'],original['cases'])):
        require(type(row) is dict and set(row)==INPUT_KEYS|TRANSPORT_KEYS,'binary case schema')
        require(type(row['ordinal']) is int and row['ordinal']==ordinal,'canonical case order')
        presentation={k:v for k,v in row.items() if k not in TRANSPORT_KEYS}
        # Source canonical values are checked here, NOT reconstructed by native
        # JSON parsing. This also binds IDs/meta/hash under coordinated changes.
        require(canonical(presentation)==canonical(expected),'canonical decimal presentation changed')
        decoded=decode_inputs(row['input64_le'])
        require(input_bits(decoded)==input_bits(expected),'canonical binary input changed')
        require(row['transport_sha256']==sha(canonical({k:v for k,v in row.items() if k!='transport_sha256'})),'transport identity')
    return payload['cases']


def parse_binary_output(raw,payload,*,cases_sha256,program_sha256):
    """Validate schema2 metadata, then apply the unchanged strict legacy gates."""
    validate_binary_cases(payload);require(type(raw) is bytes,'output bytes')
    rows=[];banner=0
    def unique(pairs):
        result={}
        for key,value in pairs:
            require(key not in result,'duplicate output key');result[key]=value
        return result
    for line in raw.decode('utf-8',errors='strict').splitlines():
        if line.startswith(PREFIX):
            rows.append(json.loads(line[len(PREFIX):],object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON'))))
        elif line=='Godot Engine v'+ENGINE+' - https://godotengine.org':banner+=1
        else:require(not line.strip(),'unexpected native output')
    require(banner<=1 and len(rows)==len(payload['cases'])+2,'output framing/count')
    header=rows[0]
    require(type(header) is dict and set(header)=={'kind','schema','engine','cases_sha256','program_sha256','precision','input_codec','canonical_cases_sha256'},'binary header schema')
    require(type(header['schema']) is int and header['schema']==2 and header['input_codec']==INPUT_CODEC and header['canonical_cases_sha256']==CANONICAL_CASES_SHA256,'binary header identity')
    rows[0]={k:v for k,v in header.items() if k not in ('input_codec','canonical_cases_sha256')};rows[0]['schema']=1
    for expected,row in zip(payload['cases'],rows[1:-1]):
        require(type(row) is dict and set(row)=={'kind','id','input_sha256','values','bits64','predicates','ordinal','transport_sha256','decoded_input64_le'},'binary output case schema')
        require(type(row['ordinal']) is int and row['ordinal']==expected['ordinal'] and row['transport_sha256']==expected['transport_sha256'],'binary output order/transport')
        decoded=decode_inputs(row['decoded_input64_le'])
        require(input_bits(decoded)==expected['input64_le'],'native decoded input roundtrip')
        for key in ('ordinal','transport_sha256','decoded_input64_le'):del row[key]
    projected=b'\n'.join(PREFIX.encode()+canonical(row) for row in rows)+b'\n'
    result=parse_output(projected,canonical_cases(),cases_sha256=cases_sha256,program_sha256=program_sha256)
    result.update(input_codec=INPUT_CODEC,input_transport_schema=2,canonical_cases_sha256=CANONICAL_CASES_SHA256,
                  decoded_input_bit_roundtrip_strict=True)
    return result
