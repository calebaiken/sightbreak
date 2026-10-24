"""Pure lifetime-aware kernel models; no real processes, descriptors or signals."""
import argparse
import copy
import importlib
import json
import os
from pathlib import Path
import signal
import sys
import unittest
from unittest.mock import patch

SOURCE=DATA=acquisition=protection=None
RESULTS={}


class LifetimeKernel:
    supervisor=50
    def __init__(self,scenario='stable'):
        self.current={};self.lifetimes={};self.fds={};self.closed=[];self.signals=[];self.events=[]
        self.reads={};self.scenario=scenario;self.replaced=False;self.next_fd=4000
        self.add('supervisor',50,49,1,pgrp=50,session=50)
        self.add('root',100,50,900)
        self.add('parent-old',200,100,1000)
        self.add('unrelated-ancestor',999,998,800,pgrp=999,session=999)
        if scenario in ('stable','orphan'):self.add('owned-child',300,200,1000)

    def event(self,kind,**details):self.events.append(dict(kind=kind,**details))

    def add(self,name,pid,parent,birth,*,pgrp=100,session=100):
        value=dict(name=name,exited=False,identity=dict(pid=pid,state='R',ppid=parent,pgrp=pgrp,session=session,start_ticks=birth))
        self.current[pid]=value;self.lifetimes[name]=value
        self.event('create',lifetime=name,**value['identity'])
        return value

    def exit(self,pid):
        value=self.current.pop(pid);value['exited']=True
        self.event('exit_and_reap',lifetime=value['name'],pid=pid)

    def replace_parent(self,*,child=True):
        self.exit(200)
        birth=1001 if self.scenario=='different-birth' else 1000
        self.add('foreign-parent',200,999,birth,pgrp=999,session=999)
        if child:self.add('foreign-child',300,200,birth,pgrp=999,session=999)
        self.replaced=True

    def identity(self,pid):
        self.reads[pid]=self.reads.get(pid,0)+1
        if self.scenario=='before-enumeration' and pid==200 and self.reads[pid]==3:
            self.replace_parent()
        value=self.current.get(pid)
        self.event('identity',pid=pid,lifetime=value['name'] if value else None)
        return copy.deepcopy(value['identity']) if value else None

    def children(self,pid):
        if self.scenario in ('during-enumeration','different-birth') and pid==200 and not self.replaced:
            self.replace_parent()
        children=[number for number,value in self.current.items() if value['identity']['ppid']==pid]
        self.event('children',pid=pid,result=children)
        return children

    def open_pid(self,pid):
        value=self.current[pid];self.next_fd+=1;fd=self.next_fd;self.fds[fd]=value
        self.event('open_fake_pidfd',pid=pid,fd=fd,lifetime=value['name'])
        if self.scenario=='child-reparent' and pid==200:value['identity']['ppid']=999
        return fd

    def close_pid(self,fd):self.closed.append(fd);self.event('close_fake_pidfd',fd=fd)

    def send(self,fd,signum):
        value=self.fds[fd]
        self.event('fake_pidfd_send_attempt',fd=fd,lifetime=value['name'],exited=value['exited'])
        if value['exited']:raise ProcessLookupError('original fake lifetime has exited')
        self.signals.append(dict(fd=fd,pid=value['identity']['pid'],lifetime=value['name'],signal=signum))

    def reap(self,pid):return(0,0)
    def affinity(self,pid):return[0,1]
    def executable(self,pid):return str(acquisition.ENGINE.resolve())

    def snapshot(self,tree,error=None):
        return dict(observer_error=error,seen=[dict(key=list(key),identity=row['identity'],fd=row['fd'],
                    bound_lifetime=self.fds[row['fd']]['name']) for key,row in tree.seen.items()],
                    fake_signals=self.signals,closed_fds=self.closed,
                    pidfd_lifetimes={str(fd):dict(lifetime=value['name'],exited=value['exited']) for fd,value in self.fds.items()},
                    current={str(pid):dict(lifetime=v['name'],**v['identity']) for pid,v in self.current.items()},events=self.events)


