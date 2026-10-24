"""Exact binary transport/schema controls only; no native/proc/helper execution."""
import ast
import copy
import json
import math
from pathlib import Path
import random
import struct
import unittest
from unittest.mock import patch

import fov_math_reference as r
from test_fov_math_reference import declared_binary_records,declared_records,encoded,CASES_SHA,PROGRAM_SHA

ROOT=Path(__file__).resolve().parents[1]
WIRE=ROOT/'tools/fov_math_reference'/r.BINARY_CASES_NAME
PAYLOAD=json.loads(WIRE.read_text())
ACTUAL=json.loads((ROOT/'scripts/fixtures/fov_actual_input_roundtrip_550.json').read_text())


def ancestry_baseline_segments():
    value=json.loads((ROOT/'scripts/fixtures/fov_owned_ancestry_baseline_segments.json').read_text())
    if set(value)!={'schema','source','owned_tree','fake_kernel'} or type(value['schema']) is not int or value['schema']!=1 or value['source']!='329d3ff56e686fccdefa04151667ecb7841c3d64':
        raise ValueError('unexpected ancestry baseline identity')
    for key in ('owned_tree','fake_kernel'):
        segment=value[key]
        if type(segment) is not dict or set(segment)!={'text','sha256'} or type(segment['text']) is not str or r.sha(segment['text'].encode())!=segment['sha256']:
            raise ValueError('changed ancestry baseline segment')
    return value


def erase_ancestry_class(source,name,donor):
    """Replace exactly one AST class span; preserve every adjacent source byte."""
    if type(source) is not bytes or type(donor) is not bytes or type(name) is not str:
        raise ValueError('typed ancestry source/class required')
    def span(raw,*,donating=False):
        module=ast.parse(raw)
        matches=[node for node in module.body if isinstance(node,ast.ClassDef) and node.name==name]
        if len(matches)!=1 or (donating and (len(module.body)!=1 or matches[0].decorator_list)):
            raise ValueError('one top-level '+name+' class required')
        node=matches[0];lines=raw.splitlines(keepends=True)
        bounds=(node.lineno,node.end_lineno,node.col_offset,node.end_col_offset)
        if any(type(value) is not int for value in bounds) or not (1<=node.lineno<=node.end_lineno<=len(lines)):
            raise ValueError('invalid ancestry class bounds')
        if not (0<=node.col_offset<=len(lines[node.lineno-1].rstrip(b'\r\n')) and 0<=node.end_col_offset<=len(lines[node.end_lineno-1].rstrip(b'\r\n'))):
            raise ValueError('invalid ancestry class bounds')
        start=sum(map(len,lines[:node.lineno-1]))+node.col_offset
        end=sum(map(len,lines[:node.end_lineno-1]))+node.end_col_offset
        if not (0<=start<end<=len(raw)) or not raw[start:].startswith(b'class ') or raw[end-1] in b' \t\r\n':
            raise ValueError('invalid ancestry class bounds')
        return start,end
    start,end=span(source);first,last=span(donor,donating=True)
    return source[:start]+donor[first:last]+source[end:]


def timing_binding_baseline():
    value=json.loads((ROOT/'scripts/fixtures/fov_source_binding_timing_baseline.json').read_text())
    required={'schema','source','owner_class','method','text','sha256'}
    if (type(value) is not dict or set(value)!=required or type(value['schema']) is not int or value['schema']!=1
            or value['source']!='8cc38cdcd7dfff37056782149e513c08037e4e77' or value['owner_class']!='SupervisorControls'
            or value['method']!='test_source_git_children_receive_only_remaining_whole_deadline'
            or type(value['text']) is not str or value['sha256']!='8c33308f610f09a3710106eaf0392fdad9fa9918c00d573f8796d305167e1e31'
            or r.sha(value['text'].encode())!=value['sha256']):
        raise ValueError('invalid exact timing constructor donor')
    return value


