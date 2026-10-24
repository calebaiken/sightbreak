#!/usr/bin/env python3
"""Replay new fake controls against frozen550 wrapper; no acquire/native call."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();root=a.source.resolve();here=Path(__file__).resolve().parent
a.output.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(root/'scripts'))
import test_fov_math_reference as fixture
old_path=here/'acquire_old550_preserved.py'
assert hashlib.sha256(old_path.read_bytes()).hexdigest()=='f6f0715c21581005421817988701206343683443ca1933a1e86c288e96d36dd5'
spec=importlib.util.spec_from_file_location('old550acq',old_path)
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old.ROOT=root;old.PROJECT=root/'tools/fov_math_reference';fixture.acquisition=old
selected={
    'SupervisorControls':[
        'test_unavailable_prelaunch_observer_does_not_create_native_process',
        'test_intended_root_pid_is_retained_but_does_not_replace_failed_readback',
        'test_direct_root_binding_checks_parent_and_birth_before_ownership',
        'test_live_popen_root_cannot_vanish_with_empty_discovery',
        'test_bound_exited_popen_root_has_explicit_wait_status'],
    'ProcInterfaceControls':[
        'test_existing_task_missing_interface_and_existing_parent_missing_tasks_fail',
        'test_multiple_thread_lists_deduplicate_and_invalid_pid_tokens_fail',
        'test_departed_thread_is_distinct_from_missing_children_on_live_thread',
        'test_supervisor_preflight_checks_interface_before_subreaper_mutation']}
suite=unittest.TestSuite(getattr(fixture,cls)(name) for cls,names in selected.items() for name in names)
stdout,stderr=io.StringIO(),io.StringIO()
with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
    result=unittest.TextTestRunner(stream=stderr,verbosity=2).run(suite)
(a.output/'stdout').write_text(stdout.getvalue());(a.output/'stderr').write_text(stderr.getvalue())
failed={getattr(test,'test_case',test).id() for test,error in result.failures+result.errors}
report=dict(old_source='550e96c9c2e3388a7e06e3df8aa31f973baeae59',test_source=str(root),methods=result.testsRun,
            failure_events=len(result.failures),error_events=len(result.errors),distinct_failed_methods=len(failed),
            passed_methods=result.testsRun-len(failed)-len(result.skipped),failed_method_ids=sorted(failed),
            expected_historical_failure=True,native_or_real_process_calls=0)
(a.output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,sort_keys=True))