class IndependentLifetimeControls(unittest.TestCase):
    def bound(self,kernel):
        tree=acquisition.OwnedTree(kernel,100);tree.bind_root();self.addCleanup(tree.close);return tree

    def collision(self,scenario):
        kernel=LifetimeKernel(scenario);tree=self.bound(kernel);error=None
        try:tree.observe()
        except RuntimeError as caught:error=str(caught)
        # Stable fake pidfds cannot signal the replacement through old parent's
        # descriptor. A newly imported foreign child's descriptor can signal it.
        tree.signal_all(15)
        RESULTS[scenario]=kernel.snapshot(tree,error)
        self.assertTrue(kernel.lifetimes['parent-old']['exited'])
        self.assertTrue(any(v['name']=='parent-old' and v['exited'] for v in kernel.fds.values()))
        with self.subTest(postcondition='no_foreign_descendant_adoption'):
            self.assertNotIn((300,1000),tree.seen,'unrelated child imported through reused numeric parent')
        with self.subTest(postcondition='no_foreign_lifetime_signal'):
            self.assertFalse(any(r['lifetime']=='foreign-child' for r in kernel.signals),'new foreign pidfd was signaled')

    def test_same_tick_parent_reuse_before_enumeration_never_imports_foreign_child(self):
        self.collision('before-enumeration')

    def test_same_tick_parent_reuse_during_enumeration_never_imports_foreign_child(self):
        self.collision('during-enumeration')

    def test_different_birth_reuse_rejects_without_foreign_adoption(self):
        kernel=LifetimeKernel('different-birth');tree=self.bound(kernel)
        with self.assertRaisesRegex(RuntimeError,'parent birth'):tree.observe()
        tree.signal_all(15);RESULTS['different-birth']=kernel.snapshot(tree,'safe queued-parent birth rejection')
        self.assertNotIn((300,1001),tree.seen)
        self.assertFalse(any(r['lifetime'].startswith('foreign') for r in kernel.signals))

    def test_stable_three_generation_tree_keeps_only_owned_lifetimes(self):
        kernel=LifetimeKernel();tree=self.bound(kernel);tree.observe();tree.signal_all(15)
        RESULTS['stable']=kernel.snapshot(tree)
        self.assertEqual({r['lifetime'] for r in kernel.signals},{'root','parent-old','owned-child'})
        self.assertEqual(set(tree.seen),{(100,900),(200,1000),(300,1000)})

    def test_owned_orphan_reparents_to_supervisor_without_descriptor_loss(self):
        kernel=LifetimeKernel('orphan');tree=self.bound(kernel);tree.observe();old=tree.seen[(200,1000)]['fd']
        kernel.exit(100);kernel.current[200]['identity']['ppid']=50
        tree.observe();tree.signal_all(15);RESULTS['orphan']=kernel.snapshot(tree)
        self.assertEqual(tree.seen[(200,1000)]['fd'],old)
        self.assertEqual({r['lifetime'] for r in kernel.signals},{'parent-old','owned-child'})

    def test_stale_foreign_child_list_is_safe_rejection(self):
        kernel=LifetimeKernel();kernel.current[200]['identity']['ppid']=999
        original=kernel.children
        kernel.children=lambda pid:[100,200] if pid==50 else original(pid)
        tree=self.bound(kernel)
        with self.assertRaisesRegex(RuntimeError,'ancestry'):tree.observe()
        tree.signal_all(15);RESULTS['stale-list']=kernel.snapshot(tree,'safe ancestry rejection')
        self.assertNotIn((200,1000),tree.seen)
        self.assertFalse(any(r['lifetime']=='parent-old' for r in kernel.signals))

    def test_child_reparent_during_pidfd_open_closes_unproved_descriptor(self):
        kernel=LifetimeKernel('child-reparent');tree=self.bound(kernel)
        with self.assertRaisesRegex(RuntimeError,'ancestry'):tree.observe()
        tree.signal_all(15);RESULTS['child-reparent']=kernel.snapshot(tree,'safe ancestry rejection')
        self.assertNotIn((200,1000),tree.seen)
        self.assertTrue(any(kernel.fds[fd]['name']=='parent-old' for fd in kernel.closed))
        self.assertFalse(any(r['lifetime']=='parent-old' for r in kernel.signals))

    def test_live_projection_excludes_same_tick_replacement_of_exited_pidfd(self):
        kernel=LifetimeKernel('live-projection');tree=self.bound(kernel);tree.observe();kernel.replace_parent(child=False)
        live=tree.live();RESULTS['live-projection']=dict(live=live,**kernel.snapshot(tree))
        self.assertNotIn(200,[row['pid'] for row in live],'foreign replacement reported live through exited held descriptor')

    def test_exact_protected_remainder_and_no_constructor_api_before_stream_retention(self):
        raw=(SOURCE/'scripts/acquire_fov_math_reference.py').read_bytes()
        old=(DATA/'frozen-control-source/acquire_fov_math_reference.py').read_bytes()
        donors=protection.ancestry_baseline_segments()
        self.assertEqual(protection.erase_ancestry_class(raw,'OwnedTree',donors['owned_tree']['text'].encode()),old)
        tests=(SOURCE/'scripts/test_fov_math_reference.py').read_bytes()
        self.assertEqual(protection.erase_ancestry_class(tests,'FakeKernel',donors['fake_kernel']['text'].encode()),
                         (DATA/'frozen-control-source/test_fov_math_reference.py').read_bytes())
        self.assertEqual((SOURCE/'scripts/fixtures/fov_binary_protected_segments.json').read_bytes(),
                         (DATA/'frozen-control-source/fov_binary_protected_segments.json').read_bytes())
        kernel=LifetimeKernel();before=len(kernel.events);acquisition.OwnedTree(kernel,100)
        self.assertEqual(len(kernel.events),before)
        self.assertLess(raw.index(b'tree=OwnedTree(kernel,process.pid)'),raw.index(b'streams=stream_factory(process,output)'))
        self.assertLess(raw.index(b'streams=stream_factory(process,output)'),raw.index(b'tree.bind_root()',raw.index(b'def acquire(')))
        RESULTS['protected_remainder_and_constructor']=True


def main():
    global SOURCE,DATA,acquisition,protection
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert os.sched_getaffinity(0)=={4};SOURCE=args.source.resolve();DATA=args.data.resolve()
    args.output.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(SOURCE/'scripts'))
    with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('os.pidfd_open',side_effect=AssertionError('real pidfd forbidden')),patch('signal.pidfd_send_signal',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
        acquisition=importlib.import_module('acquire_fov_math_reference');protection=importlib.import_module('test_fov_binary_input')
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(IndependentLifetimeControls)
        with (args.output/'original.stderr').open('w') as stream:result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    failed={getattr(test,'test_case',test).id() for test,_ in result.failures}
    report=dict(source=str(SOURCE),methods=result.testsRun,failure_events=len(result.failures),distinct_failed_methods=len(failed),
                errors=len(result.errors),skips=len(result.skipped),results=RESULTS,native_invocations=0,real_process_or_signal_calls=0)
    (args.output/'INDEPENDENT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))
    raise SystemExit(not result.wasSuccessful())


if __name__=='__main__':main()