def erase_timing_constructor(source):
    """Normalize ONLY the independently adjudicated timing construction."""
    if type(source) is not bytes:raise ValueError('timing source bytes required')
    baseline=timing_binding_baseline();module=ast.parse(source)
    classes=[n for n in module.body if isinstance(n,ast.ClassDef) and n.name==baseline['owner_class']]
    methods=[n for n in ast.walk(module) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==baseline['method']]
    if len(classes)!=1 or len(methods)!=1 or methods[0] not in classes[0].body:raise ValueError('one exact timing method required')
    node=methods[0]
    if not isinstance(node,ast.FunctionDef) or node.decorator_list or ast.dump(node.args)!=ast.dump(ast.parse('def f(self): pass').body[0].args):
        raise ValueError('undecorated timing method signature required')
    donor=baseline['text'].encode();original=ast.parse(b'class Holder:\n'+donor).body[0].body[0]
    def calls(root,owner,name=None):
        return [n for n in ast.walk(root) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                and isinstance(n.func.value,ast.Name) and n.func.value.id==owner and (n.func.attr==name if name else n.func.attr.startswith('assert'))]
    def dumps(nodes):return [ast.dump(n,include_attributes=False) for n in nodes]
    if dumps(calls(node,'self'))!=dumps(calls(original,'self')):raise ValueError('timing assertions changed')
    if dumps(calls(node,'acquisition','source_binding'))!=dumps(calls(original,'acquisition','source_binding')):
        raise ValueError('timing binding deadline/call changed')
    clocks=[n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='FakeClock']
    if len(clocks)!=1 or clocks[0].args or clocks[0].keywords:raise ValueError('timing clock construction changed')
    sleeps=calls(node,'clock','sleep')
    if len(sleeps)!=1 or dumps(sleeps)!=dumps([ast.parse('clock.sleep(.1)').body[0].value]):raise ValueError('timing query cost changed')
    assignments=[n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='clock' and t.attr=='now' for t in n.targets)]
    if len(assignments)!=1 or ast.dump(assignments[0],include_attributes=False)!=ast.dump(ast.parse('clock.now=101.').body[0],include_attributes=False):
        raise ValueError('timing late boundary changed')
    def no_early_return(items):
        for item in items:
            if isinstance(item,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)):continue
            if isinstance(item,(ast.Return,ast.Yield,ast.YieldFrom)):raise ValueError('timing constructor skips assertions')
            no_early_return(ast.iter_child_nodes(item))
    no_early_return(node.body)
    lines=source.splitlines(keepends=True)
    if node.col_offset!=4 or not (1<=node.lineno<=node.end_lineno<=len(lines)):raise ValueError('timing method bounds')
    if lines[node.end_lineno-1][node.end_col_offset:].strip():raise ValueError('timing trailing outside bytes')
    start=sum(map(len,lines[:node.lineno-1]));end=sum(map(len,lines[:node.end_lineno]))
    return source[:start]+donor+source[end:]


def rehash(row):row['transport_sha256']=r.sha(r.canonical({k:v for k,v in row.items() if k!='transport_sha256'}))


