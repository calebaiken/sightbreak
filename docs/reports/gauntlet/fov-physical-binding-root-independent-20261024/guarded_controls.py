"""Independent source-only runner. Only local Git may start as a child."""
import argparse
import ast
from contextlib import ExitStack
import ctypes
import hashlib
import importlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
assert sorted(os.sched_getaffinity(0))==[4]
args.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(args.source/'scripts'))
import acquire_fov_math_reference as a
import test_fov_math_reference as oldtests
import test_fov_binary_input as protection
attempts=[];git_calls=[]
def audit(event,values):
    if event=='subprocess.Popen':
        executable,command,cwd,env=values
        if not isinstance(command,(list,tuple)) or not command or command[0]!='git' or executable!='git':
            attempts.append(dict(event=event,command=repr(command)));raise AssertionError('only local Git subprocess allowed')
        git_calls.append(list(command))
    elif event in ('os.system','os.fork','os.forkpty','os.posix_spawn','ctypes.dlopen'):
        attempts.append(dict(event=event));raise AssertionError('native/process/library entry forbidden')
sys.addaudithook(audit)
def forbidden(*args,**kwargs):
    attempts.append(dict(event='kernel/API/proc entry'));raise AssertionError('kernel/API/proc entry forbidden')
real_open=Path.open;real_readlink=os.readlink
def source_open(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbidden()
    return real_open(path,*args,**kwargs)
def source_readlink(path,*args,**kwargs):
    if str(path)=='/proc' or str(path).startswith('/proc/'):return forbidden()
    return real_readlink(path,*args,**kwargs)
def git(root,*command):
    return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-c','commit.gpgsign=false',*command],cwd=root,stderr=subprocess.PIPE,timeout=10)
def fixture(root):
    git(root,'init','-q');git(root,'config','core.autocrlf','false');git(root,'config','core.filemode','true')
    data={name:('independent fixture '+name+'\n').encode() for name in a.COMPONENT}
    data['scripts/native_log.py']=b'imported dependency\n';data['scripts/odd\tname\n.py']=b'\0binary source\xff'
    for name,value in data.items():
        path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value);path.chmod(0o644)
    git(root,'add','--all');git(root,'-c','user.name=IndependentCritic','-c','user.email=critic@invalid','commit','--no-gpg-sign','-qm','fixture')
    return git(root,'rev-parse','HEAD').decode().strip(),data
