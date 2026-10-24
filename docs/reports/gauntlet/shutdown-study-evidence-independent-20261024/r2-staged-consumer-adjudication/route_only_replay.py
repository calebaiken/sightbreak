"""Registered dependency correction, original test08 only; retain R1 intact."""
import ast
import ctypes
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import subprocess
import time
import unittest
from contextlib import ExitStack
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent
ROOT=REPORT.parents[4]


def main():
    assert os.sched_getaffinity(0)=={4}
    raw=(REPORT/'consumer_controls.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest()=='dcc1eda734d500d26e758228af17321966e279cd74367a622f10e71eb9d967f2'
    spec=importlib.util.spec_from_file_location('frozen_staged_controls',REPORT/'consumer_controls.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=REPORT/'pure-r2-route-only';assert not module.OUT.exists();module.OUT.mkdir()
    source=ast.parse((ROOT/'scripts/native_settings_route.py').read_bytes())
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('SETTINGS_COVER','SETTINGS_SPAWN')}
    assert constants==dict(SETTINGS_COVER=(-7.8,-21.0),SETTINGS_SPAWN=(-4.4,-21.0))
    module.source_scope.update(constants)
    ordinary=REPORT/'pure-r1/baseline-ordinary';module.BASELINES['ordinary']=(ordinary,json.loads((ordinary/'results.json').read_text()),None)
    original=module.source_scope['key_pulse'];sleep_counts=[]
    def pulse(*args,**kwargs):
        sleep=kwargs['sleep'];calls=0
        def bounded_sleep(seconds):
            nonlocal calls
            calls+=1
            if calls>32:raise AssertionError('bounded fake pulse exceeded32 sleeps')
            sleep(math.ceil(seconds*10**9)/10**9)
        kwargs['sleep']=bounded_sleep
        try:return original(*args,**kwargs)
        finally:sleep_counts.append(calls)
    module.source_scope['key_pulse']=pulse
    stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((subprocess,'Popen'),(subprocess,'run'),(os,'kill'),(os,'killpg'),(ctypes,'CDLL'),(time,'sleep')):
            guard.enter_context(patch.object(obj,name,module.forbidden))
        if hasattr(ctypes,'WinDLL'):guard.enter_context(patch.object(ctypes,'WinDLL',module.forbidden))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([module.ConsumerControls('test_08_declared_route_and_pulse_match_pure_source_branch')]))
    (module.OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),successful=result.wasSuccessful(),source_constants=constants,fake_sleep_counts=sleep_counts,fake_sleep_rounding='ceil to1ns, atmost32calls/pulse',original_test08_assertions_unchanged=True,R2_reader_or_actual_collector_executed=False,native_API_helper_or_study_trials=0)
    (module.OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