class CodecControls(unittest.TestCase):
    def test_all588_canonical_values_ids_order_hashes_and13_primitives_exact(self):
        self.assertEqual(r.generate_binary_cases(),PAYLOAD);self.assertEqual(len(r.validate_binary_cases(PAYLOAD)),588)
        original=r.canonical_cases()
        self.assertEqual(r.sha((ROOT/'tools/fov_math_reference/cases.json').read_bytes()),r.CANONICAL_CASES_SHA256)
        for ordinal,(row,case) in enumerate(zip(PAYLOAD['cases'],original['cases'])):
            self.assertEqual(row['ordinal'],ordinal);self.assertEqual(row['id'],case['id']);self.assertEqual(row['input_sha256'],case['input_sha256'])
            self.assertEqual(r.input_bits(r.decode_inputs(row['input64_le'])),r.input_bits(case))
            self.assertEqual(sum(len(v) if isinstance(v,list) else 1 for v in row['input64_le'].values()),13)

    def test_generated_finite_bit_patterns_signed_zero_subnormals_binades_and_neighbors(self):
        values=[0.,-0.,math.ulp(0.),-math.ulp(0.),float.fromhex('0x1.fffffffffffffp+1023')]
        for exponent in (-1074,-1022,-100,-1,0,1,53,100,1023):
            value=math.ldexp(1.,exponent)
            values.extend([value,-value,math.nextafter(value,0.),math.nextafter(value,math.inf),math.nextafter(-value,-math.inf)])
        rng=random.Random(0x4249543634)
        for _ in range(2048):
            value=struct.unpack('<d',rng.getrandbits(64).to_bytes(8,'little'))[0]
            if math.isfinite(value):values.append(value)
        for value in values:
            if not math.isfinite(value):continue
            wire=r.bits64(value);self.assertEqual(r.bits64(r.decode_binary64(wire)),wire)
        self.assertNotEqual(r.bits64(r.decode_binary64(r.bits64(0.))),r.bits64(r.decode_binary64(r.bits64(-0.))))

    def test_invalid_hex_type_size_case_and_nonfinite_reject_before_decode(self):
        bad=[None,False,0,[],{},'', '0'*15,'0'*17,'G'*16,'000000000000F03F', '１２３４５６７８９０１２３４５６７']
        bad += [r.bits64(value) for value in (math.nan,math.inf,-math.inf)]
        for value in bad:
            with self.subTest(value=value),self.assertRaises(ValueError):r.decode_binary64(value)

    def test_numeric_decimals_are_presentation_not_authority_and_all18_bad_bits_reject(self):
        self.assertEqual(len(ACTUAL['scalar_mismatches']),18)
        mapping={row['id']:row for row in PAYLOAD['cases']}
        for old in ACTUAL['scalar_mismatches']:
            row=mapping[old['id']];name=old['field'];expected=old['expected_le'];reported=old['reported_le']
            self.assertEqual(r.bits64(old['expected']),expected);self.assertEqual(r.bits64(old['reported']),reported)
            self.assertNotEqual(expected,reported);self.assertEqual(row['input64_le'][name],expected)
            self.assertEqual(r.bits64(r.decode_inputs(row['input64_le'])[name]),expected)
            bad=copy.deepcopy(PAYLOAD);bad['cases'][row['ordinal']]['input64_le'][name]=reported;rehash(bad['cases'][row['ordinal']])
            with self.subTest(id=old['id']),self.assertRaisesRegex(ValueError,'canonical binary'):r.validate_binary_cases(bad)

    def test_coordinated_decimal_binary_local_hash_corruptions_cannot_change_canonical_case(self):
        for old in ACTUAL['scalar_mismatches']:
            bad=copy.deepcopy(PAYLOAD);row=next(x for x in bad['cases'] if x['id']==old['id']);name=old['field']
            row[name]=old['reported'];row['input64_le'][name]=old['reported_le']
            presentation={k:v for k,v in row.items() if k not in r.TRANSPORT_KEYS and k!='input_sha256'}
            row['input_sha256']=r.sha(r.canonical(presentation));rehash(row)
            with self.subTest(id=old['id']),self.assertRaisesRegex(ValueError,'canonical decimal'):r.validate_binary_cases(bad)

    def test_payload_schema_order_binary_shape_endian_and_canonical_identity_mutations_reject(self):
        changes=[lambda p:p.update(schema=1),lambda p:p.update(schema=True),lambda p:p.update(input_codec='decimal'),
                 lambda p:p.update(canonical_cases_sha256='0'*64),lambda p:p['cases'].reverse(),lambda p:p['cases'].pop(),
                 lambda p:p['cases'][0].update(ordinal=True),lambda p:p['cases'][0].update(extra=1),
                 lambda p:p['cases'][0]['input64_le'].update(extra='0'*16),lambda p:p['cases'][0]['input64_le'].update(actor_position=['0'*16]),
                 lambda p:p['cases'][0]['input64_le'].update(threshold=r.bits64(p['cases'][0]['threshold'])[::-1]),
                 lambda p:p['cases'][0].update(transport_sha256='0'*64)]
        for change in changes:
            data=copy.deepcopy(PAYLOAD);change(data)
            with self.subTest(change=change),self.assertRaises(ValueError):r.validate_binary_cases(data)
        corrupted=(ROOT/'tools/fov_math_reference/cases.json').read_bytes().replace(b'"schema": 1',b'"schema": 2')
        with patch.object(Path,'read_bytes',return_value=corrupted),self.assertRaisesRegex(ValueError,'protected canonical'):r.canonical_cases()

    def test_every_numeric_input_including_positions_and_ids_rejects_coordinated_change(self):
        for field in r.INPUT_SCALARS+r.INPUT_VECTORS:
            bad=copy.deepcopy(PAYLOAD);row=bad['cases'][0]
            if field in r.INPUT_VECTORS:row[field][0]=math.nextafter(float(row[field][0]),math.inf)
            else:row[field]=float(row[field])+1.
            row['input64_le']=r.input_bits(row);row['input_sha256']='0'*64;rehash(row)
            with self.subTest(field=field),self.assertRaises(ValueError):r.validate_binary_cases(bad)


class OutputControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rows=declared_binary_records()
    def parse(self,rows):return r.parse_binary_output(encoded(rows),PAYLOAD,cases_sha256=r.sha(WIRE.read_bytes()),program_sha256=PROGRAM_SHA)

    def test_declared_output_passes_only_exact_inputs_and_retains_unresolved_scope(self):
        result=self.parse(self.rows)
        self.assertTrue(result['decoded_input_bit_roundtrip_strict']);self.assertEqual(result['input_transport_schema'],2)
        self.assertEqual(result['broader_cutoff_parity'],'UNRESOLVED');self.assertFalse(result['visibility_gameplay_physical_acceptance'])
        self.assertTrue(all(x['transfer']=='UNRESOLVED_FOR_UNMEASURED_INPUTS' for x in result['comparisons']))

    def test_legacy_output_is_not_silently_promoted_to_binary_output(self):
        with self.assertRaises(ValueError):self.parse(declared_records())
        # Original legacy parser still rejects actual observed seeded022 input
        # drift even when the output's numeric/bit values are consistent.
        rows=declared_records();old=ACTUAL['scalar_mismatches'][0]
        row=next(x for x in rows if x.get('id')==old['id']);row['values'][old['field']]=old['reported'];row['bits64'][old['field']]=old['reported_le']
        with self.assertRaisesRegex(ValueError,'input scalar roundtrip'):r.parse_output(encoded(rows),r.canonical_cases(),cases_sha256=CASES_SHA,program_sha256=PROGRAM_SHA)

    def test_all18_wrong_echo_bits_or_coordinated_value_bits_still_reject(self):
        for old in ACTUAL['scalar_mismatches']:
            for echo in (False,True):
                rows=copy.deepcopy(self.rows);row=next(x for x in rows if x.get('id')==old['id'])
                if echo:row['decoded_input64_le'][old['field']]=old['reported_le']
                else:row['values'][old['field']]=old['reported'];row['bits64'][old['field']]=old['reported_le']
                with self.subTest(id=old['id'],echo=echo),self.assertRaises(ValueError):self.parse(rows)

    def test_missing_extra_duplicate_order_schema_and_framing_changes_reject(self):
        changes=[lambda rows:rows[0].update(schema=1),lambda rows:rows[0].update(input_codec='other'),
                 lambda rows:rows[0].update(canonical_cases_sha256='0'*64),lambda rows:rows[1].pop('decoded_input64_le'),
                 lambda rows:rows[1].update(ordinal=True),lambda rows:rows[1].update(transport_sha256='0'*64),
                 lambda rows:rows[1]['decoded_input64_le'].update(yaw='0'*15),lambda rows:rows[1].update(extra=1),
                 lambda rows:rows.__setitem__(slice(1,3),[rows[2],rows[1]]),lambda rows:rows.pop()]
        for change in changes:
            rows=copy.deepcopy(self.rows);change(rows)
            with self.subTest(change=change),self.assertRaises(ValueError):self.parse(rows)
        for raw in [encoded(self.rows)+b'unknown\n',encoded(self.rows).replace(b'"schema":2',b'"schema":2,"schema":2',1)]:
            with self.assertRaises(ValueError):r.parse_binary_output(raw,PAYLOAD,cases_sha256=r.sha(WIRE.read_bytes()),program_sha256=PROGRAM_SHA)