records={}
class IndependentControls(unittest.TestCase):
    def test_original_binding_positive_and_three_hidden_changes(self):
        raw=git(args.source,'show','8cc38cdcd7dfff37056782149e513c08037e4e77:scripts/acquire_fov_math_reference.py')
        tree=ast.parse(raw);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='source_binding')
        function=ast.Module(body=[node],type_ignores=[])
        namespace=dict(time=time,subprocess=subprocess,COMPONENT=a.COMPONENT,digest=a.digest,require=a.require)
        exec(compile(function,'<exact-old8cc-binding>','exec'),namespace)
        results=[]
        for kind in ('exact','acquire-bytes','owner-exec','native-log'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);commit,files=fixture(root);namespace['ROOT']=root
                if kind!='exact':
                    name='scripts/native_log.py' if kind=='native-log' else 'scripts/acquire_fov_math_reference.py'
                    git(root,'update-index','--assume-unchanged','--',name)
                    if kind=='owner-exec':git(root,'config','core.filemode','false');(root/name).chmod(0o755)
                    else:(root/name).write_bytes(files[name]+b'changed physical source')
                    git(root,'diff','--quiet')
                self.assertEqual(namespace['source_binding'](commit,deadline=time.monotonic()+30)['commit'],commit)
                with patch.object(a,'ROOT',root):
                    if kind=='exact':self.assertEqual(a.source_binding(commit,deadline=time.monotonic()+30)['non_doc_paths'],len(files));outcome='ACCEPT'
                    else:
                        with self.assertRaises(RuntimeError):a.source_binding(commit,deadline=time.monotonic()+30)
                        outcome='REJECT'
                results.append(dict(case=kind,old='ACCEPT',candidate=outcome))
        records['benchmark']=results
    def test_actual_timing_assertions_execute_with_four_queries(self):
        counts={};case=oldtests.SupervisorControls('test_source_git_children_receive_only_remaining_whole_deadline')
        for name in ('assertEqual','assertTrue','assertRaises'):
            original=getattr(case,name)
            def counted(*values,_name=name,_original=original,**options):
                counts[_name]=counts.get(_name,0)+1;return _original(*values,**options)
            setattr(case,name,counted)
        result=unittest.TestResult();case.run(result)
        self.assertEqual((len(result.failures),len(result.errors)),(0,0));self.assertEqual(counts,{'assertEqual':3,'assertTrue':1,'assertRaises':1})
        records['actual_timing_assertion_calls']=counts
    def test_deadline_reached_during_final_head_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);commit,files=fixture(root);clock=oldtests.FakeClock();real=subprocess.check_output;calls=[]
            def output(command,**options):
                calls.append(command);value=real(command,**options)
                if len(calls)==4:clock.now=101.
                return value
            with patch.object(a,'ROOT',root),patch.object(subprocess,'check_output',side_effect=output),self.assertRaisesRegex(RuntimeError,'deadline'):
                a.source_binding(commit,deadline=101.,clock=clock)
            self.assertEqual([x[1] for x in calls],['rev-parse','ls-tree','cat-file','rev-parse'])
        records['final_head_deadline']='REJECT'
    def test_guard_presence_limit_and_current_outside_bytes(self):
        raw=(args.source/'scripts/test_fov_math_reference.py').read_bytes();tree=ast.parse(raw)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SupervisorControls')
        node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='test_source_git_children_receive_only_remaining_whole_deadline')
        lines=raw.splitlines(keepends=True);first=node.lineno;last=node.end_lineno
        variant=b''.join(lines[:first])+b'        if False:\n'+b''.join(b'    '+line for line in lines[first:last])+b''.join(lines[last:])
        normalized=protection.erase_timing_constructor(variant)
        self.assertEqual(hashlib.sha256(normalized).hexdigest(),'036b76a9107e3198e312605686fdc5a487d88f0aa686d7021f4e4c4c7475ab89')
        altered=next(n for n in ast.parse(variant).body if isinstance(n,ast.ClassDef) and n.name=='SupervisorControls')
        method=next(n for n in altered.body if isinstance(n,ast.FunctionDef) and n.name==node.name)
        namespace={};exec(compile(ast.Module(body=[method],type_ignores=[]),'<hypothetical-skipped-variant>','exec'),namespace)
        class Counter:
            def __getattr__(self,name):raise AssertionError('no assertion or fixture should execute in false branch')
        self.assertIsNone(namespace[node.name](Counter()))
        changed=raw.replace(b'self.assertEqual(len(timeouts),4)',b'self.assertEqual(len(timeouts),3)',1)
        with self.assertRaises(ValueError):protection.erase_timing_constructor(changed)
        outside=raw.replace(b'class SupervisorControls',b'# outside bytes\nclass SupervisorControls',1)
        self.assertNotEqual(hashlib.sha256(protection.erase_timing_constructor(outside)).hexdigest(),hashlib.sha256(normalized).hexdigest())
        records['guard_limit']=dict(hypothetical_if_false_accepted=True,hypothetical_executed_assertions=0,current_assertions_executed=5,scope='presence guard is not execution proof; hypothetical variant only')

start=time.monotonic()
with ExitStack() as stack:
    for owner,name in ((a,'LinuxKernel'),(os,'pidfd_open'),(os,'kill'),(signal,'pidfd_send_signal'),(ctypes,'CDLL')):
        if hasattr(owner,name):stack.enter_context(patch.object(owner,name,side_effect=forbidden))
    stack.enter_context(patch.object(Path,'open',source_open));stack.enter_context(patch.object(os,'readlink',source_readlink))
    module=importlib.import_module('test_fov_physical_binding')
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(module),unittest.defaultTestLoader.loadTestsFromTestCase(IndependentControls)])
    with (args.output/'stderr').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
records.update(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),seconds=time.monotonic()-start,git_children=len(git_calls),forbidden_attempts=attempts,scope='local Git and pure source controls only',passed=result.wasSuccessful() and not attempts)
(args.output/'RESULT.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records));raise SystemExit(not records['passed'])
