#!/usr/bin/env python3
"""Target current read labels, not obsolete ordinal reads. Fake User32 only."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(sys.argv.pop(1)).resolve()
OUTPUT=Path(sys.argv.pop(1)).resolve()
assert sorted(os.sched_getaffinity(0)) == [4]
sys.path.insert(0,str(ROOT/'scripts'))
from test_native_route_pulse import RealKeyPulse

ROWS=[]

class CurrentRouteControls(unittest.TestCase):
    def exercise(self,stage,names,error_type,expected_edges,complete):
        trial=RealKeyPulse()
        def hook(actual):
            if actual==stage:raise OSError('independent '+stage+' failure')
        trial.read_hook=hook
        with self.assertRaises(error_type):trial.run(names)
        edges=[(v['key'],v['down']) for v in trial.calls]
        self.assertEqual(edges,expected_edges)
        self.assertFalse(trial.down)
        self.assertEqual(trial.receipt['status'],'FAILED')
        self.assertEqual(trial.receipt['release_complete'],complete)
        ROWS.append(dict(stage=stage,names=names,edges=edges,receipt=trial.receipt))

    def test_pre_down_read_failure_never_injects(self):
        self.exercise('before_key_down:w',('w','d'),OSError,[],True)

    def test_after_down_read_failure_releases_all_owned_edges(self):
        for names in (('d',),('w','d')):
            with self.subTest(names=names):
                expected=[(n,True) for n in names]+[(n,False) for n in names]
                self.exercise('after_down',names,OSError,expected,True)

    def test_after_release_read_failure_retains_actual_edges(self):
        for names in (('d',),('w','d')):
            with self.subTest(names=names):
                expected=[(n,True) for n in names]+[(n,False) for n in names]
                self.exercise('after_release',names,RuntimeError,expected,False)

result=unittest.main(exit=False,verbosity=2).result
OUTPUT.write_text(json.dumps(dict(source=str(ROOT),passed=result.wasSuccessful(),methods=result.testsRun,rows=ROWS),indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