class ProtectedSourceControls(unittest.TestCase):
    def test_legacy_parser_native_math_process_capability_and_cleanup_are_exact(self):
        protection=json.loads((ROOT/'scripts/fixtures/fov_binary_protected_segments.json').read_text())
        module=(ROOT/'scripts/fov_math_reference.py').read_bytes();legacy=protection['legacy_module']
        self.assertEqual(r.sha(module[:legacy['bytes']]),legacy['sha256'])
        acquisition=(ROOT/'scripts/acquire_fov_math_reference.py').read_bytes()
        ancestry=ancestry_baseline_segments()
        process=acquisition[acquisition.index(b'class LinuxKernel:'):acquisition.index(b'def acquire(')]
        process=erase_ancestry_class(process,'OwnedTree',ancestry['owned_tree']['text'].encode())
        self.assertEqual(r.sha(process),protection['process_classes']['sha256'])
        self.assertEqual(r.sha(acquisition[acquisition.index(b'    finally:\n        if tree is not None:'):acquisition.index(b'\n\ndef main():')]),protection['acquisition_finally']['sha256'])
        tests=(ROOT/'scripts/test_fov_math_reference.py').read_bytes()
        tests=erase_timing_constructor(tests)
        tests=erase_ancestry_class(tests,'FakeKernel',ancestry['fake_kernel']['text'].encode())
        start=tests.index(b'def declared_binary_records():');end=tests.index(b'class CorpusAndSchemaControls',start)
        erased=tests[:start]+tests[end:]
        erased=erased.replace(b'def setUpClass(cls):cls.raw=encoded(declared_binary_records())',b'def setUpClass(cls):cls.raw=encoded(declared_records())')
        self.assertEqual(r.sha(erased),protection['old_tests_byte_erasure_sha256'])
        native=(ROOT/'tools/fov_math_reference/reference.gd').read_bytes()
        math_block=native[native.index(b'\t\tvar age:'):native.index(b'\t\tvar values := {')].replace(b'exact["enemy_id"] == exact["attacker_id"]',b'entry["enemy_id"] == entry["attacker_id"]')
        self.assertEqual(r.sha(math_block),protection['native_math']['sha256'])
        self.assertEqual(r.sha(native[native.index(b'\t\tvar values := {'):native.index(b'\t\temit({"kind": "case"')]),protection['native_values_output']['sha256'])

    def test_native_decoding_prevalidates_api_and_never_uses_decimal_for_operational_values(self):
        source=(ROOT/'tools/fov_math_reference/reference.gd').read_text()
        decoder=source.split('func decode_binary64(',1)[1].split('\nfunc ',1)[0]
        self.assertLess(decoder.index('valid_hex(value, 16)'),decoder.index('value.hex_decode()'))
        self.assertLess(decoder.index('bytes.size() != 8'),decoder.index('bytes.decode_double(0)'))
        self.assertIn('bits64(decoded) != value',decoder);self.assertIn('not is_finite(decoded)',decoder)
        for name in ['yaw','threshold','vision_range','elapsed','damaged_at']:
            self.assertIn(f'var {name}: float = exact["{name}"]',source)
            self.assertNotIn(f'var {name}: float = entry["{name}"]',source)
        self.assertIn('vector_from(exact["actor_position"])',source);self.assertIn('vector_from(exact["enemy_position"])',source)
        self.assertNotIn('str_to_float',source);self.assertNotIn('.to_float(',source)


if __name__=='__main__':unittest.main()
