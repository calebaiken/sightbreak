"""Bounded first-group only; original158 literal outcome remains NOT PASS."""
import ast
import builtins
from contextlib import contextmanager,ExitStack
from copy import deepcopy
import ctypes
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
BOUND=REPORT/'bound-source'
OUT=REPORT/'pure-r1'
CURRENT='fab0711b9f239654a31cac745d4778eed8691d617eccea39c7fccabc6593fdf0'
OLD='d2cab3af7e441615a37caedb259b1311eb0b5b1cde46719c1000181223facba1'
HELPER='9f81e903c5932ab1762f347ae400f45ae7b928c29abf3d9f719eb6e7141ead8c'
A='FullExpiryReaderControls.test_new_positive_lifecycle_projection_and_old_helper_unchanged'
B='ExpiryHistoryControls.test_missing_legacy_connected_foundation_stays_unknown_then_later_invalid'
PHASE=None;CALLS=[];RESTORES=[];PROJECTION_CALLS={};FRAMES={}
EXPIRY=None;READER=None;HISTORICAL=None;OLD_HELPER=None


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def method_hash(name):
    raw=(BOUND/'current/scripts/test_input_consumption_expiry.py').read_bytes();tree=ast.parse(raw)
    cls_name,method=name.split('.')
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls_name]
    if len(classes)!=1:raise ValueError('ambiguous class')
    methods=[n for n in classes[0].body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==method]
    if len(methods)!=1 or type(methods[0]) is not ast.FunctionDef or methods[0].decorator_list:raise ValueError('ambiguous method')
    node=methods[0];return hashlib.sha256(b''.join(raw.splitlines(keepends=True)[node.lineno-1:node.end_lineno])).hexdigest()


TARGETS={A:dict(sha='ebc1f2658f22b837aaad83d475151565f68f684797e21f2e8d4a004712fbc6cf',lane='CURRENT'),B:dict(sha='5191e7e877caad95b280c9dea3a4446d0c357e9a7a0f12c83817f4db91c40a57',lane='HISTORICAL')}


@contextmanager
def target(name,*,sha=None,lane=None):
    if name not in TARGETS:raise ValueError('unknown method')
    spec=TARGETS[name]
    if sha is not None and sha!=spec['sha']:raise ValueError('wrong method hash')
    if lane is not None and lane!=spec['lane']:raise ValueError('wrong target')
    if method_hash(name)!=spec['sha']:raise ValueError('method source changed')
    before=dict(analyze=EXPIRY.analyze,declared_rows=EXPIRY.declared_rows)
    others={k:id(v) for k,v in EXPIRY.__dict__.items() if k not in before}
    if before['analyze'] is not READER.analyze:raise ValueError('unexpected prior target')
    changes=dict(declared_rows=OLD_HELPER)
    if spec['lane']=='HISTORICAL':changes['analyze']=HISTORICAL.analyze
    try:
        with patch.multiple(EXPIRY,**changes):
            if name==A:assert EXPIRY.analyze is READER.analyze
            else:assert EXPIRY.analyze is HISTORICAL.analyze
            yield
    finally:
        assert EXPIRY.analyze is before['analyze'] and EXPIRY.declared_rows is before['declared_rows']
        assert others=={k:id(v) for k,v in EXPIRY.__dict__.items() if k not in before}
        RESTORES.append(dict(method=name,restored=True,other_globals_unchanged=True))


def profile(frame,event,arg):
    codes={READER.analyze.__code__:('CURRENT',READER.analyze,CURRENT),HISTORICAL.analyze.__code__:('HISTORICAL',HISTORICAL.analyze,OLD)}
    if event=='call' and frame.f_code is READER.expiry_projection.__code__:PROJECTION_CALLS[PHASE]=PROJECTION_CALLS.get(PHASE,0)+1
    if frame.f_code not in codes:return
    lane,function,sha=codes[frame.f_code]
    if event=='call':
        if len(CALLS)>=5:raise AssertionError('maximum five analyze calls exceeded')
        expected='HISTORICAL' if PHASE=='B' else 'CURRENT'
        if lane!=expected:raise AssertionError('wrong actual reader target')
        row=dict(ordinal=len(CALLS)+1,phase=PHASE,lane=lane,candidate_credit=lane=='CURRENT',reader_sha256=sha,function_pointer=id(function),code_pointer=id(function.__code__),code_filename=frame.f_code.co_filename,client_sha256=hashlib.sha256(frame.f_locals['client_text'].encode()).hexdigest(),authority_sha256=hashlib.sha256(frame.f_locals['authority_text'].encode()).hexdigest())
        CALLS.append(row);FRAMES[id(frame)]=row
    elif event=='return':
        row=FRAMES.pop(id(frame));row['result']=deepcopy(arg);row['actual_status']=arg.get('transition_status') if isinstance(arg,dict) else None


def forbidden(*args,**kwargs):raise AssertionError('Real process/API effect forbidden in bounded target controls')


class ExtraControls(unittest.TestCase):
    def test_companion_current_exact_pair(self):
        global PHASE
        PHASE='companion'
        for call,want in ((2093,'CONSISTENT'),(2045,'INVALID')):
            pair=json.loads((REPORT/'pairs'/(str(call)+'.json')).read_text())
            result=READER.analyze(pair['client_text'],pair['authority_text'])
            self.assertEqual(result['transition_status'],want,result['errors'])
            self.assertEqual(result['diagnostic_complete'],want=='CONSISTENT')
    def test_scoped_binding_rejects_unknowns_and_restores_on_exception(self):
        for name,kwargs in [('unknown',{}),(A,dict(sha='0'*64)),(A,dict(lane='HISTORICAL'))]:
            with self.assertRaises(ValueError):
                with target(name,**kwargs):self.fail('invalid scope entered')
        class Sentinel(Exception):pass
        for name in (A,B):
            with self.assertRaises(Sentinel):
                with target(name):raise Sentinel('pure restoration control')
        self.assertIs(EXPIRY.analyze,READER.analyze)


