"""Independent codec controls. No native/process/proc tests or historical Git."""
import argparse
import copy
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SOURCE = DATA = None
reference = declared = PAYLOAD = CANONICAL = None
OBSERVATIONS = {}
SCALARS = ('yaw','threshold','vision_range','elapsed','damaged_at','enemy_id','attacker_id')
VECTORS = ('actor_position','enemy_position')


def encode64(value):
    """IEEE encoder from exact rational arithmetic, independent of struct."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('finite oracle only')
    sign = int(math.copysign(1., value) < 0.)
    numerator, denominator = abs(value).as_integer_ratio()
    if numerator == 0:
        raw = sign << 63
    else:
        exponent = numerator.bit_length()-denominator.bit_length()
        if exponent < -1022:
            fraction = (numerator << 1074)//denominator
            raw = (sign << 63)|fraction
        else:
            shift = 52-exponent
            significand = ((numerator << shift)//denominator if shift >= 0
                           else numerator//(denominator << -shift))
            raw = (sign << 63)|((exponent+1023) << 52)|(significand-(1 << 52))
    return raw.to_bytes(8,'little').hex()


def decode64(wire):
    raw = int.from_bytes(bytes.fromhex(wire),'little')
    sign, exponent, fraction = raw >> 63, (raw >> 52)&2047, raw&((1 << 52)-1)
    if exponent == 2047:
        raise ValueError('nonfinite')
    result = (math.ldexp(float((1 << 52)+fraction),exponent-1023-52)
              if exponent else math.ldexp(float(fraction),-1074))
    return -result if sign else result


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def rehash(row):
    row['transport_sha256'] = sha(canonical({k:v for k,v in row.items() if k!='transport_sha256'}))


def raw_records(rows):
    return b'\n'.join(b'FOV_MATH '+canonical(r) for r in rows)+b'\n'


class IndependentCodecControls(unittest.TestCase):
    def parse(self, rows):
        return reference.parse_binary_output(raw_records(rows),PAYLOAD,
                    cases_sha256=sha((SOURCE/'tools/fov_math_reference/cases-binary64-v2.json').read_bytes()),
                    program_sha256=declared.PROGRAM_SHA)

    def test_all7644_slots_match_independent_rational_ieee_oracle(self):
        count=0
        self.assertEqual(len(PAYLOAD['cases']),588)
        for ordinal,(wire,original) in enumerate(zip(PAYLOAD['cases'],CANONICAL['cases'])):
            self.assertEqual((wire['ordinal'],wire['id'],wire['input_sha256']),
                             (ordinal,original['id'],original['input_sha256']))
            for name in SCALARS+VECTORS:
                values = original[name] if name in VECTORS else [original[name]]
                bits = wire['input64_le'][name] if name in VECTORS else [wire['input64_le'][name]]
                for value, encoded in zip(values,bits):
                    self.assertEqual(encode64(value),encoded)
                    self.assertEqual(encode64(decode64(encoded)),encoded)
                    self.assertEqual(reference.bits64(reference.decode_binary64(encoded)),encoded)
                    count+=1
        self.assertEqual(count,7644)
        values=[0.,-0.,math.ulp(0.),-math.ulp(0.),float.fromhex('0x1.fffffffffffffp+1023')]
        for exponent in (-1022,-53,-1,0,1,53,1023):
            x=math.ldexp(1.,exponent)
            values.extend([x,-x,math.nextafter(x,0.),math.nextafter(x,math.inf)])
        for value in values:
            self.assertEqual(reference.bits64(value),encode64(value))
            self.assertEqual(encode64(reference.decode_binary64(encode64(value))),encode64(value))
        OBSERVATIONS['independent_ieee_slots']=count

    def test_each_of13_changed_operands_rejects_even_coordinated_local_rehash(self):
        reference.validate_binary_cases(PAYLOAD)
        ordinal=next(i for i,c in enumerate(PAYLOAD['cases']) if c['id']=='seeded/022')
        slots=[(name,None) for name in SCALARS]+[(name,k) for name in VECTORS for k in range(3)]
        for name,k in slots:
            for coordinated in (False,True):
                bad=copy.deepcopy(PAYLOAD);row=bad['cases'][ordinal]
                old=row['input64_le'][name] if k is None else row['input64_le'][name][k]
                altered=(int.from_bytes(bytes.fromhex(old),'little')^1).to_bytes(8,'little').hex()
                self.assertNotEqual(old,altered)
                if k is None:
                    row['input64_le'][name]=altered
                    if coordinated:row[name]=decode64(altered)
                else:
                    row['input64_le'][name][k]=altered
                    if coordinated:row[name][k]=decode64(altered)
                if coordinated:
                    row['input_sha256']=sha(canonical({key:value for key,value in row.items()
                        if key not in ('ordinal','input64_le','transport_sha256','input_sha256')}))
                rehash(row)
                with self.subTest(name=name,component=k,coordinated=coordinated),self.assertRaises(ValueError):
                    reference.validate_binary_cases(bad)
        OBSERVATIONS['slot_mutations']=26

    def test_echo_and_numeric_operands_are_independently_bound_including_signed_zero(self):
        baseline=declared.declared_binary_records()
        self.assertTrue(self.parse(baseline)['decoded_input_bit_roundtrip_strict'])
        targets=[('seeded/022','yaw',None),('seeded/022','actor_position',0),
                 ('axis/comparison/3','threshold',None),('recent/2/1','elapsed',None),
                 ('angle/1','yaw',None)]
        for identity,name,k in targets:
            for echo in (False,True):
                rows=copy.deepcopy(baseline);row=next(c for c in rows if c.get('id')==identity)
                old=row['decoded_input64_le'][name] if k is None else row['decoded_input64_le'][name][k]
                # ±zero and a position's real_t32 projection are separate cases.
                raw=int.from_bytes(bytes.fromhex(old),'little')
                altered=(raw^(1 << 63) if identity=='angle/1' else raw^1).to_bytes(8,'little').hex()
                self.assertNotEqual(old,altered)
                if echo:
                    if k is None:row['decoded_input64_le'][name]=altered
                    else:row['decoded_input64_le'][name][k]=altered
                elif k is None:
                    row['values'][name]=decode64(altered);row['bits64'][name]=altered
                else:
                    # Change the constructed Vector3 result by a full f32 ULP,
                    # since adjacent64 source inputs can quantize identically.
                    original=row['values'][name][k]
                    changed=original+max(abs(original)*2.**-20,2.**-20)
                    row['values'][name][k]=changed;row['bits64'][name][k]=encode64(changed)
                with self.subTest(id=identity,field=name,echo=echo),self.assertRaises(ValueError):self.parse(rows)
        self.assertTrue(self.parse(baseline)['reference_capture_schema_valid'])
        OBSERVATIONS['echo_or_numeric_mutations']=10

    def test_schema_types_mapping_order_duplicate_and_hash_binding_reject(self):
        self.assertEqual(len(reference.validate_binary_cases(PAYLOAD)),588)
        actions=[lambda p:p.update(seed=float(p['seed'])),lambda p:p['cases'][0].update(enemy_id=True),
                 lambda p:p['cases'][0].update(enemy_id=float(p['cases'][0]['enemy_id'])),
                 lambda p:p['cases'][0].update(ordinal=0.),lambda p:p['cases'][0].update(id=p['cases'][1]['id']),
                 lambda p:p['cases'][0]['input64_le'].update(threshold=bytes.fromhex(p['cases'][0]['input64_le']['threshold'])[::-1].hex()),
                 lambda p:p['cases'][0]['input64_le'].update(actor_position=p['cases'][0]['input64_le']['enemy_position']),
                 lambda p:p['cases'].append(copy.deepcopy(p['cases'][-1])),
                 lambda p:p['cases'].__setitem__(slice(0,2),list(reversed(p['cases'][:2])))]
        for action in actions:
            bad=copy.deepcopy(PAYLOAD);action(bad)
            self.assertNotEqual(canonical(bad),canonical(PAYLOAD))
            with self.assertRaises(ValueError):reference.validate_binary_cases(bad)
        rows=declared.declared_binary_records()
        changes=[lambda r:r[0].update(schema=2.),lambda r:r[1].update(ordinal=False),
                 lambda r:r[-1].update(count=588.),lambda r:r[0].update(cases_sha256=reference.CANONICAL_CASES_SHA256),
                 lambda r:r[0].update(program_sha256='f'*64),lambda r:r[1]['decoded_input64_le'].update(attacker_id=encode64(.5))]
        for change in changes:
            bad=copy.deepcopy(rows);change(bad)
            with self.assertRaises(ValueError):self.parse(bad)
        duplicate=raw_records(rows).replace(b'"ordinal":0',b'"ordinal":0,"ordinal":0',1)
        self.assertNotEqual(duplicate,raw_records(rows))
        with self.assertRaises(ValueError):reference.parse_binary_output(duplicate,PAYLOAD,cases_sha256='f'*64,program_sha256=declared.PROGRAM_SHA)
        OBSERVATIONS['schema_mapping_hash_mutations']=16

    def test_actual18_reconstruct_directly_and_original_failed_raw_stays_rejected(self):
        original=(DATA.parent/'actual-r1/originals/stdout.log').read_bytes()
        self.assertEqual(sha(original),'a973a0a9b95a04644e8b3f0b6fb69d49cc7f9e727a915341a9bd27e1ed0b1e75')
        records=[json.loads(line[len('FOV_MATH '):]) for line in original.decode().splitlines() if line.startswith('FOV_MATH ')]
        byid={r['id']:r for r in records if r.get('kind')=='case'}
        mismatches=[]
        for case in CANONICAL['cases']:
            row=byid[case['id']]
            for name in ('yaw','threshold','vision_range','elapsed','damaged_at'):
                wanted=encode64(case[name]);got=row['bits64'][name]
                if wanted!=got:mismatches.append((case['id'],name,wanted,got))
        fixture=json.loads((SOURCE/'scripts/fixtures/fov_actual_input_roundtrip_550.json').read_text())
        reported=[(r['id'],r['field'],r['expected_le'],r['reported_le']) for r in fixture['scalar_mismatches']]
        self.assertEqual(mismatches,reported);self.assertEqual(len(mismatches),18)
        with self.assertRaisesRegex(ValueError,'input scalar roundtrip'):
            reference.parse_output(original,CANONICAL,cases_sha256=reference.CANONICAL_CASES_SHA256,
                program_sha256='d0d42198ca6d70ece17224c8e5b28eb2ae1b27a568ca2b158fcfb72f37dfd9e5')
        with self.assertRaisesRegex(ValueError,'binary header schema'):
            reference.parse_binary_output(original,PAYLOAD,cases_sha256=sha((SOURCE/'tools/fov_math_reference/cases-binary64-v2.json').read_bytes()),program_sha256=declared.PROGRAM_SHA)
        OBSERVATIONS['actual_mismatches']=[dict(id=i,field=f,expected=e,reported=g) for i,f,e,g in mismatches]
        OBSERVATIONS['actual_R1_status']='FAILED; not promoted or retried'

    def test_protected_bytes_against_preserved_base_not_generated_hash_expectations(self):
        base=DATA/'frozen-control-source'
        model=(SOURCE/'scripts/fov_math_reference.py').read_bytes();oldmodel=(base/'fov_math_reference.py').read_bytes()
        self.assertEqual(model[:len(oldmodel)],oldmodel);self.assertEqual(len(oldmodel),16618)
        acquisition=(SOURCE/'scripts/acquire_fov_math_reference.py').read_bytes();oldacquisition=(base/'acquire_fov_math_reference.py').read_bytes()
        for start,end in [(b'class LinuxKernel:',b'def acquire('),(b'    finally:\n        if tree is not None:',b'\n\ndef main():')]:
            self.assertEqual(acquisition[acquisition.index(start):acquisition.index(end)],oldacquisition[oldacquisition.index(start):oldacquisition.index(end)])
        tests=(SOURCE/'scripts/test_fov_math_reference.py').read_bytes();a=tests.index(b'def declared_binary_records():');b=tests.index(b'class CorpusAndSchemaControls',a)
        erased=(tests[:a]+tests[b:]).replace(b'def setUpClass(cls):cls.raw=encoded(declared_binary_records())',b'def setUpClass(cls):cls.raw=encoded(declared_records())')
        self.assertEqual(erased,(base/'test_fov_math_reference.py').read_bytes())
        native=(SOURCE/'tools/fov_math_reference/reference.gd').read_bytes();oldnative=(base/'reference.gd').read_bytes()
        a,b=b'\t\tvar age:',b'\t\tvar values := {'
        self.assertEqual(native[native.index(a):native.index(b)].replace(b'exact["enemy_id"] == exact["attacker_id"]',b'entry["enemy_id"] == entry["attacker_id"]'),oldnative[oldnative.index(a):oldnative.index(b)])
        end=b'\t\temit({"kind": "case"'
        self.assertEqual(native[native.index(b):native.index(end)],oldnative[oldnative.index(b):oldnative.index(end)])
        OBSERVATIONS['protected_base_bytes_exact']=True

    def test_native_operands_and_echo_source_from_exact_decode_without_decimal_recovery(self):
        native=(SOURCE/'tools/fov_math_reference/reference.gd').read_text()
        kernel=native[native.index('\t\tvar actor :='):native.index('\t\tvar values := {')]
        for name in ('yaw','threshold','vision_range','elapsed','damaged_at'):
            self.assertIn('var '+name+': float = exact["'+name+'"]',kernel)
        for name in VECTORS:self.assertIn('vector_from(exact["'+name+'"])',kernel)
        self.assertNotIn('entry[',kernel)
        self.assertIn('"decoded_input64_le": input_bits(exact)',native)
        echo=native[native.index('func input_bits('):native.index('func emit(')]
        self.assertIn('bits64(decoded[name])',echo);self.assertIn('bits64(decoded[name][0])',echo)
        decoder=native[native.index('func decode_binary64('):native.index('func decode_inputs(')]
        self.assertLess(decoder.index('valid_hex(value, 16)'),decoder.index('value.hex_decode()'))
        self.assertLess(decoder.index('bytes.size() != 8'),decoder.index('bytes.decode_double(0)'))
        self.assertIn('not is_finite(decoded) or bits64(decoded) != value',decoder)
        self.assertNotIn('.to_float(',native);self.assertNotIn('str_to_float',native)
        OBSERVATIONS['native_API_execution']='UNMEASURED; static dataflow only'


def main():
    global SOURCE, DATA, reference, declared, PAYLOAD, CANONICAL
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();SOURCE=args.source.resolve();DATA=args.data.resolve()
    args.output.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(SOURCE/'scripts'))
    reference=importlib.import_module('fov_math_reference');declared=importlib.import_module('test_fov_math_reference')
    PAYLOAD=json.loads((SOURCE/'tools/fov_math_reference/cases-binary64-v2.json').read_text())
    CANONICAL=json.loads((SOURCE/'tools/fov_math_reference/cases.json').read_text())
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IndependentCodecControls)
    with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('real native library forbidden')):
        result=unittest.TextTestRunner(verbosity=2).run(suite)
    summary=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
                 observations=OBSERVATIONS,source=str(SOURCE),native_invocations=0)
    (args.output/'INDEPENDENT.json').write_text(json.dumps(summary,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
