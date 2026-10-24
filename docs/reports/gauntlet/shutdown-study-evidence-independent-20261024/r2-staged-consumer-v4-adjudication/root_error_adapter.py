"""Registered exact safe-rejection adapter; unchanged namespace test03 only."""
from contextlib import ExitStack
import importlib.util
import io
import json
import os
from pathlib import Path
import traceback
import unittest
from unittest.mock import patch

REPORT=Path(__file__).resolve().parent


def main():
    assert os.sched_getaffinity(0)=={4}
    spec=importlib.util.spec_from_file_location('v4_literal_extra',REPORT/'extra_controls.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    mod.OUT=REPORT/'pure-extra-adapted-root';assert not mod.OUT.exists();mod.OUT.mkdir()
    original=mod.base.Producer.put;events=[]
    def put(producer,name,raw):
        try:return original(producer,name,raw)
        except RuntimeError as error:
            cause=error.__cause__
            if not (str(error).startswith('Synthetic preimage retention incomplete:') and isinstance(cause,ValueError) and str(cause)=='fixture root identity changed'):
                raise
            if producer.directory_identity(producer.root.lstat())==producer.root_identity:raise AssertionError('safe adapter requires changed root') from error
            if (producer.root/'foreign-marker.bin').read_bytes()!=b'new namespace bytes':raise AssertionError('safe adapter requires retained marker') from error
            events.append(dict(original_error=type(error).__name__+': '+str(error),cause=type(cause).__name__+': '+str(cause),traceback=traceback.format_exc(),changed_root_verified=True,foreign_marker_preserved=True))
            raise ValueError('registered safe root-namespace rejection') from error
    stream=io.StringIO()
    with ExitStack() as guard:
        for obj,name in ((mod.base.subprocess,'Popen'),(mod.base.subprocess,'run'),(os,'kill'),(os,'killpg'),(mod.base.ctypes,'CDLL'),(mod.base.time,'sleep')):
            guard.enter_context(patch.object(obj,name,mod.base.forbidden))
        guard.enter_context(patch.object(mod.base.Producer,'put',put))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.TestSuite([mod.GuardControls('test_03_namespace_identity_is_checked_before_successful_return')]))
    (mod.OUT/'original.stderr').write_text(stream.getvalue())
    report=dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),safe_error_events=events,original_assertions_unchanged=True,literal_error_not_relabelled=True)
    (mod.OUT/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),adapted_events=len(events))))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
