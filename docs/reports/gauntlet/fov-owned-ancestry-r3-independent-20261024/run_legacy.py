"""Literal and separately preregistered adapter for two unchanged old models."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import unittest
from unittest.mock import patch

parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--data',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--adapt-safe-rejection',action='store_true');args=parser.parse_args()
assert os.sched_getaffinity(0)=={4};args.output.mkdir(parents=True,exist_ok=False)
os.environ['REVIEW_PROCESS_SOURCE']=str(args.source.resolve())
path=args.data/'frozen-control-source/literal_old_independent_controls.py'
spec=importlib.util.spec_from_file_location('literal_old_process_models',path);old=importlib.util.module_from_spec(spec)
adaptations=[]
with patch('subprocess.Popen',side_effect=AssertionError('real process forbidden')),patch('os.kill',side_effect=AssertionError('real signal forbidden')),patch('os.pidfd_open',side_effect=AssertionError('real pidfd forbidden')),patch('signal.pidfd_send_signal',side_effect=AssertionError('real signal forbidden')),patch('ctypes.CDLL',side_effect=AssertionError('native library forbidden')):
    spec.loader.exec_module(old)
    original=old.acquisition.OwnedTree.observe
    def adapted(tree):
        try:return original(tree)
        except RuntimeError as error:
            allowed={'child ancestry differs from observed owned parent':200,
                     'queued owned parent birth identity changed':300}
            if str(error) not in allowed:raise
            excluded=allowed[str(error)]
            assert excluded not in [r['identity']['pid'] for r in tree.seen.values()],'rejection happened after unrelated adoption'
            assert not any(pid==excluded for pid,_ in tree.kernel.sent),'rejection happened after unrelated signal'
            adaptations.append(dict(error=str(error),excluded_pid=excluded,seen=[r['identity'] for r in tree.seen.values()],fake_signals=list(tree.kernel.sent)))
            return tree.live()
    names=['test_stale_children_pid_with_unrelated_parent_is_never_owned_or_signaled',
           'test_queued_owned_parent_reuse_cannot_import_unrelated_descendants']
    suite=unittest.TestSuite(old.IndependentProcessControls(name) for name in names)
    def run():
        with (args.output/'original.stderr').open('w') as stream:return unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    if args.adapt_safe_rejection:
        with patch.object(old.acquisition.OwnedTree,'observe',adapted):result=run()
    else:result=run()
report=dict(source=str(args.source.resolve()),selected_unchanged_methods=names,mode='adapted-safe-rejection' if args.adapt_safe_rejection else 'literal',
            methods=result.testsRun,failures=len(result.failures),errors=len(result.errors),skips=len(result.skipped),
            safe_rejection_adaptations=adaptations,original_rig_results=old.RESULTS,native_invocations=0)
(args.output/'LEGACY.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('original_rig_results','safe_rejection_adaptations')}))
raise SystemExit(not result.wasSuccessful())
