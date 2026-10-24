#!/usr/bin/env python3
"""Independent frozen-case, strict-schema and fake-admission controls; no engine."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(os.environ['REVIEW_MATH_SOURCE']).resolve()
sys.path.insert(0, str(ROOT / 'scripts'))
import acquire_fov_math_reference as acq
import fov_math_reference as ref
import test_fov_math_reference as fixtures

SOURCE = '550e96c9c2e3388a7e06e3df8aa31f973baeae59'
PAYLOAD_SHA = 'd3e3cbc53b89cd0f872d333262524e43a84155c2b8ae0aaab06850e1337dcbae'
PAYLOAD_RAW = (ROOT / 'tools/fov_math_reference/cases.json').read_bytes()
PAYLOAD = json.loads(PAYLOAD_RAW)
PROGRAM_SHA = hashlib.sha256((ROOT / 'tools/fov_math_reference/reference.gd').read_bytes()).hexdigest()
COUNTS = {}


def read(rows):
    return ref.parse_output(fixtures.encoded(rows), PAYLOAD,
                            cases_sha256=PAYLOAD_SHA, program_sha256=PROGRAM_SHA)


class IndependentMathControls(unittest.TestCase):
    def test_exact_captured_provenance_without_generator(self):
        self.assertEqual(hashlib.sha256(PAYLOAD_RAW).hexdigest(), PAYLOAD_SHA)
        raw = (ROOT / 'game/tests/fixtures/bot_objective_timeout.jsonl').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '45edbe3a9572386a99653098624c1dbbc764bae7322e3a5ac2fb464b4dfff697')
        poses = {r['event_index']:r for r in map(json.loads, raw.decode().splitlines())}
        cases = {r['id']:r for r in PAYLOAD['cases']}
        pairs = []
        for event in (120,122,127):
            for actor in poses[event]['actors']:
                for enemy in poses[event]['actors']:
                    if actor['team'] == enemy['team']:
                        continue
                    identity = f'captured/{event}/{actor["id"]}/{enemy["id"]}'
                    row = cases[identity]
                    self.assertEqual(row['actor_position'], actor['position'])
                    self.assertEqual(row['enemy_position'], enemy['position'])
                    self.assertEqual(row['yaw'], actor['yaw'])
                    self.assertEqual(row['meta']['actor_alive'], actor['alive'])
                    self.assertEqual(row['meta']['enemy_alive'], enemy['alive'])
                    self.assertEqual(row['elapsed'], poses[event]['elapsed'])
                    pairs.append(identity)
        self.assertEqual(len(pairs),150)
        source = cases['captured/122/6/2']; synthetic = cases['captured/122/6/2/yaw-zero-synthetic']
        self.assertEqual(source['actor_position'],synthetic['actor_position'])
        self.assertEqual(source['enemy_position'],synthetic['enemy_position'])
        self.assertEqual(synthetic['yaw'],0.)
        self.assertIn('synthetic',synthetic['meta']['scope'])
        actor = next(r for r in poses[127]['actors'] if r['id']==6)
        for enemy_id in (8,9,10):
            row=cases[f'defuse/6/{enemy_id}']
            enemy=next(r for r in poses[127]['actors'] if r['id']==enemy_id)
            self.assertEqual(row['actor_position'],[-15.,0.,10.])
            self.assertEqual(row['enemy_position'],enemy['position'])
            self.assertEqual(row['yaw'],actor['yaw'])
            self.assertEqual(row['meta']['synthetic_team'],1)
        COUNTS['captured_pairs_independently_bound']=150
        COUNTS['synthetic_defuse_inputs_bound']=3

    def test_cutoff_inputs_are_actual_binary32_neighbors_not_native_verdicts(self):
        groups={-.05:[], -.15:[], -.25:[]}
        for row in PAYLOAD['cases']:
            if row['group']!='cutoff32':continue
            value=row['meta']['target_dot']
            encoded=struct.unpack('<I',struct.pack('<f',value))[0]
            self.assertEqual(row['meta']['float32_bits'],f'{encoded:08x}')
            self.assertEqual(struct.unpack('<f',struct.pack('<f',value))[0],value)
            self.assertEqual(row['enemy_position'][2],-value)
            self.assertEqual(row['threshold'],float(row['threshold']))
            groups[row['threshold']].append(encoded)
        for threshold,codes in groups.items():
            center=struct.unpack('<I',struct.pack('<f',threshold))[0]
            span=128 if threshold==-.15 else 1
            self.assertEqual(sorted(codes),list(range(center-span,center+span+1)))
            self.assertNotEqual(threshold,struct.unpack('<f',struct.pack('<f',threshold))[0]) if threshold!=-.25 else None
        COUNTS['fixed_binary32_neighbor_inputs']=263

    def test_independent_axis_zero_and_strict_equality_controls(self):
        rows=fixtures.declared_records()
        expected={'axis/front':(1.,16.),'axis/back':(-1.,16.),'axis/left':(0.,16.),
                  'axis/right':(0.,16.),'axis/zero':(0.,0.)}
        for row in rows:
            if row.get('id') in expected:
                dot,distance=expected[row['id']]
                self.assertEqual(row['values']['dot'],dot)
                self.assertEqual(row['values']['distance'],distance)
        result=read(rows)
        self.assertTrue(result['reference_capture_schema_valid'])
        for case in PAYLOAD['cases']:
            if case['id'] in ('axis/comparison/0','axis/comparison/1','axis/comparison/2'):
                row=next(r for r in rows if r.get('id')==case['id'])
                self.assertEqual(row['values']['dot'],case['threshold'])
                self.assertIs(row['predicates']['geometric'],False)
        COUNTS['exact_equality_controls']=3

    def test_coordinated_analytical_corruptions_are_rejected(self):
        for identity in ('axis/front','axis/back','axis/zero','axis/comparison/2','recent/3/1'):
            for field in ('dot','toward','distance'):
                rows=fixtures.declared_records();row=next(r for r in rows if r.get('id')==identity)
                row['values'][field]=[.5,0.,0.] if field=='toward' else .5
                row['bits64']=ref.bit_tree(row['values'])
                values=row['values'];geo=values['dot']>values['threshold'];recent=row['predicates']['recent_attacker']
                row['predicates'].update(range_reject=values['distance']>values['vision_range'],geometric=geo,in_fov=geo or recent)
                row['predicates']['stage']='range' if row['predicates']['range_reject'] else ('requires_visibility' if row['predicates']['in_fov'] else 'fov')
                with self.subTest(identity=identity,field=field),self.assertRaises(ValueError):read(rows)
        COUNTS['coordinated_analytical_mutations']=15

    def test_general_model_difference_stays_unresolved_without_epsilon_acceptance(self):
        rows=fixtures.declared_records();row=next(r for r in rows if r.get('id','').startswith('cutoff32/'))
        row['values']['dot']=-.5;row['bits64']['dot']=ref.bits64(-.5)
        row['predicates'].update(geometric=False,in_fov=False,stage='fov')
        result=read(rows);comparison=next(r for r in result['comparisons'] if r['id']==row['id'])
        self.assertEqual(comparison['classification'],'UNRESOLVED_MODEL_DIFFERENCE')
        self.assertEqual(comparison['transfer'],'UNRESOLVED_FOR_UNMEASURED_INPUTS')
        self.assertEqual(result['broader_cutoff_parity'],'UNRESOLVED')
        self.assertIs(result['visibility_gameplay_physical_acceptance'],False)

    def test_source_git_metadata_calls_have_remaining_timeouts(self):
        clock=fixtures.FakeClock();calls=[]
        def output(command,**kwargs):
            calls.append((command,kwargs));clock.sleep(1.)
            return SOURCE+'\n' if command[1]=='rev-parse' else b''
        def run(command,**kwargs):
            calls.append((command,kwargs));clock.sleep(1.);return type('R',(),{'returncode':0})()
        with patch.object(acq.subprocess,'check_output',side_effect=output),patch.object(acq.subprocess,'run',side_effect=run):
            binding=acq.source_binding(SOURCE,deadline=160.,clock=clock)
        self.assertEqual(binding['commit'],SOURCE)
        self.assertEqual([kwargs['timeout'] for _,kwargs in calls],[60.,59.,58.,57.])
        self.assertEqual(len(binding['files']),6)
        with patch.object(acq.subprocess,'check_output',side_effect=AssertionError('must not call expired child')):
            with self.assertRaises(RuntimeError):acq.source_binding(SOURCE,deadline=clock(),clock=clock)
        COUNTS['remaining_deadline_git_calls']=4

    def test_wrong_root_affinity_or_executable_retains_failure_streams(self):
        trial=fixtures.SupervisorControls(methodName='test_one_isolated_pinned_invocation_and_complete_success')
        trial.raw=fixtures.encoded(fixtures.declared_records())
        for method,value in (('affinity',[2]),('executable','/declared/wrong-engine')):
            with patch.object(fixtures.FakeKernel,method,return_value=value):
                tmp,out,report,calls,kernel,process,clock=trial.trial()
            try:
                self.assertFalse(report['passed']);self.assertEqual(len(calls),1)
                self.assertEqual((out/'stdout.log').read_bytes(),trial.raw)
                self.assertTrue(report['failure_log_coverage_complete'])
                self.assertEqual(report['stream_eof'],{'stdout':True,'stderr':True})
                self.assertFalse(kernel.table)
            finally:tmp.cleanup()
        COUNTS['early_readback_failure_controls']=2

    def test_late_final_cleanup_observation_cannot_pass(self):
        trial=fixtures.SupervisorControls(methodName='test_one_isolated_pinned_invocation_and_complete_success')
        trial.raw=fixtures.encoded(fixtures.declared_records())
        original=acq.cleanup
        def late(process,tree,deadline,**kwargs):
            result=original(process,tree,deadline,**kwargs)
            kwargs['clock'].now=160.
            return result
        with patch.object(acq,'cleanup',side_effect=late):
            tmp,out,report,calls,kernel,process,clock=trial.trial()
        try:
            self.assertFalse(report['passed']);self.assertEqual(report['finished_monotonic'],160.)
            self.assertIn('whole deadline',report['error'])
            self.assertEqual(len(calls),1)
        finally:tmp.cleanup()
        COUNTS['late_final_completion_controls']=1


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentMathControls))
    print(json.dumps(dict(source=str(ROOT),methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),cases=COUNTS),sort_keys=True))
    sys.exit(not result.wasSuccessful())