def main():
    global EXPIRY,READER,HISTORICAL,OLD_HELPER,PHASE
    assert os.sched_getaffinity(0)=={4};assert not OUT.exists();OUT.mkdir()
    assert digest(BOUND/'current/scripts/analyze_input_consumption.py')==CURRENT
    assert digest(BOUND/'historical/analyze_input_consumption.py')==OLD
    assert digest(BOUND/'historical/test_input_consumption_observation.py')==HELPER
    assert digest(BOUND/'run_frozen_baseline.py')=='d14e0dc14f10c10f56d53b4f056353dd17d259de639b2b5187c0975d8ca0842d'
    assert len(TARGETS)==2 and all(method_hash(name)==v['sha'] for name,v in TARGETS.items())
    previous_profile=sys.getprofile();assert previous_profile is None
    stream=io.StringIO();results=[]
    real_open=builtins.open;real_path_open=Path.open
    def opened(file,*args,**kwargs):
        if isinstance(file,(str,bytes,Path)) and str(file).startswith('/proc'):raise AssertionError('proc access forbidden')
        return real_open(file,*args,**kwargs)
    def path_open(path,*args,**kwargs):
        if str(path).startswith('/proc'):raise AssertionError('proc access forbidden')
        return real_path_open(path,*args,**kwargs)
    with ExitStack() as guard:
        for obj,name in ((subprocess,'Popen'),(subprocess,'run'),(os,'kill'),(os,'killpg'),(os,'system'),(ctypes,'CDLL')):
            guard.enter_context(patch.object(obj,name,forbidden))
        for name in ('fork','posix_spawn','wait','waitpid','waitid','pidfd_open'):
            if hasattr(os,name):guard.enter_context(patch.object(os,name,forbidden))
        if hasattr(ctypes,'WinDLL'):guard.enter_context(patch.object(ctypes,'WinDLL',forbidden))
        guard.enter_context(patch.object(builtins,'open',opened));guard.enter_context(patch.object(Path,'open',path_open))
        assert 'analyze_input_consumption' not in sys.modules
        sys.path.insert(0,str(BOUND/'current/scripts'))
        READER=importlib.import_module('analyze_input_consumption');EXPIRY=importlib.import_module('test_input_consumption_expiry')
        HISTORICAL=types.ModuleType('frozen_expiry_only_d2');HISTORICAL.__file__=str(BOUND/'historical/analyze_input_consumption.py')
        exec(compile((BOUND/'historical/analyze_input_consumption.py').read_bytes(),HISTORICAL.__file__,'exec'),HISTORICAL.__dict__)
        parsed=ast.parse((BOUND/'historical/test_input_consumption_observation.py').read_bytes())
        constructors=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ('control','declared_rows')];assert len(constructors)==2
        namespace={'deepcopy':deepcopy};exec(compile(ast.Module(body=constructors,type_ignores=[]),'<frozen old9f constructors>','exec'),namespace);OLD_HELPER=namespace['declared_rows']
        reader_globals={k:id(v) for k,v in READER.__dict__.items()};analyze=READER.analyze
        sys.setprofile(profile)
        try:
            for name,phase in ((A,'A'),(B,'B')):
                PHASE=phase;cls,method=name.split('.')
                with target(name):r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([getattr(EXPIRY,cls)(method)]))
                results.append(dict(name=name,methods=r.testsRun,failures=len(r.failures),errors=len(r.errors),skips=len(r.skipped),candidate_credit=name==A))
            PHASE='non-reader'
            r=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExtraControls))
            results.append(dict(name='additive_companion_and_scope',methods=r.testsRun,failures=len(r.failures),errors=len(r.errors),skips=len(r.skipped)))
        finally:sys.setprofile(previous_profile)
        assert READER.analyze is analyze and reader_globals=={k:id(v) for k,v in READER.__dict__.items()}
        assert EXPIRY.analyze is READER.analyze
    (OUT/'original.stderr').write_text(stream.getvalue())
    summary=dict(results=results,analyze_calls=len(CALLS),current_calls=sum(r['lane']=='CURRENT' for r in CALLS),historical_calls=sum(r['lane']=='HISTORICAL' for r in CALLS),calls=CALLS,restoration=RESTORES,current_projection_calls_by_phase=PROJECTION_CALLS,current_reader_module_globals_unchanged=True,existing18_adapter_not_executed=True,original158_status='NOT PASS',actual207_or_native_API_proc_engine_study_capability_calls=0)
    (OUT/'RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n')
    assert len(CALLS)==5 and summary['current_calls']==3 and summary['historical_calls']==2
    assert PROJECTION_CALLS.get('B',0)==0
    assert [r['actual_status'] for r in CALLS]==['CONSISTENT','UNKNOWN','INVALID','CONSISTENT','INVALID']
    success=all(not r['failures'] and not r['errors'] and not r['skips'] for r in results)
    print(json.dumps(dict(methods=sum(r['methods'] for r in results),failures=sum(r['failures'] for r in results),errors=sum(r['errors'] for r in results),skips=sum(r['skips'] for r in results),calls=len(CALLS),current=3,historical=2,original158='NOT PASS')))
    return 0 if success else 1


if __name__=='__main__':raise SystemExit(main())
