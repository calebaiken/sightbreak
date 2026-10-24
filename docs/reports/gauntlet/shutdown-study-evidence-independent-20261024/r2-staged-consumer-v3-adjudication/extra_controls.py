"""Five registered V3 file/wait guard families; no reader or collector calls."""
from contextlib import ExitStack
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v3_guard_data',REPORT/'consumer_controls.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
OUT=REPORT/'pure-extra-r1';CACHE=None


def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')


def producer(name):
    global CACHE
    if CACHE is None:
        with tempfile.TemporaryDirectory(prefix='v3-private-data-only-') as tmp:
            source=Path(tmp)/'template';content=base.scope['_write_format_trial_v1'](source,base.scope['fixture_identity'](),observer=None)
            files={p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*') if p.is_file()}
            CACHE=(content,files,source)
    content,files,source=CACHE
    return base.Producer(OUT/name,content,files,clock=base.Clock(),snapshot=base.scope['_snapshot'],observer=None,template_root=source)


class GuardControls(unittest.TestCase):
    def test_01_false_and_missing_predicates_cannot_complete(self):
        p=producer('false-predicate')
        try:
            with self.assertRaisesRegex(TimeoutError,'predicate not observed'):p.wait('never',1,predicate=lambda:False)
            self.assertEqual(p.clock.monotonic(),p.started+1)
            self.assertFalse(any(r['event']=='wait_completed' for r in p.actions))
            self.assertFalse(list(p.root.glob('*.png')))
            with self.assertRaises(TypeError):p.wait('missing',1)
            with self.assertRaises(ValueError):p.wait('not-callable',1,predicate=False)
        finally:self.assertEqual(p.close_owned(),[])
    def test_02_same_inode_change_and_preimage_collision_preserve_bytes(self):
        p=producer('same-inode');old=b'initial';foreign=b'foreign';name='actions.json';p.put(name,old)
        path=p.root/name;info=path.stat();path.write_bytes(foreign);os.utime(path,ns=(info.st_atime_ns,info.st_mtime_ns))
        directory=p.root/'construction-failure-preimages';directory.mkdir();stem=hashlib.sha256(name.encode()).hexdigest();marker=directory/(stem+'-0.bin');marker.write_bytes(b'unrelated preimage marker')
        try:
            with self.assertRaisesRegex(ValueError,'owned output'):p.put(name,b'new')
            self.assertEqual(path.read_bytes(),foreign);self.assertEqual(marker.read_bytes(),b'unrelated preimage marker')
            self.assertIn(old,[f.read_bytes() for f in directory.glob('*.bin')])
            save('SAME_INODE.json',dict(foreign_preserved=True,existing_preimage_marker_preserved=True,known_old_preimage_retained=True))
        finally:self.assertEqual(p.close_owned(),[])
    def test_03_namespace_identity_is_checked_before_successful_return(self):
        p=producer('namespace');p.put('actions.json',b'old');fd=p.owned['actions.json']['stream'].fileno();original=os.fstat;calls=0;swapped=[]
        def fstat(value):
            nonlocal calls
            if value==fd:
                calls+=1
                if calls==4:
                    moved=p.root.with_name(p.root.name+'-moved');p.root.rename(moved);p.root.mkdir()
                    os.link(moved/'actions.json',p.root/'actions.json');(p.root/'foreign-marker.bin').write_bytes(b'new namespace bytes')
                    swapped.append(str(moved))
            return original(value)
        error=None
        try:
            try:
                with patch.object(os,'fstat',fstat):p.put('actions.json',b'new')
            except (ValueError,OSError) as caught:error=type(caught).__name__+': '+str(caught)
            changed=p.directory_identity(p.root.lstat())!=p.root_identity
            save('NAMESPACE_POSTWRITE.json',dict(error=error,swapped=swapped,root_identity_changed_before_return=changed,metadata_bytes_hex=(p.root/'actions.json').read_bytes().hex(),foreign_marker_preserved=(p.root/'foreign-marker.bin').read_bytes()==b'new namespace bytes'))
            self.assertTrue(swapped);self.assertIsNotNone(error,'Visible root namespace replacement must prevent successful update return')
        finally:p.close_owned()
    def test_04_opened_file_is_closed_when_initial_identity_read_fails(self):
        p=producer('first-fstat-error');opened=[];raised=[];original_open=Path.open;original_stat=os.fstat;cause=OSError('original initial fstat error')
        def open_file(path,*args,**kwargs):
            stream=original_open(path,*args,**kwargs)
            if path==p.root/'results.json' and args and args[0]=='x+b':opened.append(stream)
            return stream
        def fstat(fd):
            if opened and not raised and fd==opened[0].fileno():raised.append(True);raise cause
            return original_stat(fd)
        caught=None
        try:
            try:
                with patch.object(Path,'open',open_file),patch.object(os,'fstat',fstat):p.run()
            except BaseException as error:caught=error
            states=[s.closed for s in opened]
            save('INITIAL_FSTAT_CLOSE.json',dict(error=None if caught is None else type(caught).__name__+': '+str(caught),opened_count=len(opened),candidate_closed_before_review_cleanup=states,known_owned_names=list(p.owned),original_cause_preserved=caught is cause or getattr(caught,'__cause__',None) is cause))
            self.assertIsNotNone(caught);self.assertEqual(len(opened),1)
            self.assertTrue(all(states),'Every exclusive-open object needs a close attempt despite identity failure')
        finally:
            p.close_owned()
            for stream in opened:stream.close()
    def test_05_all_closes_attempted_and_primary_cause_retained(self):
        p=producer('close-errors');calls=[];cause=RuntimeError('original launch failure')
        class Proxy:
            def __init__(self,name,stream,fail):self.name,self.stream,self.fail=name,stream,fail
            def __getattr__(self,name):return getattr(self.stream,name)
            def close(self):
                calls.append(self.name);self.stream.close()
                if self.fail:raise OSError('modeled close error after actual fixture close')
        def observer(event,**details):
            for index,(name,record) in enumerate(p.owned.items()):record['stream']=Proxy(name,record['stream'],index==0)
            raise cause
        p.observer=observer;caught=None
        try:p.run()
        except BaseException as error:caught=error
        save('ALL_CLOSES.json',dict(error=None if caught is None else type(caught).__name__+': '+str(caught),close_attempts=calls,expected_names=list(p.owned),primary_cause_retained=getattr(caught,'__cause__',None) is cause))
        self.assertIsInstance(caught,RuntimeError);self.assertEqual(calls,list(p.owned));self.assertIs(caught.__cause__,cause)
        self.assertTrue(all(record['stream'].closed for record in p.owned.values()))


def main():
    assert os.sched_getaffinity(0)=={4};assert not OUT.exists();OUT.mkdir();stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((base.subprocess,'Popen'),(base.subprocess,'run'),(os,'kill'),(os,'killpg'),(base.ctypes,'CDLL'),(base.time,'sleep')):
            guard.enter_context(patch.object(obj,name,base.forbidden))
        if hasattr(base.ctypes,'WinDLL'):guard.enter_context(patch.object(base.ctypes,'WinDLL',base.forbidden))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GuardControls))
    (OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),failure_names=[t.id() for t,_ in result.failures],error_names=[t.id() for t,_ in result.errors],R2_reader_or_actual_collector_executed=False,native_API_proc_study_or_helper_trials=0)
    save('RESULTS.json',report);print(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
