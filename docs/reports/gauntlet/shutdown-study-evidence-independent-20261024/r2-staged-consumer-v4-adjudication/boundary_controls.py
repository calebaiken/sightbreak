"""Three preregistered V4 namespace/registry/normal-close boundary faults."""
from contextlib import ExitStack
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v4_guard_data',REPORT/'extra_controls.py')
data=importlib.util.module_from_spec(spec);spec.loader.exec_module(data)
data.OUT=REPORT/'pure-boundaries-r1'


class BoundaryControls(unittest.TestCase):
    def test_nested_parent_replacement_rejects_after_readback(self):
        p=data.producer('parent');p.put('nested/meta.json',b'old');fd=p.owned['nested/meta.json']['stream'].fileno();original=os.fstat;count=0;changed=[]
        def fstat(value):
            nonlocal count
            if value==fd:
                count+=1
                if count==4:
                    parent=p.root/'nested';moved=p.root/'nested-moved';parent.rename(moved);parent.mkdir();os.link(moved/'meta.json',parent/'meta.json');(parent/'foreign-marker').write_bytes(b'foreign parent marker');changed.append(True)
            return original(value)
        error=None
        try:
            try:
                with patch.object(os,'fstat',fstat):p.put('nested/meta.json',b'new')
            except (ValueError,RuntimeError,OSError) as caught:error=type(caught).__name__+': '+str(caught)
            data.save('PARENT_BOUNDARY.json',dict(error=error,changed=bool(changed),marker_preserved=(p.root/'nested/foreign-marker').read_bytes()==b'foreign parent marker'))
            self.assertTrue(changed);self.assertIsNotNone(error);self.assertEqual((p.root/'nested/foreign-marker').read_bytes(),b'foreign parent marker')
        finally:self.assertEqual(p.close_owned(),[])
    def test_lifetime_registry_survives_metadata_registration_error(self):
        p=data.producer('registry');cause=OSError('modeled metadata registration error')
        class Fault(dict):
            failed=False
            def __setitem__(self,key,value):
                if key=='results.json' and not self.failed:self.failed=True;raise cause
                return super().__setitem__(key,value)
        p.owned=Fault();caught=None
        try:p.run()
        except BaseException as error:caught=error
        closed=[record['stream'].closed for name,record in p.opened]
        data.save('REGISTRY_BOUNDARY.json',dict(error=None if caught is None else type(caught).__name__+': '+str(caught),opened=[name for name,record in p.opened],closed=closed,original_cause_retained=caught is cause or getattr(caught,'__cause__',None) is cause))
        self.assertIsNotNone(caught);self.assertTrue(p.opened);self.assertTrue(all(closed));self.assertTrue(caught is cause or caught.__cause__ is cause)
    def test_namespace_changed_during_normal_closure_cannot_return_success(self):
        p=data.producer('normal-close');original=p.close_owned;changed=[]
        def close():
            errors=original();moved=p.root.with_name(p.root.name+'-moved');p.root.rename(moved);p.root.mkdir();(p.root/'foreign-marker').write_bytes(b'close boundary marker');changed.append(str(moved));return errors
        p.close_owned=close;caught=None;returned=None
        try:returned=p.run()
        except BaseException as error:caught=error
        closed=[record['stream'].closed for name,record in p.opened]
        data.save('NORMAL_CLOSE_BOUNDARY.json',dict(error=None if caught is None else type(caught).__name__+': '+str(caught),successful_return=returned is not None,changed=changed,closed=closed,marker_preserved=(p.root/'foreign-marker').read_bytes()==b'close boundary marker'))
        self.assertTrue(changed);self.assertIsNone(returned);self.assertIsNotNone(caught);self.assertTrue(all(closed));self.assertTrue((Path(changed[0])/'results.json').is_file())


def main():
    assert os.sched_getaffinity(0)=={4};assert not data.OUT.exists();data.OUT.mkdir();stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((data.base.subprocess,'Popen'),(data.base.subprocess,'run'),(os,'kill'),(os,'killpg'),(data.base.ctypes,'CDLL'),(data.base.time,'sleep')):
            guard.enter_context(patch.object(obj,name,data.base.forbidden))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryControls))
    (data.OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),native_process_API_proc_study_or_reader_calls=0)
    (data.OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
