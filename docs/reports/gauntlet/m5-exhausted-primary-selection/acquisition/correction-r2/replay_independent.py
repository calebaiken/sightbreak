#!/usr/bin/env python3
"""Replay the exact retained reviewer source against the current wrapper."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import types
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import run_acquisition


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    raw=gzip.decompress((HERE/'original-independent-controls.py.gz').read_bytes())
    digest=hashlib.sha256(raw).hexdigest()
    assert digest=='e6d26dcdbd7935dbb15fcbf7c936969ef732aef61f2e787c9a41a3ddccb5376c'
    module=types.ModuleType('unchanged_independent_controls')
    module.__file__=str(HERE/'original-independent-controls.py')
    exec(compile(raw,module.__file__,'exec'),module.__dict__)
    with (args.output/'independent.stderr.log').open('w') as log:
        result=unittest.TextTestRunner(stream=log,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    (args.output/'replay-witnesses.json').write_text(json.dumps(module.WITNESSES,indent=2,sort_keys=True)+'\n')
    receipt=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                 reviewer_source_sha256=digest,wrapper_sha256=run_acquisition.sha(Path(run_acquisition.__file__)),
                 native_processes=0,real_native_signals=0,scope='Pure mocked replay of unchanged b8ccf8f reviewer source; builder run, not independent approval')
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,sort_keys=True))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
